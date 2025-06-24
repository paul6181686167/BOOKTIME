from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import motor.motor_asyncio
import os
from dotenv import load_dotenv
import uuid
import httpx
import json

# Load environment variables
load_dotenv()

app = FastAPI(title="BOOKTIME API", description="API pour l'application de tracking de livres")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
database = client.booktime
books_collection = database.books

# Service Open Library
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
    async def get_book_by_isbn(isbn: str):
        """Récupérer un livre par ISBN depuis Open Library"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{OpenLibraryService.BASE_URL}/api/books",
                    params={
                        "bibkeys": f"ISBN:{isbn}",
                        "format": "json",
                        "jscmd": "data"
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get(f"ISBN:{isbn}")
        except Exception as e:
            print(f"Erreur lors de la récupération du livre par ISBN: {e}")
            return None
    
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
            "genre": ol_book.get("subject", [])[:5] if ol_book.get("subject") else [],  # Limiter à 5 genres
            "original_language": "anglais" if not any(lang in str(ol_book.get("publisher", [])) for lang in ["français", "french", "gallimard"]) else "français",
            "available_translations": [],
            "reading_language": "français"
        }

# Modèles Pydantic pour Open Library
class OpenLibrarySearchResult(BaseModel):
    key: str
    title: str
    author_name: Optional[List[str]] = []
    first_publish_year: Optional[int] = None
    isbn: Optional[List[str]] = []
    cover_i: Optional[int] = None
    subject: Optional[List[str]] = []
    publisher: Optional[List[str]] = []
    number_of_pages_median: Optional[int] = None

class OpenLibraryImportRequest(BaseModel):
    ol_key: str
    category: str = "roman"
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
    # Gestion des langues
    original_language: str = "français"  # Langue d'origine de l'œuvre
    available_translations: Optional[List[str]] = []  # Langues disponibles
    reading_language: str = "français"  # Langue dans laquelle l'utilisateur lit le livre

class BookCreate(BookBase):
    # Validation des catégories
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
    original_language: Optional[str] = None
    available_translations: Optional[List[str]] = None
    reading_language: Optional[str] = None

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

@app.get("/api/authors", response_model=List[AuthorInfo])
async def get_authors():
    """Récupérer tous les auteurs avec leurs statistiques"""
    pipeline = [
        {
            "$group": {
                "_id": "$author",
                "books_count": {"$sum": 1},
                "categories": {"$addToSet": "$category"},
                "sagas": {"$addToSet": "$saga"}
            }
        },
        {
            "$project": {
                "name": "$_id",
                "books_count": 1,
                "categories": {"$filter": {"input": "$categories", "cond": {"$ne": ["$$this", None]}}},
                "sagas": {"$filter": {"input": "$sagas", "cond": {"$ne": ["$$this", None]}}}
            }
        },
        {"$sort": {"books_count": -1}}
    ]
    
    authors = []
    async for author in books_collection.aggregate(pipeline):
        authors.append(AuthorInfo(
            name=author["name"],
            books_count=author["books_count"],
            categories=author["categories"],
            sagas=author["sagas"]
        ))
    return authors

@app.get("/api/authors/{author_name}/books", response_model=List[Book])
async def get_books_by_author(author_name: str):
    """Récupérer tous les livres d'un auteur"""
    books = []
    async for book in books_collection.find({"author": {"$regex": author_name, "$options": "i"}}):
        book["_id"] = str(book["_id"])
        books.append(Book(**book))
    return books

@app.get("/api/sagas", response_model=List[SagaInfo])
async def get_sagas():
    """Récupérer toutes les sagas avec leurs statistiques"""
    pipeline = [
        {"$match": {"saga": {"$exists": True, "$ne": None}}},
        {
            "$group": {
                "_id": {
                    "saga": "$saga",
                    "author": "$author",
                    "category": "$category"
                },
                "books_count": {"$sum": 1},
                "completed_books": {
                    "$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}
                },
                "volumes": {"$push": "$volume_number"}
            }
        },
        {
            "$project": {
                "name": "$_id.saga",
                "author": "$_id.author",
                "category": "$_id.category",
                "books_count": 1,
                "completed_books": 1,
                "next_volume": {
                    "$add": [{"$max": "$volumes"}, 1]
                }
            }
        },
        {"$sort": {"name": 1}}
    ]
    
    sagas = []
    async for saga in books_collection.aggregate(pipeline):
        sagas.append(SagaInfo(
            name=saga["name"],
            books_count=saga["books_count"],
            completed_books=saga["completed_books"],
            next_volume=saga.get("next_volume"),
            author=saga["author"],
            category=saga["category"]
        ))
    return sagas

@app.get("/api/sagas/{saga_name}/books", response_model=List[Book])
async def get_books_by_saga(saga_name: str):
    """Récupérer tous les livres d'une saga"""
    books = []
    async for book in books_collection.find({"saga": saga_name}).sort("volume_number", 1):
        book["_id"] = str(book["_id"])
        books.append(Book(**book))
    return books

