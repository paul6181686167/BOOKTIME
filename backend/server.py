from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

app = FastAPI(title="BOOKTIME API", description="API pour l'application de tracking de livres")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client.booktime
books_collection = database.books

# Pydantic models
class BookBase(BaseModel):
    title: str
    author: str
    category: str  # "roman", "bd", "manga"
    description: Optional[str] = None
    cover_url: Optional[str] = None
    total_pages: Optional[int] = None
    isbn: Optional[str] = None
    # Nouveaux champs pour les sagas et séries
    saga: Optional[str] = None
    series: Optional[str] = None
    volume_number: Optional[int] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    genre: Optional[List[str]] = None
    language: str = "français"

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: str = Field(alias="_id")
    status: str = "to_read"  # "to_read", "reading", "completed"
    current_page: int = 0
    rating: Optional[int] = None  # 1-5 stars
    review: Optional[str] = None
    date_added: datetime
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    # Flag pour l'ajout automatique
    auto_added: bool = False

    class Config:
        populate_by_name = True

class AuthorInfo(BaseModel):
    name: str
    books_count: int
    categories: List[str]
    sagas: List[str]

class SagaInfo(BaseModel):
    name: str
    books_count: int
    completed_books: int
    next_volume: Optional[int] = None
    author: str
    category: str

class BookUpdate(BaseModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None

# API Routes
@app.get("/")
async def root():
    return {"message": "Welcome to BOOKTIME API 📚"}

@app.get("/api/books", response_model=List[Book])
async def get_books(category: Optional[str] = None, status: Optional[str] = None):
    """Récupérer tous les livres avec filtres optionnels"""
    query = {}
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
async def create_book(book: BookCreate):
    """Créer un nouveau livre"""
    book_data = book.dict()
    book_data["_id"] = str(uuid.uuid4())
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
async def get_book(book_id: str):
    """Récupérer un livre par son ID"""
    book = await books_collection.find_one({"_id": book_id})
    if book:
        book["_id"] = str(book["_id"])
        return Book(**book)
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.put("/api/books/{book_id}", response_model=Book)
async def update_book(book_id: str, book_update: BookUpdate):
    """Mettre à jour un livre"""
    update_data = book_update.dict(exclude_unset=True)
    
    # Automatiquement définir les dates selon le statut
    if "status" in update_data:
        if update_data["status"] == "reading" and "date_started" not in update_data:
            update_data["date_started"] = datetime.utcnow()
        elif update_data["status"] == "completed" and "date_completed" not in update_data:
            update_data["date_completed"] = datetime.utcnow()
    
    result = await books_collection.update_one(
        {"_id": book_id}, 
        {"$set": update_data}
    )
    
    if result.modified_count:
        updated_book = await books_collection.find_one({"_id": book_id})
        updated_book["_id"] = str(updated_book["_id"])
        return Book(**updated_book)
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str):
    """Supprimer un livre"""
    result = await books_collection.delete_one({"_id": book_id})
    if result.deleted_count:
        return {"message": "Livre supprimé avec succès"}
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.get("/api/stats")
async def get_stats():
    """Récupérer les statistiques générales"""
    total_books = await books_collection.count_documents({})
    completed_books = await books_collection.count_documents({"status": "completed"})
    reading_books = await books_collection.count_documents({"status": "reading"})
    to_read_books = await books_collection.count_documents({"status": "to_read"})
    
    # Stats par catégorie
    roman_count = await books_collection.count_documents({"category": "roman"})
    bd_count = await books_collection.count_documents({"category": "bd"})
    manga_count = await books_collection.count_documents({"category": "manga"})
    
    return {
        "total_books": total_books,
        "completed_books": completed_books,
        "reading_books": reading_books,
        "to_read_books": to_read_books,
        "categories": {
            "roman": roman_count,
            "bd": bd_count,
            "manga": manga_count
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)