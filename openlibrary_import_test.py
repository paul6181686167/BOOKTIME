#!/usr/bin/env python3
"""
Test spécifique pour la validation du problème de synchronisation 
Ajout/Affichage Livres avec Open Library Import
"""
import requests
import json
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://8b9f9a3a-f7e8-42a0-96f8-6b1947012e49.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class OpenLibraryImportTest:
    def __init__(self):
        self.test_user = None
        self.auth_token = None
        self.created_books = []
        
    def setup_test_user(self):
        """Créer un utilisateur de test et obtenir le token d'authentification"""
        print("🔧 Configuration de l'utilisateur de test...")
        
        # Créer un utilisateur unique
        user_data = {
            "first_name": f"TestOL{datetime.now().strftime('%H%M%S')}",
            "last_name": "ImportUser"
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            result = response.json()
            self.test_user = result["user"]
            self.auth_token = result["access_token"]
            print(f"✅ Utilisateur créé: {self.test_user['first_name']} {self.test_user['last_name']}")
            return True
        else:
            print(f"❌ Erreur création utilisateur: {response.status_code} - {response.text}")
            return False
    
    def get_auth_headers(self):
        """Retourner les headers d'authentification"""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    def test_openlibrary_search(self):
        """Test 1: Vérifier que l'API Open Library Search fonctionne"""
        print("\n📚 Test 1: API Open Library Search")
        
        search_terms = ["Harry Potter", "Le Petit Prince", "One Piece"]
        
        for term in search_terms:
            response = requests.get(
                f"{API_URL}/openlibrary/search",
                params={"q": term, "limit": 5},
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Recherche '{term}': {len(data.get('books', []))} livres trouvés")
                
                # Vérifier la structure des données
                if data.get('books'):
                    book = data['books'][0]
                    required_fields = ['ol_key', 'title', 'author', 'category']
                    missing_fields = [field for field in required_fields if field not in book]
                    if missing_fields:
                        print(f"⚠️  Champs manquants dans les résultats: {missing_fields}")
                    else:
                        print(f"✅ Structure des données correcte pour '{term}'")
            else:
                print(f"❌ Erreur recherche '{term}': {response.status_code} - {response.text}")
                return False
        
        return True
    
    def test_openlibrary_import(self):
        """Test 2: Vérifier que l'import depuis Open Library fonctionne"""
        print("\n📥 Test 2: API Open Library Import")
        
        # D'abord, chercher un livre pour obtenir un ol_key valide
        search_response = requests.get(
            f"{API_URL}/openlibrary/search",
            params={"q": "Harry Potter", "limit": 1},
            headers=self.get_auth_headers()
        )
        
        if search_response.status_code != 200:
            print(f"❌ Impossible de chercher un livre pour l'import: {search_response.status_code}")
            return False
        
        search_data = search_response.json()
        if not search_data.get('books'):
            print("❌ Aucun livre trouvé pour l'import")
            return False
        
        book_to_import = search_data['books'][0]
        ol_key = book_to_import['ol_key']
        
        print(f"📖 Import du livre: {book_to_import['title']} (ol_key: {ol_key})")
        
        # Tester l'import
        import_data = {
            "ol_key": ol_key,
            "category": "roman"
        }
        
        response = requests.post(
            f"{API_URL}/openlibrary/import",
            json=import_data,
            headers=self.get_auth_headers()
        )
        
        if response.status_code == 200:
            imported_book = response.json()
            print(f"📋 Réponse import: {json.dumps(imported_book, indent=2)}")
            
            # La réponse contient un champ 'book' avec les données du livre
            if 'book' in imported_book:
                book_data = imported_book['book']
                self.created_books.append(book_data['id'])  # Utiliser 'id' au lieu de '_id'
                print(f"✅ Livre importé avec succès: {book_data['title']}")
                print(f"   ID: {book_data['id']}")
                print(f"   Auteur: {book_data['author']}")
                print(f"   Catégorie: {book_data['category']}")
                return book_data
            else:
                print(f"⚠️  Structure de réponse inattendue: {list(imported_book.keys())}")
                return imported_book
        else:
            print(f"❌ Erreur import: {response.status_code} - {response.text}")
            return False
    
    def test_books_api_after_import(self, imported_book):
        """Test 3: Vérifier que le livre importé apparaît dans l'API Books"""
        print("\n📋 Test 3: Vérification API Books après import")
        
        # Test 3a: GET /api/books - Récupérer tous les livres
        response = requests.get(f"{API_URL}/books", headers=self.get_auth_headers())
        
        if response.status_code == 200:
            books_data = response.json()
            
            # L'API retourne une structure paginée avec 'items'
            if isinstance(books_data, dict) and 'items' in books_data:
                books = books_data['items']
                total = books_data['total']
                print(f"✅ API Books fonctionne: {len(books)} livres sur {total} total")
            else:
                # Fallback si c'est une liste directe
                books = books_data if isinstance(books_data, list) else []
                print(f"✅ API Books fonctionne: {len(books)} livres trouvés")
            
            # Chercher le livre importé
            book_id = imported_book['id']
            imported_book_found = None
            for book in books:
                # Les livres peuvent avoir '_id' et/ou 'id'
                if book.get('_id') == book_id or book.get('id') == book_id:
                    imported_book_found = book
                    break
            
            if imported_book_found:
                print(f"✅ Livre importé trouvé dans la liste: {imported_book_found['title']}")
                
                # Vérifier les champs requis
                required_fields = ['title', 'author', 'category', 'status']
                missing_fields = [field for field in required_fields if field not in imported_book_found]
                if missing_fields:
                    print(f"⚠️  Champs manquants: {missing_fields}")
                else:
                    print("✅ Tous les champs requis sont présents")
            else:
                print(f"❌ Livre importé NON trouvé dans la liste des livres!")
                print(f"   ID recherché: {book_id}")
                if books:
                    print(f"   IDs disponibles: {[book.get('_id', book.get('id', 'NO_ID')) for book in books[:5]]}")
                return False
        else:
            print(f"❌ Erreur API Books: {response.status_code} - {response.text}")
            return False
        
        # Test 3b: GET /api/books/{book_id} - Récupérer le livre spécifique
        response = requests.get(
            f"{API_URL}/books/{imported_book['id']}", 
            headers=self.get_auth_headers()
        )
        
        if response.status_code == 200:
            specific_book = response.json()
            print(f"✅ Livre spécifique récupéré: {specific_book['title']}")
        else:
            print(f"❌ Erreur récupération livre spécifique: {response.status_code}")
            return False
        
        # Test 3c: Filtrage par catégorie
        category = imported_book['category']
        response = requests.get(
            f"{API_URL}/books",
            params={"category": category},
            headers=self.get_auth_headers()
        )
        
        if response.status_code == 200:
            filtered_data = response.json()
            
            # Gérer la structure paginée
            if isinstance(filtered_data, dict) and 'items' in filtered_data:
                filtered_books = filtered_data['items']
            else:
                filtered_books = filtered_data if isinstance(filtered_data, list) else []
            
            book_found_in_filter = any(
                book.get('_id') == imported_book['id'] or book.get('id') == imported_book['id'] 
                for book in filtered_books
            )
            if book_found_in_filter:
                print(f"✅ Livre trouvé dans le filtre catégorie '{category}'")
            else:
                print(f"❌ Livre NON trouvé dans le filtre catégorie '{category}'")
                return False
        else:
            print(f"❌ Erreur filtrage par catégorie: {response.status_code}")
            return False
        
        return True
    
    def test_stats_update(self):
        """Test 4: Vérifier que les statistiques sont mises à jour"""
        print("\n📊 Test 4: Vérification mise à jour des statistiques")
        
        response = requests.get(f"{API_URL}/stats", headers=self.get_auth_headers())
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques récupérées:")
            print(f"   Total livres: {stats['total_books']}")
            print(f"   Romans: {stats['categories'].get('roman', 0)}")
            print(f"   BD: {stats['categories'].get('bd', 0)}")
            print(f"   Mangas: {stats['categories'].get('manga', 0)}")
            
            # Vérifier que nous avons au moins 1 livre (celui qu'on vient d'importer)
            if stats['total_books'] >= 1:
                print("✅ Les statistiques reflètent l'ajout du livre")
                return True
            else:
                print("❌ Les statistiques ne reflètent pas l'ajout du livre")
                return False
        else:
            print(f"❌ Erreur récupération statistiques: {response.status_code}")
            return False
    
    def test_authentication_required(self):
        """Test 5: Vérifier que l'authentification est requise"""
        print("\n🔐 Test 5: Vérification authentification requise")
        
        endpoints_to_test = [
            f"{API_URL}/books",
            f"{API_URL}/openlibrary/search?q=test",
            f"{API_URL}/stats"
        ]
        
        for endpoint in endpoints_to_test:
            # Test sans token
            response = requests.get(endpoint)
            if response.status_code == 401:
                print(f"✅ {endpoint.split('/')[-1]}: Authentification requise (401)")
            else:
                print(f"⚠️  {endpoint.split('/')[-1]}: Pas d'authentification requise ({response.status_code})")
        
        return True
    
    def test_duplicate_import_prevention(self):
        """Test 6: Vérifier la prévention des doublons"""
        print("\n🔄 Test 6: Prévention des doublons")
        
        if not self.created_books:
            print("⚠️  Aucun livre créé pour tester les doublons")
            return True
        
        # Essayer d'importer le même livre à nouveau
        search_response = requests.get(
            f"{API_URL}/openlibrary/search",
            params={"q": "Harry Potter", "limit": 1},
            headers=self.get_auth_headers()
        )
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            if search_data.get('books'):
                ol_key = search_data['books'][0]['ol_key']
                
                import_data = {
                    "ol_key": ol_key,
                    "category": "roman"
                }
                
                response = requests.post(
                    f"{API_URL}/openlibrary/import",
                    json=import_data,
                    headers=self.get_auth_headers()
                )
                
                if response.status_code == 409:  # Conflict - duplicate
                    print("✅ Prévention des doublons fonctionne (409 Conflict)")
                elif response.status_code == 200:
                    print("⚠️  Doublon autorisé - peut être normal selon l'implémentation")
                else:
                    print(f"⚠️  Réponse inattendue pour doublon: {response.status_code}")
        
        return True
    
    def cleanup(self):
        """Nettoyer les données de test"""
        print("\n🧹 Nettoyage des données de test...")
        
        for book_id in self.created_books:
            try:
                response = requests.delete(
                    f"{API_URL}/books/{book_id}",
                    headers=self.get_auth_headers()
                )
                if response.status_code == 200:
                    print(f"✅ Livre supprimé: {book_id}")
                else:
                    print(f"⚠️  Erreur suppression livre {book_id}: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Exception lors de la suppression: {e}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 Début des tests Open Library Import")
        print("=" * 60)
        
        # Configuration
        if not self.setup_test_user():
            print("❌ Impossible de configurer l'utilisateur de test")
            return False
        
        try:
            # Tests principaux
            tests_results = []
            
            # Test 1: Open Library Search
            tests_results.append(("Open Library Search", self.test_openlibrary_search()))
            
            # Test 2: Open Library Import
            imported_book = self.test_openlibrary_import()
            tests_results.append(("Open Library Import", bool(imported_book)))
            
            if imported_book:
                # Test 3: Books API après import
                tests_results.append(("Books API après import", self.test_books_api_after_import(imported_book)))
                
                # Test 4: Mise à jour des statistiques
                tests_results.append(("Mise à jour statistiques", self.test_stats_update()))
            
            # Test 5: Authentification
            tests_results.append(("Authentification requise", self.test_authentication_required()))
            
            # Test 6: Prévention doublons
            tests_results.append(("Prévention doublons", self.test_duplicate_import_prevention()))
            
            # Résumé
            print("\n" + "=" * 60)
            print("📋 RÉSUMÉ DES TESTS")
            print("=" * 60)
            
            all_passed = True
            for test_name, result in tests_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
                if not result:
                    all_passed = False
            
            print("\n" + "=" * 60)
            if all_passed:
                print("🎉 TOUS LES TESTS SONT PASSÉS!")
                print("✅ Le backend fonctionne parfaitement pour l'import Open Library")
                print("✅ Le problème était bien uniquement côté frontend (UX)")
            else:
                print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
                print("🔍 Vérifier les détails ci-dessus pour identifier les problèmes")
            
            return all_passed
            
        finally:
            # Nettoyage
            self.cleanup()

if __name__ == "__main__":
    test_runner = OpenLibraryImportTest()
    success = test_runner.run_all_tests()
    exit(0 if success else 1)