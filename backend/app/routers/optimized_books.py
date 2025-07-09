# Router optimisé pour les livres avec cache et pagination avancée
"""
Router de livres optimisé intégrant :
- Pagination avancée avec métadonnées
- Cache Redis automatique
- Monitoring des performances
- Indexes MongoDB optimisés
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, Any
from ..models.book import BookCreate, BookUpdate, BookResponse
from ..services.optimized_book_service import optimized_book_service
from ..security.jwt import get_current_user
from ..utils.pagination import PaginationParams, PaginatedResponse
from ..utils.cache import cache
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/books", tags=["books-optimized"])

@router.get("/", response_model=PaginatedResponse[BookResponse])
async def get_books_optimized(
    # Paramètres de pagination
    page: int = Query(1, ge=1, description="Numéro de page"),
    limit: int = Query(20, ge=1, le=100, description="Éléments par page"),
    sort_by: str = Query("date_added", description="Champ de tri"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri"),
    
    # Paramètres de filtrage
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    
    # Dépendances
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les livres d'un utilisateur avec pagination avancée et cache
    """
    start_time = time.time()
    
    # Créer les paramètres de pagination
    pagination = PaginationParams(
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    try:
        # Utiliser le service optimisé
        result = await optimized_book_service.get_books_paginated(
            current_user["id"],
            pagination,
            category=category,
            status=status
        )
        
        # Ajouter les métriques de performance dans les headers
        duration = (time.time() - start_time) * 1000
        logger.info(f"GET /api/v2/books: {duration:.2f}ms, page {page}, {len(result.data)} items")
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur get_books_optimized: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve books")

@router.get("/stats")
async def get_stats_optimized(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les statistiques optimisées avec cache
    """
    start_time = time.time()
    
    try:
        stats = await optimized_book_service.get_stats_optimized(current_user["id"])
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"GET /api/v2/books/stats: {duration:.2f}ms")
        
        return stats
        
    except Exception as e:
        logger.error(f"Erreur get_stats_optimized: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.post("/", response_model=BookResponse)
async def create_book_optimized(
    book_data: BookCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Créer un nouveau livre avec invalidation automatique du cache
    """
    start_time = time.time()
    
    try:
        book = await optimized_book_service.create_book_optimized(
            current_user["id"],
            book_data
        )
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"POST /api/v2/books: {duration:.2f}ms, book created: {book.id}")
        
        return book
        
    except Exception as e:
        logger.error(f"Erreur create_book_optimized: {e}")
        raise HTTPException(status_code=500, detail="Failed to create book")

@router.put("/{book_id}", response_model=BookResponse)
async def update_book_optimized(
    book_id: str,
    update_data: BookUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Mettre à jour un livre avec invalidation automatique du cache
    """
    start_time = time.time()
    
    try:
        book = await optimized_book_service.update_book_optimized(
            current_user["id"],
            book_id,
            update_data
        )
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"PUT /api/v2/books/{book_id}: {duration:.2f}ms")
        
        return book
        
    except Exception as e:
        logger.error(f"Erreur update_book_optimized: {e}")
        raise HTTPException(status_code=500, detail="Failed to update book")

@router.delete("/{book_id}")
async def delete_book_optimized(
    book_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Supprimer un livre avec invalidation automatique du cache
    """
    start_time = time.time()
    
    try:
        result = await optimized_book_service.delete_book_optimized(
            current_user["id"],
            book_id
        )
        
        duration = (time.time() - start_time) * 1000
        logger.info(f"DELETE /api/v2/books/{book_id}: {duration:.2f}ms")
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur delete_book_optimized: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete book")

@router.get("/performance")
async def get_performance_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtenir les métriques de performance détaillées
    """
    try:
        metrics = await optimized_book_service.get_performance_metrics()
        
        # Ajouter des métriques supplémentaires
        metrics["endpoints"] = {
            "optimized_version": "v2",
            "features": [
                "Advanced pagination",
                "Redis caching",
                "MongoDB indexes",
                "Performance monitoring"
            ]
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Erreur get_performance_metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")

@router.post("/cache/invalidate")
async def invalidate_user_cache(
    current_user: dict = Depends(get_current_user)
):
    """
    Invalider manuellement le cache d'un utilisateur
    """
    try:
        cache.flush_user_cache(current_user["id"])
        
        return {
            "message": "Cache invalidé avec succès",
            "user_id": current_user["id"]
        }
        
    except Exception as e:
        logger.error(f"Erreur invalidate_user_cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")

@router.get("/cache/stats")
async def get_cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Obtenir les statistiques du cache Redis
    """
    try:
        stats = cache.get_cache_stats()
        
        return {
            "cache_stats": stats,
            "cache_available": cache.is_available
        }
        
    except Exception as e:
        logger.error(f"Erreur get_cache_stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")

# Routes de test pour comparer les performances
@router.get("/benchmark/pagination")
async def benchmark_pagination(
    pages: int = Query(5, ge=1, le=20, description="Nombre de pages à tester"),
    current_user: dict = Depends(get_current_user)
):
    """
    Benchmark des performances de pagination
    """
    results = []
    
    for page in range(1, pages + 1):
        start_time = time.time()
        
        pagination = PaginationParams(page=page, limit=10, sort_by="date_added", sort_order="desc")
        
        try:
            result = await optimized_book_service.get_books_paginated(
                current_user["id"],
                pagination
            )
            
            duration = (time.time() - start_time) * 1000
            
            results.append({
                "page": page,
                "duration_ms": round(duration, 2),
                "items_count": len(result.data),
                "from_cache": duration < 5  # Approximation
            })
            
        except Exception as e:
            results.append({
                "page": page,
                "error": str(e)
            })
    
    # Calculer les statistiques
    durations = [r["duration_ms"] for r in results if "duration_ms" in r]
    
    return {
        "benchmark_results": results,
        "summary": {
            "total_pages": pages,
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "total_duration_ms": round(sum(durations), 2)
        }
    }