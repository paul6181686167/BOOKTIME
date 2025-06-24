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

# API Routes Open Library - Version Avancée
@app.get("/api/openlibrary/search")
async def search_openlibrary(
    q: str, 
    limit: int = 10,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    language: Optional[str] = None,
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    author_filter: Optional[str] = None
):
    """Rechercher des livres sur Open Library avec filtres avancés"""
    if not q:
        raise HTTPException(status_code=400, detail="Le paramètre de recherche 'q' est requis")
    
    # Construction de la requête avec filtres
    search_query = q
    if author_filter:
        search_query = f"{q} author:{author_filter}"
    if year_start and year_end:
        search_query = f"{search_query} publish_year:[{year_start} TO {year_end}]"
    elif year_start:
        search_query = f"{search_query} publish_year:[{year_start} TO *]"
    elif year_end:
        search_query = f"{search_query} publish_year:[* TO {year_end}]"
    
    result = await OpenLibraryService.search_books(search_query, limit)
    
    # Filtrer par nombre de pages si spécifié
    filtered_books = result.get("docs", [])
    if min_pages or max_pages:
        def filter_by_pages(book):
            pages = book.get("number_of_pages_median")
            if not pages:
                return True  # Garder les livres sans info de pages
            if min_pages and pages < min_pages:
                return False
            if max_pages and pages > max_pages:
                return False
            return True
        filtered_books = [book for book in filtered_books if filter_by_pages(book)]
    
    # Filtrer par langue si spécifié
    if language:
        filtered_books = [book for book in filtered_books 
                         if any(language.lower() in str(pub).lower() 
                               for pub in book.get("publisher", []))]
    
    # Mapper les résultats
    mapped_books = []
    for book in filtered_books:
        mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
        mapped_book["ol_key"] = book.get("key")
        mapped_books.append(mapped_book)
    
    return {
        "total": len(mapped_books),
        "books": mapped_books,
        "filters_applied": {
            "year_range": f"{year_start or 'début'}-{year_end or 'fin'}" if year_start or year_end else None,
            "language": language,
            "pages_range": f"{min_pages or 0}-{max_pages or '∞'}" if min_pages or max_pages else None,
            "author_filter": author_filter
        }
    }

@app.get("/api/openlibrary/search-advanced")
async def search_openlibrary_advanced(
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    publisher: Optional[str] = None,
    isbn: Optional[str] = None,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    limit: int = 15
):
    """Recherche avancée avec critères multiples"""
    query_parts = []
    
    if title:
        query_parts.append(f"title:{title}")
    if author:
        query_parts.append(f"author:{author}")
    if subject:
        query_parts.append(f"subject:{subject}")
    if publisher:
        query_parts.append(f"publisher:{publisher}")
    if isbn:
        query_parts.append(f"isbn:{isbn}")
    
    if not query_parts:
        raise HTTPException(status_code=400, detail="Au moins un critère de recherche est requis")
    
    search_query = " AND ".join(query_parts)
    
    if year_start and year_end:
        search_query = f"{search_query} AND publish_year:[{year_start} TO {year_end}]"
    elif year_start:
        search_query = f"{search_query} AND publish_year:[{year_start} TO *]"
    elif year_end:
        search_query = f"{search_query} AND publish_year:[* TO {year_end}]"
    
    result = await OpenLibraryService.search_books(search_query, limit)
    
    # Mapper les résultats
    mapped_books = []
    for book in result.get("docs", []):
        mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
        mapped_book["ol_key"] = book.get("key")
        mapped_books.append(mapped_book)
    
    return {
        "total": result.get("numFound", 0),
        "books": mapped_books,
        "query_used": search_query
    }

