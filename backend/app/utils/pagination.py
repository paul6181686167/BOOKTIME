# Système de pagination optimisé pour BOOKTIME
"""
Ce module implémente un système de pagination avancé pour améliorer les performances
et l'expérience utilisateur avec de grandes collections de livres.
"""

from typing import Dict, List, Optional, Any, Generic, TypeVar
from math import ceil
from pydantic import BaseModel, Field
from fastapi import Query

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Paramètres de pagination standardisés"""
    page: int = Field(default=1, ge=1, description="Numéro de page (commence à 1)")
    limit: int = Field(default=20, ge=1, le=100, description="Nombre d'éléments par page (max 100)")
    sort_by: Optional[str] = Field(default="date_added", description="Champ de tri")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="Ordre de tri")

class PaginationMeta(BaseModel):
    """Métadonnées de pagination"""
    current_page: int
    per_page: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
    next_page: Optional[int] = None
    previous_page: Optional[int] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Réponse paginée générique"""
    data: List[T]
    meta: PaginationMeta

class AdvancedPaginator:
    """Paginateur avancé avec optimisations"""
    
    @staticmethod
    def get_pagination_params(
        page: int = Query(1, ge=1, description="Numéro de page"),
        limit: int = Query(20, ge=1, le=100, description="Éléments par page"),
        sort_by: str = Query("date_added", description="Champ de tri"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri")
    ) -> PaginationParams:
        """Extraire les paramètres de pagination des query params"""
        return PaginationParams(
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
    
    @staticmethod
    def calculate_skip_limit(page: int, limit: int) -> Dict[str, int]:
        """Calculer skip et limit pour MongoDB"""
        skip = (page - 1) * limit
        return {"skip": skip, "limit": limit}
    
    @staticmethod
    def build_sort_dict(sort_by: str, sort_order: str) -> Dict[str, int]:
        """Construire le dictionnaire de tri pour MongoDB"""
        sort_direction = -1 if sort_order == "desc" else 1
        return {sort_by: sort_direction}
    
    @staticmethod
    def create_pagination_meta(
        total_items: int,
        page: int,
        limit: int
    ) -> PaginationMeta:
        """Créer les métadonnées de pagination"""
        total_pages = ceil(total_items / limit) if total_items > 0 else 1
        has_next = page < total_pages
        has_previous = page > 1
        
        return PaginationMeta(
            current_page=page,
            per_page=limit,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_page=page + 1 if has_next else None,
            previous_page=page - 1 if has_previous else None
        )
    
    @staticmethod
    def paginate_query(
        collection,
        query: Dict[str, Any],
        pagination: PaginationParams,
        projection: Optional[Dict[str, int]] = None
    ) -> PaginatedResponse:
        """Paginer une requête MongoDB de manière optimisée"""
        
        # Calculer skip et limit
        skip_limit = AdvancedPaginator.calculate_skip_limit(
            pagination.page, 
            pagination.limit
        )
        
        # Construire le tri
        sort_dict = AdvancedPaginator.build_sort_dict(
            pagination.sort_by,
            pagination.sort_order
        )
        
        # Compter le total (optimisé avec l'index)
        total_items = collection.count_documents(query)
        
        # Exécuter la requête paginée
        cursor = collection.find(query, projection)
        
        if sort_dict:
            cursor = cursor.sort(list(sort_dict.items()))
        
        cursor = cursor.skip(skip_limit["skip"]).limit(skip_limit["limit"])
        
        # Convertir en liste
        data = list(cursor)
        
        # Créer les métadonnées
        meta = AdvancedPaginator.create_pagination_meta(
            total_items,
            pagination.page,
            pagination.limit
        )
        
        return PaginatedResponse(data=data, meta=meta)

class CursorPaginator:
    """Paginateur par curseur pour de très grandes collections"""
    
    @staticmethod
    def paginate_by_cursor(
        collection,
        query: Dict[str, Any],
        cursor_field: str = "_id",
        limit: int = 20,
        cursor_value: Optional[str] = None,
        direction: str = "next"
    ) -> Dict[str, Any]:
        """
        Pagination par curseur pour de meilleures performances
        sur de très grandes collections
        """
        
        # Modifier la requête selon le curseur
        if cursor_value:
            if direction == "next":
                query[cursor_field] = {"$gt": cursor_value}
            else:  # previous
                query[cursor_field] = {"$lt": cursor_value}
        
        # Exécuter la requête
        cursor = collection.find(query).limit(limit + 1)  # +1 pour détecter s'il y a plus
        
        # Tri selon la direction
        if direction == "next":
            cursor = cursor.sort(cursor_field, 1)
        else:
            cursor = cursor.sort(cursor_field, -1)
        
        results = list(cursor)
        
        # Déterminer s'il y a plus de pages
        has_more = len(results) > limit
        if has_more:
            results = results[:-1]  # Supprimer le dernier élément
        
        # Curseurs pour les pages suivante/précédente
        next_cursor = None
        previous_cursor = None
        
        if results:
            if direction == "next":
                next_cursor = results[-1][cursor_field] if has_more else None
                previous_cursor = results[0][cursor_field]
            else:
                next_cursor = results[0][cursor_field]
                previous_cursor = results[-1][cursor_field] if has_more else None
        
        return {
            "data": results,
            "has_next": has_more and direction == "next",
            "has_previous": has_more and direction == "previous",
            "next_cursor": str(next_cursor) if next_cursor else None,
            "previous_cursor": str(previous_cursor) if previous_cursor else None,
            "count": len(results)
        }

class SearchPaginator:
    """Paginateur spécialisé pour la recherche textuelle"""
    
    @staticmethod
    def paginate_text_search(
        collection,
        search_query: str,
        base_filter: Dict[str, Any],
        pagination: PaginationParams,
        search_fields: Optional[List[str]] = None
    ) -> PaginatedResponse:
        """Paginer une recherche textuelle avec score de pertinence"""
        
        if search_fields is None:
            search_fields = ["title", "author", "saga", "description"]
        
        # Construire la requête de recherche textuelle
        text_search = {
            "$text": {
                "$search": search_query,
                "$caseSensitive": False,
                "$diacriticSensitive": False
            }
        }
        
        # Combiner avec le filtre de base
        combined_query = {**base_filter, **text_search}
        
        # Projection avec score de pertinence
        projection = {
            "score": {"$meta": "textScore"},
            "_id": 0  # Exclure l'_id MongoDB
        }
        
        # Calculer skip et limit
        skip_limit = AdvancedPaginator.calculate_skip_limit(
            pagination.page,
            pagination.limit
        )
        
        # Compter le total
        total_items = collection.count_documents(combined_query)
        
        # Exécuter la requête avec tri par score de pertinence
        cursor = collection.find(combined_query, projection)
        cursor = cursor.sort([("score", {"$meta": "textScore"})])
        cursor = cursor.skip(skip_limit["skip"]).limit(skip_limit["limit"])
        
        data = list(cursor)
        
        # Créer les métadonnées
        meta = AdvancedPaginator.create_pagination_meta(
            total_items,
            pagination.page,
            pagination.limit
        )
        
        return PaginatedResponse(data=data, meta=meta)

# Utilitaires pour intégration FastAPI
def create_pagination_dependency():
    """Créer une dépendance FastAPI pour la pagination"""
    return AdvancedPaginator.get_pagination_params

# Exemple d'utilisation avec FastAPI
"""
@router.get("/books")
async def get_books_paginated(
    pagination: PaginationParams = Depends(create_pagination_dependency()),
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    
    result = AdvancedPaginator.paginate_query(
        books_collection,
        query,
        pagination
    )
    
    return result
"""