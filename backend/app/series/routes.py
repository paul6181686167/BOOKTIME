from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import uuid
import re
from ..database.connection import books_collection, series_library_collection
from ..security.jwt import get_current_user
from ..models.series import VolumeData, SeriesLibraryCreate

router = APIRouter(prefix="/api/series", tags=["series"])

@router.get("/popular")
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
            "description": "Les aventures d'Astérix et Obélix en Gaule",
            "first_published": 1961,
            "status": "completed"
        },
        "tintin": {
            "name": "Tintin",
            "category": "bd",
            "score": 17000,
            "keywords": ["tintin", "milou", "capitaine haddock", "dupont"],
            "authors": ["Hergé"],
            "variations": ["Tintin", "Adventures of Tintin"],
            "volumes": 24,
            "languages": ["fr", "en"],
            "description": "Les aventures du reporter Tintin et de son chien Milou",
            "first_published": 1929,
            "status": "completed"
        }
    }
    
    # Filtrer par catégorie si spécifiée
    if category:
        series_data = {k: v for k, v in series_data.items() if v["category"] == category}
    
    # Filtrer par langue si spécifiée
    if language:
        series_data = {k: v for k, v in series_data.items() if language in v["languages"]}
    
    # Convertir en liste et trier par score
    series_list = []
    for series_id, series_info in series_data.items():
        series_list.append({
            "id": series_id,
            **series_info
        })
    
    # Trier par score et limiter
    series_list.sort(key=lambda x: x["score"], reverse=True)
    series_list = series_list[:limit]
    
    return {
        "series": series_list,
        "total": len(series_list)
    }

@router.get("/search")
async def search_series(
    q: str,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Rechercher des séries par nom, mots-clés ou auteur
    """
    if not q or len(q.strip()) < 2:
        return {"series": [], "total": 0, "search_term": q}
    
    # Récupérer les séries populaires
    popular_response = await get_popular_series(category, "fr", 1000, current_user)
    all_series = popular_response["series"]
    
    search_term = q.strip().lower()
    matching_series = []
    
    for series in all_series:
        # Chercher dans le nom
        if search_term in series["name"].lower():
            matching_series.append(series)
            continue
        
        # Chercher dans les mots-clés
        if any(search_term in keyword for keyword in series["keywords"]):
            matching_series.append(series)
            continue
        
        # Chercher dans les auteurs
        if any(search_term in author.lower() for author in series["authors"]):
            matching_series.append(series)
            continue
        
        # Chercher dans les variations
        if any(search_term in variation.lower() for variation in series["variations"]):
            matching_series.append(series)
            continue
    
    return {
        "series": matching_series,
        "total": len(matching_series),
        "search_term": q
    }

@router.get("/detect")
async def detect_series(
    title: str,
    author: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Détecter si un livre appartient à une série connue
    """
    if not title or len(title.strip()) < 2:
        return {"detected_series": [], "book_info": {"title": title, "author": author}}
    
    # Récupérer les séries populaires
    popular_response = await get_popular_series(None, "fr", 1000, current_user)
    all_series = popular_response["series"]
    
    detected_series = []
    title_lower = title.lower()
    author_lower = author.lower() if author else ""
    
    for series in all_series:
        confidence = 0
        
        # Vérifier le nom de la série
        if series["name"].lower() in title_lower:
            confidence += 80
        
        # Vérifier les mots-clés
        matching_keywords = sum(1 for keyword in series["keywords"] if keyword in title_lower)
        confidence += matching_keywords * 20
        
        # Vérifier l'auteur
        if author_lower and any(author_name.lower() in author_lower for author_name in series["authors"]):
            confidence += 50
        
        # Vérifier les variations
        if any(variation.lower() in title_lower for variation in series["variations"]):
            confidence += 60
        
        # Seuil de confiance
        if confidence >= 40:
            detected_series.append({
                "series_name": series["name"],
                "confidence": confidence,
                "authors": series["authors"],
                "category": series["category"],
                "volumes": series["volumes"],
                "description": series["description"]
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

@router.post("/complete")
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
    
    # Vérifier les volumes existants
    existing_volumes = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": {"$regex": re.escape(series_name), "$options": "i"}
    }))
    
    existing_volume_numbers = {book.get("volume_number", 1) for book in existing_volumes}
    
    # Créer les volumes manquants
    created_books = []
    for volume_num in range(1, target_volumes + 1):
        if volume_num not in existing_volume_numbers:
            # Utiliser le titre spécifique si disponible
            volume_title = f"{series_name} - Tome {volume_num}"
            if series_info and series_info["tomes"] and volume_num <= len(series_info["tomes"]):
                volume_title = series_info["tomes"][volume_num - 1]
            
            book_id = str(uuid.uuid4())
            new_book = {
                "id": book_id,
                "user_id": current_user["id"],
                "title": volume_title,
                "author": base_author,
                "category": base_category,
                "saga": series_name,
                "volume_number": volume_num,
                "status": "to_read",
                "genre": base_genre,
                "publisher": base_publisher,
                "auto_added": True,
                "date_added": datetime.utcnow(),
                "description": f"Tome {volume_num} de la série {series_name}",
                "total_pages": None,
                "current_page": None,
                "rating": None,
                "review": "",
                "cover_url": "",
                "publication_year": None,
                "isbn": "",
                "date_started": None,
                "date_completed": None,
                "updated_at": datetime.utcnow()
            }
            
            books_collection.insert_one(new_book)
            created_books.append(new_book)
    
    return {
        "success": True,
        "message": f"{len(created_books)} tome(s) ajouté(s) à votre bibliothèque !",
        "series_name": series_name,
        "created_books": len(created_books),
        "existing_volumes": len(existing_volumes),
        "created_volumes": len(created_books)
    }

@router.get("/library")
async def get_series_library_endpoint(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint de délégation pour obtenir les séries de la bibliothèque"""
    # Importer la fonction depuis library.routes
    from app.library.routes import get_series_library
    
    # Déléguer l'appel à la fonction existante
    return await get_series_library(category, current_user)

@router.post("/library")
async def add_series_to_library_endpoint(
    series_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint de délégation pour ajouter une série à la bibliothèque"""
    # Importer la fonction depuis library.routes
    from app.library.routes import create_series_library
    from app.models.series import SeriesLibraryCreate
    
    # Convertir les données en modèle Pydantic
    series_create = SeriesLibraryCreate(**series_data)
    
    # Déléguer l'appel à la fonction existante
    return await create_series_library(series_create, current_user)

@router.put("/library/{series_id}/volume/{volume_number}")
async def update_volume_status_endpoint(
    series_id: str,
    volume_number: int,
    volume_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint de délégation pour mettre à jour le statut d'un volume"""
    # Importer la fonction depuis library.routes
    from app.library.routes import update_volume_status
    
    # Déléguer l'appel à la fonction existante
    return await update_volume_status(series_id, volume_number, volume_data, current_user)

@router.put("/library/{series_id}")
async def update_series_status_endpoint(
    series_id: str,
    series_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint de délégation pour mettre à jour le statut global d'une série"""
    # Importer la fonction depuis library.routes
    from app.library.routes import update_series_status
    
    # Déléguer l'appel à la fonction existante
    return await update_series_status(series_id, series_data, current_user)

@router.delete("/library/{series_id}")
async def delete_series_from_library_endpoint(
    series_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Endpoint de délégation pour supprimer une série de la bibliothèque"""
    # Importer la fonction depuis library.routes
    from app.library.routes import delete_series
    
    # Déléguer l'appel à la fonction existante
    return await delete_series(series_id, current_user)