@app.get("/api/openlibrary/search-isbn")
async def search_by_isbn(isbn: str):
    """Recherche par ISBN spécifique"""
    if not isbn:
        raise HTTPException(status_code=400, detail="ISBN requis")
    
    # Nettoyer l'ISBN
    clean_isbn = isbn.replace("-", "").replace(" ", "")
    
    try:
        # Rechercher par ISBN
        result = await OpenLibraryService.search_books(f"isbn:{clean_isbn}", 5)
        
        if not result.get("docs"):
            # Essayer avec l'API Books directement
            book_data = await OpenLibraryService.get_book_by_isbn(clean_isbn)
            if book_data:
                # Convertir les données de l'API Books au format de recherche
                mapped_book = {
                    "title": book_data.get("title", "Titre inconnu"),
                    "author": ", ".join([auth.get("name", "Auteur inconnu") 
                                       for auth in book_data.get("authors", [])]),
                    "category": "roman",  # Défaut
                    "description": book_data.get("subtitle", ""),
                    "total_pages": book_data.get("number_of_pages"),
                    "isbn": clean_isbn,
                    "publication_year": book_data.get("publish_date"),
                    "publisher": ", ".join(book_data.get("publishers", [])),
                    "ol_key": book_data.get("key", f"/books/{clean_isbn}")
                }
                return {
                    "total": 1,
                    "books": [mapped_book],
                    "source": "books_api"
                }
            else:
                raise HTTPException(status_code=404, detail="Aucun livre trouvé pour cet ISBN")
        
        # Mapper les résultats de la recherche normale
        mapped_books = []
        for book in result.get("docs", []):
            mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
            mapped_book["ol_key"] = book.get("key")
            mapped_books.append(mapped_book)
        
        return {
            "total": len(mapped_books),
            "books": mapped_books,
            "isbn_searched": clean_isbn,
            "source": "search_api"
        }
        
    except Exception as e:
        print(f"Erreur lors de la recherche par ISBN: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche par ISBN")

@app.get("/api/openlibrary/search-author")
async def search_by_author(author: str, limit: int = 20):
    """Recherche spécialisée par auteur"""
    if not author:
        raise HTTPException(status_code=400, detail="Nom d'auteur requis")
    
    search_query = f"author:{author}"
    result = await OpenLibraryService.search_books(search_query, limit)
    
    # Grouper par série/saga si possible
    books_by_series = {}
    standalone_books = []
    
    for book in result.get("docs", []):
        mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
        mapped_book["ol_key"] = book.get("key")
        
        # Essayer de détecter les séries dans le titre
        title = book.get("title", "")
        series_indicators = ["tome", "volume", "vol.", "book", "#", "part"]
        
        is_series = any(indicator in title.lower() for indicator in series_indicators)
        if is_series:
            # Extraction simple du nom de série
            series_name = title.split(" - ")[0] if " - " in title else title.split(" tome")[0] if " tome" in title.lower() else title.split(" volume")[0] if " volume" in title.lower() else title.split(" #")[0] if " #" in title else title
            series_name = series_name.strip()
            
            if series_name not in books_by_series:
                books_by_series[series_name] = []
            books_by_series[series_name].append(mapped_book)
        else:
            standalone_books.append(mapped_book)
    
    return {
        "total": result.get("numFound", 0),
        "author": author,
        "series": [{"name": name, "books": books} for name, books in books_by_series.items()],
        "standalone_books": standalone_books,
        "total_series": len(books_by_series),
        "total_standalone": len(standalone_books)
    }

