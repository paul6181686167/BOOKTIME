from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import jwt
import os
import requests
from functools import wraps
import re
import time
from pydantic import BaseModel
from typing import Optional, List
from deep_translator import GoogleTranslator

# Chargement des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="BookTime API", description="Votre bibliothèque personnelle")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
authors_collection = db.authors

# Security
security = HTTPBearer()

# Fonction de traduction automatique pour les résumés
def translate_to_french(text):
    """Traduit automatiquement un texte en français s'il n'est pas déjà en français"""
    if not text or len(text.strip()) < 10:  # Ignorer les textes très courts
        return text
    
    try:
        # Détecter si le texte est déjà en français (méthode simple)
        french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont', 'être', 'avoir', 'qui', 'que', 'dont', 'où']
        text_lower = text.lower()
        french_word_count = sum(1 for word in french_words if f' {word} ' in f' {text_lower} ')
        
        # Si le texte contient déjà beaucoup de mots français, ne pas traduire
        if french_word_count >= 3:
            return text
        
        # Traduire en français
        translator = GoogleTranslator(source='auto', target='fr')
        translated_text = translator.translate(text)
        
        # Vérifier que la traduction a réussi
        if translated_text and len(translated_text) > 0:
            return translated_text
        else:
            return text
            
    except Exception as e:
        print(f"Erreur lors de la traduction: {e}")
        return text  # Retourner le texte original en cas d'erreur

# Modèles Pydantic
class UserAuth(BaseModel):
    first_name: str
    last_name: str

class BookCreate(BaseModel):
    title: str
    author: str
    category: str = "roman"
    description: str = ""
    saga: str = ""
    cover_url: str = ""
    status: str = "to_read"
    rating: Optional[int] = None
    review: str = ""
    publication_year: Optional[int] = None
    isbn: str = ""
    publisher: str = ""
    genre: List[str] = []
    pages: Optional[int] = None
    pages_read: int = 0
    reading_start_date: Optional[str] = None
    reading_end_date: Optional[str] = None

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    saga: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    genre: Optional[List[str]] = None
    pages: Optional[int] = None
    pages_read: Optional[int] = None
    reading_start_date: Optional[str] = None
    reading_end_date: Optional[str] = None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get('sub')
        current_user = users_collection.find_one({"id": current_user_id})
        if not current_user:
            raise HTTPException(status_code=401, detail='User not found!')
        return current_user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired!')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Token is invalid!')

# Fonctions utilitaires pour l'enrichissement des données
def get_openlibrary_work_details(work_key):
    """Récupère les détails d'une œuvre depuis OpenLibrary et traduit les résumés en français"""
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
        
        # Traduire la description si elle existe
        if work_data.get('description'):
            description = work_data['description']
            if isinstance(description, dict):
                description = description.get('value', '')
            
            # Traduire la description en français
            if description:
                work_data['description'] = translate_to_french(description)
        
        # Traduire la première phrase si elle existe
        if work_data.get('first_sentence'):
            first_sentence = work_data['first_sentence']
            if isinstance(first_sentence, dict):
                first_sentence = first_sentence.get('value', '')
            
            # Traduire la première phrase en français
            if first_sentence:
                if isinstance(work_data['first_sentence'], dict):
                    work_data['first_sentence']['value'] = translate_to_french(first_sentence)
                else:
                    work_data['first_sentence'] = translate_to_french(first_sentence)
        
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
@app.get("/")
async def read_root():
    return {"message": "BookTime API - Votre bibliothèque personnelle"}

@app.get("/health")
async def health():
    try:
        # Test de connexion à la base de données
        client.admin.command('ping')
        return {"status": "ok", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Routes d'authentification
@app.post("/api/auth/register")
async def register(user_data: UserAuth):
    # Vérifier si l'utilisateur existe déjà (même prénom et nom)
    existing_user = users_collection.find_one({
        "first_name": user_data.first_name, 
        "last_name": user_data.last_name
    })
    if existing_user:
        raise HTTPException(status_code=400, detail='User with this name already exists')
    
    # Créer le nouvel utilisateur
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user)
    
    # Créer le token d'accès
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        }
    }

