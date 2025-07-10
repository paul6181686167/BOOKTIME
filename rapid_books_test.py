#!/usr/bin/env python3
"""
Test rapide pour l'endpoint /api/books - Investigation du problème de séries non retournées
"""
import requests
import json
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://eb6d8796-4140-48cc-ae5a-ffd6c9e0d24c.preview.emergentagent.com"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MGYxM2VhOS03MzZlLTRiYWQtYTdjZC1hNWYwZGQwNmU1OWQiLCJleHAiOjE3NTIxNTI1OTN9.55uecngVVunkozOPlbrF-jn92P_znD_8Q5ORWrDOWqE"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def test_books_endpoint():
    """Test l'endpoint /api/books avec différents paramètres"""
    print("=== TEST ENDPOINT /api/books ===")
    
    # Test 1: GET /api/books basique
    print("\n1. Test GET /api/books basique:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Items count: {len(data.get('items', []))}")
            print(f"Total: {data.get('total', 0)}")
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 2: GET /api/books avec limit
    print("\n2. Test GET /api/books avec limit=50:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books?limit=50", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 3: GET /api/books avec view_mode=series
    print("\n3. Test GET /api/books avec view_mode=series:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books?view_mode=series", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 4: GET /api/books avec différents formats
    print("\n4. Test GET /api/books avec format=json:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books?format=json", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")

def test_series_endpoints():
    """Test les endpoints liés aux séries"""
    print("\n=== TEST ENDPOINTS SÉRIES ===")
    
    # Test 1: GET /api/series/library
    print("\n1. Test GET /api/series/library:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/series/library", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")

def test_stats_endpoint():
    """Test l'endpoint des statistiques"""
    print("\n=== TEST ENDPOINT /api/stats ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/stats", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total books: {data.get('total_books', 0)}")
            print(f"Categories: {data.get('categories', {})}")
        
    except Exception as e:
        print(f"Erreur: {e}")

def test_openlibrary_import():
    """Test d'ajout d'un livre via OpenLibrary pour comparaison"""
    print("\n=== TEST AJOUT LIVRE VIA OPENLIBRARY ===")
    
    # Test d'import d'un livre simple
    print("\n1. Test import d'un livre Harry Potter:")
    try:
        import_data = {
            "ol_key": "OL82563W",  # Harry Potter à l'école des sorciers
            "category": "roman"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/openlibrary/import", 
                               headers=headers, 
                               json=import_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Vérifier si le livre apparaît maintenant
    print("\n2. Vérification GET /api/books après import:")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")

def test_direct_book_creation():
    """Test de création directe d'un livre"""
    print("\n=== TEST CRÉATION DIRECTE LIVRE ===")
    
    try:
        book_data = {
            "title": "Test Book Direct",
            "author": "Test Author",
            "category": "roman",
            "status": "to_read"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/books", 
                               headers=headers, 
                               json=book_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Vérifier si le livre apparaît
        print("\nVérification GET /api/books après création directe:")
        response = requests.get(f"{BACKEND_URL}/api/books", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Erreur: {e}")

def main():
    """Fonction principale de test"""
    print(f"=== TEST RAPIDE /api/books - {datetime.now()} ===")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"JWT Token: {JWT_TOKEN[:50]}...")
    
    # Tests dans l'ordre logique
    test_stats_endpoint()
    test_books_endpoint()
    test_series_endpoints()
    test_direct_book_creation()
    test_openlibrary_import()
    
    print("\n=== FIN DES TESTS ===")

if __name__ == "__main__":
    main()