@app.post("/api/openlibrary/import-bulk")
async def import_bulk_from_openlibrary(request: dict):
    """Import en lot de plusieurs livres"""
    books_to_import = request.get("books", [])
    
    if not books_to_import:
        raise HTTPException(status_code=400, detail="Aucun livre à importer")
    
    results = {
        "imported": [],
        "skipped": [],
        "errors": []
    }
    
    for book_data in books_to_import:
        try:
            ol_key = book_data.get("ol_key")
            category = book_data.get("category", "roman")
            
            if not ol_key:
                results["errors"].append({
                    "book": book_data.get("title", "Titre inconnu"),
                    "error": "Clé Open Library manquante"
                })
                continue
            
            # Vérifier si le livre existe déjà
            search_result = await OpenLibraryService.search_books(f"key:{ol_key}")
            if not search_result.get("docs"):
                results["errors"].append({
                    "book": book_data.get("title", "Titre inconnu"),
                    "error": "Livre non trouvé sur Open Library"
                })
                continue
            
            ol_book = search_result["docs"][0]
            mapped_book = OpenLibraryService.map_openlibrary_to_booktime(ol_book, category)
            
            # Vérifier les doublons
            existing_book = None
            if mapped_book.get("isbn"):
                existing_book = await books_collection.find_one({"isbn": mapped_book["isbn"]})
            
            if not existing_book:
                existing_book = await books_collection.find_one({
                    "title": {"$regex": mapped_book["title"], "$options": "i"},
                    "author": {"$regex": mapped_book["author"], "$options": "i"}
                })
            
            if existing_book:
                results["skipped"].append({
                    "book": mapped_book["title"],
                    "reason": "Déjà dans la collection"
                })
                continue
            
            # Importer le livre
            mapped_book["_id"] = str(uuid.uuid4())
            mapped_book["status"] = "to_read"
            mapped_book["current_page"] = 0
            mapped_book["date_added"] = datetime.utcnow()
            mapped_book["category"] = category.lower()
            
            result = await books_collection.insert_one(mapped_book)
            if result.inserted_id:
                created_book = await books_collection.find_one({"_id": mapped_book["_id"]})
                created_book["_id"] = str(created_book["_id"])
                results["imported"].append(Book(**created_book))
            
        except Exception as e:
            results["errors"].append({
                "book": book_data.get("title", "Titre inconnu"),
                "error": str(e)
            })
    
    return {
        "summary": {
            "total_requested": len(books_to_import),
            "imported": len(results["imported"]),
            "skipped": len(results["skipped"]),
            "errors": len(results["errors"])
        },
        "results": results
    }

@app.get("/api/openlibrary/recommendations")
async def get_personalized_recommendations(limit: int = 10):
    """Obtenir des recommandations personnalisées basées sur la collection"""
    # Analyser la collection existante
    user_books = []
    async for book in books_collection.find({}):
        user_books.append(book)
    
    if not user_books:
        raise HTTPException(status_code=400, detail="Collection vide - impossible de générer des recommandations")
    
    # Analyser les préférences
    authors = {}
    categories = {}
    genres = {}
    
    for book in user_books:
        # Compter les auteurs préférés
        author = book.get("author", "")
        authors[author] = authors.get(author, 0) + 1
        
        # Compter les catégories préférées
        category = book.get("category", "")
        categories[category] = categories.get(category, 0) + 1
        
        # Compter les genres préférés
        book_genres = book.get("genre", [])
        for genre in book_genres:
            genres[genre] = genres.get(genre, 0) + 1
    
    # Obtenir les auteurs et genres favoris
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:3]
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:2]
    top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]
    
    recommendations = []
    
    # Rechercher des livres d'auteurs similaires
    for author, count in top_authors:
        if len(recommendations) >= limit:
            break
        try:
            result = await OpenLibraryService.search_books(f"author:{author}", 5)
            for book in result.get("docs", []):
                if len(recommendations) >= limit:
                    break
                
                # Vérifier si pas déjà dans la collection
                title = book.get("title", "")
                existing = any(
                    title.lower() in existing_book.get("title", "").lower() or 
                    existing_book.get("title", "").lower() in title.lower()
                    for existing_book in user_books
                )
                
                if not existing:
                    mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
                    mapped_book["ol_key"] = book.get("key")
                    mapped_book["recommendation_reason"] = f"Basé sur votre appréciation de {author}"
                    recommendations.append(mapped_book)
        except Exception as e:
            print(f"Erreur lors de la recherche pour {author}: {e}")
    
    # Rechercher par genres favoris
    for genre, count in top_genres:
        if len(recommendations) >= limit:
            break
        try:
            result = await OpenLibraryService.search_books(f"subject:{genre}", 3)
            for book in result.get("docs", []):
                if len(recommendations) >= limit:
                    break
                
                title = book.get("title", "")
                existing = any(
                    title.lower() in existing_book.get("title", "").lower() or 
                    existing_book.get("title", "").lower() in title.lower()
                    for existing_book in user_books
                )
                
                if not existing and not any(rec.get("title") == title for rec in recommendations):
                    mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
                    mapped_book["ol_key"] = book.get("key")
                    mapped_book["recommendation_reason"] = f"Basé sur votre intérêt pour {genre}"
                    recommendations.append(mapped_book)
        except Exception as e:
            print(f"Erreur lors de la recherche pour {genre}: {e}")
    
    return {
        "total": len(recommendations),
        "recommendations": recommendations[:limit],
        "based_on": {
            "top_authors": [author for author, count in top_authors],
            "top_categories": [cat for cat, count in top_categories],
            "top_genres": [genre for genre, count in top_genres]
        }
    }

