#!/usr/bin/env python3
"""
Phase 2.4 : Monitoring - Métriques et logs structurés
Système de monitoring complet pour BOOKTIME
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
import os
import sys

# Configuration du logging structuré
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/backend/logs/booktime.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class PerformanceMonitor:
    """Moniteur de performance pour les opérations BOOKTIME"""
    
    def __init__(self):
        self.metrics = {
            'requests': {},
            'database': {},
            'cache': {},
            'errors': [],
            'performance': {}
        }
        self.logger = logging.getLogger('booktime.performance')
    
    def log_request(self, endpoint: str, method: str, duration: float, status_code: int, user_id: str = None):
        """Enregistre une métrique de requête"""
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'duration_ms': round(duration * 1000, 2),
            'status_code': status_code,
            'user_id': user_id
        }
        
        # Stockage en mémoire
        if endpoint not in self.metrics['requests']:
            self.metrics['requests'][endpoint] = []
        
        self.metrics['requests'][endpoint].append(request_data)
        
        # Log structuré
        self.logger.info(json.dumps({
            'type': 'request',
            'data': request_data
        }))
    
    def log_database_query(self, collection: str, operation: str, duration: float, document_count: int = 0):
        """Enregistre une métrique de base de données"""
        db_data = {
            'timestamp': datetime.now().isoformat(),
            'collection': collection,
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'document_count': document_count
        }
        
        # Stockage en mémoire
        if collection not in self.metrics['database']:
            self.metrics['database'][collection] = []
        
        self.metrics['database'][collection].append(db_data)
        
        # Log structuré
        self.logger.info(json.dumps({
            'type': 'database',
            'data': db_data
        }))
    
    def log_cache_operation(self, operation: str, key: str, hit: bool, duration: float = 0):
        """Enregistre une métrique de cache"""
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'key_hash': hash(key) % 10000,  # Hash pour la confidentialité
            'hit': hit,
            'duration_ms': round(duration * 1000, 2)
        }
        
        # Stockage en mémoire
        if 'operations' not in self.metrics['cache']:
            self.metrics['cache']['operations'] = []
        
        self.metrics['cache']['operations'].append(cache_data)
        
        # Log structuré
        self.logger.info(json.dumps({
            'type': 'cache',
            'data': cache_data
        }))
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Enregistre une erreur"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.metrics['errors'].append(error_data)
        
        # Log structuré
        self.logger.error(json.dumps({
            'type': 'error',
            'data': error_data
        }))
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Récupère un résumé des métriques"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Métriques des requêtes
        recent_requests = []
        for endpoint, requests in self.metrics['requests'].items():
            for request in requests:
                if datetime.fromisoformat(request['timestamp']) > cutoff_time:
                    recent_requests.append(request)
        
        # Métriques de base de données
        recent_db_ops = []
        for collection, operations in self.metrics['database'].items():
            for operation in operations:
                if datetime.fromisoformat(operation['timestamp']) > cutoff_time:
                    recent_db_ops.append(operation)
        
        # Métriques de cache
        recent_cache_ops = []
        if 'operations' in self.metrics['cache']:
            for operation in self.metrics['cache']['operations']:
                if datetime.fromisoformat(operation['timestamp']) > cutoff_time:
                    recent_cache_ops.append(operation)
        
        # Calculs des statistiques
        avg_response_time = sum(r['duration_ms'] for r in recent_requests) / len(recent_requests) if recent_requests else 0
        cache_hit_rate = sum(1 for op in recent_cache_ops if op['hit']) / len(recent_cache_ops) if recent_cache_ops else 0
        
        return {
            'period_hours': hours,
            'summary': {
                'total_requests': len(recent_requests),
                'avg_response_time_ms': round(avg_response_time, 2),
                'database_operations': len(recent_db_ops),
                'cache_hit_rate': round(cache_hit_rate * 100, 2),
                'error_count': len([e for e in self.metrics['errors'] 
                                  if datetime.fromisoformat(e['timestamp']) > cutoff_time])
            },
            'top_endpoints': self._get_top_endpoints(recent_requests),
            'slowest_operations': self._get_slowest_operations(recent_requests),
            'cache_performance': self._get_cache_performance(recent_cache_ops)
        }
    
    def _get_top_endpoints(self, requests: List[Dict], limit: int = 10) -> List[Dict]:
        """Récupère les endpoints les plus sollicités"""
        endpoint_counts = {}
        for request in requests:
            endpoint = request['endpoint']
            if endpoint not in endpoint_counts:
                endpoint_counts[endpoint] = {'count': 0, 'total_duration': 0}
            
            endpoint_counts[endpoint]['count'] += 1
            endpoint_counts[endpoint]['total_duration'] += request['duration_ms']
        
        # Tri par nombre d'appels
        sorted_endpoints = sorted(endpoint_counts.items(), 
                                key=lambda x: x[1]['count'], reverse=True)
        
        return [
            {
                'endpoint': endpoint,
                'count': data['count'],
                'avg_duration_ms': round(data['total_duration'] / data['count'], 2)
            }
            for endpoint, data in sorted_endpoints[:limit]
        ]
    
    def _get_slowest_operations(self, requests: List[Dict], limit: int = 10) -> List[Dict]:
        """Récupère les opérations les plus lentes"""
        sorted_requests = sorted(requests, key=lambda x: x['duration_ms'], reverse=True)
        
        return [
            {
                'endpoint': req['endpoint'],
                'method': req['method'],
                'duration_ms': req['duration_ms'],
                'timestamp': req['timestamp']
            }
            for req in sorted_requests[:limit]
        ]
    
    def _get_cache_performance(self, cache_ops: List[Dict]) -> Dict[str, Any]:
        """Analyse la performance du cache"""
        if not cache_ops:
            return {'hit_rate': 0, 'total_operations': 0}
        
        hits = sum(1 for op in cache_ops if op['hit'])
        total = len(cache_ops)
        
        return {
            'hit_rate': round((hits / total) * 100, 2),
            'total_operations': total,
            'hits': hits,
            'misses': total - hits
        }

# Décorateur pour monitorer les fonctions
def monitor_performance(operation_name: str = None):
    """Décorateur pour monitorer les performances d'une fonction"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log de performance
                performance_monitor.logger.info(json.dumps({
                    'type': 'performance',
                    'operation': op_name,
                    'duration_ms': round(duration * 1000, 2),
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }))
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log d'erreur avec contexte
                performance_monitor.log_error(e, {
                    'operation': op_name,
                    'duration_ms': round(duration * 1000, 2),
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                })
                
                raise
        
        return wrapper
    return decorator

