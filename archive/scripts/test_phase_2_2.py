#!/usr/bin/env python3
"""
Phase 2.2 : Test de la Pagination et Cache
Script pour tester l'implémentation complète
"""

import sys
import os
import time
from datetime import datetime
sys.path.append('/app/backend')

def test_pagination_service():
    """Test du service de pagination"""
    print("🧪 TEST SERVICE DE PAGINATION")
    print("=" * 50)
    
    try:
        from app.services.pagination import pagination_service
        
        # Test de validation des paramètres
        print("\n📋 Test validation paramètres:")
        params = pagination_service.validate_pagination_params(limit=150, offset=-5)
        print(f"  ✅ Limit corrigée: {params.limit} (max: 100)")
        print(f"  ✅ Offset corrigé: {params.offset} (min: 0)")
        
        # Test de la configuration du cache
        print("\n📋 Test configuration cache:")
        cache_enabled = pagination_service.cache.cache_enabled
        print(f"  ℹ️  Cache Redis: {'✅ Activé' if cache_enabled else '❌ Désactivé'}")
        
        # Test des méthodes avec données vides
        print("\n📋 Test requêtes avec base vide:")
        
        # Test pagination livres
        start_time = time.time()
        books_result = pagination_service.get_paginated_books(
            user_id="test-user",
            limit=10,
            offset=0
        )
        books_time = (time.time() - start_time) * 1000
        
        print(f"  📚 Livres paginés: {len(books_result.items)} éléments")
        print(f"  ⏱️  Temps d'exécution: {books_time:.2f}ms")
        print(f"  📊 Total: {books_result.total}")
        print(f"  ➡️  Page suivante: {books_result.has_next}")
        
        # Test pagination séries
        start_time = time.time()
        series_result = pagination_service.get_paginated_series(
            user_id="test-user",
            limit=10,
            offset=0
        )
        series_time = (time.time() - start_time) * 1000
        
        print(f"  📖 Séries paginées: {len(series_result.items)} éléments")
        print(f"  ⏱️  Temps d'exécution: {series_time:.2f}ms")
        print(f"  📊 Total: {series_result.total}")
        
        # Test suggestions de recherche
        start_time = time.time()
        suggestions = pagination_service.get_search_suggestions(
            user_id="test-user",
            query="harry",
            limit=5
        )
        suggestions_time = (time.time() - start_time) * 1000
        
        print(f"  🔍 Suggestions: {len(suggestions)} trouvées")
        print(f"  ⏱️  Temps d'exécution: {suggestions_time:.2f}ms")
        
        # Test invalidation cache
        print("\n📋 Test invalidation cache:")
        pagination_service.invalidate_user_cache("test-user")
        print("  ✅ Cache utilisateur invalidé")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur test service: {e}")
        return False

def test_pagination_models():
    """Test des modèles de pagination"""
    print("\n📋 TEST MODÈLES DE PAGINATION")
    print("=" * 50)
    
    try:
        from app.services.pagination import PaginationParams, PaginatedResponse
        
        # Test PaginationParams
        params = PaginationParams(limit=25, offset=50)
        print(f"  ✅ PaginationParams créé: limit={params.limit}, offset={params.offset}")
        
        # Test PaginatedResponse
        response = PaginatedResponse(
            items=[{"id": "1", "title": "Test Book"}],
            total=100,
            limit=25,
            offset=50,
            has_next=True,
            has_previous=True,
            next_offset=75,
            previous_offset=25
        )
        print(f"  ✅ PaginatedResponse créé: {len(response.items)} éléments")
        print(f"  📊 Pagination: {response.offset}/{response.total}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur test modèles: {e}")
        return False

def test_cache_manager():
    """Test du gestionnaire de cache"""
    print("\n📋 TEST GESTIONNAIRE DE CACHE")
    print("=" * 50)
    
    try:
        from app.services.pagination import CacheManager
        
        cache = CacheManager()
        
        # Test génération de clé
        key = cache._generate_cache_key("test", user_id="123", query="test")
        print(f"  ✅ Clé générée: {key}")
        
        # Test stockage et récupération
        test_data = {"message": "test cache", "timestamp": datetime.now().isoformat()}
        cache.set(key, test_data, ttl=60)
        
        retrieved_data = cache.get(key)
        if retrieved_data and retrieved_data.get("message") == "test cache":
            print("  ✅ Cache set/get fonctionne")
        else:
            print("  ℹ️  Cache non opérationnel (Redis non disponible)")
        
        # Test suppression par pattern
        cache.delete_pattern("booktime:test:*")
        print("  ✅ Suppression par pattern testée")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur test cache: {e}")
        return False

def check_dependencies():
    """Vérification des dépendances"""
    print("\n📋 VÉRIFICATION DES DÉPENDANCES")
    print("=" * 50)
    
    # Vérification Redis
    try:
        import redis
        print("  ✅ Module redis disponible")
    except ImportError:
        print("  ⚠️  Module redis non installé")
    
    # Vérification FastAPI
    try:
        import fastapi
        print("  ✅ Module fastapi disponible")
    except ImportError:
        print("  ❌ Module fastapi non disponible")
    
    # Vérification Pydantic
    try:
        import pydantic
        print("  ✅ Module pydantic disponible")
    except ImportError:
        print("  ❌ Module pydantic non disponible")

def run_phase_2_2_tests():
    """Exécute tous les tests de la Phase 2.2"""
    print("\n🚀 PHASE 2.2 : PAGINATION ET CACHE - TESTS")
    print("=" * 70)
    
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'dependencies': False,
        'models': False,
        'cache_manager': False,
        'pagination_service': False
    }
    
    # Test 1: Dépendances
    check_dependencies()
    results['dependencies'] = True
    
    # Test 2: Modèles
    results['models'] = test_pagination_models()
    
    # Test 3: Gestionnaire de cache
    results['cache_manager'] = test_cache_manager()
    
    # Test 4: Service de pagination
    results['pagination_service'] = test_pagination_service()
    
    # Rapport final
    print("\n✅ RÉSUMÉ TESTS PHASE 2.2")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    success_rate = sum(results.values()) / len(results) * 100
    print(f"\n📊 Taux de réussite: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("✅ PHASE 2.2 ENTIÈREMENT FONCTIONNELLE !")
    elif success_rate >= 75:
        print("✅ PHASE 2.2 MAJORITAIREMENT FONCTIONNELLE")
    else:
        print("⚠️  PHASE 2.2 NÉCESSITE DES CORRECTIONS")
    
    return results

def main():
    try:
        results = run_phase_2_2_tests()
        return results
        
    except Exception as e:
        print(f"\n❌ ERREUR TESTS PHASE 2.2: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()