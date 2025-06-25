from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import uuid
import os
from pydantic import BaseModel
from typing import Optional, List

# Chargement des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

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

# Client MongoDB
client = MongoClient(MONGO_URL)
db = client.booktime
books_collection = db.books

# Modèles Pydantic
class BookCreate(BaseModel):
    title: str
    author: str
    category: str = "roman"
    description: str = ""
    saga: str = ""
    cover_url: str = ""
    status: str = "to_read"
    volume_number: Optional[int] = None

# Routes de base
@app.get("/")
async def read_root():
    return {"message": "BookTime API - Mode Simple"}

@app.get("/health")
async def health():
    try:
        client.admin.command('ping')
        return {"status": "ok", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Routes sans authentification pour test
@app.get("/api/books")
async def get_books(category: Optional[str] = None):
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    
    books = list(books_collection.find(filter_dict, {"_id": 0}))
    return books

@app.post("/api/books")
async def create_book(book_data: BookCreate):
    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": "test-user",  # Utilisateur fixe pour test
        **book_data.dict(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    books_collection.insert_one(book)
    book.pop("_id", None)
    return book

@app.get("/api/stats")
async def get_stats():
    total_books = books_collection.count_documents({})
    completed_books = books_collection.count_documents({"status": "completed"})
    reading_books = books_collection.count_documents({"status": "reading"})
    to_read_books = books_collection.count_documents({"status": "to_read"})
    
    sagas = books_collection.distinct("saga", {"saga": {"$ne": ""}})
    sagas_count = len(sagas)
    
    return {
        "total_books": total_books,
        "completed_books": completed_books,
        "reading_books": reading_books,
        "to_read_books": to_read_books,
        "categories": {
            "roman": 0,
            "bd": 0,
            "manga": 0
        },
        "authors_count": 0,
        "sagas_count": sagas_count
    }

# Routes pour les séries
@app.get("/api/series")
async def get_series():
    """Récupérer toutes les séries avec statistiques"""
    try:
        books_with_saga = list(books_collection.find(
            {"saga": {"$ne": "", "$exists": True}}, 
            {"_id": 0}
        ))
        
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
                
                status = book.get("status", "to_read")
                if status == "completed":
                    series_map[saga_name]["completed_books"] += 1
                elif status == "reading":
                    series_map[saga_name]["reading_books"] += 1
                else:
                    series_map[saga_name]["to_read_books"] += 1
        
        for series in series_map.values():
            series["books"].sort(key=lambda x: x.get("volume_number", 0) or 0)
        
        series_list = sorted(series_map.values(), key=lambda x: x["name"])
        
        return {
            "series": series_list,
            "total_series": len(series_list)
        }
        
    except Exception as e:
        print(f"Erreur lors de la récupération des séries: {e}")
        raise HTTPException(status_code=500, detail='Internal server error')

@app.get("/api/series/{series_name}")
async def get_series_details(series_name: str):
    """Récupérer les détails d'une série spécifique"""
    try:
        books = list(books_collection.find(
            {"saga": series_name}, 
            {"_id": 0}
        ))
        
        if not books:
            raise HTTPException(status_code=404, detail='Series not found')
        
        books.sort(key=lambda x: x.get("volume_number", 0) or 0)
        
        stats = {
            "total_books": len(books),
            "completed_books": len([b for b in books if b.get("status") == "completed"]),
            "reading_books": len([b for b in books if b.get("status") == "reading"]),
            "to_read_books": len([b for b in books if b.get("status") == "to_read"]),
        }
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)