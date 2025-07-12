#!/usr/bin/env python3
"""
Script pour créer des livres Harry Potter pour l'utilisateur Test User
et tester le masquage des vignettes
"""

import requests
import json

# Configuration
BACKEND_URL = "https://e9f1d2bf-e80d-4695-805f-09976ca1a870.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def get_token():
    """Obtenir un token d'authentification"""
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "first_name": "Test",
            "last_name": "User"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"⚠️ Tentative de création utilisateur...")
            requests.post(f"{API_URL}/auth/register", json={
                "first_name": "Test", 
                "last_name": "User"
            })
            response = requests.post(f"{API_URL}/auth/login", json={
                "first_name": "Test",
                "last_name": "User"
            })
            if response.status_code == 200:
                return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
    return None

def create_harry_potter_books():
    """Créer les 7 tomes Harry Potter pour tester le masquage"""
    token = get_token()
    if not token:
        print("❌ Impossible d'obtenir un token")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Livres Harry Potter avec saga
    harry_potter_books = [
        {
            "title": "Harry Potter à l'école des sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "saga": "Harry Potter",
            "volume_number": 1,
            "description": "Le premier tome de la saga Harry Potter",
            "status": "completed",
            "total_pages": 320,
            "cover_url": "https://images-na.ssl-images-amazon.com/images/I/51HSkTKlauL._SX195_.jpg"
        },
        {
            "title": "Harry Potter et la Chambre des secrets",
            "author": "J.K. Rowling",
            "category": "roman",
            "saga": "Harry Potter",
            "volume_number": 2,
            "description": "Le deuxième tome de la saga Harry Potter",
            "status": "completed",
            "total_pages": 368,
            "cover_url": "https://images-na.ssl-images-amazon.com/images/I/51jNORv6nQL._SX195_.jpg"
        },
        {
            "title": "Harry Potter et le Prisonnier d'Azkaban",
            "author": "J.K. Rowling",
            "category": "roman",
            "saga": "Harry Potter",
            "volume_number": 3,
            "description": "Le troisième tome de la saga Harry Potter",
            "status": "reading",
            "total_pages": 448,
            "current_page": 200
        },
        {
            "title": "Harry Potter et la Coupe de feu",
            "author": "J.K. Rowling",
            "category": "roman",
            "saga": "Harry Potter",
            "volume_number": 4,
            "description": "Le quatrième tome de la saga Harry Potter",
            "status": "to_read",
            "total_pages": 768
        },
        {
            "title": "Harry Potter et l'Ordre du phénix",
            "author": "J.K. Rowling",
            "category": "roman",
            "saga": "Harry Potter",
            "volume_number": 5,
            "description": "Le cinquième tome de la saga Harry Potter",
            "status": "to_read",
            "total_pages": 960
        }
    ]
    
    # Quelques livres standalone pour tester le contraste
    standalone_books = [
        {
            "title": "L'Étranger",
            "author": "Albert Camus",
            "category": "roman",
            "description": "Roman philosophique d'Albert Camus",
            "status": "completed",
            "total_pages": 186
        },
        {
            "title": "1984",
            "author": "George Orwell", 
            "category": "roman",
            "description": "Dystopie d'Orwell",
            "status": "to_read",
            "total_pages": 368
        }
    ]
    
    print("🧙 Création des livres Harry Potter pour tester le masquage...")
    print("=" * 60)
    
    created_books = []
    
    # Créer les livres Harry Potter (DOIVENT être masqués)
    for book in harry_potter_books:
        try:
            response = requests.post(f"{API_URL}/books", headers=headers, json=book)
            if response.status_code == 200:
                created_book = response.json()
                created_books.append(created_book)
                print(f"✅ {book['title']} - Volume {book['volume_number']} | Saga: '{book['saga']}'")
            else:
                print(f"❌ Erreur création {book['title']}: {response.status_code}")
                print(f"   Détail: {response.text}")
        except Exception as e:
            print(f"❌ Exception {book['title']}: {e}")
    
    print("\n📖 Création des livres standalone pour contraste...")
    print("=" * 60)
    
    # Créer les livres standalone (DOIVENT être affichés)
    for book in standalone_books:
        try:
            response = requests.post(f"{API_URL}/books", headers=headers, json=book)
            if response.status_code == 200:
                created_book = response.json()
                created_books.append(created_book)
                print(f"✅ {book['title']} | Saga: AUCUNE (standalone)")
            else:
                print(f"❌ Erreur création {book['title']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception {book['title']}: {e}")
    
    return len(created_books) > 0

