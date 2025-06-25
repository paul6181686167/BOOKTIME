from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import jwt
import os
import requests
from functools import wraps
import re
import time

# Chargement des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Client MongoDB
client = MongoClient(MONGO_URL)
db = client.booktime
users_collection = db.users
books_collection = db.books
authors_collection = db.authors  # Nouvelle collection pour le cache des auteurs

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Token format invalid!'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user_id = payload.get('sub')
            current_user = users_collection.find_one({"id": current_user_id})
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Fonctions utilitaires pour l'enrichissement des données
def get_openlibrary_work_details(work_key):
    """Récupère les détails d'une œuvre depuis OpenLibrary"""
    try:
        if not work_key:
            return None
            
        # Nettoyer la clé work
        if work_key.startswith('/works/'):
            work_key = work_key[7:]
        elif work_key.startswith('OL') and work_key.endswith('W'):
            pass  # Déjà au bon format
        else:
            return None
            
        work_url = f"https://openlibrary.org/works/{work_key}.json"
        response = requests.get(work_url, timeout=10)
        response.raise_for_status()
        
        work_data = response.json()
        
        # Récupérer aussi les éditions pour plus d'infos
        editions_url = f"https://openlibrary.org/works/{work_key}/editions.json"
        editions_response = requests.get(editions_url, timeout=10)
        editions_data = editions_response.json() if editions_response.ok else {"entries": []}
        
        return {
            "work": work_data,
            "editions": editions_data.get("entries", [])[:5]  # Limiter à 5 éditions
        }
    except Exception as e:
        print(f"Erreur lors de la récupération des détails OpenLibrary: {e}")
        return None