@app.get("/api/openlibrary/missing-volumes")
async def detect_missing_saga_volumes(saga: str):
    """Détecter les tomes manquants d'une saga"""
    # Récupérer les livres de la saga dans la collection
    saga_books = []
    async for book in books_collection.find({"saga": saga}).sort("volume_number", 1):
        saga_books.append(book)
    
    if not saga_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée dans votre collection")
    
    # Analyser les tomes présents
    present_volumes = []
    author = saga_books[0].get("author", "")
    category = saga_books[0].get("category", "roman")
    
    for book in saga_books:
        vol_num = book.get("volume_number")
        if vol_num:
            present_volumes.append(vol_num)
    
    present_volumes.sort()
    
    # Détecter les trous dans la séquence
    missing_volumes = []
    if present_volumes:
        for i in range(1, max(present_volumes) + 1):
            if i not in present_volumes:
                missing_volumes.append(i)
    
    # Rechercher les tomes manquants sur Open Library
    found_missing = []
    
    for vol_num in missing_volumes:
        search_queries = [
            f"{saga} tome {vol_num} {author}",
            f"{saga} volume {vol_num} {author}",
            f"{saga} vol {vol_num} {author}",
            f"{saga} #{vol_num} {author}"
        ]
        
        for query in search_queries:
            try:
                result = await OpenLibraryService.search_books(query, 3)
                for book in result.get("docs", []):
                    title = book.get("title", "")
                    if (str(vol_num) in title or 
                        f"tome {vol_num}" in title.lower() or 
                        f"volume {vol_num}" in title.lower()):
                        
                        mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book, category)
                        mapped_book["ol_key"] = book.get("key")
                        mapped_book["suggested_volume"] = vol_num
                        found_missing.append(mapped_book)
                        break
                if found_missing and found_missing[-1].get("suggested_volume") == vol_num:
                    break
            except Exception as e:
                print(f"Erreur lors de la recherche du tome {vol_num}: {e}")
    
    # Chercher les tomes suivants (après le dernier tome)
    next_volumes = []
    if present_volumes:
        max_vol = max(present_volumes)
        for next_vol in range(max_vol + 1, max_vol + 4):  # Chercher 3 tomes suivants
            search_queries = [
                f"{saga} tome {next_vol} {author}",
                f"{saga} volume {next_vol} {author}",
                f"{saga} vol {next_vol} {author}"
            ]
            
            for query in search_queries:
                try:
                    result = await OpenLibraryService.search_books(query, 2)
                    for book in result.get("docs", []):
                        title = book.get("title", "")
                        if (str(next_vol) in title or 
                            f"tome {next_vol}" in title.lower() or 
                            f"volume {next_vol}" in title.lower()):
                            
                            mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book, category)
                            mapped_book["ol_key"] = book.get("key")
                            mapped_book["suggested_volume"] = next_vol
                            next_volumes.append(mapped_book)
                            break
                    if next_volumes and next_volumes[-1].get("suggested_volume") == next_vol:
                        break
                except Exception as e:
                    print(f"Erreur lors de la recherche du tome {next_vol}: {e}")
    
    return {
        "saga": saga,
        "author": author,
        "present_volumes": present_volumes,
        "missing_volumes": missing_volumes,
        "found_missing": found_missing,
        "suggested_next": next_volumes,
        "total_present": len(present_volumes),
        "total_missing": len(missing_volumes),
        "total_found": len(found_missing),
        "total_next": len(next_volumes)
    }

