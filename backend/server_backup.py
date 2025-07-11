from fastapi import FastAPI, HTTPException, Depends, status, Query
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
series_library_collection = db.series_library

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

# Modèles pour les séries en bibliothèque
class VolumeData(BaseModel):
    volume_number: int
    volume_title: str
    is_read: bool = False
    date_read: Optional[str] = None

class SeriesLibraryCreate(BaseModel):
    series_name: str
    authors: List[str]
    category: str
    volumes: List[VolumeData]
    description_fr: str = ""
    cover_image_url: str = ""
    first_published: str = ""
    last_published: str = ""
    publisher: str = ""
    series_status: str = "to_read"

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
@app.get("/api/library/series")
async def get_library_series(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les séries de la bibliothèque comme entités uniques.
    Chaque série est représentée comme UNE carte avec indicateur de progression.
    """
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    
    # Grouper les livres par saga avec informations de progression
    pipeline = [
        {"$match": {**filter_dict, "saga": {"$ne": "", "$exists": True}}},
        {"$group": {
            "_id": {
                "saga": "$saga",
                "author": "$author",
                "category": "$category"
            },
            "books_count": {"$sum": 1},
            "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "reading_books": {"$sum": {"$cond": [{"$eq": ["$status", "reading"]}, 1, 0]}},
            "to_read_books": {"$sum": {"$cond": [{"$eq": ["$status", "to_read"]}, 1, 0]}},
            "first_added": {"$min": "$date_added"},
            "last_updated": {"$max": "$updated_at"},
            "cover_url": {"$first": "$cover_url"},  # Prendre la première couverture disponible
            "max_volume": {"$max": "$volume_number"},
            "books": {"$push": {
                "id": "$id",
                "title": "$title", 
                "volume_number": "$volume_number",
                "status": "$status",
                "cover_url": "$cover_url"
            }}
        }},
        {"$sort": {"last_updated": -1, "first_added": -1}}
    ]
    
    series_data = list(books_collection.aggregate(pipeline))
    
    # Formater les données pour l'affichage en cartes séries
    formatted_series = []
    for series in series_data:
        # Calculer le pourcentage de progression
        completion_percentage = 0
        if series["books_count"] > 0:
            completion_percentage = round((series["completed_books"] / series["books_count"]) * 100)
        
        # Déterminer le statut global de la série
        global_status = "to_read"
        if series["reading_books"] > 0:
            global_status = "reading"
        elif series["completed_books"] == series["books_count"]:
            global_status = "completed"
        
        # Trouver la meilleure couverture (priorité aux derniers tomes)
        best_cover = ""
        if series["books"]:
            sorted_books = sorted(series["books"], key=lambda x: x.get("volume_number", 0), reverse=True)
            for book in sorted_books:
                if book.get("cover_url"):
                    best_cover = book["cover_url"]
                    break
        
        formatted_series.append({
            "id": f"series_{series['_id']['saga'].lower().replace(' ', '_')}",
            "name": series["_id"]["saga"],
            "author": series["_id"]["author"],
            "category": series["_id"]["category"],
            "isSeriesCard": True,
            "isOwnedSeries": True,  # Marquer comme série possédée
            "total_books": series["books_count"],
            "completed_books": series["completed_books"],
            "reading_books": series["reading_books"],
            "to_read_books": series["to_read_books"],
            "completion_percentage": completion_percentage,
            "status": global_status,
            "cover_url": best_cover,
            "max_volume": series["max_volume"] or 0,
            "first_added": series["first_added"],
            "last_updated": series["last_updated"],
            "progress_text": f"{series['completed_books']}/{series['books_count']} tomes lus",
            "books": series["books"]  # Liste des tomes pour la fiche détaillée
        })
    
    return formatted_series

@app.get("/api/books")
async def get_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    view_mode: Optional[str] = "books",  # "books" ou "series"
    current_user: dict = Depends(get_current_user)
):
    """
    Route mise à jour pour supporter l'affichage par séries ou par livres individuels.
    """
    # Si le mode série est demandé, retourner les séries comme entités uniques
    if view_mode == "series":
        return await get_library_series(category, current_user)
    
    # Mode livres classique : retourner tous les livres individuels SAUF ceux qui font partie d'une série
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    if status:
        filter_dict["status"] = status
    
    # Exclure les livres qui font partie d'une série (pour éviter la duplication)
    # En mode livres, on ne montre que les livres isolés
    filter_dict["$or"] = [
        {"saga": {"$exists": False}},
        {"saga": ""},
        {"saga": None}
    ]
    
    books = list(books_collection.find(filter_dict, {"_id": 0}))
    return books

@app.get("/api/books/search-grouped")
async def search_books_grouped(
    q: str,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche de livres avec regroupement intelligent par saga - SÉRIE FIRST
    """
    if not q or len(q.strip()) < 2:
        return {"results": [], "total_books": 0, "total_sagas": 0, "search_term": q}
    
    search_term = q.strip().lower()
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    
    # Recherche dans tous les champs pertinents
    search_filter = {
        "$or": [
            {"title": {"$regex": re.escape(search_term), "$options": "i"}},
            {"author": {"$regex": re.escape(search_term), "$options": "i"}},
            {"saga": {"$regex": re.escape(search_term), "$options": "i"}},
            {"description": {"$regex": re.escape(search_term), "$options": "i"}},
            {"genre": {"$regex": re.escape(search_term), "$options": "i"}},
            {"publisher": {"$regex": re.escape(search_term), "$options": "i"}}
        ]
    }
    
    # Combiner les filtres
    final_filter = {"$and": [filter_dict, search_filter]}
    
    # Récupérer tous les livres correspondants
    matching_books = list(books_collection.find(final_filter, {"_id": 0}))
    
    if not matching_books:
        return {"results": [], "total_books": 0, "total_sagas": 0, "search_term": q}
    
    # NOUVELLE LOGIQUE: Grouper TOUS les livres par saga d'abord
    saga_groups = {}
    books_without_saga = []
    
    for book in matching_books:
        saga = book.get("saga", "").strip()
        
        if saga:  # Si le livre appartient à une saga
            if saga not in saga_groups:
                saga_groups[saga] = {
                    "type": "saga",
                    "id": f"saga_{saga.lower().replace(' ', '_')}",
                    "name": saga,
                    "books": [],
                    "total_books": 0,
                    "completed_books": 0,
                    "reading_books": 0,
                    "to_read_books": 0,
                    "author": book.get("author", ""),
                    "category": book.get("category", "roman"),
                    "cover_url": book.get("cover_url", ""),
                    "latest_volume": 0,
                    "status": "to_read",  # Statut global de la série
                    "match_reason": "saga_match" if saga.lower().find(search_term) != -1 else "title_match"
                }
            
            saga_groups[saga]["books"].append(book)
            saga_groups[saga]["total_books"] += 1
            
            # Compter par statut
            status = book.get("status", "to_read")
            if status == "completed":
                saga_groups[saga]["completed_books"] += 1
            elif status == "reading":
                saga_groups[saga]["reading_books"] += 1
            else:
                saga_groups[saga]["to_read_books"] += 1
            
            # Trouver le dernier tome
            volume = book.get("volume_number", 0)
            if volume > saga_groups[saga]["latest_volume"]:
                saga_groups[saga]["latest_volume"] = volume
                
            # Mise à jour de la couverture avec le dernier tome
            if volume > 0 and book.get("cover_url"):
                saga_groups[saga]["cover_url"] = book.get("cover_url")
        else:
            # Livre sans saga
            books_without_saga.append({
                "type": "book",
                **book,
                "match_reason": "individual_book"
            })
    
    # Calculer le statut global des sagas
    for saga_name, saga_data in saga_groups.items():
        # Pourcentage de completion
        completion_percentage = 0
        if saga_data["total_books"] > 0:
            completion_percentage = round((saga_data["completed_books"] / saga_data["total_books"]) * 100)
        saga_data["completion_percentage"] = completion_percentage
        
        # Statut global de la série
        if saga_data["reading_books"] > 0:
            saga_data["status"] = "reading"
        elif saga_data["completed_books"] == saga_data["total_books"]:
            saga_data["status"] = "completed"
        else:
            saga_data["status"] = "to_read"
        
        # Trier les livres par numéro de tome
        saga_data["books"].sort(key=lambda x: x.get("volume_number", 0))
    
    # Préparer les résultats finaux - SÉRIE FIRST
    results = []
    
    # 1. D'abord toutes les sagas trouvées (triées par pertinence puis par nombre de livres)
    sorted_sagas = sorted(saga_groups.values(), key=lambda x: (
        -1 if x["match_reason"] == "saga_match" else 0,  # Priorité aux matchs sur le nom de saga
        -x["total_books"],  # Puis par nombre de livres
        x["name"].lower()  # Puis par ordre alphabétique
    ))
    
    results.extend(sorted_sagas)
    
    # 2. Ensuite les livres individuels SEULEMENT s'ils ne font pas partie d'une saga
    # Et seulement si moins de 3 sagas trouvées (pour éviter l'encombrement)
    if len(saga_groups) < 3:
        results.extend(books_without_saga)
    
    return {
        "results": results,
        "total_books": len(matching_books),
        "total_sagas": len(saga_groups),
        "search_term": q,
        "grouped_by_saga": True,
        "series_first": True
    }

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
        **book_data.model_dump(),
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
    
    update_data = book_update.model_dump(exclude_unset=True)
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

# Routes pour les séries étendues
@app.get("/api/series/popular")
async def get_popular_series(
    category: Optional[str] = None,
    language: Optional[str] = "fr",
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer la liste des séries populaires avec métadonnées complètes
    """
    # Mapping complet des séries populaires (côté backend)
    series_data = {
        # ROMANS FANTASY/SF
        "harry_potter": {
            "name": "Harry Potter",
            "category": "roman",
            "score": 18000,
            "keywords": ["harry", "potter", "hogwarts", "sorcier", "wizard", "poudlard", "voldemort"],
            "authors": ["J.K. Rowling"],
            "variations": ["Harry Potter", "École des Sorciers", "Chambre des Secrets"],
            "volumes": 7,
            "languages": ["fr", "en"],
            "description": "La saga emblématique du jeune sorcier Harry Potter",
            "first_published": 1997,
            "status": "completed"
        },
        "seigneur_des_anneaux": {
            "name": "Le Seigneur des Anneaux",
            "category": "roman",
            "score": 18000,
            "keywords": ["anneau", "terre du milieu", "hobbit", "frodo", "gandalf"],
            "authors": ["J.R.R. Tolkien"],
            "variations": ["Seigneur des Anneaux", "Lord of the Rings"],
            "volumes": 3,
            "languages": ["fr", "en"],
            "description": "L'épopée fantasy légendaire de Tolkien",
            "first_published": 1954,
            "status": "completed"
        },
        "game_of_thrones": {
            "name": "Game of Thrones",
            "category": "roman",
            "score": 16000,
            "keywords": ["trône de fer", "westeros", "stark", "lannister"],
            "authors": ["George R.R. Martin"],
            "variations": ["Game of Thrones", "Trône de Fer"],
            "volumes": 5,
            "languages": ["fr", "en"],
            "description": "La saga politique et fantastique de Westeros",
            "first_published": 1996,
            "status": "ongoing"
        },
        # MANGAS
        "one_piece": {
            "name": "One Piece",
            "category": "manga",
            "score": 18000,
            "keywords": ["luffy", "pirates", "chapeau de paille", "grand line"],
            "authors": ["Eiichiro Oda"],
            "variations": ["One Piece"],
            "volumes": 108,
            "languages": ["fr", "en", "jp"],
            "description": "L'aventure du pirate Luffy à la recherche du One Piece",
            "first_published": 1997,
            "status": "ongoing"
        },
        "naruto": {
            "name": "Naruto",
            "category": "manga",
            "score": 17000,
            "keywords": ["naruto", "ninja", "konoha", "sasuke", "hokage"],
            "authors": ["Masashi Kishimoto"],
            "variations": ["Naruto", "Boruto"],
            "volumes": 72,
            "languages": ["fr", "en", "jp"],
            "description": "L'histoire du ninja Naruto Uzumaki",
            "first_published": 1999,
            "status": "completed"
        },
        "dragon_ball": {
            "name": "Dragon Ball",
            "category": "manga",
            "score": 17000,
            "keywords": ["goku", "saiyan", "kamehameha", "vegeta"],
            "authors": ["Akira Toriyama"],
            "variations": ["Dragon Ball", "Dragon Ball Z", "Dragon Ball Super"],
            "volumes": 42,
            "languages": ["fr", "en", "jp"],
            "description": "Les aventures de Son Goku et des Dragon Balls",
            "first_published": 1984,
            "status": "completed"
        },
        # BANDES DESSINÉES
        "asterix": {
            "name": "Astérix",
            "category": "bd",
            "score": 18000,
            "keywords": ["astérix", "obélix", "gaulois", "potion magique"],
            "authors": ["René Goscinny", "Albert Uderzo"],
            "variations": ["Astérix", "Asterix"],
            "volumes": 39,
            "languages": ["fr", "en"],
            "description": "Les aventures du petit gaulois Astérix",
            "first_published": 1959,
            "status": "ongoing"
        },
        "tintin": {
            "name": "Tintin",
            "category": "bd",
            "score": 18000,
            "keywords": ["tintin", "milou", "capitaine haddock", "tournesol"],
            "authors": ["Hergé"],
            "variations": ["Tintin", "Aventures de Tintin"],
            "volumes": 24,
            "languages": ["fr", "en"],
            "description": "Les aventures du jeune reporter Tintin",
            "first_published": 1929,
            "status": "completed"
        }
    }
    
    # Filtrer par catégorie si spécifiée
    filtered_series = {}
    for key, series in series_data.items():
        if category and series["category"] != category:
            continue
        if language and language not in series["languages"]:
            continue
        filtered_series[key] = series
    
    # Trier par score et limiter
    sorted_series = sorted(
        filtered_series.items(), 
        key=lambda x: x[1]["score"], 
        reverse=True
    )[:limit]
    
    return {
        "series": [series[1] for series in sorted_series],
        "total": len(sorted_series),
        "category": category,
        "language": language
    }

@app.get("/api/series/search")
async def search_series(
    q: str,
    category: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche de séries par nom avec scoring de pertinence
    """
    if not q or len(q.strip()) < 2:
        return {"series": [], "total": 0, "search_term": q}
    
    search_term = q.strip().lower()
    
    # Récupérer les séries populaires
    series_response = await get_popular_series(category=category, limit=1000, current_user=current_user)
    all_series = series_response["series"]
    
    matching_series = []
    
    for series in all_series:
        score = 0
        match_reasons = []
        
        # Correspondance exacte du nom
        if series["name"].lower() == search_term:
            score += 10000
            match_reasons.append("exact_name")
        # Correspondance partielle du nom
        elif search_term in series["name"].lower():
            if series["name"].lower().startswith(search_term):
                score += 8000
                match_reasons.append("name_starts_with")
            else:
                score += 5000
                match_reasons.append("name_contains")
        
        # Correspondance variations
        for variation in series["variations"]:
            if variation.lower() == search_term:
                score += 9000
                match_reasons.append("exact_variation")
                break
            elif search_term in variation.lower():
                score += 4000
                match_reasons.append("variation_contains")
        
        # Correspondance auteur
        for author in series["authors"]:
            if search_term in author.lower():
                score += 3000
                match_reasons.append("author_match")
                break
        
        # Correspondance mots-clés
        keyword_matches = 0
        for keyword in series["keywords"]:
            if keyword in search_term or search_term in keyword:
                keyword_matches += 1
        
        if keyword_matches > 0:
            score += keyword_matches * 1000
            match_reasons.append(f"keywords_{keyword_matches}")
        
        # Bonus pour séries populaires
        score += series.get("score", 0) // 10
        
        if score > 500:  # Seuil de pertinence
            matching_series.append({
                **series,
                "isSeriesCard": True,
                "search_score": score,
                "match_reasons": match_reasons
            })
    
    # Trier par score de pertinence
    matching_series.sort(key=lambda x: x["search_score"], reverse=True)
    
    return {
        "series": matching_series[:limit],
        "total": len(matching_series),
        "search_term": q
    }

@app.get("/api/series/detect")
async def detect_series_from_book(
    title: str,
    author: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Détecter automatiquement à quelle série appartient un livre
    """
    # Récupérer les séries populaires
    series_response = await get_popular_series(limit=100, current_user=current_user)
    series_list = series_response["series"]
    
    detected_series = []
    title_lower = title.lower()
    author_lower = author.lower() if author else ""
    
    for series in series_list:
        confidence = 0
        match_reasons = []
        
        # Vérification auteur
        if author and any(a.lower() in author_lower for a in series["authors"]):
            confidence += 80
            match_reasons.append("author_match")
        
        # Vérification variations dans le titre
        for variation in series["variations"]:
            if variation.lower() in title_lower:
                confidence += 60
                match_reasons.append("title_variation")
                break
        
        # Vérification mots-clés
        keyword_matches = 0
        for keyword in series["keywords"]:
            if keyword in title_lower:
                keyword_matches += 1
        
        if keyword_matches > 0:
            confidence += keyword_matches * 20
            match_reasons.append(f"keywords_match_{keyword_matches}")
        
        # Seuil de confiance
        if confidence >= 60:
            detected_series.append({
                "series": series,
                "confidence": confidence,
                "match_reasons": match_reasons
            })
    
    # Trier par confiance
    detected_series.sort(key=lambda x: x["confidence"], reverse=True)
    
    return {
        "detected_series": detected_series[:5],  # Top 5
        "book_info": {
            "title": title,
            "author": author
        }
    }

@app.post("/api/series/complete")
async def auto_complete_series(
    series_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Auto-compléter une série en ajoutant tous les volumes manquants
    """
    series_name = series_data.get("series_name")
    target_volumes = series_data.get("target_volumes", 10)
    template_book_id = series_data.get("template_book_id")
    
    if not series_name:
        raise HTTPException(status_code=400, detail="Nom de série requis")
    
    # Base de données des séries pour obtenir les informations par défaut
    SERIES_INFO = {
        "Le Seigneur des Anneaux": {
            "author": "J.R.R. Tolkien",
            "category": "roman",
            "volumes": 3,
            "tomes": ["La Communauté de l'Anneau", "Les Deux Tours", "Le Retour du Roi"]
        },
        "Harry Potter": {
            "author": "J.K. Rowling", 
            "category": "roman",
            "volumes": 7,
            "tomes": [
                "Harry Potter à l'école des sorciers",
                "Harry Potter et la Chambre des secrets", 
                "Harry Potter et le Prisonnier d'Azkaban",
                "Harry Potter et la Coupe de feu",
                "Harry Potter et l'Ordre du phénix",
                "Harry Potter et le Prince de sang-mêlé",
                "Harry Potter et les Reliques de la Mort"
            ]
        },
        "One Piece": {
            "author": "Eiichiro Oda",
            "category": "manga", 
            "volumes": 100,
            "tomes": []
        },
        "Naruto": {
            "author": "Masashi Kishimoto",
            "category": "manga",
            "volumes": 72,
            "tomes": []
        },
        "Astérix": {
            "author": "René Goscinny et Albert Uderzo",
            "category": "bd",
            "volumes": 39,
            "tomes": []
        }
    }
    
    # Récupérer le livre modèle si existe
    template_book = None
    if template_book_id:
        template_book = books_collection.find_one({
            "id": template_book_id,
            "user_id": current_user["id"]
        })
    
    # Sinon, chercher un livre de cette série
    if not template_book:
        template_book = books_collection.find_one({
            "user_id": current_user["id"],
            "saga": {"$regex": re.escape(series_name), "$options": "i"}
        })
    
    # Si pas de livre modèle, utiliser les informations de la base de données
    series_info = SERIES_INFO.get(series_name)
    if not template_book and not series_info:
        raise HTTPException(status_code=404, detail="Série non reconnue et aucun livre modèle trouvé")
    
    # Déterminer les informations de base
    if template_book:
        base_author = template_book.get("author", "")
        base_category = template_book.get("category", "roman")
        base_genre = template_book.get("genre", "")
        base_publisher = template_book.get("publisher", "")
    elif series_info:
        base_author = series_info["author"]
        base_category = series_info["category"]
        base_genre = ""
        base_publisher = ""
        if series_info["volumes"] < target_volumes:
            target_volumes = series_info["volumes"]
    
    # Récupérer les volumes existants
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": {"$regex": re.escape(series_name), "$options": "i"}
    }))
    
    existing_volumes = set()
    for book in existing_books:
        vol_num = book.get("volume_number", 0)
        if vol_num > 0:
            existing_volumes.add(vol_num)
    
    # Créer les volumes manquants
    created_books = []
    for vol_num in range(1, target_volumes + 1):
        if vol_num not in existing_volumes:
            book_id = str(uuid.uuid4())
            
            # Déterminer le titre du tome
            if series_info and series_info.get("tomes") and vol_num <= len(series_info["tomes"]):
                tome_title = series_info["tomes"][vol_num - 1]
            else:
                tome_title = f"{series_name} - Tome {vol_num}"
            
            new_book = {
                "id": book_id,
                "user_id": current_user["id"],
                "title": tome_title,
                "author": base_author,
                "category": base_category,
                "saga": series_name,
                "volume_number": vol_num,
                "status": "to_read",
                "auto_added": True,
                "date_added": datetime.utcnow(),
                "description": f"Tome {vol_num} de la série {series_name}",
                "total_pages": None,
                "current_page": None,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": base_genre,
                "publication_year": None,
                "publisher": base_publisher,
                "isbn": "",
                "date_started": None,
                "date_completed": None
            }
            
            books_collection.insert_one(new_book)
            new_book.pop("_id", None)
            created_books.append(new_book)
    
    return {
        "message": f"{len(created_books)} tome(s) ajouté(s) à la série {series_name}",
        "created_books": created_books,
        "series_name": series_name,
        "total_volumes": target_volumes,
        "existing_volumes": len(existing_volumes),
        "created_volumes": len(created_books)
    }
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
    user_filter = {"user_id": current_user["id"]}
    
    # Grouper les livres par saga
    pipeline = [
        {"$match": {**user_filter, "saga": {"$ne": ""}}},
        {"$group": {
            "_id": "$saga",
            "books_count": {"$sum": 1},
            "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "author": {"$first": "$author"},
            "category": {"$first": "$category"},
            "max_volume": {"$max": "$volume_number"},
            "volumes": {"$push": {"volume_number": "$volume_number", "status": "$status"}}
        }},
        {"$sort": {"books_count": -1}}
    ]
    
    sagas_data = list(books_collection.aggregate(pipeline))
    
    sagas = []
    for saga_data in sagas_data:
        # Calculer le prochain tome
        volumes = [v["volume_number"] for v in saga_data["volumes"] if v["volume_number"]]
        next_volume = max(volumes) + 1 if volumes else 1
        
        saga = {
            "name": saga_data["_id"],
            "books_count": saga_data["books_count"],
            "completed_books": saga_data["completed_books"],
            "author": saga_data["author"],
            "category": saga_data["category"],
            "next_volume": next_volume,
            "completion_percentage": round((saga_data["completed_books"] / saga_data["books_count"]) * 100) if saga_data["books_count"] > 0 else 0
        }
        sagas.append(saga)
    
    return sagas

