#!/usr/bin/env python3
"""
Test de confirmation du problème exclude_series
"""
import requests
import json

# Configuration
BACKEND_URL = "https://b09342c8-9dc0-484d-b070-5d26209b0bbb.preview.emergentagent.com"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MGYxM2VhOS03MzZlLTRiYWQtYTdjZC1hNWYwZGQwNmU1OWQiLCJleHAiOjE3NTIxNTI1OTN9.55uecngVVunkozOPlbrF-jn92P_znD_8Q5ORWrDOWqE"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

def test_books_endpoints():
    """Test des différents endpoints books"""
    print("=== CONFIRMATION DU PROBLÈME exclude_series ===")
    
    # Test 1: GET /api/books (exclut les séries)
    print("\n1. GET /api/books (exclude_series=True par défaut):")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Items count: {len(data.get('items', []))}")
            print(f"Total: {data.get('total', 0)}")
            if data.get('items'):
                print("Premier livre:")
                print(f"  - Titre: {data['items'][0].get('title')}")
                print(f"  - Saga: '{data['items'][0].get('saga', '')}'")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Erreur: {e}")
    
    # Test 2: GET /api/books/all (inclut tous les livres)
    print("\n2. GET /api/books/all (exclude_series=False):")
    try:
        response = requests.get(f"{BACKEND_URL}/api/books/all", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Items count: {len(data.get('items', []))}")
            print(f"Total: {data.get('total', 0)}")
            if data.get('items'):
                print("Livres trouvés:")
                for i, book in enumerate(data['items'][:3]):  # Afficher les 3 premiers
                    print(f"  {i+1}. Titre: {book.get('title')}")
                    print(f"     Auteur: {book.get('author')}")
                    print(f"     Saga: '{book.get('saga', '')}'")
                    print(f"     Catégorie: {book.get('category')}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Erreur: {e}")

def main():
    test_books_endpoints()

if __name__ == "__main__":
    main()