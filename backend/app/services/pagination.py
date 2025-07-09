# Phase 2.2 : Pagination et Cache - Backend
"""
Implémentation de la pagination et du cache pour optimiser les performances
"""

from fastapi import Query, HTTPException
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import redis
import json
import hashlib
from datetime import datetime, timedelta
import os
from ..database import db
from ..config import DEFAULT_LIMIT, MAX_LIMIT, DEFAULT_OFFSET

# Configuration Redis (optionnel)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

class PaginationParams(BaseModel):
    """Paramètres de pagination standardisés"""
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET
    sort_by: str = "date_added"
    sort_order: str = "desc"  # "asc" ou "desc"

class PaginatedResponse(BaseModel):
    """Réponse paginée standardisée"""
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool
    next_offset: Optional[int] = None
    previous_offset: Optional[int] = None

class CacheManager:
    """Gestionnaire de cache pour les requêtes fréquentes"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = False
        
        # Tentative de connexion Redis
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            self.redis_client.ping()
            self.cache_enabled = True
            print("✅ Redis connecté - Cache activé")
        except:
            print("ℹ️  Redis non disponible - Cache désactivé")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Génère une clé de cache unique"""
        key_data = json.dumps(kwargs, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"booktime:{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Dict]:
        """Récupère une valeur du cache"""
        if not self.cache_enabled:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except:
            pass
        
        return None
    
    def set(self, key: str, value: Dict, ttl: int = CACHE_TTL):
        """Stocke une valeur dans le cache"""
        if not self.cache_enabled:
            return
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except:
            pass
    
    def delete_pattern(self, pattern: str):
        """Supprime toutes les clés correspondant au pattern"""
        if not self.cache_enabled:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except:
            pass

class PaginationService:
    """Service de pagination avec cache intégré"""
    
    def __init__(self):
        self.cache = CacheManager()
        self.db = db
    
    def validate_pagination_params(self, limit: int, offset: int) -> PaginationParams:
        """Valide et normalise les paramètres de pagination"""
        # Validation des limites
        if limit < 1:
            limit = DEFAULT_LIMIT
        elif limit > MAX_LIMIT:
            limit = MAX_LIMIT
        
        # Validation de l'offset
        if offset < 0:
            offset = DEFAULT_OFFSET
        
        return PaginationParams(limit=limit, offset=offset)
    
    def get_paginated_books(
        self,
        user_id: str,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        category: Optional[str] = None,
        status: Optional[str] = None,
        author: Optional[str] = None,
        saga: Optional[str] = None,
        sort_by: str = "date_added",
        sort_order: str = "desc",
        exclude_series: bool = False
    ) -> PaginatedResponse:
        """
        Récupère les livres avec pagination et cache
        
        Args:
            user_id: ID de l'utilisateur
            limit: Nombre d'éléments par page
            offset: Décalage pour la pagination
            category: Filtre par catégorie
            status: Filtre par statut
            author: Filtre par auteur
            saga: Filtre par saga
            sort_by: Champ de tri
            sort_order: Ordre de tri (asc/desc)
            
        Returns:
            PaginatedResponse avec les livres paginés
        """
        
        # Validation des paramètres
        params = self.validate_pagination_params(limit, offset)
        
        # Construction de la requête
        query = {"user_id": user_id}
        
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        if saga:
            query["saga"] = {"$regex": saga, "$options": "i"}
        
        # Exclusion des livres de séries si demandé
        if exclude_series:
            query["$or"] = [
                {"saga": {"$exists": False}},
                {"saga": ""},
                {"saga": None}
            ]
        
        # Génération de la clé de cache
        cache_key = self.cache._generate_cache_key(
            "books",
            user_id=user_id,
            limit=limit,
            offset=offset,
            query=query,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Vérification du cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return PaginatedResponse(**cached_result)
        
        # Construction du tri
        sort_direction = 1 if sort_order == "asc" else -1
        sort_spec = [(sort_by, sort_direction)]
        
        # Exécution de la requête
        books_collection = self.db.books
        
        # Compte total (pour la pagination)
        total_count = books_collection.count_documents(query)
        
        # Récupération des livres paginés
        books_cursor = books_collection.find(query).sort(sort_spec).skip(offset).limit(limit)
        books = list(books_cursor)
        
        # Conversion des ObjectId en strings
        for book in books:
            if "_id" in book:
                book["_id"] = str(book["_id"])
        
        # Calcul des informations de pagination
        has_next = offset + limit < total_count
        has_previous = offset > 0
        
        next_offset = offset + limit if has_next else None
        previous_offset = max(0, offset - limit) if has_previous else None
        
        # Construction de la réponse
        response_data = {
            "items": books,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_offset": next_offset,
            "previous_offset": previous_offset
        }
        
        # Mise en cache
        self.cache.set(cache_key, response_data)
        
        return PaginatedResponse(**response_data)
    
    def get_paginated_series(
        self,
        user_id: str,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> PaginatedResponse:
        """
        Récupère les séries avec pagination et cache
        """
        
        # Validation des paramètres
        params = self.validate_pagination_params(limit, offset)
        
        # Construction de la requête
        query = {"user_id": user_id}
        
        if category:
            query["category"] = category
        if status:
            query["status"] = status
        
        # Génération de la clé de cache
        cache_key = self.cache._generate_cache_key(
            "series",
            user_id=user_id,
            limit=limit,
            offset=offset,
            query=query
        )
        
        # Vérification du cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return PaginatedResponse(**cached_result)
        
        # Exécution de la requête
        series_collection = self.db.series_library
        
        # Compte total
        total_count = series_collection.count_documents(query)
        
        # Récupération des séries paginées
        series_cursor = series_collection.find(query).sort([("date_added", -1)]).skip(offset).limit(limit)
        series = list(series_cursor)
        
        # Conversion des ObjectId en strings
        for serie in series:
            if "_id" in serie:
                serie["_id"] = str(serie["_id"])
        
        # Calcul des informations de pagination
        has_next = offset + limit < total_count
        has_previous = offset > 0
        
        next_offset = offset + limit if has_next else None
        previous_offset = max(0, offset - limit) if has_previous else None
        
        # Construction de la réponse
        response_data = {
            "items": series,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_offset": next_offset,
            "previous_offset": previous_offset
        }
        
        # Mise en cache
        self.cache.set(cache_key, response_data)
        
        return PaginatedResponse(**response_data)
    
    def invalidate_user_cache(self, user_id: str):
        """Invalide le cache pour un utilisateur spécifique"""
        patterns = [
            f"booktime:books:*user_id*{user_id}*",
            f"booktime:series:*user_id*{user_id}*",
            f"booktime:stats:*user_id*{user_id}*"
        ]
        
        for pattern in patterns:
            self.cache.delete_pattern(pattern)
    
    def get_search_suggestions(self, user_id: str, query: str, limit: int = 5) -> List[str]:
        """
        Récupère des suggestions de recherche avec cache
        """
        cache_key = self.cache._generate_cache_key(
            "search_suggestions",
            user_id=user_id,
            query=query.lower(),
            limit=limit
        )
        
        # Vérification du cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result.get("suggestions", [])
        
        # Recherche dans la base
        books_collection = self.db.books
        
        # Recherche par titre
        title_suggestions = books_collection.distinct("title", {
            "user_id": user_id,
            "title": {"$regex": query, "$options": "i"}
        })[:limit]
        
        # Recherche par auteur
        author_suggestions = books_collection.distinct("author", {
            "user_id": user_id,
            "author": {"$regex": query, "$options": "i"}
        })[:limit]
        
        # Recherche par saga
        saga_suggestions = books_collection.distinct("saga", {
            "user_id": user_id,
            "saga": {"$regex": query, "$options": "i"}
        })[:limit]
        
        # Combinaison et déduplication
        all_suggestions = list(set(title_suggestions + author_suggestions + saga_suggestions))[:limit]
        
        # Mise en cache
        result = {"suggestions": all_suggestions}
        self.cache.set(cache_key, result, ttl=600)  # 10 minutes
        
        return all_suggestions

# Instance globale du service de pagination
pagination_service = PaginationService()