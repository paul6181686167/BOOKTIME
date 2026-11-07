#!/usr/bin/env python3
"""
Test des nouvelles APIs d'enrichissement d'images
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:8001"
TEST_USER = {
    "first_name": "Test",
    "last_name": "User"
}

def get_auth_token():
    """Obtenir un token d'authentification"""
    try:
        # Essayer de se connecter
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            # Créer le compte s'il n'existe pas
            response = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
            if response.status_code == 200:
                return response.json()["access_token"]
            else:
                print(f"❌ Erreur authentification: {response.status_code}")
                print(response.text)
                return None
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def test_image_apis():
    """Tester les APIs d'enrichissement d'images"""
    print("🧪 Test des APIs d'enrichissement d'images")
    print("=" * 50)
    
    # Obtenir le token
    token = get_auth_token()
    if not token:
        print("❌ Impossible d'obtenir un token")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Statut d'enrichissement
    print("\n1. 📊 Test statut enrichissement...")
    try:
        response = requests.get(f"{BASE_URL}/api/series/images/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statut: {data}")
        else:
            print(f"❌ Erreur statut: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Enrichissement échantillon
    print("\n2. 🎯 Test enrichissement échantillon...")
    try:
        response = requests.get(f"{BASE_URL}/api/series/enrich/sample?count=3", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Échantillon enrichi: {data['enriched_count']}/{data['total_count']}")
            
            # Afficher quelques séries avec images
            for series in data.get('series', [])[:3]:
                name = series.get('name', 'Unknown')
                has_image = bool(series.get('cover_url'))
                print(f"   📖 {name}: {'✅' if has_image else '❌'}")
                if has_image:
                    print(f"      🔗 {series['cover_url']}")
        else:
            print(f"❌ Erreur échantillon: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Enrichissement série unique
    print("\n3. 📚 Test enrichissement série unique...")
    try:
        test_series = {
            "name": "Tintin",
            "authors": ["Hergé"],
            "category": "bd",
            "volumes": 24
        }
        
        response = requests.post(f"{BASE_URL}/api/series/enrich/single", 
                               headers=headers, 
                               json=test_series)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Série enrichie: {data}")
        else:
            print(f"❌ Erreur série unique: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n✅ Tests terminés")

if __name__ == "__main__":
    test_image_apis()