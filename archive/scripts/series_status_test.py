#!/usr/bin/env python3
"""
BOOKTIME - Test Backend Complet
Test des fonctionnalités de changement de statut des séries
Focus sur la correction RCA des boutons de statut série
"""

import requests
import sys
import json
from datetime import datetime
import time

class BookTimeAPITester:
    def __init__(self, base_url="https://changelog-reader-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_books = []  # Pour nettoyer après les tests

    def log(self, message, level="INFO"):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Exécuter un test API"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Test {self.tests_run}: {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASS - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                self.log(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAIL - Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test de santé de l'API"""
        self.log("🏥 Test de santé de l'API")
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success

    def test_register_or_login_user(self):
        """Créer un utilisateur de test ou utiliser un existant"""
        import random
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        test_user = {
            "username": f"test_series_{timestamp}_{random_suffix}",
            "email": f"test_series_{timestamp}_{random_suffix}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Series"
        }
        
        self.log(f"👤 Tentative création utilisateur: {test_user['username']}")
        success, response = self.run_test(
            "Register User",
            "POST",
            "api/auth/register",
            200,
            test_user
        )
        
        if not success:
            # Si l'utilisateur existe déjà, essayer de se connecter
            self.log("👤 Utilisateur existe, tentative de connexion")
            if self.test_login(test_user['username'], test_user['password']):
                return True, test_user
            else:
                # Essayer avec un utilisateur de test générique
                test_user = {
                    "username": "testuser",
                    "email": "test@example.com", 
                    "password": "testpass",
                    "first_name": "Test",
                    "last_name": "User"
                }
                self.log("👤 Tentative avec utilisateur générique")
                return True, test_user
        
        if success:
            self.user_id = response.get('user', {}).get('id')
            self.log(f"✅ Utilisateur créé avec ID: {self.user_id}")
        
        return success, test_user

    def test_login(self, username, password):
        """Test de connexion"""
        self.log(f"🔐 Connexion utilisateur: {username}")
        success, response = self.run_test(
            "Login",
            "POST",
            "api/auth/login",
            200,
            {"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log(f"✅ Token obtenu: {self.token[:20]}...")
            return True
        return False

    def test_series_search(self):
        """Test de recherche de séries"""
        self.log("🔍 Test recherche de séries")
        
        # Test recherche Harry Potter
        success, response = self.run_test(
            "Search Harry Potter Series",
            "GET",
            "api/series/search?q=Harry Potter",
            200
        )
        
        if success:
            series_found = len(response.get('series', []))
            self.log(f"📚 Séries trouvées: {series_found}")
            
            # Retourner la première série Harry Potter trouvée
            for series in response.get('series', []):
                if 'harry' in series.get('name', '').lower():
                    self.log(f"🎯 Série sélectionnée: {series['name']}")
                    return True, series
        
        return False, None

    def test_add_series_to_library(self, series):
        """Test d'ajout d'une série à la bibliothèque"""
        if not series:
            return False, None
            
        self.log(f"➕ Ajout série à la bibliothèque: {series['name']}")
        
        # Créer un livre "série" avec statut "À lire"
        series_book = {
            "title": series['name'],
            "author": series.get('authors', ['Auteur inconnu'])[0],
            "category": series.get('category', 'roman'),
            "description": f"Collection {series['name']} - {series.get('volumes', 0)} tome(s)",
            "saga": series['name'],
            "volume_number": None,
            "status": "to_read",
            "cover_url": series.get('cover_url', ''),
            "total_pages": None,
            "is_series": True
        }
        
        success, response = self.run_test(
            "Add Series to Library",
            "POST",
            "api/books",
            201,
            series_book
        )
        
        if success:
            book_id = response.get('id')
            self.created_books.append(book_id)
            self.log(f"✅ Série ajoutée avec ID: {book_id}")
            return True, response
        
        return False, None

    def test_check_series_ownership(self, series_name):
        """Test de vérification de possession de série"""
        self.log(f"🔍 Vérification possession série: {series_name}")
        
        success, response = self.run_test(
            "Check Series Ownership",
            "GET",
            f"api/books/all?saga={requests.utils.quote(series_name)}",
            200
        )
        
        if success:
            items = response.get('items', [])
            self.log(f"📚 Livres trouvés: {len(items)}")
            
            # Chercher le livre série avec la logique corrigée (case-insensitive substring)
            series_book = None
            for book in items:
                book_saga = book.get('saga', '').lower()
                if series_name.lower() in book_saga and (book.get('is_series') or 'collection' in book.get('title', '').lower()):
                    series_book = book
                    break
            
            if series_book:
                self.log(f"✅ Série trouvée: {series_book['title']} (Status: {series_book.get('status')})")
                return True, series_book
            else:
                self.log(f"❌ Série non trouvée dans la bibliothèque")
                return False, None
        
        return False, None

    def test_change_series_status(self, series_book, new_status):
        """Test de changement de statut de série"""
        if not series_book:
            return False
            
        book_id = series_book.get('id')
        self.log(f"🔄 Changement statut série vers: {new_status}")
        
        success, response = self.run_test(
            f"Change Series Status to {new_status}",
            "PUT",
            f"api/books/{book_id}",
            200,
            {"status": new_status}
        )
        
        if success:
            updated_status = response.get('status')
            self.log(f"✅ Statut mis à jour: {updated_status}")
            return success
        
        return False

    def test_series_status_workflow(self):
        """Test complet du workflow de changement de statut des séries"""
        self.log("🎯 DÉBUT TEST WORKFLOW STATUT SÉRIE")
        
        # 1. Rechercher une série
        success, series = self.test_series_search()
        if not success:
            self.log("❌ Échec recherche série")
            return False
        
        # 2. Ajouter la série à la bibliothèque
        success, series_book = self.test_add_series_to_library(series)
        if not success:
            self.log("❌ Échec ajout série")
            return False
        
        # 3. Vérifier que la série est bien possédée
        success, owned_series = self.test_check_series_ownership(series['name'])
        if not success:
            self.log("❌ Série non trouvée après ajout")
            return False
        
        # 4. Tester les changements de statut
        statuses = ['reading', 'completed', 'to_read']
        for status in statuses:
            success = self.test_change_series_status(owned_series, status)
            if not success:
                self.log(f"❌ Échec changement vers {status}")
                return False
            
            # Vérifier que le changement a bien été appliqué
            time.sleep(0.5)  # Petite pause pour la cohérence
            success, updated_series = self.test_check_series_ownership(series['name'])
            if success and updated_series.get('status') == status:
                self.log(f"✅ Statut {status} confirmé")
            else:
                self.log(f"❌ Statut {status} non confirmé")
                return False
        
        self.log("🎯 WORKFLOW STATUT SÉRIE TERMINÉ AVEC SUCCÈS")
        return True

    def cleanup(self):
        """Nettoyer les données de test"""
        self.log("🧹 Nettoyage des données de test")
        
        for book_id in self.created_books:
            try:
                self.run_test(
                    f"Delete Book {book_id}",
                    "DELETE",
                    f"api/books/{book_id}",
                    200
                )
            except:
                pass

    def run_all_tests(self):
        """Exécuter tous les tests"""
        self.log("🚀 DÉBUT DES TESTS BACKEND BOOKTIME")
        self.log("=" * 60)
        
        try:
            # Test de santé
            if not self.test_health_check():
                self.log("❌ API non disponible")
                return False
            
            # Création et connexion utilisateur
            success, test_user = self.test_register_or_login_user()
            if not success:
                self.log("❌ Échec création utilisateur")
                return False
            
            if not self.test_login(test_user['username'], test_user['password']):
                self.log("❌ Échec connexion")
                return False
            
            # Test principal: workflow statut série
            if not self.test_series_status_workflow():
                self.log("❌ Échec workflow principal")
                return False
            
            self.log("=" * 60)
            self.log(f"🎉 TESTS TERMINÉS: {self.tests_passed}/{self.tests_run} réussis")
            
            if self.tests_passed == self.tests_run:
                self.log("✅ TOUS LES TESTS SONT PASSÉS!")
                return True
            else:
                self.log(f"❌ {self.tests_run - self.tests_passed} test(s) échoué(s)")
                return False
                
        except Exception as e:
            self.log(f"❌ Erreur générale: {str(e)}")
            return False
        finally:
            self.cleanup()

def main():
    """Point d'entrée principal"""
    tester = BookTimeAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())