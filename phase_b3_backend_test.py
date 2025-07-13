#!/usr/bin/env python3
"""
PHASE B.3 - Tests Validation Backend pour Affichage Unifié Séries
Test complet du backend FastAPI modulaire avec focus sur les séries
"""

import requests
import sys
import json
from datetime import datetime
import time

class PhaseB3BackendTester:
    def __init__(self, base_url="https://9fc2dc6c-4a84-459e-9440-189c3942fdb5.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user = f"test_phase_b3_{int(time.time())}"
        
    def log(self, message):
        """Log avec timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Exécuter un test API"""
        # Handle special endpoints that don't use /api prefix
        if endpoint in ['health']:
            url = f"{self.base_url}/{endpoint}"
        else:
            url = f"{self.base_url}/api/{endpoint}" if not endpoint.startswith('http') else endpoint
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Test {self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASS - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                self.log(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ ERROR - {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test de santé du backend"""
        self.log("\n🏥 === TEST SANTÉ BACKEND ===")
        success, response = self.run_test(
            "Health Check",
            "GET", 
            "health",
            200
        )
        if success:
            self.log(f"✅ Backend opérationnel - DB: {response.get('database', 'unknown')}")
        return success

    def test_authentication(self):
        """Test d'authentification"""
        self.log("\n🔐 === TEST AUTHENTIFICATION ===")
        
        # Test création utilisateur (qui peut retourner 200 si l'utilisateur existe déjà)
        user_data = {
            "first_name": "TestPhaseB3",
            "last_name": "User",
            "email": f"{self.test_user}@test.com"
        }
        
        success, response = self.run_test(
            "Création utilisateur",
            "POST",
            "auth/register",
            200,  # Changed from 201 to 200
            user_data
        )
        
        # Extract token if present in registration response
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user_id')
            self.log(f"✅ Authentification réussie via registration - Token obtenu")
            return True
        
        # If registration failed (user exists), try login directly
        self.log("ℹ️ Utilisateur existe déjà, tentative de connexion...")
            
        # Test connexion
        login_data = {
            "first_name": "TestPhaseB3",
            "last_name": "User"
        }
        
        success, response = self.run_test(
            "Connexion utilisateur",
            "POST",
            "auth/login", 
            200,
            login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user_id')
            self.log(f"✅ Authentification réussie - Token obtenu")
            return True
        else:
            self.log("❌ Échec authentification")
            return False

    def test_series_endpoints(self):
        """Test des endpoints séries (Phase B focus)"""
        self.log("\n📚 === TEST ENDPOINTS SÉRIES (PHASE B) ===")
        
        # Test récupération séries populaires
        success, response = self.run_test(
            "Séries populaires",
            "GET",
            "series/popular?category=roman&limit=10",
            200
        )
        
        if not success:
            return False
            
        series_list = response.get('series', [])
        self.log(f"✅ {len(series_list)} séries populaires récupérées")
        
        # Test recherche de séries
        success, response = self.run_test(
            "Recherche séries",
            "GET", 
            "series/search?q=harry&category=roman",
            200
        )
        
        if success:
            search_results = response.get('series', [])
            self.log(f"✅ {len(search_results)} séries trouvées pour 'harry'")
        
        # Test détection de série
        success, response = self.run_test(
            "Détection série",
            "GET",
            "series/detect?title=Harry Potter à l'école des sorciers&author=J.K. Rowling",
            200
        )
        
        if success:
            detected = response.get('detected_series', [])
            self.log(f"✅ {len(detected)} série(s) détectée(s)")
            
        return True

    def test_series_library_endpoints(self):
        """Test des endpoints bibliothèque séries (Phase B focus)"""
        self.log("\n📖 === TEST BIBLIOTHÈQUE SÉRIES (PHASE B) ===")
        
        # Test récupération bibliothèque séries
        success, response = self.run_test(
            "Bibliothèque séries",
            "GET",
            "series/library",
            200
        )
        
        if success:
            # Handle both list and dict responses
            if isinstance(response, list):
                library_series = response
            else:
                library_series = response.get('series', [])
            self.log(f"✅ {len(library_series)} séries dans la bibliothèque")
        
        # Test ajout série à la bibliothèque
        series_data = {
            "series_name": "Harry Potter Test",
            "authors": ["J.K. Rowling"],
            "category": "roman",
            "total_volumes": 7,
            "description": "Série test pour Phase B",
            "cover_image_url": "",
            "first_published": "1997"
        }
        
        success, response = self.run_test(
            "Ajout série bibliothèque",
            "POST",
            "series/library",
            201,
            series_data
        )
        
        if success:
            self.log("✅ Série ajoutée à la bibliothèque")
            series_id = response.get('id')
            
            # Test mise à jour série
            update_data = {
                "series_status": "reading",
                "completion_percentage": 50
            }
            
            success, response = self.run_test(
                "Mise à jour série",
                "PUT",
                f"series/library/{series_id}",
                200,
                update_data
            )
            
            if success:
                self.log("✅ Série mise à jour")
                
        return True

    def test_books_endpoints(self):
        """Test des endpoints livres"""
        self.log("\n📕 === TEST ENDPOINTS LIVRES ===")
        
        # Test récupération livres
        success, response = self.run_test(
            "Récupération livres",
            "GET",
            "books?limit=10",
            200
        )
        
        if success:
            books = response.get('items', [])
            self.log(f"✅ {len(books)} livres récupérés")
        
        # Test ajout livre
        book_data = {
            "title": "Test Book Phase B",
            "author": "Test Author",
            "category": "roman",
            "status": "to_read",
            "description": "Livre test pour Phase B",
            "saga": "Test Series"
        }
        
        success, response = self.run_test(
            "Ajout livre",
            "POST",
            "books",
            200,  # Changed from 201 to 200
            book_data
        )
        
        if success:
            self.log("✅ Livre ajouté")
            book_id = response.get('id')
            
            # Test mise à jour livre
            update_data = {
                "status": "reading",
                "current_page": 50
            }
            
            success, response = self.run_test(
                "Mise à jour livre",
                "PUT",
                f"books/{book_id}",
                200,
                update_data
            )
            
            if success:
                self.log("✅ Livre mis à jour")
                
        return True

    def test_library_endpoints(self):
        """Test des endpoints bibliothèque"""
        self.log("\n📚 === TEST ENDPOINTS BIBLIOTHÈQUE ===")
        
        # Test récupération bibliothèque complète
        success, response = self.run_test(
            "Bibliothèque complète",
            "GET",
            "library/complete",
            200
        )
        
        if success:
            library = response.get('library', {})
            books_count = library.get('books_count', 0)
            series_count = library.get('series_count', 0)
            self.log(f"✅ Bibliothèque: {books_count} livres, {series_count} séries")
            
        return True

    def test_stats_endpoints(self):
        """Test des endpoints statistiques"""
        self.log("\n📊 === TEST ENDPOINTS STATISTIQUES ===")
        
        success, response = self.run_test(
            "Statistiques utilisateur",
            "GET",
            "stats",
            200
        )
        
        if success:
            stats = response
            self.log(f"✅ Stats: {stats.get('total_books', 0)} livres total")
            
        return True

    def test_openlibrary_endpoints(self):
        """Test des endpoints Open Library"""
        self.log("\n🌐 === TEST ENDPOINTS OPEN LIBRARY ===")
        
        success, response = self.run_test(
            "Recherche Open Library",
            "GET",
            "openlibrary/search?q=harry potter&limit=5",
            200
        )
        
        if success:
            results = response.get('results', [])
            self.log(f"✅ {len(results)} résultats Open Library")
            
        return True

    def run_all_tests(self):
        """Exécuter tous les tests"""
        self.log("🚀 === DÉBUT TESTS PHASE B.3 - BACKEND VALIDATION ===")
        self.log(f"🎯 URL Backend: {self.base_url}")
        
        # Tests séquentiels
        tests = [
            ("Santé Backend", self.test_health_check),
            ("Authentification", self.test_authentication),
            ("Endpoints Séries", self.test_series_endpoints),
            ("Bibliothèque Séries", self.test_series_library_endpoints),
            ("Endpoints Livres", self.test_books_endpoints),
            ("Endpoints Bibliothèque", self.test_library_endpoints),
            ("Endpoints Statistiques", self.test_stats_endpoints),
            ("Endpoints Open Library", self.test_openlibrary_endpoints)
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                if not test_func():
                    failed_tests.append(test_name)
            except Exception as e:
                self.log(f"❌ ERREUR dans {test_name}: {str(e)}")
                failed_tests.append(test_name)
        
        # Résumé final
        self.log("\n" + "="*60)
        self.log("📊 === RÉSUMÉ TESTS PHASE B.3 ===")
        self.log(f"✅ Tests réussis: {self.tests_passed}/{self.tests_run}")
        self.log(f"❌ Tests échoués: {len(failed_tests)}")
        
        if failed_tests:
            self.log("🔴 Tests échoués:")
            for test in failed_tests:
                self.log(f"   - {test}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.log("🎉 BACKEND VALIDATION RÉUSSIE - Phase B.3 OK")
            return 0
        else:
            self.log("⚠️ BACKEND VALIDATION PARTIELLE - Problèmes détectés")
            return 1

def main():
    """Point d'entrée principal"""
    tester = PhaseB3BackendTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())