@app.post("/api/sagas/{saga_name}/auto-add")
async def auto_add_next_volume(saga_name: str):
    """Ajouter automatiquement le prochain tome d'une saga à la liste 'à lire'"""
    # Trouver la saga
    saga_books = await books_collection.find({"saga": saga_name}).sort("volume_number", -1).to_list(1)
    if not saga_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    last_book = saga_books[0]
    next_volume = (last_book.get("volume_number", 0) or 0) + 1
    
    # Créer le nouveau livre
    new_book_data = {
        "_id": str(uuid.uuid4()),
        "title": f"{saga_name} - Tome {next_volume}",
        "author": last_book["author"],
        "category": last_book["category"],
        "saga": saga_name,
        "volume_number": next_volume,
        "description": f"Tome {next_volume} de la saga {saga_name}",
        "status": "to_read",
        "current_page": 0,
        "date_added": datetime.utcnow(),
        "auto_added": True,
        "genre": last_book.get("genre", []),
        "publisher": last_book.get("publisher"),
        "original_language": last_book.get("original_language", "français"),
        "available_translations": last_book.get("available_translations", []),
        "reading_language": last_book.get("reading_language", "français")
    }
    
    result = await books_collection.insert_one(new_book_data)
    if result.inserted_id:
        new_book_data["_id"] = str(new_book_data["_id"])
        return Book(**new_book_data)
    
    raise HTTPException(status_code=400, detail="Erreur lors de l'ajout automatique")

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
    
    # Stats des sagas
    sagas_count = len(await books_collection.distinct("saga", {"saga": {"$ne": None}}))
    authors_count = len(await books_collection.distinct("author"))
    auto_added_count = await books_collection.count_documents({"auto_added": True})
    
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

# API Routes Open Library
@app.get("/api/openlibrary/search")
async def search_openlibrary(q: str, limit: int = 10):
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
        "total": result.get("numFound", 0),
        "books": mapped_books
    }

@app.post("/api/openlibrary/import")
async def import_from_openlibrary(import_request: OpenLibraryImportRequest):
    """Importer un livre depuis Open Library"""
    try:
        # Rechercher le livre spécifique pour obtenir les détails
        search_result = await OpenLibraryService.search_books(f"key:{import_request.ol_key}")
        
        if not search_result.get("docs"):
            raise HTTPException(status_code=404, detail="Livre non trouvé sur Open Library")
        
        ol_book = search_result["docs"][0]
        
        # Mapper vers le format BOOKTIME
        book_data = OpenLibraryService.map_openlibrary_to_booktime(ol_book, import_request.category)
        
        # Vérifier si le livre existe déjà (par ISBN ou titre+auteur)
        existing_book = None
        if book_data.get("isbn"):
            existing_book = await books_collection.find_one({"isbn": book_data["isbn"]})
        
        if not existing_book:
            # Recherche par titre et auteur
            existing_book = await books_collection.find_one({
                "title": {"$regex": book_data["title"], "$options": "i"},
                "author": {"$regex": book_data["author"], "$options": "i"}
            })
        
        if existing_book:
            raise HTTPException(status_code=409, detail="Ce livre existe déjà dans votre collection")
        
        # Créer le nouveau livre
        book_data["_id"] = str(uuid.uuid4())
        book_data["status"] = "to_read"
        book_data["current_page"] = 0
        book_data["date_added"] = datetime.utcnow()
        book_data["category"] = import_request.category.lower()
        
        result = await books_collection.insert_one(book_data)
        if result.inserted_id:
            created_book = await books_collection.find_one({"_id": book_data["_id"]})
            created_book["_id"] = str(created_book["_id"])
            return Book(**created_book)
        
        raise HTTPException(status_code=400, detail="Erreur lors de l'import du livre")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de l'import Open Library: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.post("/api/books/{book_id}/enrich")
async def enrich_book_from_openlibrary(book_id: str):
    """Enrichir un livre existant avec les données Open Library"""
    try:
        # Récupérer le livre existant
        book = await books_collection.find_one({"_id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Livre non trouvé")
        
        # Rechercher sur Open Library par titre et auteur
        search_query = f"{book['title']} {book['author']}"
        search_result = await OpenLibraryService.search_books(search_query, limit=5)
        
        if not search_result.get("docs"):
            raise HTTPException(status_code=404, detail="Aucune correspondance trouvée sur Open Library")
        
        # Prendre le premier résultat qui semble correspondre
        ol_book = search_result["docs"][0]
        
        # Enrichir les données existantes
        enriched_data = {}
        
        # Couverture si pas déjà présente
        if not book.get("cover_url") and ol_book.get("cover_i"):
            enriched_data["cover_url"] = f"https://covers.openlibrary.org/b/id/{ol_book['cover_i']}-L.jpg"
        
        # ISBN si pas déjà présent
        if not book.get("isbn") and ol_book.get("isbn"):
            enriched_data["isbn"] = ol_book["isbn"][0] if isinstance(ol_book["isbn"], list) else ol_book["isbn"]
        
        # Nombre de pages si pas déjà présent
        if not book.get("total_pages") and ol_book.get("number_of_pages_median"):
            enriched_data["total_pages"] = ol_book["number_of_pages_median"]
        
        # Genres si pas déjà présents
        if not book.get("genre") and ol_book.get("subject"):
            enriched_data["genre"] = ol_book["subject"][:5]  # Limiter à 5 genres
        
        # Editeur si pas déjà présent
        if not book.get("publisher") and ol_book.get("publisher"):
            enriched_data["publisher"] = ol_book["publisher"][0] if isinstance(ol_book["publisher"], list) else ol_book["publisher"]
        
        # Année de publication si pas déjà présente
        if not book.get("publication_year") and ol_book.get("first_publish_year"):
            enriched_data["publication_year"] = ol_book["first_publish_year"]
        
        if not enriched_data:
            return {"message": "Aucune nouvelle donnée trouvée pour enrichir ce livre"}
        
        # Mettre à jour le livre
        result = await books_collection.update_one(
            {"_id": book_id}, 
            {"$set": enriched_data}
        )
        
        if result.modified_count:
            updated_book = await books_collection.find_one({"_id": book_id})
            updated_book["_id"] = str(updated_book["_id"])
            return {
                "message": "Livre enrichi avec succès",
                "enriched_fields": list(enriched_data.keys()),
                "book": Book(**updated_book)
            }
        
        raise HTTPException(status_code=400, detail="Erreur lors de l'enrichissement")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de l'enrichissement: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)