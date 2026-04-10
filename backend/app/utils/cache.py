# Système de cache Redis pour BOOKTIME
"""
Ce module implémente un système de cache sophistiqué avec Redis
pour améliorer drastiquement les performances de l'application.
"""

import json
import hashlib
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import redis
import os
from datetime import timedelta
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheConfig:
    """Configuration du cache Redis"""
    
    # Durées de cache par type de données
    CACHE_DURATIONS = {
        "user_stats": timedelta(minutes=5),      # Statistiques utilisateur
        "series_popular": timedelta(hours=1),    # Séries populaires
        "book_details": timedelta(minutes=30),   # Détails d'un livre
        "search_results": timedelta(minutes=10), # Résultats de recherche
        "user_books": timedelta(minutes=15),     # Liste des livres utilisateur
        "openlibrary": timedelta(hours=6),       # Résultats Open Library
        "aggregations": timedelta(minutes=20),   # Résultats d'agrégations
        "health_check": timedelta(minutes=1),    # Health checks
    }
    
    # Préfixes pour les clés de cache
    CACHE_PREFIXES = {
        "user_stats": "stats:user:",
        "series_popular": "series:popular:",
        "book_details": "book:details:",
        "search_results": "search:results:",
        "user_books": "books:user:",
        "openlibrary": "ol:search:",
        "aggregations": "agg:",
        "health_check": "health:",
    }

class RedisCache:
    """Gestionnaire de cache Redis"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialiser la connexion Redis"""
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client = None
        self._connect()
    
    def _connect(self):
        """Établir la connexion Redis"""
        try:
            # Configuration Redis avec fallback
            if self.redis_url.startswith("redis://"):
                self._client = redis.from_url(self.redis_url, decode_responses=True)
            else:
                self._client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
            
            # Test de la connexion
            self._client.ping()
            logger.info("[OK] Redis connecte avec succes")
            
        except Exception as e:
            logger.warning(f"[WARN] Redis non disponible: {e}")
            logger.info("[INFO] Mode degrade sans cache active")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Vérifier si Redis est disponible"""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Générer une clé de cache unique"""
        # Créer un hash des arguments pour une clé unique
        key_data = f"{args}:{kwargs}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"{prefix}{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Récupérer une valeur du cache"""
        if not self.is_available:
            return None
        
        try:
            data = self._client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Erreur lecture cache {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, duration: timedelta = None) -> bool:
        """Stocker une valeur dans le cache"""
        if not self.is_available:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if duration:
                return self._client.setex(key, duration, serialized)
            else:
                return self._client.set(key, serialized)
        except Exception as e:
            logger.warning(f"Erreur écriture cache {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Supprimer une clé du cache"""
        if not self.is_available:
            return False
        
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.warning(f"Erreur suppression cache {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Supprimer toutes les clés correspondant à un pattern"""
        if not self.is_available:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Erreur suppression pattern {pattern}: {e}")
            return 0
    
    def flush_user_cache(self, user_id: str):
        """Vider tout le cache d'un utilisateur"""
        patterns = [
            f"stats:user:{user_id}:*",
            f"books:user:{user_id}:*",
            f"search:results:{user_id}:*",
            f"agg:{user_id}:*"
        ]
        
        for pattern in patterns:
            self.delete_pattern(pattern)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques du cache"""
        if not self.is_available:
            return {"status": "unavailable"}
        
        try:
            info = self._client.info()
            return {
                "status": "available",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Instance globale du cache
cache = RedisCache()

class CacheDecorator:
    """Décorateurs pour le cache automatique"""
    
    @staticmethod
    def cached(cache_type: str, duration: Optional[timedelta] = None):
        """
        Décorateur pour cache automatique des fonctions
        
        Usage:
        @cached("user_stats", duration=timedelta(minutes=5))
        async def get_user_stats(user_id: str):
            # logique coûteuse
            return stats
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Générer la clé de cache
                prefix = CacheConfig.CACHE_PREFIXES.get(cache_type, f"{cache_type}:")
                cache_key = cache._generate_key(prefix, *args, **kwargs)
                
                # Essayer de récupérer du cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached_result
                
                # Exécuter la fonction
                logger.debug(f"Cache MISS: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Stocker en cache
                cache_duration = duration or CacheConfig.CACHE_DURATIONS.get(cache_type)
                cache.set(cache_key, result, cache_duration)
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def cache_invalidate(cache_patterns: List[str]):
        """
        Décorateur pour invalider le cache après modification
        
        Usage:
        @cache_invalidate(["stats:user:{user_id}:*", "books:user:{user_id}:*"])
        async def update_book(user_id: str, book_id: str, data: dict):
            # logique de mise à jour
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                
                # Invalider les patterns de cache
                for pattern in cache_patterns:
                    # Remplacer les placeholders avec les arguments
                    try:
                        # Simple remplacement pour {user_id}, etc.
                        if 'user_id' in kwargs:
                            pattern = pattern.replace('{user_id}', kwargs['user_id'])
                        elif args:
                            pattern = pattern.replace('{user_id}', str(args[0]))
                        
                        cache.delete_pattern(pattern)
                        logger.debug(f"Cache invalidé: {pattern}")
                    except Exception as e:
                        logger.warning(f"Erreur invalidation cache {pattern}: {e}")
                
                return result
            return wrapper
        return decorator

# Utilitaires pour cache spécifique

class BookCacheManager:
    """Gestionnaire de cache spécialisé pour les livres"""
    
    @staticmethod
    def get_user_stats_key(user_id: str) -> str:
        return f"stats:user:{user_id}"
    
    @staticmethod
    def get_user_books_key(user_id: str, filters: str = "") -> str:
        filters_hash = hashlib.md5(filters.encode()).hexdigest()[:8]
        return f"books:user:{user_id}:{filters_hash}"
    
    @staticmethod
    def get_search_key(user_id: str, query: str) -> str:
        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
        return f"search:results:{user_id}:{query_hash}"
    
    @staticmethod
    def invalidate_user_cache(user_id: str):
        """Invalider tout le cache d'un utilisateur"""
        cache.flush_user_cache(user_id)

# Exemples d'utilisation

"""
# Dans un service
@CacheDecorator.cached("user_stats", duration=timedelta(minutes=5))
async def get_user_statistics(user_id: str):
    # Logique coûteuse de calcul des stats
    return stats

@CacheDecorator.cache_invalidate(["stats:user:{user_id}:*", "books:user:{user_id}:*"])
async def create_book(user_id: str, book_data: dict):
    # Logique de création
    return new_book

# Utilisation manuelle
async def get_popular_series():
    cache_key = "series:popular:all"
    
    # Essayer le cache
    cached_series = cache.get(cache_key)
    if cached_series:
        return cached_series
    
    # Calculer et mettre en cache
    series = await compute_popular_series()
    cache.set(cache_key, series, timedelta(hours=1))
    
    return series
"""