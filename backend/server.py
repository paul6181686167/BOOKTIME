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
    volume_number: Optional[int] = None

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
    volume_number: Optional[int] = None

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

# Routes d'authentification simplifiées pour test
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

# Routes des statistiques
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

# Routes pour les séries
@app.get("/api/series")
async def get_series(current_user = Depends(get_current_user)):
    """Récupérer toutes les séries de l'utilisateur avec statistiques"""
    try:
        # Récupérer tous les livres de l'utilisateur qui ont une saga
        books_with_saga = list(books_collection.find(
            {"user_id": current_user["id"], "saga": {"$ne": "", "$exists": True}}, 
            {"_id": 0}
        ))
        
        # Grouper par saga
        series_map = {}
        for book in books_with_saga:
            saga_name = book.get("saga", "")
            if saga_name:
                if saga_name not in series_map:
                    series_map[saga_name] = {
                        "name": saga_name,
                        "books": [],
                        "total_books": 0,
                        "completed_books": 0,
                        "reading_books": 0,
                        "to_read_books": 0,
                        "author": book.get("author", ""),
                        "category": book.get("category", "roman"),
                        "cover_url": book.get("cover_url", ""),
                        "description": ""
                    }
                
                series_map[saga_name]["books"].append(book)
                series_map[saga_name]["total_books"] += 1
                
                # Compter par statut
                status = book.get("status", "to_read")
                if status == "completed":
                    series_map[saga_name]["completed_books"] += 1
                elif status == "reading":
                    series_map[saga_name]["reading_books"] += 1
                else:
                    series_map[saga_name]["to_read_books"] += 1
        
        # Trier les livres par numéro de tome dans chaque série
        for series in series_map.values():
            series["books"].sort(key=lambda x: x.get("volume_number", 0) or 0)
            # Utiliser la description du premier livre si pas de description série
            if series["books"] and not series["description"]:
                series["description"] = series["books"][0].get("description", "")
        
        # Convertir en liste et trier par nom de série
        series_list = sorted(series_map.values(), key=lambda x: x["name"])
        
        return {
            "series": series_list,
            "total_series": len(series_list)
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération des séries: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get("/api/series/{series_name}")
async def get_series_details(series_name: str, current_user = Depends(get_current_user)):
    """Récupérer les détails d'une série spécifique"""
    try:
        # Récupérer tous les livres de cette série
        books = list(books_collection.find(
            {"user_id": current_user["id"], "saga": series_name}, 
            {"_id": 0}
        ))
        
        if not books:
            raise HTTPException(status_code=404, detail='Series not found')
        
        # Trier par numéro de tome
        books.sort(key=lambda x: x.get("volume_number", 0) or 0)
        
        # Calculer les statistiques
        stats = {
            "total_books": len(books),
            "completed_books": len([b for b in books if b.get("status") == "completed"]),
            "reading_books": len([b for b in books if b.get("status") == "reading"]),
            "to_read_books": len([b for b in books if b.get("status") == "to_read"]),
        }
        
        # Informations générales de la série
        first_book = books[0]
        series_info = {
            "name": series_name,
            "author": first_book.get("author", ""),
            "category": first_book.get("category", "roman"),
            "description": first_book.get("description", ""),
            "cover_url": first_book.get("cover_url", ""),
            "books": books,
            "stats": stats
        }
        
        return series_info
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la récupération des détails de la série: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get("/api/series/{series_name}/books")
async def get_series_books(series_name: str, current_user = Depends(get_current_user)):
    """Récupérer tous les livres d'une série"""
    try:
        books = list(books_collection.find(
            {"user_id": current_user["id"], "saga": series_name}, 
            {"_id": 0}
        ))
        
        if not books:
            raise HTTPException(status_code=404, detail='Series not found')
        
        # Trier par numéro de tome
        books.sort(key=lambda x: x.get("volume_number", 0) or 0)
        
        return {
            "series_name": series_name,
            "books": books,
            "total_books": len(books)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la récupération des livres de la série: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get("/api/search/series")
async def search_series(q: str, current_user = Depends(get_current_user)):
    """Rechercher des séries par nom"""
    try:
        if not q:
            return {"series": [], "books": []}
        
        # Rechercher dans les séries existantes
        series_books = list(books_collection.find(
            {
                "user_id": current_user["id"], 
                "saga": {"$regex": q, "$options": "i", "$ne": ""}
            }, 
            {"_id": 0}
        ))
        
        # Grouper par saga
        series_map = {}
        for book in series_books:
            saga_name = book.get("saga", "")
            if saga_name:
                if saga_name not in series_map:
                    series_map[saga_name] = {
                        "name": saga_name,
                        "books_count": 0,
                        "author": book.get("author", ""),
                        "category": book.get("category", "roman"),
                        "cover_url": book.get("cover_url", ""),
                        "first_book": book
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