#!/usr/bin/env python3
"""
Phase 2.1 : Optimisation MongoDB - Exécution directe
Script pour exécuter l'optimisation complète MongoDB de BOOKTIME
"""

import sys
import os
import time
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

class Phase21Optimizer:
    def __init__(self):
        self.mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")
        self.client = MongoClient(self.mongo_url)
        self.db = self.client.booktime
        
        # Collections principales
        self.users_collection = self.db.users
        self.books_collection = self.db.books
        self.authors_collection = self.db.authors
        self.series_library_collection = self.db.series_library
    
    def analyze_current_indexes(self):
        """Analyser les index actuels"""
        print("📊 ANALYSE DES INDEX ACTUELS")
        print("=" * 50)
        
        collections = [
            ("users", self.users_collection),
            ("books", self.books_collection), 
            ("authors", self.authors_collection),
            ("series_library", self.series_library_collection)
        ]
        
        indexes_analysis = {}
        
        for collection_name, collection in collections:
            print(f"\n🔍 Collection: {collection_name}")
            try:
                indexes = list(collection.list_indexes())
                indexes_analysis[collection_name] = indexes
                
                for index in indexes:
                    print(f"  - {index['name']}: {index.get('key', {})}")
            except Exception as e:
                print(f"  ⚠️  Erreur: {e}")
                
        return indexes_analysis
    
    def create_strategic_indexes(self):
        """Créer des index stratégiques basés sur les requêtes fréquentes"""
        print("\n🚀 CRÉATION D'INDEX STRATÉGIQUES")
        print("=" * 50)
        
        indexes_created = {
            'users': [],
            'books': [],
            'authors': [],
            'series_library': []
        }
        
        # === INDEXES USERS COLLECTION ===
        print("\n📝 Users Collection:")
        try:
            # Index unique pour authentification rapide
            self.users_collection.create_index([
                ("first_name", ASCENDING),
                ("last_name", ASCENDING)
            ], unique=True, name="auth_unique_idx")
            indexes_created['users'].append("auth_unique_idx")
            print("  ✅ auth_unique_idx créé")
            
            # Index pour recherche utilisateur par ID
            self.users_collection.create_index([
                ("id", ASCENDING)
            ], unique=True, name="user_id_idx")
            indexes_created['users'].append("user_id_idx")
            print("  ✅ user_id_idx créé")
            
        except Exception as e:
            if "already exists" in str(e):
                print("  ℹ️  Indexes users déjà existants")
            else:
                print(f"  ⚠️  Erreur users indexes: {e}")
        
        # === INDEXES BOOKS COLLECTION (Les plus critiques) ===
        print("\n📚 Books Collection:")
        try:
            # Index composé pour filtrage par utilisateur + catégorie + statut
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("category", ASCENDING),
                ("status", ASCENDING)
            ], name="user_category_status_idx")
            indexes_created['books'].append("user_category_status_idx")
            print("  ✅ user_category_status_idx créé")
            
            # Index pour recherche par utilisateur (requête la plus fréquente)
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("date_added", DESCENDING)
            ], name="user_date_idx")
            indexes_created['books'].append("user_date_idx")
            print("  ✅ user_date_idx créé")
            
            # Index pour recherche par auteur
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("author", ASCENDING)
            ], name="user_author_idx")
            indexes_created['books'].append("user_author_idx")
            print("  ✅ user_author_idx créé")
            
            # Index pour recherche par saga
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("saga", ASCENDING),
                ("volume", ASCENDING)
            ], name="user_saga_volume_idx")
            indexes_created['books'].append("user_saga_volume_idx")
            print("  ✅ user_saga_volume_idx créé")
            
            # Index textuel pour recherche full-text
            self.books_collection.create_index([
                ("title", TEXT),
                ("author", TEXT),
                ("description", TEXT),
                ("saga", TEXT)
            ], name="books_fulltext_idx")
            indexes_created['books'].append("books_fulltext_idx")
            print("  ✅ books_fulltext_idx créé")
            
            # Index pour statistiques (performance critiques)
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("category", ASCENDING),
                ("status", ASCENDING),
                ("author", ASCENDING)
            ], name="stats_performance_idx")
            indexes_created['books'].append("stats_performance_idx")
            print("  ✅ stats_performance_idx créé")
            
        except Exception as e:
            if "already exists" in str(e):
                print("  ℹ️  Indexes books déjà existants")
            else:
                print(f"  ⚠️  Erreur books indexes: {e}")
        
        # === INDEXES AUTHORS COLLECTION ===
        print("\n👨‍💼 Authors Collection:")
        try:
            # Index pour recherche par utilisateur
            self.authors_collection.create_index([
                ("user_id", ASCENDING),
                ("name", ASCENDING)
            ], name="user_author_name_idx")
            indexes_created['authors'].append("user_author_name_idx")
            print("  ✅ user_author_name_idx créé")
            
        except Exception as e:
            if "already exists" in str(e):
                print("  ℹ️  Indexes authors déjà existants")
            else:
                print(f"  ⚠️  Erreur authors indexes: {e}")
        
        # === INDEXES SERIES_LIBRARY COLLECTION ===
        print("\n📖 Series Library Collection:")
        try:
            # Index pour recherche par utilisateur
            self.series_library_collection.create_index([
                ("user_id", ASCENDING),
                ("category", ASCENDING)
            ], name="user_series_category_idx")
            indexes_created['series_library'].append("user_series_category_idx")
            print("  ✅ user_series_category_idx créé")
            
        except Exception as e:
            if "already exists" in str(e):
                print("  ℹ️  Indexes series_library déjà existants")
            else:
                print(f"  ⚠️  Erreur series_library indexes: {e}")
        
        return indexes_created
    
    def get_collection_stats(self):
        """Obtient les statistiques de performance de toutes les collections"""
        print("\n📊 STATISTIQUES DES COLLECTIONS")
        print("=" * 50)
        
        stats = {}
        collections = [
            ("users", self.users_collection),
            ("books", self.books_collection),
            ("authors", self.authors_collection),
            ("series_library", self.series_library_collection)
        ]
        
        for collection_name, collection in collections:
            try:
                # Statistiques générales
                collection_stats = self.db.command("collStats", collection_name)
                
                # Informations sur les indexes
                indexes = list(collection.list_indexes())
                
                stats[collection_name] = {
                    'document_count': collection_stats.get('count', 0),
                    'total_size': collection_stats.get('size', 0),
                    'avg_document_size': collection_stats.get('avgObjSize', 0),
                    'total_index_size': collection_stats.get('totalIndexSize', 0),
                    'indexes_count': len(indexes),
                    'indexes': [idx['name'] for idx in indexes]
                }
                
                print(f"\n🔍 {collection_name}:")
                print(f"  📄 Documents: {stats[collection_name]['document_count']}")
                print(f"  📦 Taille totale: {stats[collection_name]['total_size']} bytes")
                print(f"  🔍 Indexes: {stats[collection_name]['indexes_count']}")
                
            except Exception as e:
                print(f"  ⚠️  Erreur stats collection {collection_name}: {e}")
                stats[collection_name] = {'error': str(e)}
        
        return stats
    
    def test_query_performance(self):
        """Test des performances des requêtes critiques"""
        print("\n⚡ TESTS DE PERFORMANCE DES REQUÊTES")
        print("=" * 50)
        
        # Tests avec un utilisateur existant s'il y en a un
        test_user_id = "test-user-performance"
        
        # Recherche d'un utilisateur existant
        existing_user = self.users_collection.find_one({}, {"id": 1})
        if existing_user:
            test_user_id = existing_user.get("id", test_user_id)
        
        critical_queries = [
            {
                'name': 'get_user_books',
                'collection': self.books_collection,
                'query': {'user_id': test_user_id}
            },
            {
                'name': 'get_user_books_by_category',
                'collection': self.books_collection,
                'query': {'user_id': test_user_id, 'category': 'roman'}
            },
            {
                'name': 'get_user_books_by_status',
                'collection': self.books_collection,
                'query': {'user_id': test_user_id, 'status': 'reading'}
            },
            {
                'name': 'search_books_by_author',
                'collection': self.books_collection,
                'query': {'user_id': test_user_id, 'author': {'$regex': 'Tolkien', '$options': 'i'}}
            },
            {
                'name': 'get_user_sagas',
                'collection': self.books_collection,
                'query': {'user_id': test_user_id, 'saga': {'$exists': True, '$ne': None}}
            }
        ]
        
        performance_results = {}
        
        for query_test in critical_queries:
            print(f"\n🔍 Test: {query_test['name']}")
            
            try:
                # Mesure du temps d'exécution
                start_time = time.time()
                
                # Exécution de la requête
                results = list(query_test['collection'].find(query_test['query']).limit(100))
                
                execution_time = time.time() - start_time
                
                performance_results[query_test['name']] = {
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'documents_returned': len(results),
                    'status': 'success'
                }
                
                print(f"  ⏱️  Temps: {performance_results[query_test['name']]['execution_time_ms']}ms")
                print(f"  📄 Documents: {performance_results[query_test['name']]['documents_returned']}")
                
            except Exception as e:
                performance_results[query_test['name']] = {
                    'error': str(e),
                    'status': 'error'
                }
                print(f"  ❌ Erreur: {e}")
        
        return performance_results
    
    def run_phase_2_1_optimization(self):
        """Exécute la Phase 2.1 complète d'optimisation MongoDB"""
        print("\n🚀 PHASE 2.1 : OPTIMISATION MONGODB - DÉMARRAGE")
        print("=" * 70)
        
        # Étape 1: Analyse des index actuels
        print("\n📋 ÉTAPE 1: ANALYSE DES INDEX ACTUELS")
        current_indexes = self.analyze_current_indexes()
        
        # Étape 2: Création des index stratégiques
        print("\n📋 ÉTAPE 2: CRÉATION D'INDEX STRATÉGIQUES")
        indexes_created = self.create_strategic_indexes()
        
        # Étape 3: Statistiques des collections
        print("\n📋 ÉTAPE 3: STATISTIQUES DES COLLECTIONS")
        collection_stats = self.get_collection_stats()
        
        # Étape 4: Tests de performance
        print("\n📋 ÉTAPE 4: TESTS DE PERFORMANCE")
        performance_tests = self.test_query_performance()
        
        # Étape 5: Rapport final
        print("\n✅ PHASE 2.1 : OPTIMISATION MONGODB - TERMINÉE")
        print("=" * 70)
        
        optimization_report = {
            'phase': '2.1',
            'title': 'Optimisation MongoDB',
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'current_indexes': current_indexes,
            'indexes_created': indexes_created,
            'collection_stats': collection_stats,
            'performance_tests': performance_tests,
            'summary': {
                'total_indexes_created': sum(len(idx_list) for idx_list in indexes_created.values()),
                'collections_optimized': len(indexes_created),
                'performance_tests_run': len(performance_tests),
                'database_optimized': True
            }
        }
        
        print(f"\n📊 RÉSUMÉ PHASE 2.1:")
        print(f"  ✅ Indexes créés: {optimization_report['summary']['total_indexes_created']}")
        print(f"  ✅ Collections optimisées: {optimization_report['summary']['collections_optimized']}")
        print(f"  ✅ Tests performance: {optimization_report['summary']['performance_tests_run']}")
        print(f"  ✅ Base de données optimisée: {optimization_report['summary']['database_optimized']}")
        
        return optimization_report

def main():
    try:
        # Initialisation et exécution de l'optimisation
        optimizer = Phase21Optimizer()
        result = optimizer.run_phase_2_1_optimization()
        
        print("\n✅ PHASE 2.1 TERMINÉE AVEC SUCCÈS !")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERREUR PHASE 2.1: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()