@app.get("/api/sagas/{saga_name}/books")
async def get_saga_books(saga_name: str, current_user: dict = Depends(get_current_user)):
    """
    Récupérer les livres d'une série spécifique avec filtrage strict.
    Ne retourne QUE les livres appartenant exactement à cette série.
    """
    # Filtrage strict par série ET auteur spécifique
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }, {"_id": 0}).sort("volume_number", 1))
    
    if not books:
        return books
    
    # Obtenir l'auteur principal de la série (du premier livre trouvé)
    main_author = books[0].get("author", "").lower().strip()
    
    # Filtrer strictement par série ET auteur principal pour exclure :
    # - Les spin-offs par d'autres auteurs
    # - Les suites non-officielles  
    # - Les adaptations par d'autres créateurs
    # - Les continuations posthumes non autorisées
    filtered_books = []
    for book in books:
        book_author = book.get("author", "").lower().strip()
        book_title = book.get("title", "").lower()
        
        # Vérifications pour inclusion stricte
        include_book = True
        
        # 1. Vérifier que l'auteur correspond (avec tolérance pour co-auteurs)
        if main_author and book_author:
            # Accepter si l'auteur principal est mentionné dans l'auteur du livre
            # ou si le livre est du même auteur principal
            author_match = (
                main_author in book_author or 
                book_author in main_author or
                any(word in book_author for word in main_author.split() if len(word) > 2)
            )
            if not author_match:
                include_book = False
        
        # 2. Vérifier que le titre contient bien le nom de la série
        if saga_name.lower() not in book_title and not any(
            variant.lower() in book_title for variant in [
                saga_name.replace(" ", ""),  # Sans espaces
                saga_name.replace("-", " "),  # Tirets remplacés par espaces
            ]
        ):
            # Tolérance pour les titres de tomes qui peuvent être différents
            # mais seulement si c'est le même auteur principal
            if not author_match:
                include_book = False
        
        # 3. Exclure explicitement certains mots-clés suspects
        suspicious_keywords = [
            "spin-off", "spinoff", "hors-série", "guide", "artbook", 
            "companion", "compagnon", "making of", "adaptation", 
            "suite", "continuation", "legacy", "next generation",
            "prequel", "sequel", "side story"
        ]
        if any(keyword in book_title for keyword in suspicious_keywords):
            include_book = False
        
        if include_book:
            filtered_books.append(book)
    
    return filtered_books

