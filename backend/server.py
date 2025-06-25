from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime, timedelta
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import uuid
import httpx
import json
import bcrypt
from jose import JWTError, jwt

# Load environment variables
load_dotenv()

app = FastAPI(title="BOOKTIME API", description="API pour l'application de tracking de livres avec authentification")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client.booktime
books_collection = database.books
users_collection = database.users

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Security
security = HTTPBearer()

# User Models
class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Email format invalid')
        return v.lower()

class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    is_active: bool = True

    class Config:
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Password utilities
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token without expiration"""
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"_id": user_id})
    if user is None:
        raise credentials_exception
    
    user["_id"] = str(user["_id"])
    return User(**user)

# Service Open Library (unchanged)
class OpenLibraryService:
    BASE_URL = "https://openlibrary.org"
    
    @staticmethod
    async def search_books(query: str, limit: int = 10):
        """Rechercher des livres sur Open Library"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{OpenLibraryService.BASE_URL}/search.json",
                    params={
                        "q": query,
                        "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,publisher,number_of_pages_median",
                        "limit": limit
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Erreur lors de la recherche Open Library: {e}")
            return {"docs": [], "numFound": 0}
    
    @staticmethod
    def map_openlibrary_to_booktime(ol_book, category="roman"):
        """Mapper un livre Open Library vers le format BOOKTIME"""
        # Déterminer la catégorie basée sur les sujets
        subjects = ol_book.get("subject", [])
        if any(term in " ".join(subjects).lower() for term in ["comic", "graphic", "bd", "bande dessinée"]):
            category = "bd"
        elif any(term in " ".join(subjects).lower() for term in ["manga", "japanese"]):
            category = "manga"
        
        # URL de couverture
        cover_url = None
        if ol_book.get("cover_i"):
            cover_url = f"https://covers.openlibrary.org/b/id/{ol_book['cover_i']}-L.jpg"
        
        # ISBN
        isbn = None
        if ol_book.get("isbn"):
            isbn = ol_book["isbn"][0] if isinstance(ol_book["isbn"], list) else ol_book["isbn"]
        
        return {
            "title": ol_book.get("title", "Titre inconnu"),
            "author": ", ".join(ol_book.get("author_name", ["Auteur inconnu"])),
            "category": category,
            "description": f"Publié en {ol_book.get('first_publish_year', 'année inconnue')}",
            "cover_url": cover_url,
            "total_pages": ol_book.get("number_of_pages_median"),
            "isbn": isbn,
            "publication_year": ol_book.get("first_publish_year"),
            "publisher": ol_book.get("publisher", [None])[0] if ol_book.get("publisher") else None,
            "genre": ol_book.get("subject", [])[:5] if ol_book.get("subject") else [],
            "original_language": "anglais" if not any(lang in str(ol_book.get("publisher", [])) for lang in ["français", "french", "gallimard"]) else "français",
            "available_translations": [],
            "reading_language": "français"
        }

# Book Models (updated with user_id)
class BookBase(BaseModel):
    title: str
    author: str
    category: str  # "roman", "bd", "manga"
    description: Optional[str] = None
    cover_url: Optional[str] = None
    total_pages: Optional[int] = None
    isbn: Optional[str] = None
    saga: Optional[str] = None
    series: Optional[str] = None
    volume_number: Optional[int] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    genre: Optional[List[str]] = None
    original_language: str = "français"
    available_translations: Optional[List[str]] = []
    reading_language: str = "français"

class BookCreate(BookBase):
    def __init__(self, **data):
        super().__init__(**data)
        if self.category.lower() not in ['roman', 'bd', 'manga']:
            raise ValueError(f"Category must be one of: roman, bd, manga. Got: {self.category}")

class Book(BookBase):
    id: str = Field(alias="_id")
    user_id: str
    status: str = "to_read"
    current_page: int = 0
    rating: Optional[int] = None
    review: Optional[str] = None
    date_added: datetime
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    auto_added: bool = False

    class Config:
        populate_by_name = True

class BookUpdate(BaseModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    original_language: Optional[str] = None
    available_translations: Optional[List[str]] = None
    reading_language: Optional[str] = None

# Authentication Routes
@app.post("/api/auth/register", response_model=Token)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    user_dict = {
        "_id": str(uuid.uuid4()),
        "email": user_data.email.lower(),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await users_collection.insert_one(user_dict)
    if not result.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la création du compte"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user_dict["_id"]})
    
    # Return user without password
    user_dict.pop("password")
    user_dict["_id"] = str(user_dict["_id"])
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(**user_dict)
    )

@app.post("/api/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """Login user"""
    # Find user by email
    user = await users_collection.find_one({"email": user_credentials.email.lower()})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte désactivé"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    # Return user without password
    user.pop("password")
    user["_id"] = str(user["_id"])
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(**user)
    )

@app.get("/api/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

# API Routes (updated with authentication)
@app.get("/")
async def root():
    return {"message": "Welcome to BOOKTIME API 📚"}

@app.get("/api/books", response_model=List[Book])
async def get_books(
    category: Optional[str] = None, 
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Récupérer tous les livres de l'utilisateur avec filtres optionnels"""
    query = {"user_id": current_user.id}
    if category:
        query["category"] = category.lower()
    if status:
        query["status"] = status
    
    books = []
    async for book in books_collection.find(query):
        book["_id"] = str(book["_id"])
        books.append(Book(**book))
    return books

@app.post("/api/books", response_model=Book)
async def create_book(book: BookCreate, current_user: User = Depends(get_current_user)):
    """Créer un nouveau livre pour l'utilisateur"""
    book_data = book.dict()
    book_data["_id"] = str(uuid.uuid4())
    book_data["user_id"] = current_user.id
    book_data["status"] = "to_read"
    book_data["current_page"] = 0
    book_data["date_added"] = datetime.utcnow()
    book_data["category"] = book_data["category"].lower()
    
    result = await books_collection.insert_one(book_data)
    if result.inserted_id:
        created_book = await books_collection.find_one({"_id": book_data["_id"]})
        created_book["_id"] = str(created_book["_id"])
        return Book(**created_book)
    raise HTTPException(status_code=400, detail="Erreur lors de la création du livre")

@app.get("/api/books/{book_id}", response_model=Book)
async def get_book(book_id: str, current_user: User = Depends(get_current_user)):
    """Récupérer un livre par son ID"""
    book = await books_collection.find_one({"_id": book_id, "user_id": current_user.id})
    if book:
        book["_id"] = str(book["_id"])
        return Book(**book)
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.put("/api/books/{book_id}", response_model=Book)
async def update_book(book_id: str, book_update: BookUpdate, current_user: User = Depends(get_current_user)):
    """Mettre à jour un livre"""
    # Verify book belongs to user
    existing_book = await books_collection.find_one({"_id": book_id, "user_id": current_user.id})
    if not existing_book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    update_data = book_update.dict(exclude_unset=True)
    
    # Automatiquement définir les dates selon le statut
    if "status" in update_data:
        if update_data["status"] == "reading" and "date_started" not in update_data:
            update_data["date_started"] = datetime.utcnow()
        elif update_data["status"] == "completed" and "date_completed" not in update_data:
            update_data["date_completed"] = datetime.utcnow()
    
    result = await books_collection.update_one(
        {"_id": book_id, "user_id": current_user.id}, 
        {"$set": update_data}
    )
    
    if result.modified_count:
        updated_book = await books_collection.find_one({"_id": book_id})
        updated_book["_id"] = str(updated_book["_id"])
        return Book(**updated_book)
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str, current_user: User = Depends(get_current_user)):
    """Supprimer un livre"""
    result = await books_collection.delete_one({"_id": book_id, "user_id": current_user.id})
    if result.deleted_count:
        return {"message": "Livre supprimé avec succès"}
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.get("/api/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    """Récupérer les statistiques de l'utilisateur"""
    user_filter = {"user_id": current_user.id}
    
    total_books = await books_collection.count_documents(user_filter)
    completed_books = await books_collection.count_documents({**user_filter, "status": "completed"})
    reading_books = await books_collection.count_documents({**user_filter, "status": "reading"})
    to_read_books = await books_collection.count_documents({**user_filter, "status": "to_read"})
    
    # Stats par catégorie
    roman_count = await books_collection.count_documents({**user_filter, "category": "roman"})
    bd_count = await books_collection.count_documents({**user_filter, "category": "bd"})
    manga_count = await books_collection.count_documents({**user_filter, "category": "manga"})
    
    # Stats des sagas
    sagas_count = len(await books_collection.distinct("saga", {**user_filter, "saga": {"$ne": None}}))
    authors_count = len(await books_collection.distinct("author", user_filter))
    auto_added_count = await books_collection.count_documents({**user_filter, "auto_added": True})
    
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
        "sagas_count": sagas_count,
        "authors_count": authors_count,
        "auto_added_count": auto_added_count
    }

# OpenLibrary routes (unchanged but protected)
@app.get("/api/openlibrary/search")
async def search_openlibrary(
    q: str, 
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Rechercher des livres sur Open Library"""
    if not q:
        raise HTTPException(status_code=400, detail="Le paramètre de recherche 'q' est requis")
    
    result = await OpenLibraryService.search_books(q, limit)
    
    # Mapper les résultats
    mapped_books = []
    for book in result.get("docs", []):
        mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
        mapped_book["ol_key"] = book.get("key")
        mapped_books.append(mapped_book)
    
    return {
        "total": len(mapped_books),
        "books": mapped_books
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)