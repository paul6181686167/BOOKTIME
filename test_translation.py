#!/usr/bin/env python3
"""
Script de test pour vérifier la traduction des résumés en français
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8001"

def register_test_user():
    """Créer un utilisateur de test"""
    user_data = {
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    elif response.status_code == 400:
        # Utilisateur existe déjà, essayons de se connecter
        response = requests.post(f"{BASE_URL}/api/auth/login", json=user_data)
        if response.status_code == 200:
            return response.json()["access_token"]
    
    print(f"Erreur lors de l'authentification: {response.text}")
    return None

def test_translation():
    """Tester la traduction des résumés"""
    token = register_test_user()
    if not token:
        print("Impossible de s'authentifier")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Test de recherche OpenLibrary avec traduction...")
    
    # Rechercher un livre anglophone populaire
    response = requests.get(
        f"{BASE_URL}/api/openlibrary/search-universal?q=Harry Potter and the Philosopher's Stone&limit=1",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Recherche réussie! Livres trouvés: {len(data.get('books', []))}")
        
        if data.get('books'):
            book = data['books'][0]
            print(f"📖 Livre: {book.get('title', 'N/A')}")
            print(f"✍️ Auteur: {book.get('author', 'N/A')}")
            print(f"🔑 Work Key: {book.get('work_key', 'N/A')}")
            
            # Tester les détails du livre avec traduction
            if book.get('work_key'):
                print(f"\n🔍 Test des détails du livre avec traduction...")
                detail_response = requests.get(
                    f"{BASE_URL}/api/openlibrary/book/{book['work_key']}",
                    headers=headers
                )
                
                if detail_response.status_code == 200:
                    details = detail_response.json()
                    description = details.get('description', '')
                    first_sentence = details.get('first_sentence', '')
                    
                    print(f"📝 Description traduite: {description[:200]}..." if len(description) > 200 else f"📝 Description traduite: {description}")
                    if first_sentence:
                        print(f"🥇 Première phrase traduite: {first_sentence[:200]}..." if len(first_sentence) > 200 else f"🥇 Première phrase traduite: {first_sentence}")
                    
                    # Vérifier si la traduction a bien eu lieu
                    french_indicators = ['le', 'la', 'les', 'un', 'une', 'des', 'et', 'avec', 'dans', 'pour']
                    description_lower = description.lower()
                    french_found = any(f' {word} ' in f' {description_lower} ' for word in french_indicators)
                    
                    if french_found:
                        print("✅ La description semble être en français!")
                    else:
                        print("⚠️ La description ne semble pas être en français...")
                        
                    return True
                else:
                    print(f"❌ Erreur lors de la récupération des détails: {detail_response.text}")
                    return False
        else:
            print("❌ Aucun livre trouvé")
            return False
    else:
        print(f"❌ Erreur lors de la recherche: {response.text}")
        return False

if __name__ == "__main__":
    success = test_translation()
    sys.exit(0 if success else 1)