#!/usr/bin/env python3
"""
Test Phase A - Unification Système Ajout Séries
Validation que le nouveau système series unifié fonctionne correctement
"""

import asyncio
import json
import requests
import time
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

def create_test_user():
    """Créer un utilisateur de test"""
    try:
        # Tentative de connexion
        login_data = {
            "first_name": "Test",
            "last_name": "PhaseA"
        }
        
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            print("✅ Utilisateur Test PhaseA connecté")
            return response.json()['access_token']
        else:
            # Créer l'utilisateur
            register_response = requests.post(f"{BACKEND_URL}/api/auth/register", json=login_data)
            if register_response.status_code == 200:
                print("✅ Utilisateur Test PhaseA créé et connecté")
                return register_response.json()['access_token']
            else:
                print("❌ Erreur création utilisateur:", register_response.text)
                return None
                
    except Exception as e:
        print(f"❌ Erreur authentification: {e}")
        return None

def test_series_library_endpoint(token):
    """Test 1: Vérifier endpoints série fonctionnels"""
    print("\n📋 TEST 1: Endpoints série fonctionnels")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        # Test GET /api/series/library
        response = requests.get(f"{BACKEND_URL}/api/series/library", headers=headers)
        if response.status_code == 200:
            data = response.json()
            # L'API retourne une liste directement, pas un objet avec une clé 'series'
            series_count = len(data) if isinstance(data, list) else 0
            print(f"✅ GET /api/series/library : {series_count} séries")
            return True
        else:
            print(f"❌ GET /api/series/library failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test endpoints: {e}")
        return False

def test_add_series_via_api(token):
    """Test 2: Ajouter série via API backend directement"""
    print("\n📋 TEST 2: Ajout série via API backend")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Données de test série
    test_series = {
        "series_name": "Test Phase A Series",
        "authors": ["Test Author"],
        "category": "roman",
        "total_volumes": 3,
        "volumes": [
            {"volume_number": 1, "volume_title": "Tome 1", "is_read": False},
            {"volume_number": 2, "volume_title": "Tome 2", "is_read": False},
            {"volume_number": 3, "volume_title": "Tome 3", "is_read": False}
        ],
        "description_fr": "Série de test pour Phase A",
        "series_status": "to_read"
    }
    
    try:
        # Ajouter la série
        response = requests.post(f"{BACKEND_URL}/api/series/library", json=test_series, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Série ajoutée via API: {data.get('message', 'Success')}")
            
            # Vérifier présence dans la liste
            check_response = requests.get(f"{BACKEND_URL}/api/series/library", headers=headers)
            if check_response.status_code == 200:
                series_list = check_response.json().get('series', [])
                found = any(s['series_name'] == "Test Phase A Series" for s in series_list)
                
                if found:
                    print("✅ Série trouvée dans la liste après ajout")
                    return True
                else:
                    print("❌ Série non trouvée dans la liste")
                    return False
            else:
                print("❌ Erreur vérification liste")
                return False
                
        elif response.status_code == 409:
            print("⚠️ Série déjà existante (normal si test répété)")
            return True
        else:
            print(f"❌ Erreur ajout série: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test ajout série: {e}")
        return False

def test_books_api_still_works(token):
    """Test 3: Vérifier que l'API books fonctionne toujours (régression)"""
    print("\n📋 TEST 3: API livres individuels (régression)")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Données de test livre individuel
    test_book = {
        "title": "Test Book Phase A",
        "author": "Test Author",
        "category": "roman",
        "description": "Livre de test pour vérifier régression Phase A"
    }
    
    try:
        # Ajouter le livre
        response = requests.post(f"{BACKEND_URL}/api/books", json=test_book, headers=headers)
        
        if response.status_code == 200:
            print("✅ Livre individuel ajouté via API books")
            
            # Vérifier présence dans la liste
            check_response = requests.get(f"{BACKEND_URL}/api/books", headers=headers)
            if check_response.status_code == 200:
                books_list = check_response.json()
                found = any(b['title'] == "Test Book Phase A" for b in books_list)
                
                if found:
                    print("✅ Livre trouvé dans la liste")
                    return True
                else:
                    print("❌ Livre non trouvé dans la liste")
                    return False
            else:
                print("❌ Erreur vérification liste livres")
                return False
                
        else:
            print(f"❌ Erreur ajout livre: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test livres: {e}")
        return False

def test_frontend_accessibility():
    """Test 4: Vérifier que le frontend est accessible"""
    print("\n📋 TEST 4: Accessibilité frontend")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200 and "BookTime" in response.text:
            print("✅ Frontend accessible et fonctionnel")
            return True
        else:
            print(f"❌ Frontend non accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test frontend: {e}")
        return False

def main():
    """Test principal Phase A"""
    print("🧪 TESTS VALIDATION PHASE A - UNIFICATION SYSTÈME SÉRIES")
    print("=" * 60)
    
    # Vérifier services
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend en ligne")
        else:
            print("❌ Backend non accessible")
            return
    except:
        print("❌ Backend non accessible")
        return
    
    # Créer utilisateur de test
    token = create_test_user()
    if not token:
        print("❌ Impossible de créer utilisateur de test")
        return
    
    # Exécuter les tests
    test_results = []
    
    test_results.append(("Endpoints série", test_series_library_endpoint(token)))
    test_results.append(("Ajout série API", test_add_series_via_api(token)))
    test_results.append(("API livres (régression)", test_books_api_still_works(token)))
    test_results.append(("Frontend accessible", test_frontend_accessibility()))
    
    # Résultats
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS TESTS PHASE A")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RÉSUMÉ: {passed}/{total} tests réussis")
    
    if passed == total:
        print("✅ PHASE A.3 - VALIDATION RÉUSSIE")
        print("🔄 Prêt pour Phase B - Intégration affichage unifié")
    else:
        print("❌ PHASE A.3 - VALIDATION ÉCHOUÉE")
        print("🔧 Corrections nécessaires avant Phase B")

if __name__ == "__main__":
    main()