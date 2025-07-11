#!/usr/bin/env python3
"""
Test complémentaire pour vérifier les fonctionnalités CRUD de base
"""

import requests
import json
import uuid
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://8c8b9cc8-8549-4c1c-a355-e2de2cd1dbe0.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def log_test(test_name, status, details=""):
    """Log des résultats de test"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {test_name}")
    if details:
        print(f"   {details}")
    return status

def test_crud_operations():
    """Test des opérations CRUD de base"""
    try:
        # Register a test user
        unique_id = str(uuid.uuid4())[:8]
        test_user = {
            "first_name": f"TestCRUD{unique_id}",
            "last_name": "Operations"
        }
        
        register_response = requests.post(f"{API_BASE}/auth/register", json=test_user, timeout=10)
        
        if register_response.status_code != 200:
            return log_test("CRUD Operations", False, "Failed to register user")
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test CREATE - Add a book
        test_book = {
            "title": "Test Book CRUD",
            "author": "Test Author",
            "category": "roman",
            "description": "A test book for CRUD operations"
        }
        
        create_response = requests.post(f"{API_BASE}/books", json=test_book, headers=headers, timeout=10)
        
        if create_response.status_code != 200:
            return log_test("CRUD Operations", False, f"Failed to create book: {create_response.status_code}")
        
        book_data = create_response.json()
        book_id = book_data["id"]
        
        # Test READ - Get the book
        read_response = requests.get(f"{API_BASE}/books/{book_id}", headers=headers, timeout=10)
        
        if read_response.status_code != 200:
            return log_test("CRUD Operations", False, f"Failed to read book: {read_response.status_code}")
        
        # Test UPDATE - Update the book
        update_data = {"status": "reading", "current_page": 50}
        update_response = requests.put(f"{API_BASE}/books/{book_id}", json=update_data, headers=headers, timeout=10)
        
        if update_response.status_code != 200:
            return log_test("CRUD Operations", False, f"Failed to update book: {update_response.status_code}")
        
        # Test DELETE - Delete the book
        delete_response = requests.delete(f"{API_BASE}/books/{book_id}", headers=headers, timeout=10)
        
        if delete_response.status_code != 200:
            return log_test("CRUD Operations", False, f"Failed to delete book: {delete_response.status_code}")
        
        return log_test("CRUD Operations", True, "Create, Read, Update, Delete all successful")
        
    except Exception as e:
        return log_test("CRUD Operations", False, f"Exception: {str(e)}")

def test_search_functionality():
    """Test de la fonctionnalité de recherche"""
    try:
        # Register a test user
        unique_id = str(uuid.uuid4())[:8]
        test_user = {
            "first_name": f"TestSearch{unique_id}",
            "last_name": "Functionality"
        }
        
        register_response = requests.post(f"{API_BASE}/auth/register", json=test_user, timeout=10)
        
        if register_response.status_code != 200:
            return log_test("Search Functionality", False, "Failed to register user")
        
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test OpenLibrary search
        search_response = requests.get(f"{API_BASE}/openlibrary/search?q=harry potter&limit=3", headers=headers, timeout=15)
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            if "books" in search_data and len(search_data["books"]) > 0:
                return log_test("Search Functionality", True, f"OpenLibrary search returned {len(search_data['books'])} results")
            else:
                return log_test("Search Functionality", False, "OpenLibrary search returned no results")
        else:
            return log_test("Search Functionality", False, f"OpenLibrary search failed: {search_response.status_code}")
        
    except Exception as e:
        return log_test("Search Functionality", False, f"Exception: {str(e)}")

def main():
    """Fonction principale de test complémentaire"""
    print("🔍 Tests complémentaires des fonctionnalités principales")
    print("=" * 60)
    
    results = []
    
    # Test CRUD operations
    results.append(test_crud_operations())
    
    # Test search functionality
    results.append(test_search_functionality())
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS COMPLÉMENTAIRES")
    print("=" * 60)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"Tests réussis: {success_count}/{total_count}")
    print(f"Taux de réussite: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 TOUS LES TESTS COMPLÉMENTAIRES SONT PASSÉS!")
        return True
    else:
        print("⚠️  Certains tests complémentaires ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)