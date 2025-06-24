# Backend BOOKTIME pour Vercel Serverless
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import os
import json
import uuid
from pathlib import Path

# Créer l'application FastAPI
app = FastAPI(title="BOOKTIME API", description="API pour l'application de tracking de livres")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Stockage en fichier JSON (simple pour les tests)
DATA_FILE = "/tmp/booktime_data.json"

def load_data():
    """Charger les données depuis le fichier JSON"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"books": []}

def save_data(data):
    """Sauvegarder les données dans le fichier JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

# Modèles Pydantic
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
    status: str = "to_read"  # "to_read", "reading", "completed"
    current_page: int = 0
    rating: Optional[int] = None  # 1-5 stars
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

# Routes API
@app.get("/")
async def root():
    return {"message": "Welcome to BOOKTIME API 📚"}

@app.get("/api/books")
async def get_books(category: Optional[str] = None, status: Optional[str] = None):
    """Récupérer tous les livres avec filtres optionnels"""
    data = load_data()
    books = data.get("books", [])
    
    if category:
        books = [book for book in books if book.get("category", "").lower() == category.lower()]
    if status:
        books = [book for book in books if book.get("status") == status]
    
    return books

@app.post("/api/books")
async def create_book(book: BookCreate):
    """Créer un nouveau livre"""
    data = load_data()
    
    book_data = book.dict()
    book_data["_id"] = str(uuid.uuid4())
    book_data["id"] = book_data["_id"]
    book_data["status"] = "to_read"
    book_data["current_page"] = 0
    book_data["date_added"] = datetime.utcnow()
    book_data["category"] = book_data["category"].lower()
    
    data["books"].append(book_data)
    save_data(data)
    
    return book_data

@app.get("/api/books/{book_id}")
async def get_book(book_id: str):
    """Récupérer un livre par son ID"""
    data = load_data()
    books = data.get("books", [])
    
    book = next((book for book in books if book.get("_id") == book_id or book.get("id") == book_id), None)
    if book:
        return book
    raise HTTPException(status_code=404, detail="Livre non trouvé")

@app.put("/api/books/{book_id}")
async def update_book(book_id: str, book_update: BookUpdate):
    """Mettre à jour un livre"""
    data = load_data()
    books = data.get("books", [])
    
    book_index = next((i for i, book in enumerate(books) if book.get("_id") == book_id or book.get("id") == book_id), None)
    if book_index is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    update_data = book_update.dict(exclude_unset=True)
    
    # Automatiquement définir les dates selon le statut
    if "status" in update_data:
        if update_data["status"] == "reading" and "date_started" not in update_data:
            update_data["date_started"] = datetime.utcnow()
        elif update_data["status"] == "completed" and "date_completed" not in update_data:
            update_data["date_completed"] = datetime.utcnow()
    
    books[book_index].update(update_data)
    save_data(data)
    
    return books[book_index]

@app.delete("/api/books/{book_id}")
async def delete_book(book_id: str):
    """Supprimer un livre"""
    data = load_data()
    books = data.get("books", [])
    
    book_index = next((i for i, book in enumerate(books) if book.get("_id") == book_id or book.get("id") == book_id), None)
    if book_index is None:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    deleted_book = books.pop(book_index)
    save_data(data)
    
    return {"message": "Livre supprimé avec succès"}

@app.get("/api/stats")
async def get_stats():
    """Récupérer les statistiques générales"""
    data = load_data()
    books = data.get("books", [])
    
    total_books = len(books)
    completed_books = len([book for book in books if book.get("status") == "completed"])
    reading_books = len([book for book in books if book.get("status") == "reading"])
    to_read_books = len([book for book in books if book.get("status") == "to_read"])
    
    # Stats par catégorie
    roman_count = len([book for book in books if book.get("category") == "roman"])
    bd_count = len([book for book in books if book.get("category") == "bd"])
    manga_count = len([book for book in books if book.get("category") == "manga"])
    
    # Stats des sagas et auteurs
    sagas = list(set([book.get("saga") for book in books if book.get("saga")]))
    authors = list(set([book.get("author") for book in books if book.get("author")]))
    auto_added_count = len([book for book in books if book.get("auto_added")])
    
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
        "sagas_count": len(sagas),
        "authors_count": len(authors),
        "auto_added_count": auto_added_count
    }

# Pour Vercel
from fastapi import Request

async def handler(request: Request):
    return await app(request.scope, request.receive, request.send)