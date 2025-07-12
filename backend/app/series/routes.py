from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import re
import json
import os
import asyncio
import logging
from ..database.connection import books_collection, series_library_collection
from ..security.jwt import get_current_user
from ..models.series import VolumeData, SeriesLibraryCreate, SeriesReadingPreferences, SeriesReadingPreferencesUpdate
from .image_service import image_service

logger = logging.getLogger(__name__)

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

# ✅ NOUVEAUX ENDPOINTS : Gestion des préférences de lecture des tomes par série

@router.get("/reading-preferences/{series_name}")
async def get_series_reading_preferences(
    series_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les préférences de lecture d'une série pour l'utilisateur connecté
    """
    try:
        # Chercher les préférences existantes pour cette série et cet utilisateur
        preferences = series_library_collection.find_one({
            "user_id": current_user["id"],
            "series_name": series_name
        }, {"_id": 0})
        
        if preferences and "read_tomes" in preferences:
            return {
                "series_name": series_name,
                "read_tomes": preferences["read_tomes"]
            }
        else:
            # Aucune préférence trouvée, retourner liste vide
            return {
                "series_name": series_name,
                "read_tomes": []
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des préférences: {str(e)}")

@router.post("/reading-preferences")
async def save_series_reading_preferences(
    preferences: SeriesReadingPreferences,
    current_user: dict = Depends(get_current_user)
):
    """
    Sauvegarder les préférences de lecture d'une série pour l'utilisateur connecté
    """
    try:
        # Préparer les données à sauvegarder
        preference_data = {
            "user_id": current_user["id"],
            "series_name": preferences.series_name,
            "read_tomes": preferences.read_tomes,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Upsert (créer ou mettre à jour) les préférences
        result = series_library_collection.update_one(
            {
                "user_id": current_user["id"],
                "series_name": preferences.series_name
            },
            {
                "$set": preference_data,
                "$setOnInsert": {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )
        
        return {
            "message": "Préférences de lecture sauvegardées avec succès",
            "series_name": preferences.series_name,
            "read_tomes": preferences.read_tomes,
            "updated": result.modified_count > 0,
            "created": result.upserted_id is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde des préférences: {str(e)}")

@router.put("/reading-preferences/{series_name}")
async def update_series_reading_preferences(
    series_name: str,
    preferences: SeriesReadingPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Mettre à jour les préférences de lecture d'une série pour l'utilisateur connecté
    """
    try:
        # Mettre à jour les préférences existantes
        result = series_library_collection.update_one(
            {
                "user_id": current_user["id"],
                "series_name": series_name
            },
            {
                "$set": {
                    "read_tomes": preferences.read_tomes,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.matched_count == 0:
            # Aucune préférence trouvée, créer une nouvelle entrée
            preference_data = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "series_name": series_name,
                "read_tomes": preferences.read_tomes,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            series_library_collection.insert_one(preference_data)
            
            return {
                "message": "Nouvelles préférences de lecture créées",
                "series_name": series_name,
                "read_tomes": preferences.read_tomes,
                "created": True
            }
        
        return {
            "message": "Préférences de lecture mises à jour avec succès",
            "series_name": series_name,
            "read_tomes": preferences.read_tomes,
            "updated": result.modified_count > 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour des préférences: {str(e)}")

@router.delete("/reading-preferences/{series_name}")
async def delete_series_reading_preferences(
    series_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer les préférences de lecture d'une série pour l'utilisateur connecté
    """
    try:
        result = series_library_collection.delete_one({
            "user_id": current_user["id"],
            "series_name": series_name
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Aucune préférence trouvée pour cette série")
        
        return {
            "message": f"Préférences de lecture supprimées pour la série '{series_name}'",
            "deleted": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression des préférences: {str(e)}")

# ✅ NOUVELLES ROUTES : Enrichissement d'images pour les séries

@router.post("/enrich/images")
async def enrich_series_with_images(
    request_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Enrichir une liste de séries avec des images de couverture
    """
    try:
        series_list = request_data.get('series_list', [])
        if not series_list:
            raise HTTPException(status_code=400, detail="Liste de séries vide")
        
        # Traitement en arrière-plan pour éviter les timeouts
        background_tasks.add_task(
            _enrich_series_background,
            series_list,
            current_user["id"]
        )
        
        return {
            "message": f"Enrichissement de {len(series_list)} séries démarré en arrière-plan",
            "status": "processing",
            "series_count": len(series_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de l'enrichissement: {str(e)}")

@router.get("/enrich/sample")
async def enrich_sample_series(
    count: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Enrichir un échantillon de séries populaires avec des images
    """
    try:
        # Récupérer un échantillon de séries populaires
        popular_response = await get_popular_series(None, "fr", count, current_user)
        series_list = popular_response["series"]
        
        # Enrichir chaque série avec une image
        enriched_series = await image_service.batch_enrich_series(series_list, max_concurrent=3)
        
        return {
            "message": f"Échantillon de {len(enriched_series)} séries enrichi",
            "enriched_count": sum(1 for s in enriched_series if s.get('cover_url')),
            "total_count": len(enriched_series),
            "series": enriched_series
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enrichissement de l'échantillon: {str(e)}")

@router.post("/enrich/single")
async def enrich_single_series_image(
    series_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Enrichir une série unique avec une image de couverture
    """
    try:
        if not series_data.get('name'):
            raise HTTPException(status_code=400, detail="Nom de série requis")
        
        # Enrichir la série
        enriched_series = await image_service.enrich_series_with_image(series_data)
        
        return {
            "message": f"Série '{series_data['name']}' enrichie",
            "found_image": bool(enriched_series.get('cover_url')),
            "series": enriched_series
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enrichissement de la série: {str(e)}")

@router.post("/enrich/database")
async def enrich_database_with_images(
    request_data: Dict,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Enrichir la base de données complète des séries avec des images
    """
    try:
        sample_size = request_data.get('sample_size', None)
        database_path = "/app/backend/data/extended_series_database.json"
        
        if not os.path.exists(database_path):
            raise HTTPException(status_code=404, detail="Base de données des séries non trouvée")
        
        # Traitement en arrière-plan pour éviter les timeouts
        background_tasks.add_task(
            _enrich_database_background,
            database_path,
            sample_size,
            current_user["id"]
        )
        
        return {
            "message": f"Enrichissement de la base de données démarré (échantillon: {sample_size or 'toute la base'})",
            "status": "processing",
            "database_path": database_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de l'enrichissement: {str(e)}")

@router.get("/images/status")
async def get_image_enrichment_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtenir le statut de l'enrichissement d'images
    """
    try:
        database_path = "/app/backend/data/extended_series_database.json"
        
        if not os.path.exists(database_path):
            return {"status": "no_database", "message": "Base de données non trouvée"}
        
        # Charger un échantillon pour analyser l'état
        with open(database_path, 'r', encoding='utf-8') as f:
            series_data = json.load(f)
        
        total_series = len(series_data)
        series_with_images = sum(1 for series in series_data if series.get('cover_url'))
        
        return {
            "total_series": total_series,
            "series_with_images": series_with_images,
            "enrichment_percentage": (series_with_images / total_series * 100) if total_series > 0 else 0,
            "status": "complete" if series_with_images == total_series else "partial"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la vérification du statut: {str(e)}")

# Fonctions utilitaires pour les tâches en arrière-plan

async def _enrich_series_background(series_list: List[Dict], user_id: str):
    """Enrichir une liste de séries en arrière-plan"""
    try:
        enriched_series = await image_service.batch_enrich_series(series_list, max_concurrent=5)
        logger.info(f"✅ Enrichissement terminé pour utilisateur {user_id}: {len(enriched_series)} séries")
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement arrière-plan: {e}")

async def _enrich_database_background(database_path: str, sample_size: Optional[int], user_id: str):
    """Enrichir la base de données en arrière-plan"""
    try:
        result = await image_service.enrich_series_database(
            database_path, 
            sample_size=sample_size
        )
        logger.info(f"✅ Enrichissement base terminé pour utilisateur {user_id}: {result}")
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement base arrière-plan: {e}")