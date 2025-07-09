from fastapi import APIRouter, Depends
from typing import Optional
from ..database.connection import books_collection, series_library_collection
from ..security.jwt import get_current_user
from ..models.series import SeriesLibraryCreate, VolumeData

router = APIRouter(prefix="/api/library", tags=["library"])

@router.get("/series")
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

# Routes pour les séries en bibliothèque (nouvelle fonctionnalité)
@router.post("/series")
async def create_series_library(
    series_data: SeriesLibraryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle série dans la bibliothèque"""
    import uuid
    from datetime import datetime
    
    series_id = str(uuid.uuid4())
    series = {
        "id": series_id,
        "user_id": current_user["id"],
        **series_data.model_dump(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    series_library_collection.insert_one(series)
    series.pop("_id", None)
    
    return {
        "success": True,
        "message": "Série créée avec succès",
        "series": series
    }

@router.get("/series")
async def get_series_library(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Obtenir toutes les séries de la bibliothèque"""
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    
    series_list = list(series_library_collection.find(filter_dict, {"_id": 0}))
    
    return series_list

@router.put("/series/{series_id}/volume/{volume_number}")
async def update_volume_status(
    series_id: str,
    volume_number: int,
    volume_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour le statut d'un volume dans une série"""
    from datetime import datetime
    
    # Vérifier que la série appartient à l'utilisateur
    series = series_library_collection.find_one({
        "id": series_id,
        "user_id": current_user["id"]
    })
    
    if not series:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    # Mettre à jour le volume
    result = series_library_collection.update_one(
        {
            "id": series_id,
            "user_id": current_user["id"],
            "volumes.volume_number": volume_number
        },
        {
            "$set": {
                "volumes.$.is_read": volume_data.get("is_read", False),
                "volumes.$.date_read": datetime.utcnow().isoformat() if volume_data.get("is_read") else None,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Volume non trouvé")
    
    return {
        "success": True,
        "message": f"Volume {volume_number} mis à jour"
    }

@router.put("/series/{series_id}")
async def update_series_status(
    series_id: str,
    series_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour le statut global d'une série"""
    from datetime import datetime
    
    new_status = series_data.get("series_status")
    if not new_status or new_status not in ["to_read", "reading", "completed"]:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    result = series_library_collection.update_one(
        {
            "id": series_id,
            "user_id": current_user["id"]
        },
        {
            "$set": {
                "series_status": new_status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    return {
        "success": True,
        "message": "Statut de la série mis à jour"
    }

@router.delete("/series/{series_id}")
async def delete_series(
    series_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer une série de la bibliothèque"""
    from fastapi import HTTPException
    
    result = series_library_collection.delete_one({
        "id": series_id,
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    return {"success": True, "message": "Série supprimée de votre bibliothèque"}