#!/usr/bin/env python3
"""
Script de diagnostic pour analyser la structure des livres dans BOOKTIME
et identifier pourquoi le masquage des séries ne fonctionne pas
"""

import requests
import json
import sys

# Configuration
BACKEND_URL = "https://6efff0cd-ae10-47b6-9f6c-a805e1b2bcd5.preview.emergentagent.com"
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
            # Essayer de créer l'utilisateur
            requests.post(f"{API_URL}/auth/register", json={
                "first_name": "Test", 
                "last_name": "User"
            })
            # Réessayer la connexion
            response = requests.post(f"{API_URL}/auth/login", json={
                "first_name": "Test",
                "last_name": "User"
            })
            if response.status_code == 200:
                return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
    return None

def analyze_books():
    """Analyser tous les livres pour comprendre la structure des séries"""
    token = get_token()
    if not token:
        print("❌ Impossible d'obtenir un token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_URL}/books", headers=headers)
        if response.status_code != 200:
            print(f"❌ Erreur API: {response.status_code}")
            return
            
        books = response.json()
        if isinstance(books, str):
            books = json.loads(books)
        if not isinstance(books, list):
            print(f"❌ Format de données inattendu: {type(books)}")
            print(f"📄 Données reçues: {books}")
            return
        
        # Analyser chaque livre
        series_books = []
        standalone_books = []
        harry_potter_books = []
        
        for book in books:
            title = book.get('title', 'Titre inconnu')
            saga = book.get('saga', '')
            
            print(f"\n📖 LIVRE: {title}")
            print(f"   🏷️  ID: {book.get('id', 'N/A')}")
            print(f"   👤 Auteur: {book.get('author', 'N/A')}")
            print(f"   📚 Saga: '{saga}' (Type: {type(saga)}, Longueur: {len(str(saga))})")
            print(f"   📋 Catégorie: {book.get('category', 'N/A')}")
            print(f"   📊 Statut: {book.get('status', 'N/A')}")
            print(f"   🔢 Volume: {book.get('volume_number', 'N/A')}")
            
            # Tester la logique de masquage
            belongs_to_series = bool(saga and str(saga).strip())
            print(f"   🎯 APPARTIENT À UNE SÉRIE: {belongs_to_series}")
            
            if belongs_to_series:
                series_books.append(book)
                if 'harry potter' in title.lower() or 'harry potter' in str(saga).lower():
                    harry_potter_books.append(book)
            else:
                standalone_books.append(book)
                
            print("   " + "="*50)
        
        # Résumé
        print(f"\n🎯 RÉSUMÉ DE L'ANALYSE:")
        print(f"📚 Livres appartenant à des séries: {len(series_books)}")
        print(f"📖 Livres standalone: {len(standalone_books)}")
        print(f"⚡ Livres Harry Potter détectés: {len(harry_potter_books)}")
        
        if harry_potter_books:
            print(f"\n🧙 DÉTAIL HARRY POTTER:")
            for book in harry_potter_books:
                print(f"   - {book.get('title')}")
                print(f"     Saga: '{book.get('saga')}' | Volume: {book.get('volume_number')}")
        
        # Groupement par saga
        series_groups = {}
        for book in series_books:
            saga_key = str(book.get('saga', '')).lower().strip()
            if saga_key not in series_groups:
                series_groups[saga_key] = []
            series_groups[saga_key].append(book)
        
        print(f"\n📊 SÉRIES DÉTECTÉES ({len(series_groups)}):")
        for saga, books_in_saga in series_groups.items():
            print(f"   📚 '{saga}': {len(books_in_saga)} livre(s)")
            for book in books_in_saga:
                print(f"      - {book.get('title')} (Vol. {book.get('volume_number', '?')})")
                
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")

if __name__ == "__main__":
    analyze_books()