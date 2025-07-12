#!/usr/bin/env python3
"""
Test simple pour vérifier la structure des réponses API
"""
import requests
import json

# Configuration
BACKEND_URL = "https://65d53dfa-2f5a-4168-bc0c-06e70f6dc95a.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def test_api_structure():
    print("🔍 Test de la structure des APIs")
    
    # Créer un utilisateur de test
    user_data = {
        "first_name": "TestStructure",
        "last_name": "User"
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"❌ Erreur création utilisateur: {response.status_code}")
        return
    
    result = response.json()
    auth_token = result["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    print(f"✅ Utilisateur créé: {result['user']['first_name']}")
    
    # Test 1: Structure de la recherche Open Library
    print("\n📚 Test structure Open Library Search:")
    response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&limit=1", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"Structure: {list(data.keys())}")
        if data.get('books'):
            print(f"Structure livre: {list(data['books'][0].keys())}")
    
    # Test 2: Structure de l'import Open Library
    print("\n📥 Test structure Open Library Import:")
    # D'abord chercher un livre
    search_response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&limit=1", headers=headers)
    if search_response.status_code == 200:
        search_data = search_response.json()
        if search_data.get('books'):
            ol_key = search_data['books'][0]['ol_key']
            import_data = {"ol_key": ol_key, "category": "roman"}
            
            response = requests.post(f"{API_URL}/openlibrary/import", json=import_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"Structure import: {list(data.keys())}")
                if data.get('book'):
                    print(f"Structure livre importé: {list(data['book'].keys())}")
                    book_id = data['book']['id']
                    
                    # Test 3: Structure de l'API Books
                    print("\n📋 Test structure API Books:")
                    response = requests.get(f"{API_URL}/books", headers=headers)
                    if response.status_code == 200:
                        books_data = response.json()
                        print(f"Structure books API: {type(books_data)} - {list(books_data.keys()) if isinstance(books_data, dict) else 'Liste'}")
                        
                        if isinstance(books_data, dict) and books_data.get('items'):
                            print(f"Structure livre dans items: {list(books_data['items'][0].keys()) if books_data['items'] else 'Aucun livre'}")
                        elif isinstance(books_data, list) and books_data:
                            print(f"Structure livre dans liste: {list(books_data[0].keys())}")
                    
                    # Nettoyage
                    requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
                    print(f"✅ Livre supprimé: {book_id}")

if __name__ == "__main__":
    test_api_structure()