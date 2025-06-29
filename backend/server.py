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
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }, {"_id": 0}).sort("volume_number", 1))
    
    return books

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)