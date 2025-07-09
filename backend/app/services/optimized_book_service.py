# Service de livres optimisé avec cache et pagination avancée
"""
Version optimisée du service de livres intégrant :
- Pagination avancée
- Cache Redis
- Indexes MongoDB optimisés
- Monitoring des performances
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from ..database import books_collection, authors_collection
from ..models.book import BookCreate, BookUpdate, BookResponse, BookSearchResponse
from ..models.common import StatsResponse, AuthorStats, SagaStats
from ..config import VALID_CATEGORIES, VALID_STATUSES
from ..utils.pagination import AdvancedPaginator, PaginationParams, PaginatedResponse
from ..utils.cache import CacheDecorator, cache, BookCacheManager
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedBookService:
    """Service de livres optimisé pour les performances"""
    
    @staticmethod
    @CacheDecorator.cached("user_books", duration=timedelta(minutes=15))
    async def get_books_paginated(
        user_id: str, 
        pagination: PaginationParams,
        category: Optional[str] = None, 
        status: Optional[str] = None
    ) -> PaginatedResponse[BookResponse]:
        """
        Récupère les livres d'un utilisateur avec pagination optimisée
        """
        start_time = time.time()
        
        # Construire la requête de filtrage
        query = {"user_id": user_id}
        
        if category:
            if category.lower() not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
                )
            query["category"] = category.lower()
        
        if status:
            if status.lower() not in VALID_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status must be one of: {', '.join(VALID_STATUSES)}"
                )
            query["status"] = status.lower()
        
        try:
            # Utiliser le paginateur optimisé
            result = AdvancedPaginator.paginate_query(
                books_collection,
                query,
                pagination,
                projection={"_id": 0}  # Exclure l'_id MongoDB
            )
            
            # Convertir en BookResponse
            book_responses = [BookResponse(**book) for book in result.data]
            
            # Log des performances
            duration = (time.time() - start_time) * 1000
            logger.info(f"get_books_paginated: {duration:.2f}ms, {len(book_responses)} books")
            
            return PaginatedResponse(
                data=book_responses,
                meta=result.meta
            )
            
        except Exception as e:
            logger.error(f"Erreur get_books_paginated: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve books"
            )
    
    @staticmethod
    @CacheDecorator.cached("user_stats", duration=timedelta(minutes=5))
    async def get_stats_optimized(user_id: str) -> StatsResponse:
        """
        Récupère les statistiques optimisées avec cache
        """
        start_time = time.time()
        
        try:
            # Pipeline d'agrégation optimisé
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_books": {"$sum": 1},
                    "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                    "reading_books": {"$sum": {"$cond": [{"$eq": ["$status", "reading"]}, 1, 0]}},
                    "to_read_books": {"$sum": {"$cond": [{"$eq": ["$status", "to_read"]}, 1, 0]}},
                    "roman_count": {"$sum": {"$cond": [{"$eq": ["$category", "roman"]}, 1, 0]}},
                    "bd_count": {"$sum": {"$cond": [{"$eq": ["$category", "bd"]}, 1, 0]}},
                    "manga_count": {"$sum": {"$cond": [{"$eq": ["$category", "manga"]}, 1, 0]}},
                    "auto_added_count": {"$sum": {"$cond": ["$auto_added", 1, 0]}},
                    "authors": {"$addToSet": "$author"},
                    "sagas": {"$addToSet": "$saga"}
                }}
            ]
            
            result = list(books_collection.aggregate(pipeline))
            
            if result:
                data = result[0]
                # Filtrer les auteurs et sagas vides
                authors_count = len([a for a in data.get("authors", []) if a])
                sagas_count = len([s for s in data.get("sagas", []) if s])
                
                stats = StatsResponse(
                    total_books=data.get("total_books", 0),
                    completed_books=data.get("completed_books", 0),
                    reading_books=data.get("reading_books", 0),
                    to_read_books=data.get("to_read_books", 0),
                    categories={
                        "roman": data.get("roman_count", 0),
                        "bd": data.get("bd_count", 0),
                        "manga": data.get("manga_count", 0)
                    },
                    authors_count=authors_count,
                    sagas_count=sagas_count,
                    auto_added_count=data.get("auto_added_count", 0)
                )
            else:
                # Utilisateur sans livres
                stats = StatsResponse(
                    total_books=0,
                    completed_books=0,
                    reading_books=0,
                    to_read_books=0,
                    categories={"roman": 0, "bd": 0, "manga": 0},
                    authors_count=0,
                    sagas_count=0,
                    auto_added_count=0
                )
            
            # Log des performances
            duration = (time.time() - start_time) * 1000
            logger.info(f"get_stats_optimized: {duration:.2f}ms")
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur get_stats_optimized: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve statistics"
            )
    
    @staticmethod
    @CacheDecorator.cache_invalidate(["stats:user:{user_id}:*", "books:user:{user_id}:*"])
    async def create_book_optimized(user_id: str, book_data: BookCreate) -> BookResponse:
        """
        Crée un nouveau livre avec invalidation automatique du cache
        """
        start_time = time.time()
        
        # Valider la catégorie
        if book_data.category.lower() not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        
        # Créer le livre
        book_id = str(uuid.uuid4())
        book_doc = {
            "id": book_id,
            "user_id": user_id,
            "title": book_data.title,
            "author": book_data.author,
            "category": book_data.category.lower(),
            "description": book_data.description,
            "cover_url": book_data.cover_url,
            "pages": book_data.pages,
            "current_page": None,
            "status": "to_read",
            "rating": None,
            "review": None,
            "date_added": datetime.now(),
            "date_started": None,
            "date_completed": None,
            "saga": book_data.saga,
            "volume_number": book_data.volume_number,
            "publication_year": book_data.publication_year,
            "genre": book_data.genre,
            "publisher": book_data.publisher,
            "isbn": book_data.isbn,
            "language": book_data.language or "fr",
            "auto_added": False,
            "ol_key": book_data.ol_key,
            "ol_work_id": book_data.ol_work_id,
            "ol_edition_id": book_data.ol_edition_id
        }
        
        try:
            books_collection.insert_one(book_doc)
            
            # Log des performances
            duration = (time.time() - start_time) * 1000
            logger.info(f"create_book_optimized: {duration:.2f}ms")
            
            return BookResponse(**book_doc)
            
        except Exception as e:
            logger.error(f"Erreur create_book_optimized: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create book"
            )
    
    @staticmethod
    @CacheDecorator.cache_invalidate(["stats:user:{user_id}:*", "books:user:{user_id}:*"])
    async def update_book_optimized(user_id: str, book_id: str, update_data: BookUpdate) -> BookResponse:
        """
        Met à jour un livre avec invalidation automatique du cache
        """
        start_time = time.time()
        
        # Vérifier si le livre existe
        book = books_collection.find_one({"id": book_id, "user_id": user_id})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Préparer les données de mise à jour
        update_dict = update_data.dict(exclude_unset=True)
        
        # Valider la catégorie si fournie
        if "category" in update_dict:
            if update_dict["category"].lower() not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
                )
            update_dict["category"] = update_dict["category"].lower()
        
        # Valider le statut si fourni
        if "status" in update_dict:
            if update_dict["status"].lower() not in VALID_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status must be one of: {', '.join(VALID_STATUSES)}"
                )
            update_dict["status"] = update_dict["status"].lower()
            
            # Gérer les dates selon le statut
            if update_dict["status"] == "reading" and not book.get("date_started"):
                update_dict["date_started"] = datetime.now()
            elif update_dict["status"] == "completed":
                if not book.get("date_started"):
                    update_dict["date_started"] = datetime.now()
                update_dict["date_completed"] = datetime.now()
        
        # Mettre à jour le livre
        try:
            books_collection.update_one(
                {"id": book_id, "user_id": user_id},
                {"$set": update_dict}
            )
            
            # Récupérer le livre mis à jour
            updated_book = books_collection.find_one({"id": book_id, "user_id": user_id})
            
            # Log des performances
            duration = (time.time() - start_time) * 1000
            logger.info(f"update_book_optimized: {duration:.2f}ms")
            
            return BookResponse(**updated_book)
            
        except Exception as e:
            logger.error(f"Erreur update_book_optimized: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update book"
            )
    
    @staticmethod
    @CacheDecorator.cache_invalidate(["stats:user:{user_id}:*", "books:user:{user_id}:*"])
    async def delete_book_optimized(user_id: str, book_id: str) -> dict:
        """
        Supprime un livre avec invalidation automatique du cache
        """
        start_time = time.time()
        
        # Vérifier si le livre existe
        book = books_collection.find_one({"id": book_id, "user_id": user_id})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Supprimer le livre
        try:
            result = books_collection.delete_one({"id": book_id, "user_id": user_id})
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found"
                )
            
            # Log des performances
            duration = (time.time() - start_time) * 1000
            logger.info(f"delete_book_optimized: {duration:.2f}ms")
            
            return {"message": "Book deleted successfully"}
            
        except Exception as e:
            logger.error(f"Erreur delete_book_optimized: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete book"
            )
    
    @staticmethod
    async def get_performance_metrics() -> Dict[str, Any]:
        """
        Obtenir les métriques de performance
        """
        try:
            # Statistiques du cache
            cache_stats = cache.get_cache_stats()
            
            # Statistiques MongoDB (approximatives)
            db_stats = {
                "books_count": books_collection.count_documents({}),
                "indexes_count": len(list(books_collection.list_indexes())),
            }
            
            return {
                "cache": cache_stats,
                "database": db_stats,
                "optimizations": {
                    "pagination": "Advanced pagination enabled",
                    "caching": "Redis caching enabled" if cache.is_available else "Redis unavailable",
                    "indexes": "Strategic indexes created"
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur get_performance_metrics: {e}")
            return {"error": str(e)}

# Instance du service optimisé
optimized_book_service = OptimizedBookService()