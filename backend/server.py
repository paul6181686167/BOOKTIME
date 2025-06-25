from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import bcrypt
import jwt
import os
import requests
from functools import wraps

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

# Fonctions utilitaires
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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

# Route de recherche OpenLibrary
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)