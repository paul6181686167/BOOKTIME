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

# Chargement des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="BookTime API", description="Votre bibliothèque personnelle")

# Configuration CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
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

# Modèles Pydantic
class UserAuth(BaseModel):
    first_name: str
    last_name: str

class BookCreate(BaseModel):
    title: str
    author: str
    category: str = "roman"
    description: str = ""
    total_pages: Optional[int] = None
    status: str = "to_read"
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: str = ""
    cover_url: str = ""
    saga: str = ""
    volume_number: Optional[int] = None
    genre: str = ""
    publication_year: Optional[int] = None
    publisher: str = ""
    isbn: str = ""
    auto_added: bool = False

class BookUpdate(BaseModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    description: Optional[str] = None
    total_pages: Optional[int] = None

# Functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        user = users_collection.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def validate_category(category: str) -> str:
    valid_categories = ["roman", "bd", "manga"]
    category_lower = category.lower()
    if category_lower not in valid_categories:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}"
        )
    return category_lower

# Open Library functions
def search_open_library_books(query: str, limit: int = 10, language: str = None, year_start: int = None, year_end: int = None, min_pages: int = None, max_pages: int = None, author_filter: str = None):
    """Rechercher des livres sur Open Library avec filtres avancés"""
    try:
        base_url = "https://openlibrary.org/search.json"
        params = {
            "q": query,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,publisher,number_of_pages,cover_i,subject"
        }
        
        # Filtres avancés
        if language:
            params["language"] = language
        if author_filter:
            params["author"] = author_filter
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for book_data in data.get("docs", []):
            # Filtres côté client
            if year_start and book_data.get("first_publish_year", 0) < year_start:
                continue
            if year_end and book_data.get("first_publish_year", 9999) > year_end:
                continue
            if min_pages and book_data.get("number_of_pages", 0) < min_pages:
                continue
            if max_pages and book_data.get("number_of_pages", 9999) > max_pages:
                continue
            
            book = map_open_library_book(book_data)
            books.append(book)
        
        return books
    except Exception as e:
        print(f"Erreur lors de la recherche Open Library: {e}")
        return []

def map_open_library_book(book_data):
    """Mapper les données d'Open Library vers notre format"""
    authors = book_data.get("author_name", ["Auteur inconnu"])
    if isinstance(authors, list):
        author = authors[0] if authors else "Auteur inconnu"
    else:
        author = authors
    
    # Déterminer la catégorie automatiquement
    category = detect_category_from_subjects(book_data.get("subject", []))
    
    # Formater l'ISBN
    isbn = ""
    if "isbn" in book_data and book_data["isbn"]:
        isbn_list = book_data["isbn"]
        if isinstance(isbn_list, list) and isbn_list:
            isbn = str(isbn_list[0])
        else:
            isbn = str(isbn_list)
    
    # URL de couverture
    cover_url = ""
    if book_data.get("cover_i"):
        cover_url = f"https://covers.openlibrary.org/b/id/{book_data['cover_i']}-L.jpg"
    
    return {
        "ol_key": book_data.get("key", ""),
        "title": book_data.get("title", "Titre inconnu"),
        "author": author,
        "category": category,
        "description": "",
        "total_pages": book_data.get("number_of_pages", 0),
        "publication_year": book_data.get("first_publish_year"),
        "publisher": book_data.get("publisher", [""])[0] if book_data.get("publisher") else "",
        "isbn": isbn,
        "cover_url": cover_url
    }