# Moniteur de santé système
class SystemHealthMonitor:
    """Moniteur de santé du système"""
    
    def __init__(self):
        self.logger = logging.getLogger('booktime.health')
    
    def check_database_health(self) -> Dict[str, Any]:
        """Vérifie la santé de la base de données"""
        try:
            from ..database import db
            
            start_time = time.time()
            
            # Test simple de connectivité
            result = db.command("ping")
            duration = time.time() - start_time
            
            # Test d'écriture/lecture
            test_doc = {"test": True, "timestamp": datetime.now().isoformat()}
            test_collection = db.health_check
            
            write_start = time.time()
            test_collection.insert_one(test_doc)
            write_duration = time.time() - write_start
            
            read_start = time.time()
            found_doc = test_collection.find_one({"test": True})
            read_duration = time.time() - read_start
            
            # Nettoyage
            test_collection.delete_one({"test": True})
            
            health_data = {
                'status': 'healthy',
                'ping_ms': round(duration * 1000, 2),
                'write_ms': round(write_duration * 1000, 2),
                'read_ms': round(read_duration * 1000, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(json.dumps({
                'type': 'health_check',
                'component': 'database',
                'data': health_data
            }))
            
            return health_data
            
        except Exception as e:
            health_data = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.error(json.dumps({
                'type': 'health_check',
                'component': 'database',
                'data': health_data
            }))
            
            return health_data
    
    def check_cache_health(self) -> Dict[str, Any]:
        """Vérifie la santé du cache Redis"""
        try:
            from ..services.pagination import CacheManager
            
            cache = CacheManager()
            
            if not cache.cache_enabled:
                return {
                    'status': 'disabled',
                    'message': 'Cache Redis non configuré',
                    'timestamp': datetime.now().isoformat()
                }
            
            start_time = time.time()
            
            # Test de ping
            cache.redis_client.ping()
            ping_duration = time.time() - start_time
            
            # Test d'écriture/lecture
            test_key = "health_check"
            test_value = {"test": True, "timestamp": datetime.now().isoformat()}
            
            write_start = time.time()
            cache.set(test_key, test_value, ttl=60)
            write_duration = time.time() - write_start
            
            read_start = time.time()
            retrieved = cache.get(test_key)
            read_duration = time.time() - read_start
            
            # Nettoyage
            cache.remove(test_key)
            
            health_data = {
                'status': 'healthy',
                'ping_ms': round(ping_duration * 1000, 2),
                'write_ms': round(write_duration * 1000, 2),
                'read_ms': round(read_duration * 1000, 2),
                'test_success': retrieved is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(json.dumps({
                'type': 'health_check',
                'component': 'cache',
                'data': health_data
            }))
            
            return health_data
            
        except Exception as e:
            health_data = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.error(json.dumps({
                'type': 'health_check',
                'component': 'cache',
                'data': health_data
            }))
            
            return health_data
    
    def get_full_health_report(self) -> Dict[str, Any]:
        """Rapport de santé complet"""
        database_health = self.check_database_health()
        cache_health = self.check_cache_health()
        
        overall_status = 'healthy'
        if database_health['status'] == 'unhealthy':
            overall_status = 'unhealthy'
        elif cache_health['status'] == 'unhealthy':
            overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'components': {
                'database': database_health,
                'cache': cache_health
            },
            'timestamp': datetime.now().isoformat()
        }

# Instances globales
performance_monitor = PerformanceMonitor()
health_monitor = SystemHealthMonitor()

# Fonction utilitaire pour créer le dossier de logs
def ensure_log_directory():
    """Crée le dossier de logs s'il n'existe pas"""
    log_dir = '/app/backend/logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"✅ Dossier de logs créé: {log_dir}")

# Initialisation
ensure_log_directory()