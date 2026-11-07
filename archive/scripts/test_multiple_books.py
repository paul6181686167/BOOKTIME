#!/usr/bin/env python3
"""
Test de traduction avec plusieurs livres anglophones
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def get_auth_token():
    """Obtenir un token d'authentification"""
    user_data = {"first_name": "Test", "last_name": "User"}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=user_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_multiple_books():
    """Tester la traduction avec plusieurs livres"""
    token = get_auth_token()
    if not token:
        print("❌ Impossible de s'authentifier")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    test_books = [
        "Lord of the Rings",
        "Pride and Prejudice", 
        "To Kill a Mockingbird"
    ]
    
    for book_title in test_books:
        print(f"\n🔍 Test avec: {book_title}")
        
        response = requests.get(
            f"{BASE_URL}/api/openlibrary/search-universal?q={book_title}&limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('books'):
                book = data['books'][0]
                work_key = book.get('work_key')
                
                if work_key:
                    detail_response = requests.get(
                        f"{BASE_URL}/api/openlibrary/book/{work_key}",
                        headers=headers
                    )
                    
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        description = details.get('description', '')
                        
                        if description:
                            print(f"📝 Description traduite: {description[:150]}...")
                            
                            # Vérification simple si c'est en français
                            french_words = ['le', 'la', 'les', 'un', 'une', 'et', 'dans', 'avec', 'pour']
                            desc_lower = description.lower()
                            french_count = sum(1 for word in french_words if f' {word} ' in f' {desc_lower} ')
                            
                            if french_count >= 2:
                                print("✅ Semble être en français!")
                            else:
                                print(f"⚠️ Peut-être pas entièrement en français (score: {french_count})")
                        else:
                            print("ℹ️ Pas de description disponible")
                    else:
                        print(f"❌ Erreur détails: {detail_response.status_code}")
                else:
                    print("ℹ️ Pas de work_key disponible")
        else:
            print(f"❌ Erreur recherche: {response.status_code}")

if __name__ == "__main__":
    test_multiple_books()