@app.post("/api/auth/login")
async def login(user_data: UserAuth):
    # Trouver l'utilisateur
    user = users_collection.find_one({
        "first_name": user_data.first_name, 
        "last_name": user_data.last_name
    })
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    
    # Créer le token d'accès
    access_token = create_access_token(data={"sub": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    }

@app.get("/api/auth/me")
async def get_me(current_user = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"]
    }

# Routes pour les livres
@app.get("/api/books")
async def get_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    # Construire le filtre
    filter_dict = {"user_id": current_user["id"]}
    if category:
        filter_dict["category"] = category
    if status:
        filter_dict["status"] = status
    
    # Récupérer les livres
    books = list(books_collection.find(filter_dict, {"_id": 0}))
    return books

@app.get("/api/books/{book_id}")
async def get_book_details(book_id: str, current_user = Depends(get_current_user)):
    """Récupère les détails complets d'un livre avec enrichissement OpenLibrary"""
    try:
        # Récupérer le livre de base
        book = books_collection.find_one({"id": book_id, "user_id": current_user["id"]}, {"_id": 0})
        if not book:
            raise HTTPException(status_code=404, detail='Book not found')
        
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
                                    'description': translate_to_french(work.get('description', {}).get('value', '') if isinstance(work.get('description'), dict) else work.get('description', '')),
                                    'subjects': work.get('subjects', [])[:10],
                                    'first_sentence': translate_to_french(work.get('first_sentence', {}).get('value', '') if isinstance(work.get('first_sentence'), dict) else ''),
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
        
        return result
        
    except Exception as e:
        print(f"Erreur lors de la récupération des détails du livre: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

@app.post("/api/books")
async def create_book(book_data: BookCreate, current_user = Depends(get_current_user)):
    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": current_user["id"],
        **book_data.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    books_collection.insert_one(book)
    book.pop("_id", None)  # Retirer l'ObjectId de MongoDB
    return book

@app.put("/api/books/{book_id}")
async def update_book(book_id: str, updates: BookUpdate, current_user = Depends(get_current_user)):
    # Vérifier que le livre appartient à l'utilisateur
    book = books_collection.find_one({"id": book_id, "user_id": current_user["id"]})
    if not book:
        raise HTTPException(status_code=404, detail='Book not found')
    
    # Préparer les mises à jour
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Mettre à jour le livre
    books_collection.update_one(
        {"id": book_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    # Retourner le livre mis à jour
    updated_book = books_collection.find_one({"id": book_id}, {"_id": 0})
    return updated_book

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str, current_user = Depends(get_current_user)):
    # Vérifier que le livre appartient à l'utilisateur
    result = books_collection.delete_one({"id": book_id, "user_id": current_user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Book not found')
    
    return {"message": "Book deleted successfully"}

# Routes pour les auteurs
@app.get("/api/authors/{author_name}")
async def get_author_details(author_name: str, current_user = Depends(get_current_user)):
    """Récupère les détails complets d'un auteur avec enrichissement"""
    try:
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
                return cached_author
        
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
            biography = wikipedia_info.get('extract', '')
            # S'assurer que la biographie est en français (elle devrait déjà l'être depuis Wikipedia FR)
            # Mais on peut la nettoyer si nécessaire
            author_info.update({
                'biography': biography,  # Pas besoin de traduire, Wikipedia FR retourne déjà du français
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
        
        return author_info
        
    except Exception as e:
        print(f"Erreur lors de la récupération des détails de l'auteur: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get("/api/authors/{author_name}/books")
async def get_author_books(author_name: str, current_user = Depends(get_current_user)):
    """Récupère tous les livres d'un auteur (utilisateur + OpenLibrary)"""
    try:
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
        
        return {
            'author': author_name,
            'total_books': len(all_books),
            'user_books_count': len(user_books),
            'books': sorted(all_books, key=lambda x: x.get('first_publish_year') or 0, reverse=True)
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération des livres de l'auteur: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

# Route des statistiques
@app.get("/api/stats")
async def get_stats(current_user = Depends(get_current_user)):
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
    
    return {
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
    }

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
@app.get("/api/openlibrary/search")
async def search_openlibrary(q: str, limit: int = 10, current_user = Depends(get_current_user)):
    try:
        # Appel à l'API OpenLibrary
        response = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": q, "limit": limit},
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
        
        return {
            "books": books,
            "total": data.get("numFound", 0)
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f'OpenLibrary service unavailable: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error searching OpenLibrary: {str(e)}')

@app.get("/api/openlibrary/search-universal")
async def search_openlibrary_universal(
    q: str,
    limit: int = 20,
    category: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Recherche universelle dans OpenLibrary avec détection de catégorie et statut utilisateur"""
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
        
        return {
            "books": books,
            "total": data.get("numFound", 0),
            "search_query": q,
            "category_filter": category,
            "results_count": len(books)
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f'OpenLibrary service unavailable: {str(e)}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error in universal search: {str(e)}')

@app.get("/api/openlibrary/book/{work_key}")
async def get_openlibrary_book_details(work_key: str, current_user = Depends(get_current_user)):
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
            raise HTTPException(status_code=404, detail='Book not found')
        
        work = work_details['work']
        editions = work_details['editions']
        
        # Construire les détails du livre
        book_data = {
            "work_key": clean_work_key,
            "title": work.get('title', ''),
            "description": translate_to_french(work.get('description', {}).get('value', '') if isinstance(work.get('description'), dict) else work.get('description', '')),
            "subjects": work.get('subjects', [])[:15],
            "first_sentence": translate_to_french(work.get('first_sentence', {}).get('value', '') if isinstance(work.get('first_sentence'), dict) else ''),
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
            book_data['editions'].append(edition_data)
        
        # Détection automatique de catégorie
        book_data["category"] = detect_category_from_subjects(book_data["subjects"])
        
        # Vérifier si le livre est dans la bibliothèque de l'utilisateur
        existing_book = check_book_in_user_library(current_user, book_data)
        book_data["in_user_library"] = existing_book is not None
        if existing_book:
            book_data["user_book_id"] = existing_book.get("id")
            book_data["user_status"] = existing_book.get("status")
            book_data["user_rating"] = existing_book.get("rating")
        
        # Prendre les infos de la première édition pour les détails basiques
        if book_data["editions"]:
            first_edition = book_data["editions"][0]
            book_data["isbn"] = first_edition["isbn_13"][0] if first_edition["isbn_13"] else (first_edition["isbn_10"][0] if first_edition["isbn_10"] else None)
            book_data["publisher"] = ", ".join(first_edition["publishers"][:2])
            book_data["pages"] = first_edition["number_of_pages"]
            book_data["publication_year"] = first_edition.get("publish_date", "").split()[-1] if first_edition.get("publish_date") else None
            
            # URL de couverture
            if first_edition["covers"]:
                book_data["cover_url"] = f"https://covers.openlibrary.org/b/id/{first_edition['covers'][0]}-L.jpg"
        
        # Prendre le premier auteur comme auteur principal
        if book_data["authors"]:
            book_data["author"] = book_data["authors"][0]["name"]
        
        return book_data
        
    except Exception as e:
        print(f"Erreur lors de la récupération des détails du livre OpenLibrary: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)