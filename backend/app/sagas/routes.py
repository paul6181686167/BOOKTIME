from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import uuid
import re
from ..database.connection import books_collection
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/sagas", tags=["sagas"])

@router.get("")
async def get_sagas(current_user: dict = Depends(get_current_user)):
    """Obtenir la liste des sagas de l'utilisateur"""
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

@router.get("/{saga_name}/books")
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
            "spin-off", "prequel", "sequel", "adaptation", "remix", "reboot",
            "alternate", "alternative", "what if", "side story", "gaiden"
        ]
        
        if any(keyword in book_title for keyword in suspicious_keywords):
            include_book = False
        
        if include_book:
            filtered_books.append(book)
    
    return filtered_books

@router.post("/{saga_name}/auto-add")
async def auto_add_next_volume(
    saga_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Ajouter automatiquement le prochain tome d'une saga
    """
    # Récupérer les livres existants de la saga
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }).sort("volume_number", 1))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Trouver le prochain numéro de volume
    volume_numbers = [book.get("volume_number", 1) for book in existing_books]
    next_volume = max(volume_numbers) + 1 if volume_numbers else 1
    
    # Utiliser le premier livre comme modèle
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
        "genre": template_book.get("genre", ""),
        "publisher": template_book.get("publisher", ""),
        "auto_added": True,
        "date_added": datetime.utcnow(),
        "description": f"Tome {next_volume} de la saga {saga_name}",
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
    
    return {
        "success": True,
        "message": f"Tome {next_volume} ajouté à la saga {saga_name}",
        "book": new_book
    }

@router.put("/{saga_name}/bulk-status")
async def bulk_update_saga_status(
    saga_name: str,
    status_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Mettre à jour le statut de tous les livres d'une saga
    """
    new_status = status_data.get("status")
    if not new_status or new_status not in ["to_read", "reading", "completed"]:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    # Mettre à jour tous les livres de la saga
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }
    
    # Ajouter les dates selon le statut
    if new_status == "reading":
        update_data["date_started"] = datetime.utcnow()
    elif new_status == "completed":
        update_data["date_started"] = datetime.utcnow()
        update_data["date_completed"] = datetime.utcnow()
    
    result = books_collection.update_many(
        {
            "user_id": current_user["id"],
            "saga": saga_name
        },
        {"$set": update_data}
    )
    
    return {
        "success": True,
        "message": f"Statut mis à jour pour {result.modified_count} livre(s) de la saga {saga_name}",
        "updated_count": result.modified_count
    }

@router.post("/{saga_name}/auto-complete")
async def auto_complete_saga(
    saga_name: str,
    completion_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Compléter automatiquement une saga avec tous ses volumes
    """
    target_volumes = completion_data.get("target_volumes", 10)
    
    # Récupérer les livres existants de la saga
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Utiliser le premier livre comme modèle
    template_book = existing_books[0]
    
    # Déterminer les volumes existants
    existing_volumes = {book.get("volume_number", 1) for book in existing_books}
    
    # Créer les volumes manquants
    created_books = []
    for volume_num in range(1, target_volumes + 1):
        if volume_num not in existing_volumes:
            book_id = str(uuid.uuid4())
            new_book = {
                "id": book_id,
                "user_id": current_user["id"],
                "title": f"{saga_name} - Tome {volume_num}",
                "author": template_book.get("author", ""),
                "category": template_book.get("category", "roman"),
                "saga": saga_name,
                "volume_number": volume_num,
                "status": "to_read",
                "genre": template_book.get("genre", ""),
                "publisher": template_book.get("publisher", ""),
                "auto_added": True,
                "date_added": datetime.utcnow(),
                "description": f"Tome {volume_num} de la saga {saga_name}",
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
        "message": f"{len(created_books)} tome(s) ajouté(s) à la saga {saga_name}",
        "created_books": len(created_books),
        "existing_books": len(existing_books),
        "total_volumes": target_volumes
    }

@router.get("/{saga_name}/missing-analysis")
async def analyze_missing_volumes(
    saga_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyser les volumes manquants d'une saga
    """
    # Récupérer les livres existants de la saga
    existing_books = list(books_collection.find({
        "user_id": current_user["id"],
        "saga": saga_name
    }))
    
    if not existing_books:
        raise HTTPException(status_code=404, detail="Saga non trouvée")
    
    # Analyser les volumes
    volume_numbers = [book.get("volume_number", 1) for book in existing_books if book.get("volume_number")]
    
    if not volume_numbers:
        return {
            "saga_name": saga_name,
            "total_books": len(existing_books),
            "has_volume_numbers": False,
            "missing_volumes": [],
            "gaps": []
        }
    
    min_volume = min(volume_numbers)
    max_volume = max(volume_numbers)
    
    # Identifier les volumes manquants
    missing_volumes = []
    for vol_num in range(min_volume, max_volume + 1):
        if vol_num not in volume_numbers:
            missing_volumes.append(vol_num)
    
    # Identifier les gaps (séquences manquantes)
    gaps = []
    if missing_volumes:
        gap_start = missing_volumes[0]
        gap_end = missing_volumes[0]
        
        for i in range(1, len(missing_volumes)):
            if missing_volumes[i] == gap_end + 1:
                gap_end = missing_volumes[i]
            else:
                gaps.append({"start": gap_start, "end": gap_end})
                gap_start = missing_volumes[i]
                gap_end = missing_volumes[i]
        
        gaps.append({"start": gap_start, "end": gap_end})
    
    return {
        "saga_name": saga_name,
        "total_books": len(existing_books),
        "has_volume_numbers": True,
        "volume_range": {
            "min": min_volume,
            "max": max_volume
        },
        "missing_volumes": missing_volumes,
        "gaps": gaps,
        "completion_percentage": round((len(volume_numbers) / (max_volume - min_volume + 1)) * 100) if volume_numbers else 0
    }