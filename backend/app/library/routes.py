from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from ..database.connection import series_library_collection
from ..security.jwt import get_current_user
from ..models.series import SeriesLibraryCreate, VolumeData
from .series_library_helpers import (
    normalize_series_library_doc,
    series_library_duplicate_query,
)

router = APIRouter(prefix="/api/library", tags=["library"])

# Routes pour les séries en bibliothèque (nouvelle fonctionnalité)
@router.post("/series")
async def create_series_library(
    series_data: SeriesLibraryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer ou mettre à jour une série dans la bibliothèque (upsert pour éviter les doublons)"""
    import uuid
    from datetime import datetime, timezone

    user_id = current_user["id"]
    data = series_data.model_dump()
    series_name = (data.get("series_name") or data.get("name") or "").strip()

    # Vérifier si la série existe déjà pour cet utilisateur (clé canonique `series_name`, repli `name` legacy)
    existing = series_library_collection.find_one(
        series_library_duplicate_query(user_id, series_name)
    )
    if existing:
        existing.pop("_id", None)
        return {
            "success": True,
            "message": "Série déjà dans ta bibliothèque",
            "series": normalize_series_library_doc(existing),
        }

    # total_volumes dérivé des tomes si absent / à 0
    vols = data.get("volumes") or []
    if not data.get("total_volumes"):
        data["total_volumes"] = len(vols)

    series_id = str(uuid.uuid4())
    series = {
        "id": series_id,
        "user_id": user_id,
        **data,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    series_library_collection.insert_one(series)
    series.pop("_id", None)

    return {
        "success": True,
        "message": "Série ajoutée à ta bibliothèque",
        "series": normalize_series_library_doc(series),
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

    return [normalize_series_library_doc(s) for s in series_list]

@router.put("/series/{series_id}/volume/{volume_number}")
async def update_volume_status(
    series_id: str,
    volume_number: int,
    volume_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour le statut d'un volume dans une série"""
    from datetime import datetime, timezone
    
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
                "volumes.$.date_read": datetime.now(timezone.utc).isoformat() if volume_data.get("is_read") else None,
                "updated_at": datetime.now(timezone.utc)
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
    """Mettre à jour le statut global et/ou la page courante d'une série (livre rétrogradé inclus)."""
    from datetime import datetime, timezone
    
    new_status = series_data.get("series_status")
    has_page = "current_page" in series_data
    has_total = "total_pages" in series_data
    if new_status is not None and new_status not in ["to_read", "reading", "completed"]:
        raise HTTPException(status_code=400, detail="Statut invalide")
    if new_status is None and not has_page and not has_total:
        raise HTTPException(status_code=400, detail="Aucune mise à jour fournie")

    update_fields: dict = {"updated_at": datetime.now(timezone.utc)}
    if new_status is not None:
        update_fields["series_status"] = new_status
    if has_page:
        raw_page = series_data.get("current_page")
        if raw_page is None or raw_page == "":
            update_fields["current_page"] = None
        else:
            try:
                page_i = int(raw_page)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="current_page invalide")
            if page_i < 0:
                raise HTTPException(status_code=400, detail="current_page invalide")
            update_fields["current_page"] = page_i
            # Saisie d'une page ⇒ considéré en cours de lecture
            if page_i > 0 and new_status is None:
                update_fields["series_status"] = "reading"
    if has_total:
        raw_total = series_data.get("total_pages")
        if raw_total is None or raw_total == "":
            update_fields["total_pages"] = None
        else:
            try:
                total_i = int(raw_total)
            except (TypeError, ValueError):
                raise HTTPException(status_code=400, detail="total_pages invalide")
            if total_i <= 0:
                raise HTTPException(status_code=400, detail="total_pages invalide")
            update_fields["total_pages"] = total_i

    result = series_library_collection.update_one(
        {
            "id": series_id,
            "user_id": current_user["id"]
        },
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Série non trouvée")
    
    return {
        "success": True,
        "message": "Série mise à jour",
        "updated": {k: v for k, v in update_fields.items() if k != "updated_at"},
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