def verify_masking_logic():
    """Vérifier que les livres sont correctement créés et analyser la logique de masquage"""
    token = get_token()
    if not token:
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Vérification des livres créés...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_URL}/books?limit=20", headers=headers)
        if response.status_code != 200:
            print(f"❌ Erreur récupération livres: {response.status_code}")
            return False
        
        data = response.json()
        books = data.get('items', [])
        
        print(f"📚 TOTAL LIVRES TROUVÉS: {len(books)}")
        print("=" * 60)
        
        series_books = []
        standalone_books = []
        harry_potter_books = []
        
        for book in books:
            title = book.get('title', 'Titre inconnu')
            saga = book.get('saga', '')
            
            print(f"\n📖 {title}")
            print(f"   🏷️ Saga: '{saga}' (Type: {type(saga)})")
            print(f"   📋 Statut: {book.get('status', 'N/A')}")
            print(f"   🔢 Volume: {book.get('volume_number', 'N/A')}")
            
            # Test de la logique de masquage
            belongs_to_series = bool(saga and str(saga).strip())
            print(f"   🎯 APPARTIENT À UNE SÉRIE: {belongs_to_series}")
            
            if belongs_to_series:
                series_books.append(book)
                if 'harry potter' in str(saga).lower():
                    harry_potter_books.append(book)
                print(f"   ➡️ ACTION: SERA MASQUÉ (regroupé dans vignette série)")
            else:
                standalone_books.append(book)
                print(f"   ➡️ ACTION: SERA AFFICHÉ (vignette individuelle)")
        
        print(f"\n🎯 RÉSUMÉ LOGIQUE DE MASQUAGE:")
        print("=" * 60)
        print(f"📚 Livres avec saga (MASQUÉS): {len(series_books)}")
        print(f"📖 Livres standalone (AFFICHÉS): {len(standalone_books)}")
        print(f"⚡ Livres Harry Potter (MASQUÉS): {len(harry_potter_books)}")
        
        if harry_potter_books:
            print(f"\n🧙 DÉTAIL LIVRES HARRY POTTER (doivent être masqués):")
            for book in harry_potter_books:
                print(f"   - {book.get('title')} | Volume {book.get('volume_number', '?')}")
        
        # Prédiction résultat masquage
        print(f"\n🔮 PRÉDICTION INTERFACE:")
        print("=" * 60)
        print(f"✅ DEVRAIT AFFICHER: 1 vignette série 'Harry Potter' (grande)")
        print(f"✅ DEVRAIT AFFICHER: {len(standalone_books)} vignettes livres individuels")
        print(f"❌ NE DEVRAIT PAS AFFICHER: {len(harry_potter_books)} vignettes Harry Potter individuelles")
        
        return len(harry_potter_books) > 0
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

if __name__ == "__main__":
    print("🎯 SESSION 81.2 - Test masquage vignettes série Harry Potter")
    print("=" * 60)
    
    # Étape 1: Créer les livres de test
    success = create_harry_potter_books()
    if not success:
        print("❌ Échec création des livres")
        exit(1)
    
    print("\n" + "="*60)
    
    # Étape 2: Vérifier la logique
    success = verify_masking_logic()
    if success:
        print(f"\n🎉 LIVRES CRÉÉS AVEC SUCCÈS!")
        print(f"🔗 Testez maintenant sur: {BACKEND_URL}")
        print(f"👤 Utilisateur: Test User")
        print(f"🎯 Attendu: 1 vignette série Harry Potter + livres standalone")
    else:
        print(f"\n❌ Problème lors de la vérification")