@app.post("/api/sagas/{saga_name}/auto-add")
async def auto_add_next_volume(saga_name: str, current_user: dict = Depends(get_current_user)):
    # Trouver les livres existants de cette saga
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Calculer le prochain numéro de tome
    volumes = [book.get("volume_number", 0) for book in existing_books if book.get("volume_number")]
    next_volume = max(volumes) + 1 if volumes else 1
    
    # Utiliser les informations du premier livre comme modèle
    template_book = existing_books[0]
    
    # Créer le nouveau livre
    book_id = str(uuid.uuid4())
    new_book = {
        "id": book_id,
        "user_id": current_user["id"],
        "title": f"{saga_name} - Tome {next_volume}",
        "author": template_book.get("author", ""),
        "category": template_book.get("category", "roman"),
        "saga": saga_name,
        "volume_number": next_volume,
        "status": "to_read",
        "auto_added": True,
        "date_added": datetime.utcnow(),
        "date_started": None,
        "date_completed": None,
        "description": "",
        "total_pages": None,
        "current_page": None,
        "rating": None,
        "review": "",
        "cover_url": "",
        "genre": template_book.get("genre", ""),
        "publication_year": None,
        "publisher": "",
        "isbn": ""
    }
    
    books_collection.insert_one(new_book)
    new_book.pop("_id", None)
    
    return {"message": f"Tome {next_volume} ajouté à la saga {saga_name}", "book": new_book}

