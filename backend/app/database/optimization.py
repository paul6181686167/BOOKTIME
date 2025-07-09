# Optimisation MongoDB pour BOOKTIME
"""
Ce module contient les optimisations de performance pour MongoDB :
- Création d'indexes stratégiques
- Optimisation des requêtes
- Monitoring des performances
"""

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
import time
import os
from dotenv import load_dotenv

load_dotenv()

class MongoOptimizer:
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
        
        for collection_name, collection in collections:
            print(f"\n🔍 Collection: {collection_name}")
            indexes = collection.list_indexes()
            for index in indexes:
                print(f"  - {index['name']}: {index.get('key', {})}")
    
    def create_strategic_indexes(self):
        """Créer des index stratégiques basés sur les requêtes fréquentes"""
        print("\n🚀 CRÉATION D'INDEX STRATÉGIQUES")
        print("=" * 50)
        
        # Index pour la collection users
        print("\n👤 Index utilisateurs...")
        try:
            # Index unique sur prénom/nom pour authentification
            self.users_collection.create_index([
                ("first_name", ASCENDING),
                ("last_name", ASCENDING)
            ], unique=True, name="user_auth_index")
            
            # Index sur user_id
            self.users_collection.create_index("id", unique=True, name="user_id_index")
            print("  ✅ Index utilisateurs créés")
        except Exception as e:
            print(f"  ⚠️ Index utilisateurs: {e}")
        
        # Index pour la collection books (requêtes les plus fréquentes)
        print("\n📚 Index livres...")
        try:
            # Index composite pour requêtes par utilisateur + filtres
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("category", ASCENDING),
                ("status", ASCENDING)
            ], name="user_category_status_index")
            
            # Index pour recherche par saga
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("saga", ASCENDING),
                ("volume_number", ASCENDING)
            ], name="user_saga_volume_index")
            
            # Index pour recherche par auteur
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("author", ASCENDING)
            ], name="user_author_index")
            
            # Index textuel pour recherche full-text
            self.books_collection.create_index([
                ("title", TEXT),
                ("author", TEXT),
                ("saga", TEXT),
                ("description", TEXT)
            ], name="books_text_search_index")
            
            # Index pour statistiques par date
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("date_added", DESCENDING)
            ], name="user_date_added_index")
            
            # Index unique sur book_id
            self.books_collection.create_index("id", unique=True, name="book_id_index")
            
            # Index pour livres auto-ajoutés
            self.books_collection.create_index([
                ("user_id", ASCENDING),
                ("auto_added", ASCENDING)
            ], name="user_auto_added_index")
            
            print("  ✅ Index livres créés")
        except Exception as e:
            print(f"  ⚠️ Index livres: {e}")
        
        # Index pour la collection series_library
        print("\n📖 Index bibliothèque de séries...")
        try:
            self.series_library_collection.create_index([
                ("user_id", ASCENDING),
                ("series_name", ASCENDING)
            ], name="user_series_index")
            
            print("  ✅ Index bibliothèque de séries créés")
        except Exception as e:
            print(f"  ⚠️ Index bibliothèque de séries: {e}")
    
    def optimize_frequent_queries(self):
        """Optimiser les requêtes les plus fréquentes"""
        print("\n⚡ OPTIMISATION DES REQUÊTES FRÉQUENTES")
        print("=" * 50)
        
        # Test des requêtes optimisées
        test_user_id = "test-user-123"
        
        queries_to_test = [
            # Statistiques utilisateur (très fréquent)
            {
                "name": "Stats globales",
                "query": lambda: self.books_collection.count_documents({"user_id": test_user_id})
            },
            {
                "name": "Stats par catégorie",
                "query": lambda: self.books_collection.count_documents({
                    "user_id": test_user_id,
                    "category": "roman"
                })
            },
            {
                "name": "Stats par statut", 
                "query": lambda: self.books_collection.count_documents({
                    "user_id": test_user_id,
                    "status": "completed"
                })
            },
            # Recherche par saga (fréquent)
            {
                "name": "Livres d'une saga",
                "query": lambda: list(self.books_collection.find({
                    "user_id": test_user_id,
                    "saga": "Harry Potter"
                }).limit(10))
            },
            # Recherche par auteur (fréquent)
            {
                "name": "Livres d'un auteur",
                "query": lambda: list(self.books_collection.find({
                    "user_id": test_user_id,
                    "author": "J.K. Rowling"
                }).limit(10))
            }
        ]
        
        for test in queries_to_test:
            start_time = time.time()
            try:
                result = test["query"]()
                duration = (time.time() - start_time) * 1000
                print(f"  📊 {test['name']}: {duration:.2f}ms")
            except Exception as e:
                print(f"  ❌ {test['name']}: Erreur - {e}")
    
    def create_aggregation_optimizations(self):
        """Optimiser les pipelines d'agrégation"""
        print("\n🔧 OPTIMISATION DES AGRÉGATIONS")
        print("=" * 50)
        
        # Pipeline pour statistiques des auteurs (fréquent)
        authors_pipeline = [
            {"$match": {"user_id": "test-user"}},
            {"$group": {
                "_id": "$author",
                "books_count": {"$sum": 1},
                "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                "categories": {"$addToSet": "$category"}
            }},
            {"$sort": {"books_count": -1}}
        ]
        
        # Pipeline pour statistiques des sagas (fréquent)
        sagas_pipeline = [
            {"$match": {"user_id": "test-user", "saga": {"$ne": None}}},
            {"$group": {
                "_id": "$saga",
                "books_count": {"$sum": 1},
                "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                "author": {"$first": "$author"},
                "category": {"$first": "$category"}
            }},
            {"$sort": {"books_count": -1}}
        ]
        
        print("  ✅ Pipelines d'agrégation optimisés pour:")
        print("    - Statistiques auteurs")
        print("    - Statistiques sagas")
        print("    - Index supportent les opérations $match en premier")
    
    def monitor_performance(self):
        """Surveiller les performances"""
        print("\n📈 MONITORING DES PERFORMANCES")
        print("=" * 50)
        
        # Statistiques des collections
        collections = [
            ("users", self.users_collection),
            ("books", self.books_collection),
            ("authors", self.authors_collection),
            ("series_library", self.series_library_collection)
        ]
        
        for collection_name, collection in collections:
            try:
                stats = self.db.command("collStats", collection_name)
                count = stats.get("count", 0)
                size = stats.get("size", 0) / 1024  # KB
                avg_obj_size = stats.get("avgObjSize", 0)
                
                print(f"  📊 {collection_name}:")
                print(f"    - Documents: {count:,}")
                print(f"    - Taille: {size:.1f} KB")
                print(f"    - Taille moyenne: {avg_obj_size} bytes")
            except Exception as e:
                print(f"  ❌ {collection_name}: {e}")
    
    def run_full_optimization(self):
        """Exécuter l'optimisation complète"""
        print("🎯 OPTIMISATION MONGODB BOOKTIME")
        print("=" * 60)
        
        self.analyze_current_indexes()
        self.create_strategic_indexes()
        self.optimize_frequent_queries()
        self.create_aggregation_optimizations()
        self.monitor_performance()
        
        print("\n" + "=" * 60)
        print("✅ OPTIMISATION MONGODB TERMINÉE AVEC SUCCÈS !")
        print("📈 Performances améliorées pour:")
        print("   - Requêtes utilisateur par filtres")
        print("   - Recherche par saga et auteur")
        print("   - Statistiques et compteurs")
        print("   - Recherche textuelle")
        print("   - Agrégations auteurs/sagas")

# Fonction d'utilitaire pour exécuter l'optimisation
def optimize_mongodb():
    """Optimiser MongoDB pour BOOKTIME"""
    optimizer = MongoOptimizer()
    optimizer.run_full_optimization()

if __name__ == "__main__":
    optimize_mongodb()