#!/usr/bin/env python3
"""
Test de validation de l'API complète BOOKTIME pour Vercel
Vérifie tous les endpoints principaux avant déploiement
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Pour test local
# BASE_URL = "https://votre-app.vercel.app"  # Pour test production

class BookTimeAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.test_book_id = None
        self.results = []
    
    def log_test(self, test_name, success, details="", response_time=0):
        """Logger les résultats de test"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "response_time_ms": round(response_time * 1000)
        })
        print(f"{status} {test_name} ({round(response_time * 1000)}ms)")
        if details:
            print(f"   {details}")
    
    def test_health_check(self):
        """Test 1: Health check API"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_test("Health Check", True, 
                                f"Database: {data.get('database')}, Version: {data.get('version')}", 
                                response_time)
                    return True
                else:
                    self.log_test("Health Check", False, 
                                f"Status not OK: {data.get('status')}", response_time)
            else:
                self.log_test("Health Check", False, 
                            f"HTTP {response.status_code}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Health Check", False, str(e), response_time)
        return False
    
    def test_authentication(self):
        """Test 2: Authentication (register/login)"""
        start_time = time.time()
        try:
            auth_data = {
                "first_name": "Test",
                "last_name": "APIComplete"
            }
            
            response = requests.post(
                f"{self.base_url}/api/auth/register",
                json=auth_data,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.log_test("Authentication", True, 
                                f"Token received, User ID: {data.get('user', {}).get('id')}", 
                                response_time)
                    return True
                else:
                    self.log_test("Authentication", False, 
                                "No token in response", response_time)
            else:
                self.log_test("Authentication", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Authentication", False, str(e), response_time)
        return False
    
    def test_create_book(self):
        """Test 3: Create book"""
        if not self.token:
            self.log_test("Create Book", False, "No authentication token")
            return False
        
        start_time = time.time()
        try:
            book_data = {
                "title": "Test Book API Complete",
                "author": "Test Author",
                "category": "roman",
                "description": "Livre de test pour API complète Vercel",
                "total_pages": 300
            }
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.base_url}/api/books",
                json=book_data,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                book = data.get("book", {})
                self.test_book_id = book.get("id")
                if self.test_book_id:
                    self.log_test("Create Book", True, 
                                f"Book created: {book.get('title')} (ID: {self.test_book_id})", 
                                response_time)
                    return True
                else:
                    self.log_test("Create Book", False, 
                                "No book ID in response", response_time)
            else:
                self.log_test("Create Book", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Create Book", False, str(e), response_time)
        return False
    
    def test_get_books(self):
        """Test 4: Get books"""
        if not self.token:
            self.log_test("Get Books", False, "No authentication token")
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/books",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                books = data.get("books", [])
                total = data.get("total", 0)
                self.log_test("Get Books", True, 
                            f"Retrieved {total} books", response_time)
                return True
            else:
                self.log_test("Get Books", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Get Books", False, str(e), response_time)
        return False
    
    def test_update_book(self):
        """Test 5: Update book"""
        if not self.token or not self.test_book_id:
            self.log_test("Update Book", False, "No token or book ID")
            return False
        
        start_time = time.time()
        try:
            update_data = {
                "status": "reading",
                "current_page": 50,
                "rating": 4
            }
            
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.put(
                f"{self.base_url}/api/books/{self.test_book_id}",
                json=update_data,
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Update Book", True, 
                            "Book updated successfully", response_time)
                return True
            else:
                self.log_test("Update Book", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Update Book", False, str(e), response_time)
        return False
    
    def test_get_stats(self):
        """Test 6: Get statistics"""
        if not self.token:
            self.log_test("Get Stats", False, "No authentication token")
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/stats",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                total_books = data.get("total_books", 0)
                categories = data.get("categories", {})
                self.log_test("Get Stats", True, 
                            f"Stats: {total_books} books, Categories: {categories}", 
                            response_time)
                return True
            else:
                self.log_test("Get Stats", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Get Stats", False, str(e), response_time)
        return False
    
    def test_openlibrary_search(self):
        """Test 7: OpenLibrary search"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/openlibrary/search?q=harry%20potter&limit=5",
                timeout=15  # Plus de temps pour API externe
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                books = data.get("books", [])
                total_found = data.get("total_found", 0)
                self.log_test("OpenLibrary Search", True, 
                            f"Found {len(books)} books (total: {total_found})", 
                            response_time)
                return True
            else:
                self.log_test("OpenLibrary Search", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("OpenLibrary Search", False, str(e), response_time)
        return False
    
    def test_series_popular(self):
        """Test 8: Popular series"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/series/popular?limit=5",
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                series = data.get("series", [])
                self.log_test("Popular Series", True, 
                            f"Retrieved {len(series)} popular series", response_time)
                return True
            else:
                self.log_test("Popular Series", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Popular Series", False, str(e), response_time)
        return False
    
    def test_authors(self):
        """Test 9: Get authors"""
        if not self.token:
            self.log_test("Get Authors", False, "No authentication token")
            return False
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{self.base_url}/api/authors",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                authors = data.get("authors", [])
                self.log_test("Get Authors", True, 
                            f"Retrieved {len(authors)} authors", response_time)
                return True
            else:
                self.log_test("Get Authors", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Get Authors", False, str(e), response_time)
        return False
    
    def cleanup(self):
        """Test 10: Cleanup - Delete test book"""
        if not self.token or not self.test_book_id:
            return
        
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.delete(
                f"{self.base_url}/api/books/{self.test_book_id}",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                self.log_test("Cleanup - Delete Book", True, 
                            "Test book deleted successfully", response_time)
                return True
            else:
                self.log_test("Cleanup - Delete Book", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Cleanup - Delete Book", False, str(e), response_time)
        return False
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print(f"🧪 BOOKTIME API COMPLÈTE - TESTS DE VALIDATION")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Exécuter tous les tests
        tests = [
            self.test_health_check,
            self.test_authentication,
            self.test_create_book,
            self.test_get_books,
            self.test_update_book,
            self.test_get_stats,
            self.test_openlibrary_search,
            self.test_series_popular,
            self.test_authors,
            self.cleanup
        ]
        
        passed = 0
        for test in tests:
            if test():
                passed += 1
            print()  # Ligne vide entre tests
        
        # Résumé final
        total = len(tests)
        print("=" * 60)
        print(f"📊 RÉSULTATS FINAUX:")
        print(f"✅ Tests réussis: {passed}/{total}")
        print(f"❌ Tests échoués: {total-passed}/{total}")
        print(f"📈 Taux de succès: {round(passed/total*100)}%")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT RÉUSSIS - API PRÊTE POUR VERCEL!")
        elif passed >= total * 0.8:
            print("⚠️ MAJORITÉ DES TESTS RÉUSSIS - Vérifier les échecs avant déploiement")
        else:
            print("❌ PLUSIEURS TESTS ÉCHOUÉS - Corrections nécessaires avant déploiement")
        
        return passed == total

def main():
    """Point d'entrée principal"""
    print("🚀 BOOKTIME API COMPLÈTE - VALIDATION AVANT DÉPLOIEMENT VERCEL")
    print()
    
    # Test local d'abord (si serveur local disponible)
    local_tester = BookTimeAPITester("http://localhost:8000")
    try:
        # Test rapide de connectivité
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("🏠 TESTS SERVEUR LOCAL:")
            local_success = local_tester.run_all_tests()
            print()
        else:
            print("⚠️ Serveur local non disponible, ignorer tests locaux")
    except:
        print("⚠️ Serveur local non disponible sur localhost:8000")
        print("💡 Pour tester localement: cd api && python -m uvicorn main:app --reload --port 8000")
        print()
    
    # Instructions pour tests production
    print("🌐 TESTS PRODUCTION VERCEL:")
    print("1. Déployez d'abord sur Vercel")
    print("2. Remplacez BASE_URL dans ce script par votre URL Vercel")
    print("3. Exécutez: python test-vercel-api-complete.py")
    print()
    print("Exemple URL: https://booktime-votre-repo.vercel.app")

if __name__ == "__main__":
    main()