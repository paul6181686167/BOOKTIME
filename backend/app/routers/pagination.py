# Phase 2.2 : Pagination et Cache - Routes API
"""
Nouvelles routes API avec pagination et cache intégré
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from ..auth.dependencies import get_current_user
from ..services.pagination import pagination_service, PaginatedResponse
from ..models.user import User

router = APIRouter()

@router.get("/books/paginated", response_model=PaginatedResponse)
async def get_paginated_books(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    category: Optional[str] = Query(None, description="Filtre par catégorie"),
    status: Optional[str] = Query(None, description="Filtre par statut"),
    author: Optional[str] = Query(None, description="Filtre par auteur"),
    saga: Optional[str] = Query(None, description="Filtre par saga"),
    sort_by: str = Query("date_added", description="Champ de tri"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri")
):
    """
    Récupère les livres avec pagination et cache
    
    Fonctionnalités :
    - Pagination configurable (limit/offset)
    - Filtres multiples (catégorie, statut, auteur, saga)
    - Tri personnalisable
    - Cache Redis intégré
    - Réponse optimisée avec métadonnées de pagination
    """
    
    try:
        result = pagination_service.get_paginated_books(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            category=category,
            status=status,
            author=author,
            saga=saga,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération livres: {str(e)}")

@router.get("/series/paginated", response_model=PaginatedResponse)
async def get_paginated_series(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    category: Optional[str] = Query(None, description="Filtre par catégorie"),
    status: Optional[str] = Query(None, description="Filtre par statut")
):
    """
    Récupère les séries avec pagination et cache
    
    Fonctionnalités :
    - Pagination configurable
    - Filtres par catégorie et statut
    - Cache Redis intégré
    - Métadonnées de pagination complètes
    """
    
    try:
        result = pagination_service.get_paginated_series(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            category=category,
            status=status
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération séries: {str(e)}")

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Terme de recherche"),
    limit: int = Query(5, ge=1, le=20, description="Nombre de suggestions"),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère des suggestions de recherche avec cache
    
    Fonctionnalités :
    - Recherche dans titres, auteurs, sagas
    - Cache optimisé pour les suggestions
    - Réponse ultra-rapide
    """
    
    try:
        suggestions = pagination_service.get_search_suggestions(
            user_id=current_user.id,
            query=q,
            limit=limit
        )
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur suggestions: {str(e)}")

@router.post("/cache/invalidate")
async def invalidate_user_cache(
    current_user: User = Depends(get_current_user)
):
    """
    Invalide le cache pour l'utilisateur actuel
    
    Utile après des modifications importantes
    """
    
    try:
        pagination_service.invalidate_user_cache(current_user.id)
        return {"message": "Cache invalidé avec succès"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur invalidation cache: {str(e)}")

@router.get("/cache/status")
async def get_cache_status():
    """
    Vérifie le statut du cache Redis
    """
    
    try:
        cache_enabled = pagination_service.cache.cache_enabled
        redis_info = None
        
        if cache_enabled:
            try:
                redis_info = {
                    "connected": True,
                    "ping": pagination_service.cache.redis_client.ping()
                }
            except:
                redis_info = {"connected": False}
        
        return {
            "cache_enabled": cache_enabled,
            "redis_info": redis_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur statut cache: {str(e)}")