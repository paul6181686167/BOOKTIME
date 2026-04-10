#!/usr/bin/env python3
"""
Test Phase B - Intégration userSeriesLibrary dans Affichage
Validation que les séries de la bibliothèque apparaissent dans l'interface
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

def create_test_user():
    """Créer un utilisateur de test pour Phase B"""
    try:
        login_data = {
            "first_name": "TestPhaseB",
            "last_name": "User"
        }
        
        # Tentative de connexion
        response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            print("✅ Utilisateur TestPhaseB connecté")
            return response.json()['access_token']
        else:
            # Créer l'utilisateur
            register_response = requests.post(f"{BACKEND_URL}/api/auth/register", json=login_data)
            if register_response.status_code == 200:
                print("✅ Utilisateur TestPhaseB créé et connecté")
                return register_response.json()['access_token']
            else:
                print("❌ Erreur création utilisateur:", register_response.text)
                return None
                
    except Exception as e:
        print(f"❌ Erreur authentification: {e}")
        return None

def test_add_series_to_library(token):
    """Test B.1: Ajouter une série à la bibliothèque"""
    print("\n📋 TEST B.1: Ajout série bibliothèque")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    test_series = {
        "series_name": "Test Phase B Series",
        "authors": ["Test Author B"],
        "category": "roman",
        "total_volumes": 5,
        "volumes": [
            {"volume_number": 1, "volume_title": "Tome 1", "is_read": False},
            {"volume_number": 2, "volume_title": "Tome 2", "is_read": True},
            {"volume_number": 3, "volume_title": "Tome 3", "is_read": False},
            {"volume_number": 4, "volume_title": "Tome 4", "is_read": False},
            {"volume_number": 5, "volume_title": "Tome 5", "is_read": False}
        ],
        "description_fr": "Série de test pour Phase B - Intégration affichage",
        "series_status": "reading"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/series/library", json=test_series, headers=headers)
        
        if response.status_code == 200:
            print("✅ Série ajoutée à la bibliothèque")
            return True
        elif response.status_code == 409:
            print("⚠️ Série déjà existante (normal si test répété)")
            return True
        else:
            print(f"❌ Erreur ajout série: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test ajout série: {e}")
        return False

def test_series_library_endpoint(token):
    """Test B.2: Vérifier que la série apparaît dans la bibliothèque"""
    print("\n📋 TEST B.2: Vérification série dans bibliothèque")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/series/library", headers=headers)
        
        if response.status_code == 200:
            series_list = response.json()
            
            if isinstance(series_list, list) and len(series_list) > 0:
                test_series = next((s for s in series_list if s.get('series_name') == 'Test Phase B Series'), None)
                
                if test_series:
                    print(f"✅ Série trouvée dans bibliothèque: {test_series['series_name']}")
                    print(f"   - {test_series['total_volumes']} volumes")
                    print(f"   - Statut: {test_series.get('series_status', 'N/A')}")
                    print(f"   - Progression: {test_series.get('completion_percentage', 0)}%")
                    return True
                else:
                    print("❌ Série 'Test Phase B Series' non trouvée")
                    return False
            else:
                print("❌ Aucune série dans la bibliothèque")
                return False
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_add_individual_book(token):
    """Test B.3: Ajouter un livre individuel (pour tester compatibilité)"""
    print("\n📋 TEST B.3: Ajout livre individuel (régression)")
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    test_book = {
        "title": "Livre Test Phase B",
        "author": "Auteur Test B",
        "category": "roman",
        "description": "Livre individuel pour test Phase B"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/books", json=test_book, headers=headers)
        
        if response.status_code == 200:
            print("✅ Livre individuel ajouté")
            return True
        else:
            print(f"❌ Erreur ajout livre: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test livre: {e}")
        return False

def test_frontend_loads():
    """Test B.4: Vérifier que le frontend se charge toujours"""
    print("\n📋 TEST B.4: Frontend se charge correctement")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"❌ Frontend erreur: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur frontend: {e}")
        return False

def main():
    """Test principal Phase B"""
    print("🧪 TESTS VALIDATION PHASE B - INTÉGRATION AFFICHAGE UNIFIÉ")
    print("=" * 65)
    
    # Vérifier backend
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend opérationnel")
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
    
    test_results.append(("Ajout série bibliothèque", test_add_series_to_library(token)))
    test_results.append(("Série dans bibliothèque", test_series_library_endpoint(token)))
    test_results.append(("Livre individuel (régression)", test_add_individual_book(token)))
    test_results.append(("Frontend accessible", test_frontend_loads()))
    
    # Résultats
    print("\n" + "=" * 65)
    print("📊 RÉSULTATS TESTS PHASE B")
    print("=" * 65)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 RÉSUMÉ: {passed}/{total} tests réussis")
    
    if passed == total:
        print("✅ PHASE B.2 - MODIFICATION BACKEND RÉUSSIE")
        print("🔄 Prêt pour tests frontend avec userSeriesLibrary")
    else:
        print("❌ PHASE B.2 - MODIFICATIONS À CORRIGER")
        print("🔧 Vérifier intégration userSeriesLibrary")

if __name__ == "__main__":
    main()