@app.get("/api/openlibrary/suggestions")
async def get_import_suggestions(limit: int = 15):
    """Obtenir des suggestions d'import basées sur la collection"""
    # Analyser la collection pour les suggestions
    user_books = []
    async for book in books_collection.find({}):
        user_books.append(book)
    
    suggestions = []
    
    # Suggestions basées sur les sagas incomplètes
    sagas = {}
    for book in user_books:
        saga = book.get("saga")
        if saga:
            if saga not in sagas:
                sagas[saga] = []
            sagas[saga].append(book)
    
    # Pour chaque saga, suggérer le tome suivant
    for saga_name, saga_books in sagas.items():
        if len(suggestions) >= limit:
            break
        
        volumes = [book.get("volume_number", 0) for book in saga_books if book.get("volume_number")]
        if volumes:
            next_volume = max(volumes) + 1
            author = saga_books[0].get("author", "")
            category = saga_books[0].get("category", "roman")
            
            # Rechercher le tome suivant
            search_query = f"{saga_name} tome {next_volume} {author}"
            try:
                result = await OpenLibraryService.search_books(search_query, 3)
                for book in result.get("docs", []):
                    title = book.get("title", "")
                    if str(next_volume) in title or f"tome {next_volume}" in title.lower():
                        mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book, category)
                        mapped_book["ol_key"] = book.get("key")
                        mapped_book["suggestion_type"] = "saga_continuation"
                        mapped_book["suggestion_reason"] = f"Tome {next_volume} de {saga_name}"
                        suggestions.append(mapped_book)
                        break
            except Exception as e:
                print(f"Erreur lors de la suggestion pour {saga_name}: {e}")
    
    # Suggestions basées sur les auteurs favoris
    authors = {}
    for book in user_books:
        author = book.get("author", "")
        if author:
            authors[author] = authors.get(author, 0) + 1
    
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for author, count in top_authors:
        if len(suggestions) >= limit:
            break
        
        try:
            result = await OpenLibraryService.search_books(f"author:{author}", 5)
            for book in result.get("docs", []):
                if len(suggestions) >= limit:
                    break
                
                # Vérifier si pas déjà dans la collection
                title = book.get("title", "")
                existing = any(
                    title.lower() in existing_book.get("title", "").lower() or 
                    existing_book.get("title", "").lower() in title.lower()
                    for existing_book in user_books
                )
                
                if not existing and not any(s.get("title") == title for s in suggestions):
                    mapped_book = OpenLibraryService.map_openlibrary_to_booktime(book)
                    mapped_book["ol_key"] = book.get("key")
                    mapped_book["suggestion_type"] = "favorite_author"
                    mapped_book["suggestion_reason"] = f"Nouveau livre de {author} ({count} livres dans votre collection)"
                    suggestions.append(mapped_book)
        except Exception as e:
            print(f"Erreur lors des suggestions pour {author}: {e}")
    
    return {
        "total": len(suggestions),
        "suggestions": suggestions[:limit],
        "types": {
            "saga_continuation": len([s for s in suggestions if s.get("suggestion_type") == "saga_continuation"]),
            "favorite_author": len([s for s in suggestions if s.get("suggestion_type") == "favorite_author"])
        }
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