def get_wikipedia_author_info(author_name):
    """Récupère les informations biographiques d'un auteur depuis Wikipedia"""
    try:
        # Recherche de la page Wikipedia
        search_url = "https://fr.wikipedia.org/api/rest_v1/page/summary/" + author_name.replace(" ", "_")
        response = requests.get(search_url, timeout=10)
        
        if not response.ok:
            # Essayer avec l'API de recherche
            search_api_url = "https://fr.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": author_name,
                "srlimit": 1
            }
            search_response = requests.get(search_api_url, params=search_params, timeout=10)
            search_data = search_response.json()
            
            if search_data.get("query", {}).get("search"):
                page_title = search_data["query"]["search"][0]["title"]
                summary_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
                response = requests.get(summary_url, timeout=10)
        
        if response.ok:
            data = response.json()
            return {
                "title": data.get("title", ""),
                "extract": data.get("extract", ""),
                "thumbnail": data.get("thumbnail", {}).get("source", "") if data.get("thumbnail") else "",
                "birth_date": None,  # Pourrait être extrait avec plus de travail
                "death_date": None,
                "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
    except Exception as e:
        print(f"Erreur lors de la récupération des infos Wikipedia: {e}")
    
    return None

def get_author_books_from_openlibrary(author_name):
    """Récupère tous les livres d'un auteur depuis OpenLibrary"""
    try:
        # Rechercher les œuvres de l'auteur
        search_url = "https://openlibrary.org/search.json"
        params = {
            "author": author_name,
            "limit": 50,
            "fields": "key,title,first_publish_year,cover_i,isbn,publisher,subject,language"
        }
        
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get("docs", []):
            book = {
                "title": item.get("title", ""),
                "first_publish_year": item.get("first_publish_year"),
                "cover_id": item.get("cover_i"),
                "isbn": item.get("isbn", [None])[0] if item.get("isbn") else None,
                "publisher": ", ".join(item.get("publisher", [])),
                "subjects": item.get("subject", [])[:5],  # Limiter à 5 sujets
                "languages": item.get("language", []),
                "openlibrary_key": item.get("key", "")
            }
            
            # Construire l'URL de la couverture si disponible
            if book["cover_id"]:
                book["cover_url"] = f"https://covers.openlibrary.org/b/id/{book['cover_id']}-M.jpg"
            
            books.append(book)
        
        return sorted(books, key=lambda x: x.get("first_publish_year") or 0, reverse=True)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des livres de l'auteur: {e}")
        return []

# Routes de base
@app.route('/')
def read_root():
    return jsonify({"message": "BookTime API - Votre bibliothèque personnelle"})

@app.route('/health')
def health():
    try:
        # Test de connexion à la base de données
        client.admin.command('ping')
        return jsonify({"status": "ok", "database": "connected", "timestamp": datetime.utcnow().isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database connection error: {str(e)}"}), 500

# Routes d'authentification
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validation des données
    if not data or not all(k in data for k in ('first_name', 'last_name')):
        return jsonify({'error': 'Missing required fields (first_name, last_name)'}), 400
    
    # Vérifier si l'utilisateur existe déjà (même prénom et nom)
    existing_user = users_collection.find_one({
        "first_name": data['first_name'], 
        "last_name": data['last_name']
    })
    if existing_user:
        return jsonify({'error': 'User with this name already exists'}), 400
    
    # Créer le nouvel utilisateur
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user)
    
    # Créer le token d'accès
    access_token = create_access_token(data={"sub": user_id})
    
    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "first_name": data['first_name'],
            "last_name": data['last_name']
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validation des données
    if not data or not all(k in data for k in ('first_name', 'last_name')):
        return jsonify({'error': 'Missing first_name or last_name'}), 400
    
    # Trouver l'utilisateur
    user = users_collection.find_one({
        "first_name": data['first_name'], 
        "last_name": data['last_name']
    })
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    # Créer le token d'accès
    access_token = create_access_token(data={"sub": user["id"]})
    
    return jsonify({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    })

@app.route('/api/auth/me')
@token_required
def get_me(current_user):
    return jsonify({
        "id": current_user["id"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"]
    })

# Routes pour les livres
@app.route('/api/books', methods=['GET'])
@token_required
def get_books(current_user):
    # Récupérer les paramètres de filtre
    category = request.args.get('category')
    status = request.args.get('status')
    
    # Construire le filtre
    filter_dict = {"user_id": current_user["id"]}
    if category:
        filter_dict["category"] = category
    if status:
        filter_dict["status"] = status
    
    # Récupérer les livres
    books = list(books_collection.find(filter_dict, {"_id": 0}))
    return jsonify(books)

@app.route('/api/books/<book_id>', methods=['GET'])
@token_required
def get_book_details(current_user, book_id):
    """Récupère les détails complets d'un livre avec enrichissement OpenLibrary"""
    try:
        # Récupérer le livre de base
        book = books_collection.find_one({"id": book_id, "user_id": current_user["id"]}, {"_id": 0})
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        # Chercher des informations enrichies via OpenLibrary si on a un ISBN ou titre+auteur
        enriched_data = {}
        
        if book.get('isbn'):
            # Recherche par ISBN
            try:
                search_url = f"https://openlibrary.org/search.json?isbn={book['isbn']}&limit=1"
                response = requests.get(search_url, timeout=10)
                if response.ok:
                    search_data = response.json()
                    if search_data.get('docs'):
                        doc = search_data['docs'][0]
                        work_key = doc.get('key', '').replace('/works/', '') if doc.get('key') else None
                        
                        if work_key:
                            work_details = get_openlibrary_work_details(work_key)
                            if work_details:
                                work = work_details['work']
                                editions = work_details['editions']
                                
                                enriched_data = {
                                    'description': work.get('description', {}).get('value', '') if isinstance(work.get('description'), dict) else work.get('description', ''),
                                    'subjects': work.get('subjects', [])[:10],
                                    'first_sentence': work.get('first_sentence', {}).get('value', '') if isinstance(work.get('first_sentence'), dict) else '',
                                    'work_key': work_key,
                                    'openlibrary_url': f"https://openlibrary.org/works/{work_key}",
                                    'editions_info': []
                                }
                                
                                # Informations des éditions
                                for edition in editions:
                                    edition_info = {
                                        'title': edition.get('title', ''),
                                        'publish_date': edition.get('publish_date', ''),
                                        'publishers': edition.get('publishers', []),
                                        'number_of_pages': edition.get('number_of_pages'),
                                        'languages': [lang.get('key', '').replace('/languages/', '') for lang in edition.get('languages', [])],
                                        'isbn_10': edition.get('isbn_10', []),
                                        'isbn_13': edition.get('isbn_13', [])
                                    }
                                    enriched_data['editions_info'].append(edition_info)
            except Exception as e:
                print(f"Erreur enrichissement par ISBN: {e}")
        
        # Si pas d'enrichissement par ISBN, essayer par titre/auteur
        if not enriched_data and book.get('title') and book.get('author'):
            try:
                search_query = f"{book['title']} {book['author']}"
                search_url = f"https://openlibrary.org/search.json?q={requests.utils.quote(search_query)}&limit=1"
                response = requests.get(search_url, timeout=10)
                if response.ok:
                    search_data = response.json()
                    if search_data.get('docs'):
                        doc = search_data['docs'][0]
                        # Vérifier que c'est bien le bon livre (titre similaire)
                        if doc.get('title', '').lower() in book['title'].lower() or book['title'].lower() in doc.get('title', '').lower():
                            enriched_data = {
                                'subjects': doc.get('subject', [])[:10],
                                'first_publish_year': doc.get('first_publish_year'),
                                'publishers': doc.get('publisher', [])[:5],
                                'languages': doc.get('language', [])[:3],
                                'cover_id': doc.get('cover_i'),
                                'openlibrary_key': doc.get('key', '')
                            }
                            
                            if enriched_data['cover_id']:
                                enriched_data['cover_url_large'] = f"https://covers.openlibrary.org/b/id/{enriched_data['cover_id']}-L.jpg"
            except Exception as e:
                print(f"Erreur enrichissement par titre/auteur: {e}")
        
        # Combiner les données
        result = {
            **book,
            'enriched_data': enriched_data,
            'last_enriched': datetime.utcnow().isoformat()
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des détails du livre: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/books', methods=['POST'])
@token_required
def create_book(current_user):
    data = request.get_json()
    
    # Validation des données essentielles
    if not data or not all(k in data for k in ('title', 'author')):
        return jsonify({'error': 'Missing title or author'}), 400
    
    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": current_user["id"],
        "title": data['title'],
        "author": data['author'],
        "category": data.get('category', 'roman'),
        "description": data.get('description', ''),
        "saga": data.get('saga', ''),
        "cover_url": data.get('cover_url', ''),
        "status": data.get('status', 'to_read'),
        "rating": data.get('rating'),
        "review": data.get('review', ''),
        "publication_year": data.get('publication_year'),
        "isbn": data.get('isbn', ''),
        "publisher": data.get('publisher', ''),
        "genre": data.get('genre', []),
        "pages": data.get('pages'),
        "pages_read": data.get('pages_read', 0),
        "reading_start_date": data.get('reading_start_date'),
        "reading_end_date": data.get('reading_end_date'),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    books_collection.insert_one(book)
    book.pop("_id", None)  # Retirer l'ObjectId de MongoDB
    return jsonify(book), 201

@app.route('/api/books/<book_id>', methods=['PUT'])
@token_required
def update_book(current_user, book_id):
    data = request.get_json()
    
    # Vérifier que le livre appartient à l'utilisateur
    book = books_collection.find_one({"id": book_id, "user_id": current_user["id"]})
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    
    # Préparer les mises à jour
    update_data = {k: v for k, v in data.items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Mettre à jour le livre
    books_collection.update_one(
        {"id": book_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    # Retourner le livre mis à jour
    updated_book = books_collection.find_one({"id": book_id}, {"_id": 0})
    return jsonify(updated_book)

@app.route('/api/books/<book_id>', methods=['DELETE'])
@token_required
def delete_book(current_user, book_id):
    # Vérifier que le livre appartient à l'utilisateur
    result = books_collection.delete_one({"id": book_id, "user_id": current_user["id"]})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Book not found'}), 404
    
    return jsonify({"message": "Book deleted successfully"})

# Routes pour les auteurs
@app.route('/api/authors/<author_name>', methods=['GET'])
@token_required
def get_author_details(current_user, author_name):
    """Récupère les détails complets d'un auteur avec enrichissement"""
    try:
        # Décoder le nom de l'auteur de l'URL
        author_name = requests.utils.unquote(author_name)
        
        # Vérifier le cache d'abord
        cached_author = authors_collection.find_one({"name": author_name})
        if cached_author and cached_author.get('last_updated'):
            # Vérifier si le cache est encore valide (24h)
            last_updated = cached_author['last_updated']
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            
            if (datetime.utcnow() - last_updated.replace(tzinfo=None)).total_seconds() < 86400:  # 24h
                # Ajouter les statistiques utilisateur
                user_books = list(books_collection.find({"user_id": current_user["id"], "author": author_name}, {"_id": 0}))
                cached_author['user_stats'] = {
                    'books_read': len([b for b in user_books if b.get('status') == 'completed']),
                    'books_reading': len([b for b in user_books if b.get('status') == 'reading']),
                    'books_to_read': len([b for b in user_books if b.get('status') == 'to_read']),
                    'total_user_books': len(user_books),
                    'user_books': user_books
                }
                cached_author.pop('_id', None)
                return jsonify(cached_author)
        
        # Récupérer les informations depuis les APIs externes
        author_info = {
            'name': author_name,
            'biography': '',
            'photo_url': '',
            'birth_date': None,
            'death_date': None,
            'wikipedia_url': '',
            'bibliography': [],
            'last_updated': datetime.utcnow()
        }
        
        # Récupérer les infos Wikipedia
        wikipedia_info = get_wikipedia_author_info(author_name)
        if wikipedia_info:
            author_info.update({
                'biography': wikipedia_info.get('extract', ''),
                'photo_url': wikipedia_info.get('thumbnail', ''),
                'wikipedia_url': wikipedia_info.get('wikipedia_url', ''),
                'birth_date': wikipedia_info.get('birth_date'),
                'death_date': wikipedia_info.get('death_date')
            })
        
        # Récupérer la bibliographie depuis OpenLibrary
        openlibrary_books = get_author_books_from_openlibrary(author_name)
        author_info['bibliography'] = openlibrary_books
        
        # Sauvegarder en cache
        authors_collection.replace_one(
            {"name": author_name},
            author_info,
            upsert=True
        )
        
        # Ajouter les statistiques utilisateur
        user_books = list(books_collection.find({"user_id": current_user["id"], "author": author_name}, {"_id": 0}))
        author_info['user_stats'] = {
            'books_read': len([b for b in user_books if b.get('status') == 'completed']),
            'books_reading': len([b for b in user_books if b.get('status') == 'reading']),
            'books_to_read': len([b for b in user_books if b.get('status') == 'to_read']),
            'total_user_books': len(user_books),
            'user_books': user_books
        }
        
        return jsonify(author_info)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des détails de l'auteur: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/authors/<author_name>/books', methods=['GET'])
@token_required
def get_author_books(current_user, author_name):
    """Récupère tous les livres d'un auteur (utilisateur + OpenLibrary)"""
    try:
        author_name = requests.utils.unquote(author_name)
        
        # Livres de l'utilisateur
        user_books = list(books_collection.find({"user_id": current_user["id"], "author": author_name}, {"_id": 0}))
        
        # Bibliographie complète depuis OpenLibrary
        openlibrary_books = get_author_books_from_openlibrary(author_name)
        
        # Combiner et marquer les livres lus
        all_books = []
        user_titles = {book['title'].lower() for book in user_books}
        
        for ol_book in openlibrary_books:
            # Vérifier si l'utilisateur a ce livre
            user_book = next((ub for ub in user_books if ub['title'].lower() == ol_book['title'].lower()), None)
            
            book_data = {
                **ol_book,
                'in_user_library': user_book is not None,
                'user_status': user_book.get('status') if user_book else None,
                'user_rating': user_book.get('rating') if user_book else None,
                'user_book_id': user_book.get('id') if user_book else None
            }
            all_books.append(book_data)
        
        # Ajouter les livres de l'utilisateur qui ne sont pas dans OpenLibrary
        for user_book in user_books:
            if user_book['title'].lower() not in {book['title'].lower() for book in all_books}:
                all_books.append({
                    **user_book,
                    'in_user_library': True,
                    'user_status': user_book.get('status'),
                    'user_rating': user_book.get('rating'),
                    'user_book_id': user_book.get('id'),
                    'from_user_library': True
                })
        
        return jsonify({
            'author': author_name,
            'total_books': len(all_books),
            'user_books_count': len(user_books),
            'books': sorted(all_books, key=lambda x: x.get('first_publish_year') or 0, reverse=True)
        })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des livres de l'auteur: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Route des statistiques
@app.route('/api/stats')
@token_required
def get_stats(current_user):
    user_id = current_user["id"]
    
    # Statistiques de base
    total_books = books_collection.count_documents({"user_id": user_id})
    completed_books = books_collection.count_documents({"user_id": user_id, "status": "completed"})
    reading_books = books_collection.count_documents({"user_id": user_id, "status": "reading"})
    to_read_books = books_collection.count_documents({"user_id": user_id, "status": "to_read"})
    
    # Statistiques par catégorie
    categories = books_collection.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ])
    categories_dict = {cat["_id"]: cat["count"] for cat in categories}
    
    # Compter les auteurs uniques
    authors = books_collection.distinct("author", {"user_id": user_id})
    authors_count = len(authors)
    
    # Compter les sagas uniques (non vides)
    sagas = books_collection.distinct("saga", {"user_id": user_id, "saga": {"$ne": ""}})
    sagas_count = len(sagas)
    
    return jsonify({
        "total_books": total_books,
        "completed_books": completed_books,
        "reading_books": reading_books,
        "to_read_books": to_read_books,
        "categories": {
            "roman": categories_dict.get("roman", 0),
            "bd": categories_dict.get("bd", 0),
            "manga": categories_dict.get("manga", 0)
        },
        "authors_count": authors_count,
        "sagas_count": sagas_count
    })

# Fonctions utilitaires pour l'intégration OpenLibrary universelle
def detect_category_from_subjects(subjects):
    """Détecte automatiquement la catégorie d'un livre à partir de ses sujets"""
    if not subjects:
        return 'roman'
    
    subjects_lower = [s.lower() for s in subjects]
    
    # Mots-clés pour BD/Comics
    bd_keywords = ['comic', 'comics', 'graphic novel', 'bande dessinée', 'bd', 'manga', 'strip', 'cartoon']
    if any(keyword in ' '.join(subjects_lower) for keyword in bd_keywords):
        # Distinguer manga des autres BD
        manga_keywords = ['manga', 'japanese', 'anime', 'japan']
        if any(keyword in ' '.join(subjects_lower) for keyword in manga_keywords):
            return 'manga'
        return 'bd'
    
    # Mots-clés pour manga spécifiques
    manga_keywords = ['manga', 'japanese comics', 'anime', 'light novel']
    if any(keyword in ' '.join(subjects_lower) for keyword in manga_keywords):
        return 'manga'
    
    # Par défaut : roman
    return 'roman'

def check_book_in_user_library(current_user, book_data):
    """Vérifie si un livre OpenLibrary est déjà dans la bibliothèque de l'utilisateur"""
    title = book_data.get('title', '').lower()
    author = book_data.get('author', '').lower()
    isbn = book_data.get('isbn')
    
    # Recherche par ISBN d'abord
    if isbn:
        existing = books_collection.find_one({
            "user_id": current_user["id"],
            "isbn": isbn
        })
        if existing:
            return existing
    
    # Recherche par titre + auteur
    if title and author:
        existing = books_collection.find_one({
            "user_id": current_user["id"],
            "$and": [
                {"title": {"$regex": re.escape(title), "$options": "i"}},
                {"author": {"$regex": re.escape(author), "$options": "i"}}
            ]
        })
        if existing:
            return existing
    
    return None

# Routes OpenLibrary universelles

# Route de recherche OpenLibrary (maintenue pour compatibilité)
@app.route('/api/openlibrary/search')
@token_required
def search_openlibrary(current_user):
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'Missing search query'}), 400
    
    try:
        # Appel à l'API OpenLibrary
        response = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": q, "limit": 10},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get("docs", []):
            book = {
                "title": item.get("title", ""),
                "author": ", ".join(item.get("author_name", [])),
                "first_publish_year": item.get("first_publish_year"),
                "isbn": item.get("isbn", [None])[0] if item.get("isbn") else None,
                "cover_id": item.get("cover_i"),
                "publisher": ", ".join(item.get("publisher", [])),
                "subject": item.get("subject", [])[:5]  # Limiter à 5 sujets
            }
            
            # Construire l'URL de la couverture si disponible
            if book["cover_id"]:
                book["cover_url"] = f"https://covers.openlibrary.org/b/id/{book['cover_id']}-M.jpg"
            
            books.append(book)
        
        return jsonify({
            "books": books,
            "total": data.get("numFound", 0)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'OpenLibrary service unavailable: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Error searching OpenLibrary: {str(e)}'}), 500

@app.route('/api/openlibrary/search-universal')
@token_required
def search_openlibrary_universal(current_user):
    """Recherche universelle dans OpenLibrary avec détection de catégorie et statut utilisateur"""
    q = request.args.get('q')
    limit = int(request.args.get('limit', 20))
    category = request.args.get('category')  # Filtre optionnel par catégorie
    
    if not q:
        return jsonify({'error': 'Missing search query'}), 400
    
    try:
        # Appel à l'API OpenLibrary avec plus de détails
        params = {
            "q": q,
            "limit": min(limit, 50),  # Limiter à 50 max
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,publisher,subject,language,number_of_pages_median"
        }
        
        response = requests.get(
            "https://openlibrary.org/search.json",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get("docs", []):
            # Données de base
            book_data = {
                "title": item.get("title", ""),
                "author": ", ".join(item.get("author_name", [])) if item.get("author_name") else "Auteur inconnu",
                "first_publish_year": item.get("first_publish_year"),
                "isbn": item.get("isbn", [None])[0] if item.get("isbn") else None,
                "cover_id": item.get("cover_i"),
                "publisher": ", ".join(item.get("publisher", [])[:3]) if item.get("publisher") else "",
                "subjects": item.get("subject", [])[:8],
                "languages": item.get("language", [])[:3],
                "pages": item.get("number_of_pages_median"),
                "work_key": item.get("key", "").replace("/works/", "") if item.get("key") else None
            }
            
            # Détection automatique de catégorie
            detected_category = detect_category_from_subjects(book_data["subjects"])
            book_data["category"] = detected_category
            
            # Filtrer par catégorie si demandé
            if category and detected_category != category:
                continue
            
            # URLs de couverture
            if book_data["cover_id"]:
                book_data["cover_url"] = f"https://covers.openlibrary.org/b/id/{book_data['cover_id']}-M.jpg"
                book_data["cover_url_large"] = f"https://covers.openlibrary.org/b/id/{book_data['cover_id']}-L.jpg"
            
            # Vérifier si le livre est dans la bibliothèque de l'utilisateur
            existing_book = check_book_in_user_library(current_user, book_data)
            book_data["in_user_library"] = existing_book is not None
            if existing_book:
                book_data["user_book_id"] = existing_book.get("id")
                book_data["user_status"] = existing_book.get("status")
                book_data["user_rating"] = existing_book.get("rating")
            
            books.append(book_data)
        
        return jsonify({
            "books": books,
            "total": data.get("numFound", 0),
            "search_query": q,
            "category_filter": category,
            "results_count": len(books)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'OpenLibrary service unavailable: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Error in universal search: {str(e)}'}), 500

@app.route('/api/openlibrary/book/<work_key>')
@token_required
def get_openlibrary_book_details(current_user, work_key):
    """Récupère les détails complets d'un livre OpenLibrary par sa clé work"""
    try:
        # Nettoyer la clé work
        if work_key.startswith('OL') and work_key.endswith('W'):
            clean_work_key = work_key
        else:
            clean_work_key = f"OL{work_key}W" if not work_key.startswith('OL') else work_key
        
        # Récupérer les détails de l'œuvre
        work_details = get_openlibrary_work_details(clean_work_key)
        if not work_details:
            return jsonify({'error': 'Book not found'}), 404
        
        work = work_details['work']
        editions = work_details['editions']
        
        # Construire les détails du livre
        book_data = {
            "work_key": clean_work_key,
            "title": work.get('title', ''),
            "description": work.get('description', {}).get('value', '') if isinstance(work.get('description'), dict) else work.get('description', ''),
            "subjects": work.get('subjects', [])[:15],
            "first_sentence": work.get('first_sentence', {}).get('value', '') if isinstance(work.get('first_sentence'), dict) else '',
            "authors": [],
            "editions": [],
            "category": "roman",  # Par défaut
            "openlibrary_url": f"https://openlibrary.org/works/{clean_work_key}"
        }
        
        # Récupérer les informations des auteurs
        if work.get('authors'):
            for author_ref in work['authors'][:5]:  # Limiter à 5 auteurs
                if isinstance(author_ref, dict) and author_ref.get('author'):
                    author_key = author_ref['author']['key'].replace('/authors/', '')
                    try:
                        author_response = requests.get(f"https://openlibrary.org/authors/{author_key}.json", timeout=10)
                        if author_response.ok:
                            author_data = author_response.json()
                            book_data['authors'].append({
                                "name": author_data.get('name', ''),
                                "key": author_key,
                                "bio": author_data.get('bio', {}).get('value', '') if isinstance(author_data.get('bio'), dict) else author_data.get('bio', ''),
                                "birth_date": author_data.get('birth_date', ''),
                                "death_date": author_data.get('death_date', '')
                            })
                    except:
                        continue
        
        # Récupérer les détails des meilleures éditions
        for edition in editions:
            edition_data = {
                "title": edition.get('title', ''),
                "isbn_10": edition.get('isbn_10', []),
                "isbn_13": edition.get('isbn_13', []),
                "publish_date": edition.get('publish_date', ''),
                "publishers": edition.get('publishers', []),
                "number_of_pages": edition.get('number_of_pages'),
                "languages": [lang.get('key', '').replace('/languages/', '') for lang in edition.get('languages', [])],
                "covers": edition.get('covers', [])
            }
            
            # URL de couverture pour cette édition
            if edition_data['covers']:
                edition_data['cover_url'] = f"https://covers.openlibrary.org/b/id/{edition_data['covers'][0]}-L.jpg"
            
            book_data['editions'].append(edition_data)
        
        # Détection de catégorie
        book_data["category"] = detect_category_from_subjects(book_data["subjects"])
        
        # Informations pratiques (de la première édition avec des infos)
        if book_data['editions']:
            best_edition = book_data['editions'][0]
            book_data["author"] = ", ".join([author['name'] for author in book_data['authors']])
            book_data["publication_year"] = None
            book_data["publisher"] = ", ".join(best_edition['publishers'][:2]) if best_edition['publishers'] else ""
            book_data["pages"] = best_edition['number_of_pages']
            book_data["isbn"] = (best_edition['isbn_13'] or best_edition['isbn_10'] or [None])[0]
            book_data["languages"] = best_edition['languages']
            
            # Extraire l'année de publication
            if best_edition['publish_date']:
                try:
                    import re
                    year_match = re.search(r'\b(19|20)\d{2}\b', best_edition['publish_date'])
                    if year_match:
                        book_data["publication_year"] = int(year_match.group())
                except:
                    pass
            
            # URL de couverture principale
            if best_edition.get('cover_url'):
                book_data["cover_url"] = best_edition['cover_url']
                book_data["cover_url_medium"] = best_edition['cover_url'].replace('-L.jpg', '-M.jpg')
        
        # Vérifier si le livre est dans la bibliothèque de l'utilisateur
        existing_book = check_book_in_user_library(current_user, book_data)
        book_data["in_user_library"] = existing_book is not None
        if existing_book:
            book_data["user_book_id"] = existing_book.get("id")
            book_data["user_status"] = existing_book.get("status")
            book_data["user_rating"] = existing_book.get("rating")
            book_data["user_review"] = existing_book.get("review", "")
        
        return jsonify(book_data)
        
    except Exception as e:
        print(f"Erreur lors de la récupération du livre OpenLibrary: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/openlibrary/author/<author_name>')
@token_required  
def get_openlibrary_author_universal(current_user, author_name):
    """Récupère les détails universels d'un auteur depuis OpenLibrary (différent de /api/authors/)"""
    try:
        # Décoder le nom de l'auteur
        author_name = requests.utils.unquote(author_name)
        
        # Vérifier le cache d'abord (utiliser une collection séparée pour les auteurs universels)
        cached_author = authors_collection.find_one({"name": author_name, "source": "openlibrary_universal"})
        if cached_author and cached_author.get('last_updated'):
            # Vérifier si le cache est encore valide (6h pour les données universelles)
            last_updated = cached_author['last_updated']
            if isinstance(last_updated, str):
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            
            if (datetime.utcnow() - last_updated.replace(tzinfo=None)).total_seconds() < 21600:  # 6h
                # Ajouter les statistiques utilisateur
                cached_author = add_user_stats_to_author(current_user, cached_author, author_name)
                cached_author.pop('_id', None)
                return jsonify(cached_author)
        
        # Récupérer les informations depuis OpenLibrary et Wikipedia
        author_info = {
            'name': author_name,
            'biography': '',
            'photo_url': '',
            'birth_date': None,
            'death_date': None,
            'wikipedia_url': '',
            'openlibrary_author_key': None,
            'bibliography': [],
            'source': 'openlibrary_universal',
            'last_updated': datetime.utcnow()
        }
        
        # Rechercher l'auteur sur OpenLibrary d'abord
        try:
            search_url = "https://openlibrary.org/search/authors.json"
            params = {"q": author_name, "limit": 5}
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.ok:
                search_data = response.json()
                docs = search_data.get('docs', [])
                
                # Trouver le meilleur match
                best_match = None
                for doc in docs:
                    doc_name = doc.get('name', '').lower()
                    if doc_name == author_name.lower():
                        best_match = doc
                        break
                    elif author_name.lower() in doc_name or doc_name in author_name.lower():
                        if not best_match:
                            best_match = doc
                
                if best_match:
                    author_key = best_match['key']
                    author_info['openlibrary_author_key'] = author_key
                    
                    # Récupérer les détails complets de l'auteur
                    author_detail_response = requests.get(f"https://openlibrary.org{author_key}.json", timeout=10)
                    if author_detail_response.ok:
                        author_detail = author_detail_response.json()
                        
                        # Extraire les informations
                        if author_detail.get('bio'):
                            bio = author_detail['bio']
                            if isinstance(bio, dict):
                                author_info['biography'] = bio.get('value', '')
                            else:
                                author_info['biography'] = str(bio)
                        
                        author_info['birth_date'] = author_detail.get('birth_date', '')
                        author_info['death_date'] = author_detail.get('death_date', '')
                        
                        # Photo depuis OpenLibrary
                        if author_detail.get('photos'):
                            photo_id = author_detail['photos'][0]
                            author_info['photo_url'] = f"https://covers.openlibrary.org/a/id/{photo_id}-L.jpg"
        except Exception as e:
            print(f"Erreur OpenLibrary author search: {e}")
        
        # Récupérer les infos Wikipedia (complément ou alternative)
        wikipedia_info = get_wikipedia_author_info(author_name)
        if wikipedia_info:
            # Compléter avec Wikipedia si pas d'infos OpenLibrary
            if not author_info['biography']:
                author_info['biography'] = wikipedia_info.get('extract', '')
            if not author_info['photo_url']:
                author_info['photo_url'] = wikipedia_info.get('thumbnail', '')
            author_info['wikipedia_url'] = wikipedia_info.get('wikipedia_url', '')
        
        # Récupérer la bibliographie depuis OpenLibrary
        openlibrary_books = get_author_books_from_openlibrary(author_name)
        
        # Enrichir chaque livre avec le statut utilisateur
        for book in openlibrary_books:
            existing_book = check_book_in_user_library(current_user, book)
            book['in_user_library'] = existing_book is not None
            if existing_book:
                book['user_book_id'] = existing_book.get('id')
                book['user_status'] = existing_book.get('status')
                book['user_rating'] = existing_book.get('rating')
            
            # Détecter la catégorie
            book['category'] = detect_category_from_subjects(book.get('subjects', []))
        
        author_info['bibliography'] = openlibrary_books
        
        # Sauvegarder en cache
        authors_collection.replace_one(
            {"name": author_name, "source": "openlibrary_universal"},
            author_info,
            upsert=True
        )
        
        # Ajouter les statistiques utilisateur
        author_info = add_user_stats_to_author(current_user, author_info, author_name)
        
        return jsonify(author_info)
        
    except Exception as e:
        print(f"Erreur lors de la récupération de l'auteur OpenLibrary: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def add_user_stats_to_author(current_user, author_info, author_name):
    """Ajoute les statistiques utilisateur aux informations de l'auteur"""
    # Livres de l'utilisateur pour cet auteur
    user_books = list(books_collection.find({"user_id": current_user["id"], "author": author_name}, {"_id": 0}))
    
    # Statistiques depuis la bibliographie complète
    bibliography = author_info.get('bibliography', [])
    user_books_in_bibliography = [book for book in bibliography if book.get('in_user_library')]
    
    author_info['user_stats'] = {
        'books_read': len([b for b in user_books_in_bibliography if b.get('user_status') == 'completed']),
        'books_reading': len([b for b in user_books_in_bibliography if b.get('user_status') == 'reading']),
        'books_to_read': len([b for b in user_books_in_bibliography if b.get('user_status') == 'to_read']),
        'total_user_books': len(user_books_in_bibliography),
        'total_bibliography': len(bibliography),
        'completion_percentage': round((len(user_books_in_bibliography) / len(bibliography)) * 100, 1) if bibliography else 0,
        'user_books': user_books
    }
    
    return author_info

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)