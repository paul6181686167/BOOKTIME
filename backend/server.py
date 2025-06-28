from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
import jwt
import os
import requests
import re
from pydantic import BaseModel
from typing import Optional, List

# Chargement des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

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

# Créer l'application
app = FastAPI(title="BookTime API", description="Votre bibliothèque personnelle")

# Ajouter CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

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