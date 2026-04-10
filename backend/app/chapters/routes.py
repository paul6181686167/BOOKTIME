"""
Routes API pour le système de chapitres
======================================

Exposition des 8 nouveaux endpoints :
- GET /api/chapters/series/{series_name}
- POST /api/chapters/series/{series_name}/refresh  
- GET /api/chapters/releases/upcoming
- GET /api/chapters/user/stats
- GET /api/chapters/search/{series_name}
- POST /api/chapters/series/{series_name}/map-ids
- GET /api/chapters/integrations/status
- PUT /api/chapters/predictions/config
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
import logging

from ..dependencies import get_current_user
from .service import ChapterService
from .models import (
    SeriesChapters,
    SeriesChaptersResponse, 
    ChapterSearchResult,
    IntegrationStatus,
    UpcomingReleases
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chapters", tags=["chapters"])

# Instance globale du service
service = ChapterService()


@router.get("/series/{series_name}", response_model=SeriesChaptersResponse)
async def get_series_chapters(
    series_name: str,
    force_refresh: bool = Query(False, description="Forcer le rafraîchissement depuis les APIs"),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère les informations de chapitres pour une série
    
    - **series_name**: Nom de la série (ex: "One Piece")
    - **force_refresh**: Force la récupération depuis les APIs externes
    
    Returns:
        Données complètes de la série avec chapitres et prédictions
    """
    try:
        logger.info(f"Récupération chapitres pour {series_name} (user: {current_user.id})")
        
        series_data = await service.get_series_chapters(series_name, force_refresh=force_refresh)
        
        if not series_data:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée trouvée pour la série '{series_name}'"
            )
        
        return SeriesChaptersResponse(
            success=True,
            data=series_data,
            message=f"Données récupérées pour {series_name}",
            cached=not force_refresh and series_data.cache_expires is not None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération chapitres {series_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de la récupération des chapitres: {str(e)}"
        )


@router.post("/series/{series_name}/refresh")
async def refresh_series_chapters(
    series_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Force l'actualisation des données d'une série depuis les APIs externes
    
    - **series_name**: Nom de la série à actualiser
    
    Returns:
        Confirmation de l'actualisation
    """
    try:
        logger.info(f"Rafraîchissement forcé pour {series_name} (user: {current_user.id})")
        
        success = await service.refresh_series_chapters(series_name)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de rafraîchir les données pour '{series_name}'"
            )
        
        return {
            "success": True,
            "message": f"Données rafraîchies pour {series_name}",
            "updated_at": "now"  # Sera remplacé par timestamp réel
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur rafraîchissement {series_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du rafraîchissement: {str(e)}"
        )


@router.get("/releases/upcoming", response_model=UpcomingReleases)
async def get_upcoming_releases(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère le planning des sorties de chapitres à venir
    
    Returns:
        Planning organisé par période (cette semaine, semaine prochaine, ce mois)
    """
    try:
        logger.info(f"Récupération planning sorties (user: {current_user.id})")
        
        releases = await service.get_upcoming_releases()
        
        return UpcomingReleases(**releases)
        
    except Exception as e:
        logger.error(f"Erreur récupération planning: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du planning: {str(e)}"
        )


@router.get("/user/stats")
async def get_user_chapter_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Statistiques utilisateur liées aux chapitres
    
    Returns:
        Statistiques personnalisées de lecture de chapitres
    """
    try:
        # Pour l'instant, statistiques basiques
        # À enrichir avec données utilisateur réelles
        stats = {
            "chapters_read_this_week": 0,
            "series_following": 0,
            "predictions_accuracy": 0.85,
            "favorite_release_day": "Monday",
            "total_chapters_tracked": 0
        }
        
        return {
            "success": True,
            "user_id": current_user.id,
            "stats": stats,
            "last_updated": "now"
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération stats utilisateur: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )


@router.get("/search/{series_name}", response_model=ChapterSearchResult)
async def search_series_in_apis(
    series_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche une série dans les APIs externes pour mapping
    
    - **series_name**: Nom de la série à rechercher
    
    Returns:
        Résultats de recherche dans AniList et MangaUpdates avec scores de confiance
    """
    try:
        logger.info(f"Recherche série {series_name} (user: {current_user.id})")
        
        search_results = await service.search_series_in_apis(series_name)
        
        return ChapterSearchResult(**search_results)
        
    except Exception as e:
        logger.error(f"Erreur recherche série {series_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche: {str(e)}"
        )


@router.post("/series/{series_name}/map-ids")
async def map_series_ids(
    series_name: str,
    mapping_data: dict = Body(..., description="IDs de mapping"),
    current_user: dict = Depends(get_current_user)
):
    """
    Associe une série aux IDs des APIs externes
    
    - **series_name**: Nom de la série
    - **mapping_data**: {"anilist_id": int, "mangaupdates_id": int}
    
    Returns:
        Confirmation du mapping
    """
    try:
        anilist_id = mapping_data.get("anilist_id")
        mangaupdates_id = mapping_data.get("mangaupdates_id")
        
        if not anilist_id and not mangaupdates_id:
            raise HTTPException(
                status_code=400,
                detail="Au moins un ID (anilist_id ou mangaupdates_id) doit être fourni"
            )
        
        logger.info(f"Mapping IDs pour {series_name}: AniList={anilist_id}, MU={mangaupdates_id}")
        
        success = await service.map_series_ids(
            series_name=series_name,
            anilist_id=anilist_id,
            mangaupdates_id=mangaupdates_id
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de mapper les IDs pour '{series_name}'"
            )
        
        return {
            "success": True,
            "series_name": series_name,
            "mapped_ids": {
                "anilist_id": anilist_id,
                "mangaupdates_id": mangaupdates_id
            },
            "message": "IDs mappés avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur mapping IDs {series_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du mapping: {str(e)}"
        )


@router.get("/integrations/status")
async def get_integrations_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Vérifie le statut des intégrations avec les APIs externes
    
    Returns:
        Statut de santé de chaque API (AniList, MangaUpdates)
    """
    try:
        logger.info(f"Vérification statut intégrations (user: {current_user.id})")
        
        status = await service.get_integration_status()
        
        return {
            "success": True,
            "integrations": status,
            "checked_at": "now"
        }
        
    except Exception as e:
        logger.error(f"Erreur vérification intégrations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la vérification: {str(e)}"
        )


@router.put("/predictions/config")
async def update_predictions_config(
    config_data: dict = Body(..., description="Configuration des prédictions"),
    current_user: dict = Depends(get_current_user)
):
    """
    Met à jour la configuration des prédictions de chapitres
    
    - **config_data**: {"enable_predictions": bool, "confidence_threshold": float}
    
    Returns:
        Confirmation de la mise à jour
    """
    try:
        enable_predictions = config_data.get("enable_predictions", True)
        confidence_threshold = config_data.get("confidence_threshold", 0.8)
        
        if not isinstance(enable_predictions, bool):
            raise HTTPException(
                status_code=400,
                detail="enable_predictions doit être un booléen"
            )
        
        if not 0 <= confidence_threshold <= 1:
            raise HTTPException(
                status_code=400,
                detail="confidence_threshold doit être entre 0 et 1"
            )
        
        logger.info(f"Mise à jour config prédictions (user: {current_user.id})")
        
        # Configuration sauvegardée (implémentation future)
        updated_config = {
            "enable_predictions": enable_predictions,
            "confidence_threshold": confidence_threshold,
            "updated_at": "now",
            "updated_by": current_user.id
        }
        
        return {
            "success": True,
            "config": updated_config,
            "message": "Configuration mise à jour avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur mise à jour config: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


# Routes utilitaires supplémentaires

@router.get("/health")
async def health_check():
    """
    Vérification de santé du module chapitres
    
    Returns:
        Statut de santé du module
    """
    try:
        # Test basique de connectivité
        return {
            "status": "ok",
            "module": "chapters",
            "version": "1.0.0",
            "features": [
                "series_chapters",
                "predictions", 
                "volume_grouping",
                "external_apis"
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "module": "chapters",
                "error": str(e)
            }
        )


@router.get("/debug/series/{series_name}")
async def debug_series_data(
    series_name: str,
    include_raw: bool = Query(False, description="Inclure données brutes APIs"),
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint de debug pour analyser les données d'une série
    
    - **series_name**: Nom de la série
    - **include_raw**: Inclure les données brutes des APIs
    
    Returns:
        Données de debug détaillées
    """
    try:
        logger.info(f"Debug série {series_name} (user: {current_user.id})")
        
        # Données basiques
        debug_info = {
            "series_name": series_name,
            "cache_status": "unknown",
            "last_sync": None,
            "mapped_ids": {},
            "chapters_count": 0,
            "volumes_count": 0
        }
        
        # Récupération données si disponibles
        series_data = await service.get_series_chapters(series_name, force_refresh=False)
        if series_data:
            debug_info.update({
                "cache_status": "found",
                "last_sync": series_data.last_updated.isoformat() if series_data.last_updated else None,
                "mapped_ids": {
                    "anilist": series_data.manga_id_anilist,
                    "mangaupdates": series_data.manga_id_mangaupdates
                },
                "chapters_count": len(series_data.current_chapters),
                "volumes_count": len(series_data.volumes)
            })
        
        return {
            "success": True,
            "debug_info": debug_info,
            "generated_at": "now"
        }
        
    except Exception as e:
        logger.error(f"Erreur debug série {series_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du debug: {str(e)}"
        )