# Nouvelle API pour la gestion simplifiée des états de série
@app.put("/api/sagas/{saga_name}/bulk-status")
async def update_saga_bulk_status(
    saga_name: str,
    bulk_update: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Mise à jour en lot des statuts d'une série
    Format: {"tome_1": "completed", "tome_2": "to_read", ...}
    Ou: {"from_volume": 1, "to_volume": 10, "status": "completed"}
    """
    # Vérifier que la saga existe
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    updates_made = 0
    
    # Mise à jour par plage de volumes
    if "from_volume" in bulk_update and "to_volume" in bulk_update:
        from_vol = bulk_update["from_volume"]
        to_vol = bulk_update["to_volume"]
        new_status = bulk_update.get("status", "completed")
        
        for book in existing_books:
            vol_num = book.get("volume_number", 0)
            if from_vol <= vol_num <= to_vol:
                update_data = {"status": new_status, "updated_at": datetime.utcnow()}
                
                # Gérer les dates selon le nouveau statut
                if new_status == "reading" and book.get("status") != "reading":
                    update_data["date_started"] = datetime.utcnow()
                elif new_status == "completed" and book.get("status") != "completed":
                    if not book.get("date_started"):
                        update_data["date_started"] = datetime.utcnow()
                    update_data["date_completed"] = datetime.utcnow()
                
                books_collection.update_one(
                    {"id": book["id"], "user_id": current_user["id"]},
                    {"$set": update_data}
                )
                updates_made += 1
    
    # Mise à jour individuelle par tome
    elif "tome_updates" in bulk_update:
        tome_updates = bulk_update["tome_updates"]
        for book in existing_books:
            vol_num = book.get("volume_number")
            tome_key = f"tome_{vol_num}"
            
            if tome_key in tome_updates:
                new_status = tome_updates[tome_key]
                update_data = {"status": new_status, "updated_at": datetime.utcnow()}
                
                # Gérer les dates selon le nouveau statut
                if new_status == "reading" and book.get("status") != "reading":
                    update_data["date_started"] = datetime.utcnow()
                elif new_status == "completed" and book.get("status") != "completed":
                    if not book.get("date_started"):
                        update_data["date_started"] = datetime.utcnow()
                    update_data["date_completed"] = datetime.utcnow()
                
                books_collection.update_one(
                    {"id": book["id"], "user_id": current_user["id"]},
                    {"$set": update_data}
                )
                updates_made += 1
    
    return {
        "message": f"{updates_made} tome(s) mis à jour dans la saga {saga_name}",
        "updates_made": updates_made
    }

@app.post("/api/sagas/{saga_name}/auto-complete")
async def auto_complete_saga(
    saga_name: str,
    completion_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Auto-complétion intelligente d'une saga
    Format: {"target_volume": 50, "source": "manual"} ou {"source": "openlibrary"}
    """
    # Trouver les livres existants de cette saga
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Analyser les volumes existants
    existing_volumes = set()
    template_book = existing_books[0]
    max_volume = 0
    
    for book in existing_books:
        vol_num = book.get("volume_number", 0)
        if vol_num > 0:
            existing_volumes.add(vol_num)
            max_volume = max(max_volume, vol_num)
    
    # Déterminer le nombre de tomes à créer
    target_volume = completion_data.get("target_volume", max_volume + 10)
    source = completion_data.get("source", "manual")
    
    # Créer les tomes manquants
    created_books = []
    
    for vol_num in range(1, target_volume + 1):
        if vol_num not in existing_volumes:
            book_id = str(uuid.uuid4())
            new_book = {
                "id": book_id,
                "user_id": current_user["id"],
                "title": f"{saga_name} - Tome {vol_num}",
                "author": template_book.get("author", ""),
                "category": template_book.get("category", "roman"),
                "saga": saga_name,
                "volume_number": vol_num,
                "status": "to_read",
                "auto_added": True,
                "date_added": datetime.utcnow(),
                "date_started": None,
                "date_completed": None,
                "description": f"Tome {vol_num} de la série {saga_name}",
                "total_pages": None,
                "current_page": None,
                "rating": None,
                "review": "",
                "cover_url": "",
                "genre": template_book.get("genre", ""),
                "publication_year": None,
                "publisher": template_book.get("publisher", ""),
                "isbn": ""
            }
            
            books_collection.insert_one(new_book)
            new_book.pop("_id", None)
            created_books.append(new_book)
    
    return {
        "message": f"{len(created_books)} tome(s) ajouté(s) à la saga {saga_name}",
        "created_books": created_books,
        "total_volumes": target_volume,
        "existing_volumes": len(existing_volumes)
    }

@app.get("/api/sagas/{saga_name}/missing-analysis")
async def analyze_missing_volumes(
    saga_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyse des tomes manquants dans une saga
    """
    # Trouver les livres existants de cette saga
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Analyser les volumes
    existing_volumes = []
    missing_volumes = []
    
    for book in existing_books:
        vol_num = book.get("volume_number", 0)
        if vol_num > 0:
            existing_volumes.append(vol_num)
    
    existing_volumes.sort()
    
    if existing_volumes:
        # Détecter les trous dans la série
        for i in range(1, max(existing_volumes) + 1):
            if i not in existing_volumes:
                missing_volumes.append(i)
    
    # Statistiques
    total_expected = max(existing_volumes) if existing_volumes else 0
    completion_rate = len(existing_volumes) / total_expected * 100 if total_expected > 0 else 0
    
    return {
        "saga_name": saga_name,
        "existing_volumes": existing_volumes,
        "missing_volumes": missing_volumes,
        "total_existing": len(existing_volumes),
        "total_missing": len(missing_volumes),
        "max_volume": max(existing_volumes) if existing_volumes else 0,
        "completion_rate": round(completion_rate, 1),
        "suggestions": {
            "next_volume": max(existing_volumes) + 1 if existing_volumes else 1,
            "fill_gaps": len(missing_volumes) > 0,
            "estimated_total": max(existing_volumes) + 5 if existing_volumes else 10
        }
    }

# ==========================================
# NOUVELLES ROUTES POUR FICHES SÉRIES BIBLIOTHÈQUE
# ==========================================

# Modèle Pydantic pour les fiches séries
class SeriesLibraryCreate(BaseModel):
    series_name: str
    authors: List[str]
    category: str
    total_volumes: int
    volumes: List[dict]  # Liste des tomes avec titres
    series_status: str = "to_read"
    description_fr: str = ""
    cover_image_url: str = ""
    first_published: str = ""
    last_published: str = ""
    publisher: str = ""

class SeriesLibraryUpdate(BaseModel):
    series_status: Optional[str] = None
    description_fr: Optional[str] = None

# Collection MongoDB pour les fiches séries
try:
    series_library_collection = db.series_library
except:
    series_library_collection = None

@app.post("/api/series/library")
async def add_series_to_library(
    series_data: SeriesLibraryCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Ajouter une série complète à la bibliothèque utilisateur
    """
    
    # Validation données
    if not series_data.series_name or not series_data.volumes:
        raise HTTPException(status_code=400, detail="Données série incomplètes")
    
    # Vérifier que la série n'est pas déjà en bibliothèque
    existing = series_library_collection.find_one({
        "user_id": current_user["id"],
        "series_name": series_data.series_name
    })
    
    if existing:
        raise HTTPException(status_code=409, detail="Série déjà dans votre bibliothèque")
    
    # Créer la fiche série
    series_id = str(uuid.uuid4())
    series_entry = {
        "id": series_id,
        "type": "series",
        "user_id": current_user["id"],
        "series_name": series_data.series_name,
        "authors": series_data.authors,
        "category": series_data.category,
        "total_volumes": series_data.total_volumes,
        "series_status": series_data.series_status,
        "completion_percentage": 0,
        "volumes": series_data.volumes,
        "description_fr": series_data.description_fr,
        "cover_image_url": series_data.cover_image_url,
        "first_published": series_data.first_published,
        "last_published": series_data.last_published,
        "publisher": series_data.publisher,
        "date_added": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "source": "search_series_card"
    }
    
    # Sauvegarder en base
    series_library_collection.insert_one(series_entry)
    series_entry.pop("_id", None)
    
    return {
        "success": True,
        "series_id": series_id,
        "message": f"Série '{series_data.series_name}' ajoutée à votre bibliothèque",
        "series": series_entry
    }

@app.get("/api/series/library")
async def get_user_series_library(
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer toutes les séries de la bibliothèque utilisateur
    """
    # Construire le filtre
    filter_query = {"user_id": current_user["id"]}
    
    if category:
        filter_query["category"] = category
    
    if status:
        filter_query["series_status"] = status
    
    # Récupérer les séries
    series_list = list(series_library_collection.find(filter_query, {"_id": 0}))
    
    # Calculer les statistiques pour chaque série
    for series in series_list:
        read_volumes = len([v for v in series.get("volumes", []) if v.get("is_read", False)])
        total_volumes = len(series.get("volumes", []))
        series["completion_percentage"] = round((read_volumes / total_volumes) * 100) if total_volumes > 0 else 0
    
    return {
        "series": series_list,
        "total_count": len(series_list)
    }

@app.put("/api/series/library/{series_id}/volume/{volume_number}")
async def toggle_volume_read_status(
    series_id: str,
    volume_number: int,
    is_read: bool = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle statut lu/non lu d'un tome spécifique
    """
    
    # Récupérer la série
    series = series_library_collection.find_one({
        "id": series_id,
        "user_id": current_user["id"]
    })
    
    if not series:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    # Mettre à jour le tome spécifique
    volumes = series.get("volumes", [])
    volume_found = False
    
    for volume in volumes:
        if volume.get("volume_number") == volume_number:
            volume["is_read"] = is_read
            volume["date_read"] = datetime.utcnow().isoformat() if is_read else None
            volume_found = True
            break
    
    if not volume_found:
        raise HTTPException(status_code=404, detail="Tome non trouvé")
    
    # Recalculer la progression
    read_count = sum(1 for v in volumes if v.get("is_read", False))
    completion_percentage = round((read_count / len(volumes)) * 100) if volumes else 0
    
    # Mettre à jour le statut de série automatiquement
    if completion_percentage == 100:
        series_status = "completed"
    elif completion_percentage > 0:
        series_status = "reading"
    else:
        series_status = "to_read"
    
    # Sauvegarder les modifications
    series_library_collection.update_one(
        {"id": series_id, "user_id": current_user["id"]},
        {
            "$set": {
                "volumes": volumes,
                "completion_percentage": completion_percentage,
                "series_status": series_status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "success": True,
        "completion_percentage": completion_percentage,
        "series_status": series_status,
        "message": f"Tome {volume_number} marqué comme {'lu' if is_read else 'non lu'}"
    }

@app.put("/api/series/library/{series_id}")
async def update_series_library(
    series_id: str,
    update_data: SeriesLibraryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Mettre à jour les métadonnées d'une série en bibliothèque
    """
    
    # Vérifier que la série existe
    series = series_library_collection.find_one({
        "id": series_id,
        "user_id": current_user["id"]
    })
    
    if not series:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    # Préparer les mises à jour
    updates = {"updated_at": datetime.utcnow()}
    
    if update_data.series_status is not None:
        updates["series_status"] = update_data.series_status
    
    if update_data.description_fr is not None:
        updates["description_fr"] = update_data.description_fr
    
    # Appliquer les mises à jour
    series_library_collection.update_one(
        {"id": series_id, "user_id": current_user["id"]},
        {"$set": updates}
    )
    
    # Récupérer la série mise à jour
    updated_series = series_library_collection.find_one(
        {"id": series_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    
    return {
        "success": True,
        "message": "Série mise à jour avec succès",
        "series": updated_series
    }

@app.delete("/api/series/library/{series_id}")
async def delete_series_from_library(
    series_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer une série de la bibliothèque utilisateur
    """
    
    # Vérifier que la série existe
    series = series_library_collection.find_one({
        "id": series_id,
        "user_id": current_user["id"]
    })
    
    if not series:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    # Supprimer la série
    result = series_library_collection.delete_one({
        "id": series_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=500, detail="Erreur lors de la suppression")
    
    return {
        "success": True,
        "message": f"Série '{series['series_name']}' supprimée de votre bibliothèque"
    }

@app.post("/api/sagas/{saga_name}/toggle-tome-status")
async def toggle_tome_status(
    saga_name: str,
    tome_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle simple Lu/Non Lu pour un tome spécifique
    Format: {"volume_number": 1, "is_read": true}
    """
    volume_number = tome_data.get("volume_number")
    is_read = tome_data.get("is_read", False)
    
    if volume_number is None:
        raise HTTPException(status_code=400, detail="Numéro de tome requis")
    
    # Trouver le livre
    book = books_collection.find_one({
        "user_id": current_user["id"],
        "saga": saga_name,
        "volume_number": volume_number
    })
    
    if not book:
        raise HTTPException(status_code=404, detail="Tome non trouvé")
    
    # Déterminer le nouveau statut
    new_status = "completed" if is_read else "to_read"
    update_data = {"status": new_status, "updated_at": datetime.utcnow()}
    
    # Gérer les dates
    if new_status == "completed":
        if not book.get("date_started"):
            update_data["date_started"] = datetime.utcnow()
        update_data["date_completed"] = datetime.utcnow()
    elif new_status == "to_read":
        update_data["date_started"] = None
        update_data["date_completed"] = None
    
    books_collection.update_one(
        {"id": book["id"], "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    # Récupérer le livre mis à jour
    updated_book = books_collection.find_one({
        "id": book["id"],
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    return {
        "message": f"Tome {volume_number} de {saga_name} marqué comme {'lu' if is_read else 'non lu'}",
        "book": updated_book
    }

# Utilitaires pour Open Library
def detect_category_from_subjects(subjects):
    """Détecter la catégorie d'un livre basé sur ses sujets"""
    if not subjects:
        return "roman"
    
    subjects_str = " ".join(subjects).lower()
    
    # Détection BD
    bd_keywords = [
        "comic", "comics", "graphic novel", "bande dessinée", "bd",
        "cartoons", "strips", "comic strips", "graphic novels",
        "astérix", "tintin", "lucky luke", "gaston", "spirou"
    ]
    
    # Détection Manga
    manga_keywords = [
        "manga", "anime", "japanese comic", "shonen", "shojo", "seinen",
        "one piece", "naruto", "dragon ball", "attack on titan"
    ]
    
    for keyword in bd_keywords:
        if keyword in subjects_str:
            return "bd"
    
    for keyword in manga_keywords:
        if keyword in subjects_str:
            return "manga"
    
    return "roman"

def extract_cover_url(cover_data):
    """Extraire l'URL de couverture depuis les données Open Library"""
    if not cover_data:
        return ""
    
    if isinstance(cover_data, list) and cover_data:
        cover_id = cover_data[0]
    elif isinstance(cover_data, int):
        cover_id = cover_data
    else:
        return ""
    
    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

def normalize_isbn(isbn):
    """Normaliser un ISBN en supprimant les tirets et espaces"""
    if not isbn:
        return ""
    return re.sub(r'[-\s]', '', str(isbn))

# Routes Open Library
@app.get("/api/openlibrary/search")
async def search_open_library(
    q: str,
    limit: int = 10,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    language: Optional[str] = None,
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    author_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        params = {
            "q": q,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,language"
        }
        
        # Construire la requête avec filtres
        query_parts = [q]
        
        if year_start and year_end:
            query_parts.append(f"first_publish_year:[{year_start} TO {year_end}]")
        elif year_start:
            query_parts.append(f"first_publish_year:[{year_start} TO *]")
        elif year_end:
            query_parts.append(f"first_publish_year:[* TO {year_end}]")
        
        if language:
            query_parts.append(f"language:{language}")
        
        if author_filter:
            query_parts.append(f"author:{author_filter}")
        
        params["q"] = " AND ".join(query_parts)
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for doc in data.get("docs", []):
            # Appliquer filtres de pages
            if min_pages and doc.get("number_of_pages_median", 0) < min_pages:
                continue
            if max_pages and doc.get("number_of_pages_median", float('inf')) > max_pages:
                continue
            
            book = {
                "ol_key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "category": detect_category_from_subjects(doc.get("subject", [])),
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "subjects": doc.get("subject", [])[:5],  # Premiers 5 sujets
                "number_of_pages": doc.get("number_of_pages_median"),
                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else ""
            }
            books.append(book)
        
        return {
            "books": books[:limit],
            "total_found": data.get("numFound", 0),
            "filters_applied": {
                "year_range": f"{year_start}-{year_end}" if year_start or year_end else None,
                "language": language,
                "pages_range": f"{min_pages}-{max_pages}" if min_pages or max_pages else None,
                "author": author_filter
            }
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")

@app.post("/api/openlibrary/import")
async def import_from_open_library(
    import_data: dict,
    current_user: dict = Depends(get_current_user)
):
    ol_key = import_data.get("ol_key")
    category = import_data.get("category", "roman")
    
    if not ol_key:
        raise HTTPException(status_code=400, detail="Clé Open Library manquante")
    
    try:
        # Récupérer les détails du livre
        response = requests.get(f"https://openlibrary.org{ol_key}.json", timeout=10)
        response.raise_for_status()
        book_data = response.json()
        
        # Vérifier les doublons par ISBN ou titre+auteur
        isbn = ""
        if book_data.get("isbn_13"):
            isbn = book_data["isbn_13"][0]
        elif book_data.get("isbn_10"):
            isbn = book_data["isbn_10"][0]
        
        title = book_data.get("title", "")
        authors = []
        if book_data.get("authors"):
            for author_ref in book_data["authors"]:
                author_key = author_ref.get("author", {}).get("key") or author_ref.get("key")
                if author_key:
                    author_response = requests.get(f"https://openlibrary.org{author_key}.json", timeout=5)
                    if author_response.ok:
                        author_data = author_response.json()
                        authors.append(author_data.get("name", ""))
        
        author_str = ", ".join(authors) if authors else ""
        
        # Vérifier doublons - Logique améliorée
        existing_book = None
        
        # 1. Vérification par ISBN (priorité élevée)
        if isbn:
            existing_book = books_collection.find_one({
                "user_id": current_user["id"],
                "isbn": normalize_isbn(isbn)
            })
        
        # 2. Vérification par clé Open Library (nouvelle vérification)
        if not existing_book:
            existing_book = books_collection.find_one({
                "user_id": current_user["id"],
                "ol_key": ol_key  # Ajouter cette vérification
            })
        
        # 3. Vérification par titre et auteur (avec une meilleure logique)
        if not existing_book and title and author_str:
            # Normaliser les chaînes pour une meilleure comparaison
            normalized_title = re.sub(r'[^\w\s]', '', title.lower()).strip()
            normalized_author = re.sub(r'[^\w\s]', '', author_str.lower()).strip()
            
            # Recherche exacte d'abord
            existing_book = books_collection.find_one({
                "user_id": current_user["id"],
                "title": {"$regex": f"^{re.escape(title)}$", "$options": "i"},
                "author": {"$regex": f"^{re.escape(author_str)}$", "$options": "i"}
            })
            
            # Si pas trouvé, recherche avec normalisation
            if not existing_book and len(normalized_title) > 3:
                existing_book = books_collection.find_one({
                    "user_id": current_user["id"],
                    "$and": [
                        {"title": {"$regex": re.escape(normalized_title), "$options": "i"}},
                        {"author": {"$regex": re.escape(normalized_author), "$options": "i"}}
                    ]
                })
        
        if existing_book:
            raise HTTPException(status_code=409, detail="Ce livre existe déjà dans votre collection")
        
        # Créer le nouveau livre
        book_id = str(uuid.uuid4())
        new_book = {
            "id": book_id,
            "user_id": current_user["id"],
            "ol_key": ol_key,  # Ajout de la clé Open Library pour la détection des doublons
            "title": title,
            "author": author_str,
            "category": validate_category(category),
            "description": book_data.get("description", {}).get("value", "") if isinstance(book_data.get("description"), dict) else str(book_data.get("description", "")),
            "cover_url": extract_cover_url(book_data.get("covers")),
            "isbn": normalize_isbn(isbn),
            "publication_year": book_data.get("publish_date"),
            "publisher": ", ".join(book_data.get("publishers", [])) if book_data.get("publishers") else "",
            "status": "to_read",
            "date_added": datetime.utcnow(),
            "date_started": None,
            "date_completed": None,
            "total_pages": book_data.get("number_of_pages"),
            "current_page": None,
            "rating": None,
            "review": "",
            "saga": "",
            "volume_number": None,
            "genre": "",
            "auto_added": False
        }
        
        books_collection.insert_one(new_book)
        new_book.pop("_id", None)
        
        return {"message": "Livre importé avec succès", "book": new_book}
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@app.post("/api/books/{book_id}/enrich")
async def enrich_book(book_id: str, current_user: dict = Depends(get_current_user)):
    # Récupérer le livre existant
    book = books_collection.find_one({
        "id": book_id,
        "user_id": current_user["id"]
    })
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    try:
        # Rechercher sur Open Library
        search_query = f"{book['title']} {book['author']}"
        params = {
            "q": search_query,
            "limit": 1,
            "fields": "key,title,author_name,isbn,cover_i,first_publish_year,publisher,number_of_pages_median"
        }
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("docs"):
            raise HTTPException(status_code=404, detail="Aucune correspondance trouvée sur Open Library")
        
        ol_book = data["docs"][0]
        
        # Préparer les mises à jour (seulement les champs manquants)
        updates = {}
        
        if not book.get("cover_url") and ol_book.get("cover_i"):
            updates["cover_url"] = extract_cover_url(ol_book["cover_i"])
        
        if not book.get("isbn") and ol_book.get("isbn"):
            updates["isbn"] = ol_book["isbn"][0]
        
        if not book.get("publication_year") and ol_book.get("first_publish_year"):
            updates["publication_year"] = ol_book["first_publish_year"]
        
        if not book.get("publisher") and ol_book.get("publisher"):
            updates["publisher"] = ", ".join(ol_book["publisher"]) if isinstance(ol_book["publisher"], list) else ol_book["publisher"]
        
        if not book.get("total_pages") and ol_book.get("number_of_pages_median"):
            updates["total_pages"] = ol_book["number_of_pages_median"]
        
        if updates:
            updates["updated_at"] = datetime.utcnow()
            books_collection.update_one(
                {"id": book_id, "user_id": current_user["id"]},
                {"$set": updates}
            )
        
        # Récupérer le livre mis à jour
        updated_book = books_collection.find_one({
            "id": book_id,
            "user_id": current_user["id"]
        }, {"_id": 0})
        
        return {
            "message": "Livre enrichi avec succès",
            "book": updated_book,
            "fields_updated": list(updates.keys())
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enrichissement: {str(e)}")

@app.get("/api/openlibrary/search-advanced")
async def search_open_library_advanced(
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
    if not any([title, author, subject, publisher, isbn]):
        raise HTTPException(status_code=400, detail="Au moins un critère de recherche est requis")
    
    try:
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
            query_parts.append(f"isbn:{normalize_isbn(isbn)}")
        
        if year_start and year_end:
            query_parts.append(f"first_publish_year:[{year_start} TO {year_end}]")
        elif year_start:
            query_parts.append(f"first_publish_year:[{year_start} TO *]")
        elif year_end:
            query_parts.append(f"first_publish_year:[* TO {year_end}]")
        
        params = {
            "q": " AND ".join(query_parts),
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,publisher"
        }
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for doc in data.get("docs", []):
            book = {
                "ol_key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "category": detect_category_from_subjects(doc.get("subject", [])),
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else ""
            }
            books.append(book)
        
        return {
            "books": books,
            "total_found": data.get("numFound", 0),
            "query_used": " AND ".join(query_parts)
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche avancée: {str(e)}")

@app.get("/api/openlibrary/search-isbn")
async def search_by_isbn(isbn: str, current_user: dict = Depends(get_current_user)):
    if not isbn:
        raise HTTPException(status_code=400, detail="ISBN requis")
    
    normalized_isbn = normalize_isbn(isbn)
    
    try:
        # Essayer d'abord l'API ISBN spécifique
        response = requests.get(f"https://openlibrary.org/isbn/{normalized_isbn}.json", timeout=10)
        
        if response.ok:
            book_data = response.json()
            # Récupérer les informations de l'œuvre
            if book_data.get("works"):
                work_key = book_data["works"][0]["key"]
                work_response = requests.get(f"https://openlibrary.org{work_key}.json", timeout=5)
                if work_response.ok:
                    work_data = work_response.json()
                    book_data.update(work_data)
            
            book = {
                "ol_key": book_data.get("key", ""),
                "title": book_data.get("title", ""),
                "author": "",  # À récupérer séparément
                "category": detect_category_from_subjects(book_data.get("subjects", [])),
                "cover_url": extract_cover_url(book_data.get("covers")),
                "first_publish_year": book_data.get("first_publish_date"),
                "isbn": normalized_isbn,
                "publisher": ", ".join(book_data.get("publishers", [])) if book_data.get("publishers") else ""
            }
            
            return {"book": book, "found": True}
        else:
            # Fallback à la recherche générale
            params = {
                "q": f"isbn:{normalized_isbn}",
                "limit": 1,
                "fields": "key,title,author_name,first_publish_year,isbn,cover_i,publisher"
            }
            
            search_response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if search_data.get("docs"):
                doc = search_data["docs"][0]
                book = {
                    "ol_key": doc.get("key", ""),
                    "title": doc.get("title", ""),
                    "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                    "category": "roman",  # Par défaut
                    "cover_url": extract_cover_url(doc.get("cover_i")),
                    "first_publish_year": doc.get("first_publish_year"),
                    "isbn": normalized_isbn,
                    "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else ""
                }
                return {"book": book, "found": True}
            else:
                return {"book": None, "found": False, "message": "Aucun livre trouvé pour cet ISBN"}
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche par ISBN: {str(e)}")

@app.get("/api/openlibrary/search-author")
async def search_by_author(
    author: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    if not author:
        raise HTTPException(status_code=400, detail="Nom d'auteur requis")
    
    try:
        params = {
            "q": f"author:{author}",
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,series"
        }
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Grouper les livres par série
        series_books = {}
        standalone_books = []
        
        for doc in data.get("docs", []):
            book = {
                "ol_key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "category": detect_category_from_subjects(doc.get("subject", [])),
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "series": doc.get("series", [])
            }
            
            if book["series"]:
                series_name = book["series"][0] if isinstance(book["series"], list) else book["series"]
                if series_name not in series_books:
                    series_books[series_name] = []
                series_books[series_name].append(book)
            else:
                standalone_books.append(book)
        
        return {
            "author": author,
            "series": [{"name": name, "books": books} for name, books in series_books.items()],
            "standalone_books": standalone_books,
            "total_found": data.get("numFound", 0)
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche par auteur: {str(e)}")

@app.post("/api/openlibrary/import-bulk")
async def import_bulk_from_open_library(
    import_data: dict,
    current_user: dict = Depends(get_current_user)
):
    books_to_import = import_data.get("books", [])
    
    if not books_to_import:
        raise HTTPException(status_code=400, detail="Liste de livres vide")
    
    results = {
        "imported": [],
        "errors": [],
        "duplicates": []
    }
    
    for book_data in books_to_import:
        try:
            ol_key = book_data.get("ol_key")
            category = book_data.get("category", "roman")
            
            if not ol_key:
                results["errors"].append({"book": book_data, "error": "Clé Open Library manquante"})
                continue
            
            # Utiliser la fonction d'import simple
            import_result = await import_from_open_library(
                {"ol_key": ol_key, "category": category},
                current_user
            )
            results["imported"].append(import_result["book"])
            
        except HTTPException as e:
            if e.status_code == 409:  # Doublon
                results["duplicates"].append({"book": book_data, "error": e.detail})
            else:
                results["errors"].append({"book": book_data, "error": e.detail})
        except Exception as e:
            results["errors"].append({"book": book_data, "error": str(e)})
    
    return {
        "summary": {
            "total_requested": len(books_to_import),
            "imported": len(results["imported"]),
            "duplicates": len(results["duplicates"]),
            "errors": len(results["errors"])
        },
        "results": results
    }

@app.get("/api/openlibrary/recommendations")
async def get_recommendations(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Analyser la collection de l'utilisateur
        user_books = list(books_collection.find({"user_id": current_user["id"]}, {"_id": 0}))
        
        if not user_books:
            return {"recommendations": [], "message": "Ajoutez des livres à votre collection pour obtenir des recommandations"}
        
        # Analyser les préférences
        authors = {}
        categories = {}
        genres = {}
        
        for book in user_books:
            # Compter les auteurs
            author = book.get("author", "")
            if author:
                authors[author] = authors.get(author, 0) + 1
            
            # Compter les catégories
            category = book.get("category", "")
            if category:
                categories[category] = categories.get(category, 0) + 1
            
            # Compter les genres
            genre = book.get("genre", "")
            if genre:
                genres[genre] = genres.get(genre, 0) + 1
        
        # Trouver les auteurs favoris
        favorite_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:3]
        favorite_category = max(categories.items(), key=lambda x: x[1])[0] if categories else "roman"
        
        recommendations = []
        
        # Recommandations basées sur les auteurs favoris
        for author, count in favorite_authors:
            if len(recommendations) >= limit:
                break
            
            try:
                params = {
                    "q": f"author:{author}",
                    "limit": 3,
                    "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject"
                }
                
                response = requests.get("https://openlibrary.org/search.json", params=params, timeout=5)
                if response.ok:
                    data = response.json()
                    
                    for doc in data.get("docs", [])[:2]:  # Max 2 par auteur
                        if len(recommendations) >= limit:
                            break
                        
                        title = doc.get("title", "")
                        # Vérifier que ce livre n'est pas déjà dans la collection
                        existing = any(book.get("title", "").lower() == title.lower() for book in user_books)
                        
                        if not existing:
                            recommendation = {
                                "ol_key": doc.get("key", ""),
                                "title": title,
                                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                                "category": detect_category_from_subjects(doc.get("subject", [])),
                                "cover_url": extract_cover_url(doc.get("cover_i")),
                                "first_publish_year": doc.get("first_publish_year"),
                                "reason": f"Recommandé car vous aimez {author}"
                            }
                            recommendations.append(recommendation)
            except:
                continue
        
        return {
            "recommendations": recommendations,
            "based_on": {
                "favorite_authors": [author for author, _ in favorite_authors],
                "favorite_category": favorite_category,
                "collection_size": len(user_books)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération des recommandations: {str(e)}")

@app.get("/api/openlibrary/missing-volumes")
async def detect_missing_volumes(
    saga: str,
    current_user: dict = Depends(get_current_user)
):
    if not saga:
        raise HTTPException(status_code=400, detail="Nom de saga requis")
    
    try:
        # Récupérer les volumes existants
        existing_books = list(books_collection.find({
            "user_id": current_user["id"],
            "saga": saga
        }, {"_id": 0}).sort("volume_number", 1))
        
        if not existing_books:
            raise HTTPException(status_code=404, detail="Saga non trouvée")
        
        existing_volumes = [book.get("volume_number") for book in existing_books if book.get("volume_number")]
        
        if not existing_volumes:
            return {
                "saga": saga,
                "present_volumes": [],
                "missing_volumes": [],
                "next_volume": 1,
                "suggestions": []
            }
        
        min_vol = min(existing_volumes)
        max_vol = max(existing_volumes)
        
        # Détecter les volumes manquants
        missing_volumes = []
        for i in range(min_vol, max_vol + 1):
            if i not in existing_volumes:
                missing_volumes.append(i)
        
        # Rechercher les volumes manquants sur Open Library
        author = existing_books[0].get("author", "")
        suggestions = []
        
        for vol in missing_volumes[:5]:  # Limiter à 5 suggestions
            try:
                search_query = f"{saga} tome {vol} {author}".strip()
                params = {
                    "q": search_query,
                    "limit": 3,
                    "fields": "key,title,author_name,first_publish_year,cover_i"
                }
                
                response = requests.get("https://openlibrary.org/search.json", params=params, timeout=5)
                if response.ok:
                    data = response.json()
                    
                    for doc in data.get("docs", [])[:1]:  # Premier résultat
                        suggestion = {
                            "volume_number": vol,
                            "ol_key": doc.get("key", ""),
                            "title": doc.get("title", ""),
                            "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                            "cover_url": extract_cover_url(doc.get("cover_i")),
                            "first_publish_year": doc.get("first_publish_year")
                        }
                        suggestions.append(suggestion)
                        break
            except:
                continue
        
        return {
            "saga": saga,
            "present_volumes": sorted(existing_volumes),
            "missing_volumes": missing_volumes,
            "next_volume": max_vol + 1,
            "suggestions": suggestions
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Erreur lors de la détection des volumes manquants: {str(e)}")

@app.get("/api/openlibrary/suggestions")
async def get_import_suggestions(
    limit: int = 15,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Analyser la collection
        user_books = list(books_collection.find({"user_id": current_user["id"]}, {"_id": 0}))
        
        if not user_books:
            return {"suggestions": [], "message": "Ajoutez des livres pour obtenir des suggestions"}
        
        suggestions = []
        
        # Suggestions de continuation de sagas
        sagas = {}
        for book in user_books:
            saga = book.get("saga", "")
            if saga:
                if saga not in sagas:
                    sagas[saga] = {"books": [], "author": book.get("author", "")}
                sagas[saga]["books"].append(book)
        
        for saga_name, saga_data in sagas.items():
            volumes = [book.get("volume_number") for book in saga_data["books"] if book.get("volume_number")]
            if volumes:
                next_volume = max(volumes) + 1
                
                # Rechercher le tome suivant
                try:
                    search_query = f"{saga_name} tome {next_volume} {saga_data['author']}".strip()
                    params = {
                        "q": search_query,
                        "limit": 1,
                        "fields": "key,title,author_name,cover_i"
                    }
                    
                    response = requests.get("https://openlibrary.org/search.json", params=params, timeout=3)
                    if response.ok:
                        data = response.json()
                        
                        if data.get("docs"):
                            doc = data["docs"][0]
                            suggestion = {
                                "type": "saga_continuation",
                                "ol_key": doc.get("key", ""),
                                "title": doc.get("title", ""),
                                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                                "cover_url": extract_cover_url(doc.get("cover_i")),
                                "reason": f"Tome suivant de la saga {saga_name}",
                                "saga": saga_name,
                                "volume_number": next_volume
                            }
                            suggestions.append(suggestion)
                except:
                    continue
        
        # Suggestions d'auteurs favoris
        authors = {}
        for book in user_books:
            author = book.get("author", "")
            if author:
                authors[author] = authors.get(author, 0) + 1
        
        favorite_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:3]
        
        for author, count in favorite_authors:
            if len(suggestions) >= limit:
                break
            
            try:
                params = {
                    "q": f"author:{author}",
                    "limit": 2,
                    "fields": "key,title,author_name,cover_i"
                }
                
                response = requests.get("https://openlibrary.org/search.json", params=params, timeout=3)
                if response.ok:
                    data = response.json()
                    
                    for doc in data.get("docs", []):
                        if len(suggestions) >= limit:
                            break
                        
                        title = doc.get("title", "")
                        # Vérifier que ce livre n'est pas déjà dans la collection
                        existing = any(book.get("title", "").lower() == title.lower() for book in user_books)
                        
                        if not existing:
                            suggestion = {
                                "type": "favorite_author",
                                "ol_key": doc.get("key", ""),
                                "title": title,
                                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                                "cover_url": extract_cover_url(doc.get("cover_i")),
                                "reason": f"Nouvel ouvrage de {author} ({count} livre{'s' if count > 1 else ''} dans votre collection)"
                            }
                            suggestions.append(suggestion)
            except:
                continue
        
        return {
            "suggestions": suggestions[:limit],
            "types": {
                "saga_continuation": len([s for s in suggestions if s.get("type") == "saga_continuation"]),
                "favorite_author": len([s for s in suggestions if s.get("type") == "favorite_author"])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération des suggestions: {str(e)}")

# === FONCTIONNALITÉ DE DÉCOUVERTE COMPLÈTE DE SÉRIE ===

@app.get("/api/series/discover")
async def discover_complete_series(
    series_name: str,
    author: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Découverte complète d'une série - Identifier tous les tomes et œuvres connexes
    """
    try:
        # Normaliser le nom de série pour la recherche
        normalized_series = series_name.strip().lower()
        
        # Mapping des séries populaires avec leurs variantes
        series_variants = {
            "harry potter": [
                "harry potter", "harry potter and", "harry potter et",
                "école des sorciers", "chamber of secrets", "chambre des secrets",
                "prisoner of azkaban", "prisonnier d'azkaban", "goblet of fire", "coupe de feu",
                "order of the phoenix", "ordre du phénix", "half-blood prince", "prince de sang-mêlé",
                "deathly hallows", "reliques de la mort", "cursed child", "l'enfant maudit",
                "fantastic beasts", "animaux fantastiques", "quidditch through the ages",
                "le quidditch à travers les âges", "tales of beedle the bard", "contes de beedle le barde"
            ],
            "seigneur des anneaux": [
                "lord of the rings", "seigneur des anneaux", "fellowship of the ring",
                "communauté de l'anneau", "two towers", "deux tours", "return of the king",
                "retour du roi", "hobbit", "silmarillion"
            ],
            "one piece": [
                "one piece", "wan pīsu"
            ],
            "naruto": [
                "naruto", "boruto"
            ],
            "astérix": [
                "astérix", "asterix", "obelix"
            ]
        }
        
        # Détecter les variantes de recherche pour la série
        search_terms = []
        for series_key, variants in series_variants.items():
            if any(variant in normalized_series for variant in variants[:3]):  # Check first 3 main variants
                search_terms = variants
                break
        
        if not search_terms:
            search_terms = [series_name]
        
        # Récupérer les livres existants de l'utilisateur pour cette série
        user_filter = {"user_id": current_user["id"]}
        existing_books = list(books_collection.find({
            **user_filter,
            "$or": [
                {"saga": {"$regex": re.escape(series_name), "$options": "i"}},
                {"title": {"$regex": re.escape(series_name), "$options": "i"}},
                {"author": {"$regex": re.escape(author), "$options": "i"}} if author else {}
            ]
        }, {"_id": 0}))
        
        # Recherche complète sur Open Library
        all_discovered_books = []
        unique_books = set()  # Pour éviter les doublons
        
        # 1. Recherche par termes de série
        for search_term in search_terms[:5]:  # Limiter à 5 termes pour éviter trop de requêtes
            try:
                # Recherche principale
                params = {
                    "q": search_term,
                    "limit": 50,
                    "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,language,edition_count"
                }
                
                if author:
                    params["q"] += f" AND author:{author}"
                
                response = requests.get("https://openlibrary.org/search.json", params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    
                    for doc in data.get("docs", []):
                        title = doc.get("title", "").lower()
                        book_key = doc.get("key", "")
                        
                        # Éviter les doublons
                        if book_key in unique_books:
                            continue
                        unique_books.add(book_key)
                        
                        # Filtrage intelligent pour la série
                        is_relevant = False
                        relevance_score = 0
                        book_type = "unknown"
                        
                        # Détecter le type de livre
                        if any(term in title for term in ["tome", "volume", "book", "part", "partie"]):
                            book_type = "main_series"
                            relevance_score += 10
                        elif any(term in title for term in ["guide", "companion", "encyclopedia", "encyclopédie"]):
                            book_type = "companion"
                            relevance_score += 5
                        elif any(term in title for term in ["spin-off", "prequel", "sequel", "side story"]):
                            book_type = "spin_off"
                            relevance_score += 7
                        else:
                            book_type = "related"
                            relevance_score += 3
                        
                        # Calcul de pertinence
                        for variant in search_terms[:3]:  # Check main variants
                            if variant.lower() in title:
                                is_relevant = True
                                if title.startswith(variant.lower()):
                                    relevance_score += 20
                                else:
                                    relevance_score += 10
                                break
                        
                        # Vérification de l'auteur
                        authors = doc.get("author_name", [])
                        author_match = False
                        if author and authors:
                            for auth in authors:
                                if author.lower() in auth.lower():
                                    author_match = True
                                    relevance_score += 15
                                    break
                        
                        if is_relevant or author_match:
                            # Extraire le numéro de tome si possible
                            volume_number = None
                            volume_patterns = [
                                r'tome\s*(\d+)', r'volume\s*(\d+)', r'book\s*(\d+)',
                                r'part\s*(\d+)', r'partie\s*(\d+)', r'#(\d+)',
                                r'\b(\d+)\b'  # Numéro isolé
                            ]
                            
                            for pattern in volume_patterns:
                                match = re.search(pattern, title, re.IGNORECASE)
                                if match:
                                    volume_number = int(match.group(1))
                                    break
                            
                            # Vérifier si déjà possédé
                            is_owned = any(
                                existing_book.get("title", "").lower() == doc.get("title", "").lower() or
                                existing_book.get("isbn", "") == (doc.get("isbn", [""])[0] if doc.get("isbn") else "")
                                for existing_book in existing_books
                            )
                            
                            discovered_book = {
                                "ol_key": book_key,
                                "title": doc.get("title", ""),
                                "author": ", ".join(authors) if authors else "",
                                "first_publish_year": doc.get("first_publish_year"),
                                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                                "cover_url": extract_cover_url(doc.get("cover_i")),
                                "number_of_pages": doc.get("number_of_pages_median"),
                                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else "",
                                "category": detect_category_from_subjects(doc.get("subject", [])),
                                "volume_number": volume_number,
                                "book_type": book_type,
                                "relevance_score": relevance_score,
                                "is_owned": is_owned,
                                "edition_count": doc.get("edition_count", 1)
                            }
                            
                            all_discovered_books.append(discovered_book)
                            
            except Exception as e:
                print(f"Erreur lors de la recherche pour '{search_term}': {e}")
                continue
        
        # Trier par pertinence et organiser
        all_discovered_books.sort(key=lambda x: (-x["relevance_score"], x.get("volume_number", 999) or 999, x["title"]))
        
        # Grouper par type
        main_series = [b for b in all_discovered_books if b["book_type"] == "main_series"]
        spin_offs = [b for b in all_discovered_books if b["book_type"] == "spin_off"]
        companions = [b for b in all_discovered_books if b["book_type"] == "companion"]
        related = [b for b in all_discovered_books if b["book_type"] == "related"]
        
        # Statistiques
        total_discovered = len(all_discovered_books)
        owned_count = len([b for b in all_discovered_books if b["is_owned"]])
        main_series_count = len(main_series)
        owned_main_series = len([b for b in main_series if b["is_owned"]])
        
        # Détecter les tomes manquants dans la série principale
        if main_series:
            # Filter out None values and ensure we only have integers
            volume_numbers = [b["volume_number"] for b in main_series if b["volume_number"] is not None]
            if volume_numbers:
                max_volume = max(volume_numbers)
                missing_volumes = []
                for i in range(1, max_volume + 1):
                    if i not in volume_numbers:
                        missing_volumes.append(i)
            else:
                missing_volumes = []
        else:
            missing_volumes = []
        
        return {
            "series_name": series_name,
            "author": author,
            "search_terms_used": search_terms[:5],
            "statistics": {
                "total_discovered": total_discovered,
                "owned_count": owned_count,
                "completion_percentage": round((owned_count / total_discovered * 100)) if total_discovered > 0 else 0,
                "main_series_count": main_series_count,
                "main_series_owned": owned_main_series,
                "main_series_completion": round((owned_main_series / main_series_count * 100)) if main_series_count > 0 else 0,
                "missing_volumes": missing_volumes
            },
            "books": {
                "main_series": main_series[:20],  # Limiter pour éviter une réponse trop lourde
                "spin_offs": spin_offs[:10],
                "companions": companions[:10],
                "related": related[:10]
            },
            "recommendations": {
                "next_to_buy": [b for b in main_series if not b["is_owned"]][:5],
                "missing_volumes": missing_volumes,
                "highly_rated": [b for b in all_discovered_books if b["relevance_score"] >= 15 and not b["is_owned"]][:5]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la découverte de série: {str(e)}")

@app.post("/api/series/import-missing")
async def import_missing_books(
    import_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Importer en lot les livres manquants d'une série
    """
    try:
        ol_keys = import_data.get("ol_keys", [])
        series_name = import_data.get("series_name", "")
        
        if not ol_keys:
            raise HTTPException(status_code=400, detail="Aucun livre à importer")
        
        imported_books = []
        errors = []
        
        for ol_key in ol_keys:
            try:
                # Récupérer les détails du livre depuis Open Library
                if not ol_key.startswith('/works/'):
                    ol_key = f"/works/{ol_key}"
                
                # Rechercher le livre sur Open Library pour obtenir ses détails
                search_params = {
                    "q": f"key:{ol_key}",
                    "limit": 1,
                    "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher"
                }
                
                response = requests.get("https://openlibrary.org/search.json", params=search_params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    docs = data.get("docs", [])
                    
                    if docs:
                        doc = docs[0]
                        
                        # Vérifier si le livre n'existe pas déjà
                        existing_book = books_collection.find_one({
                            "user_id": current_user["id"],
                            "$or": [
                                {"title": doc.get("title", "")},
                                {"isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else ""}
                            ]
                        })
                        
                        if existing_book:
                            errors.append(f"'{doc.get('title', '')}' est déjà dans votre collection")
                            continue
                        
                        # Extraire le numéro de tome
                        title = doc.get("title", "")
                        volume_number = None
                        volume_patterns = [
                            r'tome\s*(\d+)', r'volume\s*(\d+)', r'book\s*(\d+)',
                            r'part\s*(\d+)', r'#(\d+)', r'\b(\d+)\b'
                        ]
                        
                        for pattern in volume_patterns:
                            match = re.search(pattern, title, re.IGNORECASE)
                            if match:
                                volume_number = int(match.group(1))
                                break
                        
                        # Créer le livre
                        book_id = str(uuid.uuid4())
                        new_book = {
                            "id": book_id,
                            "user_id": current_user["id"],
                            "title": doc.get("title", ""),
                            "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                            "category": detect_category_from_subjects(doc.get("subject", [])),
                            "description": f"Importé depuis Open Library - Série: {series_name}",
                            "total_pages": doc.get("number_of_pages_median"),
                            "status": "to_read",
                            "current_page": None,
                            "rating": None,
                            "review": "",
                            "cover_url": extract_cover_url(doc.get("cover_i")),
                            "saga": series_name,
                            "volume_number": volume_number,
                            "genre": "",
                            "publication_year": doc.get("first_publish_year"),
                            "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else "",
                            "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                            "auto_added": False,
                            "date_added": datetime.utcnow(),
                            "date_started": None,
                            "date_completed": None
                        }
                        
                        books_collection.insert_one(new_book)
                        new_book.pop("_id", None)
                        imported_books.append(new_book)
                        
            except Exception as e:
                errors.append(f"Erreur lors de l'import de {ol_key}: {str(e)}")
        
        return {
            "message": f"{len(imported_books)} livre(s) importé(s) avec succès",
            "imported_books": imported_books,
            "errors": errors,
            "statistics": {
                "total_requested": len(ol_keys),
                "imported": len(imported_books),
                "errors": len(errors)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import en lot: {str(e)}")

# ============================================================================
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtenir l'utilisateur actuel depuis le token JWT"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        # Récupérer l'utilisateur depuis la base
        user = users_collection.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

# ENDPOINTS SÉRIES EN BIBLIOTHÈQUE
# ============================================================================

@app.post("/api/series/library")
async def add_series_to_library(
    series_data: SeriesLibraryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Ajouter une série complète à la bibliothèque utilisateur"""
    try:
        # 1. Validation données
        if not series_data.series_name or not series_data.volumes:
            raise HTTPException(status_code=400, detail="Données série incomplètes")
        
        # 2. Vérifier série pas déjà en bibliothèque
        existing = series_library_collection.find_one({
            "user_id": current_user["id"],
            "series_name": {"$regex": re.escape(series_data.series_name), "$options": "i"}
        })
        if existing:
            raise HTTPException(status_code=409, detail="Série déjà dans votre bibliothèque")
        
        # 3. Créer fiche série
        series_id = str(uuid.uuid4())
        series_entry = {
            "id": series_id,
            "type": "series",
            "user_id": current_user["id"],
            "series_name": series_data.series_name,
            "authors": series_data.authors,
            "category": series_data.category,
            "total_volumes": len(series_data.volumes),
            "series_status": series_data.series_status,
            "completion_percentage": 0,
            "volumes": [vol.dict() for vol in series_data.volumes],
            "description_fr": series_data.description_fr,
            "cover_image_url": series_data.cover_image_url,
            "first_published": series_data.first_published,
            "last_published": series_data.last_published,
            "publisher": series_data.publisher,
            "date_added": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "source": "search_series_card"
        }
        
        # 4. Sauvegarder en base
        result = series_library_collection.insert_one(series_entry)
        
        return {
            "success": True,
            "series_id": series_id,
            "message": f"Série '{series_data.series_name}' ajoutée à votre bibliothèque",
            "total_volumes": len(series_data.volumes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout de la série: {str(e)}")

@app.get("/api/series/library")
async def get_user_series_library(
    current_user: dict = Depends(get_current_user),
    category: Optional[str] = None,
    status: Optional[str] = None
):
    """Récupérer toutes les séries de la bibliothèque utilisateur"""
    try:
        query = {"user_id": current_user["id"], "type": "series"}
        
        if category:
            query["category"] = category
        if status:
            query["series_status"] = status
        
        series_list = list(series_library_collection.find(query, {"_id": 0}))
        
        return {
            "series": series_list,
            "total": len(series_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des séries: {str(e)}")

@app.put("/api/series/library/{series_id}/volume/{volume_number}")
async def toggle_volume_read_status(
    series_id: str,
    volume_number: int,
    is_read: bool,
    current_user: dict = Depends(get_current_user)
):
    """Toggle statut lu/non lu d'un tome"""
    try:
        # 1. Récupérer série
        series = series_library_collection.find_one({
            "id": series_id,
            "user_id": current_user["id"],
            "type": "series"
        })
        if not series:
            raise HTTPException(status_code=404, detail="Série non trouvée")
        
        # 2. Mettre à jour tome
        volumes = series["volumes"]
        volume_found = False
        for volume in volumes:
            if volume["volume_number"] == volume_number:
                volume["is_read"] = is_read
                volume["date_read"] = datetime.utcnow().isoformat() if is_read else None
                volume_found = True
                break
        
        if not volume_found:
            raise HTTPException(status_code=404, detail="Tome non trouvé")
        
        # 3. Recalculer progression
        read_count = sum(1 for v in volumes if v["is_read"])
        completion_percentage = round((read_count / len(volumes)) * 100)
        
        # 4. Mettre à jour statut série automatiquement
        if completion_percentage == 100:
            series_status = "completed"
        elif completion_percentage > 0:
            series_status = "reading"
        else:
            series_status = "to_read"
        
        # 5. Sauvegarder
        series_library_collection.update_one(
            {"id": series_id, "user_id": current_user["id"]},
            {
                "$set": {
                    "volumes": volumes,
                    "completion_percentage": completion_percentage,
                    "series_status": series_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "completion_percentage": completion_percentage,
            "series_status": series_status,
            "read_count": read_count,
            "total_volumes": len(volumes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du tome: {str(e)}")

@app.put("/api/series/library/{series_id}")
async def update_series_status(
    series_id: str,
    status_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour le statut global d'une série"""
    try:
        new_status = status_data.get("series_status")
        if new_status not in ["to_read", "reading", "completed"]:
            raise HTTPException(status_code=400, detail="Statut invalide")
        
        result = series_library_collection.update_one(
            {"id": series_id, "user_id": current_user["id"], "type": "series"},
            {
                "$set": {
                    "series_status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Série non trouvée")
        
        return {"success": True, "message": "Statut mis à jour"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")

@app.delete("/api/series/library/{series_id}")
async def delete_series_from_library(
    series_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer une série de la bibliothèque"""
    try:
        result = series_library_collection.delete_one({
            "id": series_id,
            "user_id": current_user["id"],
            "type": "series"
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Série non trouvée")
        
        return {"success": True, "message": "Série supprimée de votre bibliothèque"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)