def detect_category_from_subjects(subjects):
    """Détecter la catégorie d'un livre basé sur ses sujets"""
    if not subjects:
        return "roman"
    
    subjects_lower = [s.lower() for s in subjects if s]
    
    # Mots-clés pour BD
    bd_keywords = ["comic", "comics", "bande dessinee", "graphic novel", "cartoon", 
                   "astérix", "tintin", "lucky luke", "gaston", "spirou", "blake et mortimer"]
    
    # Mots-clés pour manga
    manga_keywords = ["manga", "japanese comics", "anime", "shonen", "seinen", "shojo", 
                      "kodansha", "shogakukan", "shueisha", "one piece", "naruto", "dragon ball"]
    
    # Vérifier BD
    for keyword in bd_keywords:
        if any(keyword in subject for subject in subjects_lower):
            return "bd"
    
    # Vérifier manga
    for keyword in manga_keywords:
        if any(keyword in subject for subject in subjects_lower):
            return "manga"
    
    return "roman"

def search_open_library_by_isbn(isbn: str):
    """Rechercher un livre par ISBN sur Open Library"""
    try:
        # Nettoyer l'ISBN
        clean_isbn = re.sub(r'[^0-9X]', '', isbn.upper())
        
        url = f"https://openlibrary.org/isbn/{clean_isbn}.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            book_data = response.json()
            # Récupérer les informations de l'œuvre
            if "works" in book_data and book_data["works"]:
                work_key = book_data["works"][0]["key"]
                work_url = f"https://openlibrary.org{work_key}.json"
                work_response = requests.get(work_url, timeout=10)
                if work_response.status_code == 200:
                    work_data = work_response.json()
                    return map_isbn_book_data(book_data, work_data)
            return map_isbn_book_data(book_data)
        else:
            # Fallback vers l'API de recherche
            search_results = search_open_library_books(f"isbn:{clean_isbn}", limit=1)
            return search_results[0] if search_results else None
            
    except Exception as e:
        print(f"Erreur lors de la recherche par ISBN: {e}")
        return None

def map_isbn_book_data(book_data, work_data=None):
    """Mapper les données d'ISBN Open Library vers notre format"""
    title = book_data.get("title", "Titre inconnu")
    if work_data and "title" in work_data:
        title = work_data["title"]
    
    # Auteur
    authors = []
    if "authors" in book_data:
        for author_ref in book_data["authors"]:
            if "key" in author_ref:
                try:
                    author_url = f"https://openlibrary.org{author_ref['key']}.json"
                    author_response = requests.get(author_url, timeout=5)
                    if author_response.status_code == 200:
                        author_data = author_response.json()
                        authors.append(author_data.get("name", "Auteur inconnu"))
                except:
                    authors.append("Auteur inconnu")
    
    author = authors[0] if authors else "Auteur inconnu"
    
    # Catégorie
    subjects = []
    if work_data and "subjects" in work_data:
        subjects = work_data["subjects"]
    category = detect_category_from_subjects(subjects)
    
    return {
        "ol_key": book_data.get("key", ""),
        "title": title,
        "author": author,
        "category": category,
        "description": work_data.get("description", "") if work_data else "",
        "total_pages": book_data.get("number_of_pages", 0),
        "publication_year": book_data.get("publish_date"),
        "publisher": book_data.get("publishers", [""])[0] if book_data.get("publishers") else "",
        "isbn": book_data.get("isbn_13", [""])[0] if book_data.get("isbn_13") else book_data.get("isbn_10", [""])[0] if book_data.get("isbn_10") else "",
        "cover_url": f"https://covers.openlibrary.org/b/id/{book_data['covers'][0]}-L.jpg" if book_data.get("covers") else ""
    }

# Routes
@app.get("/")
async def read_root():
    return {"message": "BookTime API - Version complète avec authentification"}

@app.get("/health")
async def health():
    try:
        client.admin.command('ping')
        return {"status": "ok", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Routes d'authentification
@app.post("/api/auth/register")
async def register(user_data: UserAuth):
    # Vérifier si l'utilisateur existe déjà
    existing_user = users_collection.find_one({
        "first_name": user_data.first_name, 
        "last_name": user_data.last_name
    })
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec ce nom existe déjà"
        )
    
    # Créer un nouvel utilisateur
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user)
    
    # Créer le token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    
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
    user = users_collection.find_one({
        "first_name": user_data.first_name,
        "last_name": user_data.last_name
    }, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Utilisateur non trouvé"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user

# Routes pour les livres (protégées)
@app.get("/api/books")
async def get_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    if status:
        filter_dict["status"] = status
    
    books = list(books_collection.find(filter_dict, {"_id": 0}))
    return books

@app.get("/api/books/{book_id}")
async def get_book(book_id: str, current_user: dict = Depends(get_current_user)):
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    return book

@app.post("/api/books")
async def create_book(book_data: BookCreate, current_user: dict = Depends(get_current_user)):
    # Valider la catégorie
    validated_category = validate_category(book_data.category)
    
    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": current_user["id"],
        **book_data.dict(),
        "category": validated_category,
        "date_added": datetime.utcnow(),
        "date_started": None,
        "date_completed": None
    }
    
    # Définir les dates selon le statut
    if book_data.status == "reading":
        book["date_started"] = datetime.utcnow()
    elif book_data.status == "completed":
        book["date_started"] = datetime.utcnow()
        book["date_completed"] = datetime.utcnow()
    
    books_collection.insert_one(book)
    book.pop("_id", None)
    return book

@app.put("/api/books/{book_id}")
async def update_book(
    book_id: str, 
    book_update: BookUpdate, 
    current_user: dict = Depends(get_current_user)
):
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    })
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    update_data = book_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Gérer les changements de statut
    if "status" in update_data:
        current_status = book.get("status")
        new_status = update_data["status"]
        
        if current_status != "reading" and new_status == "reading":
            update_data["date_started"] = datetime.utcnow()
        elif current_status != "completed" and new_status == "completed":
            if not book.get("date_started"):
                update_data["date_started"] = datetime.utcnow()
            update_data["date_completed"] = datetime.utcnow()
    
    books_collection.update_one(
        {"id": book_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    updated_book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    return updated_book

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    result = books_collection.delete_one({
        "id": book_id, 
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    return {"message": "Livre supprimé avec succès"}

# Routes pour les statistiques
@app.get("/api/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    user_filter = {"user_id": current_user["id"]}
    
    total_books = books_collection.count_documents(user_filter)
    completed_books = books_collection.count_documents({**user_filter, "status": "completed"})
    reading_books = books_collection.count_documents({**user_filter, "status": "reading"})
    to_read_books = books_collection.count_documents({**user_filter, "status": "to_read"})
    
    # Compter par catégorie
    roman_count = books_collection.count_documents({**user_filter, "category": "roman"})
    bd_count = books_collection.count_documents({**user_filter, "category": "bd"})
    manga_count = books_collection.count_documents({**user_filter, "category": "manga"})
    
    # Compter les auteurs uniques
    authors = books_collection.distinct("author", user_filter)
    authors_count = len([a for a in authors if a])
    
    # Compter les sagas
    sagas = books_collection.distinct("saga", {**user_filter, "saga": {"$ne": ""}})
    sagas_count = len(sagas)
    
    # Compter les livres auto-ajoutés
    auto_added_count = books_collection.count_documents({**user_filter, "auto_added": True})
    
    return {
        "total_books": total_books,
        "completed_books": completed_books,
        "reading_books": reading_books,
        "to_read_books": to_read_books,
        "categories": {
            "roman": roman_count,
            "bd": bd_count,
            "manga": manga_count
        },
        "authors_count": authors_count,
        "sagas_count": sagas_count,
        "auto_added_count": auto_added_count
    }

# Routes pour les auteurs
@app.get("/api/authors")
async def get_authors(current_user: dict = Depends(get_current_user)):
    user_filter = {"user_id": current_user["id"]}
    
    # Grouper les livres par auteur
    pipeline = [
        {"$match": user_filter},
        {"$group": {
            "_id": "$author",
            "books_count": {"$sum": 1},
            "categories": {"$addToSet": "$category"},
            "sagas": {"$addToSet": "$saga"}
        }},
        {"$match": {"_id": {"$ne": None, "$ne": ""}}},
        {"$sort": {"books_count": -1}}
    ]
    
    authors_data = list(books_collection.aggregate(pipeline))
    
    authors = []
    for author_data in authors_data:
        author = {
            "name": author_data["_id"],
            "books_count": author_data["books_count"],
            "categories": [cat for cat in author_data["categories"] if cat],
            "sagas": [saga for saga in author_data["sagas"] if saga]
        }
        authors.append(author)
    
    return authors

@app.get("/api/authors/{author_name}/books")
async def get_author_books(author_name: str, current_user: dict = Depends(get_current_user)):
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "author": {"$regex": re.escape(author_name), "$options": "i"}
    }, {"_id": 0}))
    
    return books

# Routes pour les sagas
@app.get("/api/sagas")
async def get_sagas(current_user: dict = Depends(get_current_user)):
    user_filter = {"user_id": current_user["id"], "saga": {"$ne": "", "$exists": True}}
    
    # Grouper les livres par saga
    pipeline = [
        {"$match": user_filter},
        {"$group": {
            "_id": "$saga",
            "books_count": {"$sum": 1},
            "completed_books": {
                "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
            },
            "author": {"$first": "$author"},
            "category": {"$first": "$category"},
            "max_volume": {"$max": "$volume_number"}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    sagas_data = list(books_collection.aggregate(pipeline))
    
    sagas = []
    for saga_data in sagas_data:
        next_volume = (saga_data.get("max_volume") or 0) + 1
        saga = {
            "name": saga_data["_id"],
            "books_count": saga_data["books_count"],
            "completed_books": saga_data["completed_books"],
            "next_volume": next_volume,
            "author": saga_data["author"],
            "category": saga_data["category"]
        }
        sagas.append(saga)
    
    return sagas

@app.get("/api/sagas/{saga_name}/books")
async def get_saga_books(saga_name: str, current_user: dict = Depends(get_current_user)):
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }, {"_id": 0}).sort("volume_number", 1))
    
    return books

@app.post("/api/sagas/{saga_name}/auto-add")
async def auto_add_next_volume(saga_name: str, current_user: dict = Depends(get_current_user)):
    # Vérifier que la saga existe
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Trouver le prochain numéro de volume
    max_volume = max([book.get("volume_number", 0) or 0 for book in existing_books])
    next_volume = max_volume + 1
    
    # Utiliser les données du premier livre pour les métadonnées
    first_book = existing_books[0]
    
    # Créer le nouveau livre
    book_id = str(uuid.uuid4())
    new_book = {
        "id": book_id,
        "user_id": current_user["id"],
        "title": f"{saga_name} - Tome {next_volume}",
        "author": first_book.get("author", ""),
        "category": first_book.get("category", "roman"),
        "description": "",
        "saga": saga_name,
        "volume_number": next_volume,
        "status": "to_read",
        "auto_added": True,
        "date_added": datetime.utcnow()
    }
    
    books_collection.insert_one(new_book)
    new_book.pop("_id", None)
    return new_book

# Routes Open Library
@app.get("/api/openlibrary/search")
async def search_openlibrary(
    q: str,
    limit: int = 10,
    language: Optional[str] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    author_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="La requête doit contenir au moins 2 caractères")
    
    books = search_open_library_books(q, limit, language, year_start, year_end, min_pages, max_pages, author_filter)
    
    return {
        "books": books,
        "query": q,
        "total": len(books),
        "filters_applied": {
            "language": language,
            "year_range": f"{year_start}-{year_end}" if year_start and year_end else None,
            "pages_range": f"{min_pages}-{max_pages}" if min_pages and max_pages else None,
            "author": author_filter
        }
    }

@app.post("/api/openlibrary/import")
async def import_from_openlibrary(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    ol_key = request.get("ol_key")
    category = request.get("category", "roman")
    
    if not ol_key:
        raise HTTPException(status_code=400, detail="Clé Open Library requise")
    
    # Valider la catégorie
    validated_category = validate_category(category)
    
    try:
        # Récupérer les données du livre depuis Open Library
        work_url = f"https://openlibrary.org{ol_key}.json"
        response = requests.get(work_url, timeout=10)
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Livre non trouvé sur Open Library")
        
        work_data = response.json()
        
        # Mapper les données
        title = work_data.get("title", "Titre inconnu")
        
        # Récupérer les auteurs
        authors = []
        if "authors" in work_data:
            for author_ref in work_data["authors"]:
                if "author" in author_ref and "key" in author_ref["author"]:
                    try:
                        author_url = f"https://openlibrary.org{author_ref['author']['key']}.json"
                        author_response = requests.get(author_url, timeout=5)
                        if author_response.status_code == 200:
                            author_data = author_response.json()
                            authors.append(author_data.get("name", "Auteur inconnu"))
                    except:
                        authors.append("Auteur inconnu")
        
        author = authors[0] if authors else "Auteur inconnu"
        
        # Vérifier les doublons par titre et auteur
        existing_book = books_collection.find_one({
            "user_id": current_user["id"],
            "title": title,
            "author": author
        })
        
        if existing_book:
            raise HTTPException(status_code=400, detail="Ce livre existe déjà dans votre collection")
        
        # Récupérer la couverture
        cover_url = ""
        if "covers" in work_data and work_data["covers"]:
            cover_url = f"https://covers.openlibrary.org/b/id/{work_data['covers'][0]}-L.jpg"
        
        # Créer le livre
        book_id = str(uuid.uuid4())
        book = {
            "id": book_id,
            "user_id": current_user["id"],
            "title": title,
            "author": author,
            "category": validated_category,
            "description": work_data.get("description", ""),
            "cover_url": cover_url,
            "status": "to_read",
            "date_added": datetime.utcnow(),
            "ol_key": ol_key
        }
        
        books_collection.insert_one(book)
        book.pop("_id", None)
        return book
        
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Erreur lors de la communication avec Open Library")
    except Exception as e:
        print(f"Erreur lors de l'import: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'import du livre")

@app.post("/api/books/{book_id}/enrich")
async def enrich_book(book_id: str, current_user: dict = Depends(get_current_user)):
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    })
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    # Rechercher sur Open Library
    query = f"{book['title']} {book['author']}"
    search_results = search_open_library_books(query, limit=3)
    
    if not search_results:
        raise HTTPException(status_code=404, detail="Aucune correspondance trouvée sur Open Library")
    
    # Prendre le premier résultat
    ol_book = search_results[0]
    
    # Mettre à jour uniquement les champs vides
    update_data = {}
    
    if not book.get("cover_url") and ol_book.get("cover_url"):
        update_data["cover_url"] = ol_book["cover_url"]
    
    if not book.get("isbn") and ol_book.get("isbn"):
        update_data["isbn"] = ol_book["isbn"]
    
    if not book.get("publisher") and ol_book.get("publisher"):
        update_data["publisher"] = ol_book["publisher"]
    
    if not book.get("publication_year") and ol_book.get("publication_year"):
        update_data["publication_year"] = ol_book["publication_year"]
    
    if not book.get("total_pages") and ol_book.get("total_pages"):
        update_data["total_pages"] = ol_book["total_pages"]
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        books_collection.update_one(
            {"id": book_id, "user_id": current_user["id"]},
            {"$set": update_data}
        )
    
    # Retourner le livre mis à jour
    updated_book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    return updated_book

# Routes avancées Open Library
@app.get("/api/openlibrary/search-advanced")
async def search_openlibrary_advanced(
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    publisher: Optional[str] = None,
    isbn: Optional[str] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    # Construire la requête
    criteria = []
    if title:
        criteria.append(f"title:{title}")
    if author:
        criteria.append(f"author:{author}")
    if subject:
        criteria.append(f"subject:{subject}")
    if publisher:
        criteria.append(f"publisher:{publisher}")
    if isbn:
        criteria.append(f"isbn:{isbn}")
    
    if not criteria:
        raise HTTPException(status_code=400, detail="Au moins un critère de recherche est requis")
    
    query = " AND ".join(criteria)
    books = search_open_library_books(query, limit, year_start=year_start, year_end=year_end)
    
    return {
        "books": books,
        "criteria": {
            "title": title,
            "author": author,
            "subject": subject,
            "publisher": publisher,
            "isbn": isbn,
            "year_range": f"{year_start}-{year_end}" if year_start and year_end else None
        },
        "total": len(books)
    }

@app.get("/api/openlibrary/search-isbn")
async def search_by_isbn(
    isbn: str,
    current_user: dict = Depends(get_current_user)
):
    if not isbn or len(isbn.strip()) < 10:
        raise HTTPException(status_code=400, detail="ISBN invalide")
    
    book = search_open_library_by_isbn(isbn)
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé avec cet ISBN")
    
    return {
        "book": book,
        "isbn": isbn
    }

@app.get("/api/openlibrary/search-author")
async def search_author_books(
    author: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    books = search_open_library_books(f"author:{author}", limit=limit)
    
    # Grouper par série
    series_map = {}
    standalone_books = []
    
    for book in books:
        title = book["title"]
        # Détecter les séries (basique)
        if " - " in title or ":" in title or any(word in title.lower() for word in ["tome", "volume", "book", "#"]):
            # Essayer d'extraire le nom de la série
            series_name = title.split(" - ")[0].split(":")[0].strip()
            if series_name not in series_map:
                series_map[series_name] = []
            series_map[series_name].append(book)
        else:
            standalone_books.append(book)
    
    return {
        "author": author,
        "series": [{"name": name, "books": books} for name, books in series_map.items()],
        "standalone_books": standalone_books,
        "total_books": len(books)
    }

@app.post("/api/openlibrary/import-bulk")
async def import_bulk_from_openlibrary(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    books_to_import = request.get("books", [])
    default_category = request.get("category", "roman")
    
    if not books_to_import:
        raise HTTPException(status_code=400, detail="Aucun livre à importer")
    
    imported_books = []
    errors = []
    
    for book_data in books_to_import:
        try:
            ol_key = book_data.get("ol_key")
            category = book_data.get("category", default_category)
            
            # Valider la catégorie
            validated_category = validate_category(category)
            
            # Vérifier les doublons
            existing_book = books_collection.find_one({
                "user_id": current_user["id"],
                "title": book_data.get("title"),
                "author": book_data.get("author")
            })
            
            if existing_book:
                errors.append({
                    "title": book_data.get("title"),
                    "error": "Livre déjà présent dans la collection"
                })
                continue
            
            # Créer le livre
            book_id = str(uuid.uuid4())
            book = {
                "id": book_id,
                "user_id": current_user["id"],
                "title": book_data.get("title", "Titre inconnu"),
                "author": book_data.get("author", "Auteur inconnu"),
                "category": validated_category,
                "description": book_data.get("description", ""),
                "cover_url": book_data.get("cover_url", ""),
                "isbn": book_data.get("isbn", ""),
                "publisher": book_data.get("publisher", ""),
                "publication_year": book_data.get("publication_year"),
                "total_pages": book_data.get("total_pages"),
                "status": "to_read",
                "date_added": datetime.utcnow(),
                "ol_key": ol_key
            }
            
            books_collection.insert_one(book)
            book.pop("_id", None)
            imported_books.append(book)
            
        except Exception as e:
            errors.append({
                "title": book_data.get("title", "Titre inconnu"),
                "error": str(e)
            })
    
    return {
        "imported_count": len(imported_books),
        "error_count": len(errors),
        "imported_books": imported_books,
        "errors": errors
    }

@app.get("/api/openlibrary/recommendations")
async def get_recommendations(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    # Analyser les préférences de l'utilisateur
    user_books = list(books_collection.find({
        "user_id": current_user["id"]
    }, {"_id": 0}))
    
    if len(user_books) < 2:
        raise HTTPException(status_code=400, detail="Pas assez de livres pour générer des recommandations")
    
    # Analyser les auteurs favoris
    author_counts = {}
    categories = {}
    genres = set()
    
    for book in user_books:
        author = book.get("author", "")
        if author:
            author_counts[author] = author_counts.get(author, 0) + 1
        
        category = book.get("category", "")
        if category:
            categories[category] = categories.get(category, 0) + 1
        
        genre = book.get("genre", "")
        if genre:
            genres.add(genre)
    
    # Auteurs favoris
    favorite_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    favorite_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "roman"
    
    recommendations = []
    
    # Rechercher des livres des auteurs favoris
    for author, count in favorite_authors[:2]:
        if len(recommendations) < limit:
            author_books = search_open_library_books(f"author:{author}", limit=5)
            for book in author_books:
                if len(recommendations) < limit:
                    # Vérifier que le livre n'est pas déjà dans la collection
                    existing = books_collection.find_one({
                        "user_id": current_user["id"],
                        "title": book["title"],
                        "author": book["author"]
                    })
                    
                    if not existing:
                        book["recommendation_reason"] = f"Vous avez {count} livre(s) de {author}"
                        recommendations.append(book)
    
    # Rechercher dans la catégorie favorite
    if len(recommendations) < limit:
        category_terms = {
            "roman": "fiction novel",
            "bd": "comic graphic novel",
            "manga": "manga japanese"
        }
        
        search_term = category_terms.get(favorite_category, "fiction")
        category_books = search_open_library_books(search_term, limit=10)
        
        for book in category_books:
            if len(recommendations) < limit:
                existing = books_collection.find_one({
                    "user_id": current_user["id"],
                    "title": book["title"],
                    "author": book["author"]
                })
                
                if not existing:
                    book["recommendation_reason"] = f"Basé sur votre préférence pour les {favorite_category}s"
                    recommendations.append(book)
    
    return {
        "recommendations": recommendations[:limit],
        "based_on": {
            "favorite_authors": [author for author, count in favorite_authors],
            "favorite_category": favorite_category,
            "total_books_analyzed": len(user_books)
        }
    }

@app.get("/api/openlibrary/missing-volumes")
async def find_missing_volumes(
    saga_name: str,
    current_user: dict = Depends(get_current_user)
):
    # Récupérer les livres de la saga
    saga_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }, {"_id": 0}).sort("volume_number", 1))
    
    if not saga_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Analyser les volumes présents
    volumes_present = set()
    for book in saga_books:
        vol = book.get("volume_number")
        if vol:
            volumes_present.add(vol)
    
    if not volumes_present:
        return {
            "saga_name": saga_name,
            "present_volumes": [],
            "missing_volumes": [],
            "next_volumes": [],
            "message": "Aucun numéro de volume défini pour cette saga"
        }
    
    min_vol = min(volumes_present)
    max_vol = max(volumes_present)
    
    # Trouver les volumes manquants
    missing_volumes = []
    for i in range(min_vol, max_vol + 1):
        if i not in volumes_present:
            missing_volumes.append(i)
    
    # Chercher sur Open Library
    author = saga_books[0].get("author", "")
    ol_suggestions = []
    
    if author:
        # Rechercher les volumes manquants et suivants
        search_volumes = missing_volumes + [max_vol + 1, max_vol + 2]
        
        for volume in search_volumes[:5]:  # Limiter à 5 recherches
            query = f"{saga_name} volume {volume} {author}"
            results = search_open_library_books(query, limit=3)
            
            for book in results:
                if saga_name.lower() in book["title"].lower():
                    book["suggested_volume"] = volume
                    book["is_missing"] = volume in missing_volumes
                    ol_suggestions.append(book)
    
    return {
        "saga_name": saga_name,
        "present_volumes": sorted(list(volumes_present)),
        "missing_volumes": missing_volumes,
        "next_volumes": [max_vol + 1, max_vol + 2],
        "openlibrary_suggestions": ol_suggestions
    }

@app.get("/api/openlibrary/suggestions")
async def get_import_suggestions(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    user_books = list(books_collection.find({
        "user_id": current_user["id"]
    }, {"_id": 0}))
    
    if not user_books:
        raise HTTPException(status_code=400, detail="Aucun livre dans votre collection")
    
    suggestions = []
    
    # Suggestions basées sur les sagas incomplètes
    sagas = {}
    for book in user_books:
        saga = book.get("saga")
        if saga:
            if saga not in sagas:
                sagas[saga] = []
            sagas[saga].append(book)
    
    for saga_name, saga_books in sagas.items():
        if len(suggestions) >= limit:
            break
        
        author = saga_books[0].get("author", "")
        volumes = [book.get("volume_number", 0) for book in saga_books if book.get("volume_number")]
        
        if volumes:
            max_volume = max(volumes)
            next_volume = max_volume + 1
            
            # Rechercher le volume suivant
            query = f"{saga_name} volume {next_volume} {author}"
            results = search_open_library_books(query, limit=2)
            
            for book in results:
                if saga_name.lower() in book["title"].lower():
                    book["suggestion_reason"] = f"Suite de votre saga {saga_name}"
                    book["suggested_saga"] = saga_name
                    book["suggested_volume"] = next_volume
                    suggestions.append(book)
                    break
    
    # Suggestions basées sur les auteurs favoris
    author_counts = {}
    for book in user_books:
        author = book.get("author", "")
        if author:
            author_counts[author] = author_counts.get(author, 0) + 1
    
    favorite_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for author, count in favorite_authors:
        if len(suggestions) >= limit:
            break
        
        # Rechercher d'autres livres de cet auteur
        author_books = search_open_library_books(f"author:{author}", limit=5)
        
        for book in author_books:
            if len(suggestions) >= limit:
                break
            
            # Vérifier que le livre n'est pas déjà dans la collection
            existing = books_collection.find_one({
                "user_id": current_user["id"],
                "title": book["title"],
                "author": book["author"]
            })
            
            if not existing:
                book["suggestion_reason"] = f"Autre livre de {author} (vous en avez {count})"
                suggestions.append(book)
    
    return {
        "suggestions": suggestions[:limit],
        "total_user_books": len(user_books),
        "sagas_analyzed": len(sagas),
        "favorite_authors": [author for author, count in favorite_authors]
    }

# Route de recherche des séries (pour le frontend)
@app.get("/api/series/search")
async def search_series(
    q: str,
    current_user: dict = Depends(get_current_user)
):
    """Rechercher dans les séries existantes et les titres de livres"""
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="La requête doit contenir au moins 2 caractères")
        
        # Rechercher dans les sagas existantes
        books_with_saga = list(books_collection.find(
            {
                "user_id": current_user["id"], 
                "saga": {"$regex": q, "$options": "i", "$ne": "", "$exists": True}
            }, 
            {"_id": 0}
        ))
        
        series_map = {}
        for book in books_with_saga:
            saga_name = book.get("saga", "")
            if saga_name:
                if saga_name not in series_map:
                    series_map[saga_name] = {
                        "name": saga_name,
                        "author": book.get("author", ""),
                        "category": book.get("category", "roman"),
                        "books_count": 0
                    }
                series_map[saga_name]["books_count"] += 1
        
        # Rechercher aussi dans les titres de livres
        title_books = list(books_collection.find(
            {
                "user_id": current_user["id"], 
                "title": {"$regex": q, "$options": "i"}
            }, 
            {"_id": 0}
        ))
        
        return {
            "series": list(series_map.values()),
            "books": title_books,
            "query": q
        }
        
    except Exception as e:
        print(f"Erreur lors de la recherche de séries: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)