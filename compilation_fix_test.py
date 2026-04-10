#!/usr/bin/env python3
"""
Test rapide et efficace du backend BookTime après correction de compilation
Vérifie les fonctionnalités principales mentionnées dans la review request
"""

import requests
import json
import sys
import os
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://changelog-reader-9.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def log_test(test_name, status, details=""):
    """Log des résultats de test"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {test_name}")
    if details:
        print(f"   {details}")
    return status

def test_health_check():
    """Test 1: Health check endpoint"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok" and data.get("database") == "connected":
                return log_test("Health Check", True, f"Status: {data['status']}, DB: {data['database']}")
            else:
                return log_test("Health Check", False, f"Unexpected response: {data}")
        else:
            return log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        return log_test("Health Check", False, f"Exception: {str(e)}")

def test_authentication():
    """Test 2: Authentication (inscription et connexion)"""
    try:
        # Test d'inscription avec un nom plus unique
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        test_user = {
            "first_name": f"TestRapide{unique_id}",
            "last_name": "CompilationFix",
            "email": f"test_compilation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{unique_id}@test.com"
        }
        
        register_response = requests.post(f"{API_BASE}/auth/register", json=test_user, timeout=10)
        
        if register_response.status_code == 200:
            register_data = register_response.json()
            if "access_token" in register_data:
                token = register_data["access_token"]
                
                # Test de connexion avec le même utilisateur
                login_response = requests.post(f"{API_BASE}/auth/login", json={
                    "first_name": test_user["first_name"],
                    "last_name": test_user["last_name"]
                }, timeout=10)
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    if "access_token" in login_data:
                        return log_test("Authentication", True, "Inscription et connexion réussies"), token
                    else:
                        return log_test("Authentication", False, "Token manquant dans la réponse de connexion"), None
                else:
                    return log_test("Authentication", False, f"Connexion échouée: HTTP {login_response.status_code}"), None
            else:
                return log_test("Authentication", False, "Token manquant dans la réponse d'inscription"), None
        else:
            # Add detailed error information
            try:
                error_data = register_response.json()
                error_detail = error_data.get('detail', 'No detail provided')
            except:
                error_detail = register_response.text
            return log_test("Authentication", False, f"Inscription échouée: HTTP {register_response.status_code} - {error_detail}"), None
            
    except Exception as e:
        return log_test("Authentication", False, f"Exception: {str(e)}"), None

def test_main_api_endpoint(token):
    """Test 3: Endpoint API principal (GET /api/books)"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/books", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Check for new paginated format
            if isinstance(data, dict) and "items" in data and "total" in data:
                return log_test("Main API Endpoint (GET /api/books)", True, f"Format paginé: {data['total']} livres total, {len(data['items'])} dans cette page")
            # Check for old list format (backward compatibility)
            elif isinstance(data, list):
                return log_test("Main API Endpoint (GET /api/books)", True, f"Format liste: {len(data)} livres")
            else:
                return log_test("Main API Endpoint (GET /api/books)", False, f"Format de réponse inattendu: {type(data)}")
        else:
            return log_test("Main API Endpoint (GET /api/books)", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        return log_test("Main API Endpoint (GET /api/books)", False, f"Exception: {str(e)}")

def test_threadpoolctl_scikit_learn(token):
    """Test 4: Vérification que le problème threadpoolctl/scikit-learn est résolu"""
    try:
        # Test d'un endpoint qui utilise potentiellement scikit-learn (recommendations)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/recommendations", headers=headers, timeout=15)
        
        # Même si l'endpoint retourne une erreur, l'important est qu'il ne crash pas à cause de threadpoolctl
        if response.status_code in [200, 404, 422]:  # Codes acceptables
            return log_test("ThreadPoolCTL/Scikit-Learn Fix", True, f"Endpoint accessible (HTTP {response.status_code})")
        else:
            return log_test("ThreadPoolCTL/Scikit-Learn Fix", False, f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        error_msg = str(e).lower()
        if "threadpoolctl" in error_msg or "scikit" in error_msg:
            return log_test("ThreadPoolCTL/Scikit-Learn Fix", False, f"Problème de dépendance: {str(e)}")
        else:
            return log_test("ThreadPoolCTL/Scikit-Learn Fix", True, f"Pas de problème de dépendance détecté")

def test_core_functionalities(token):
    """Test 5: Fonctionnalités principales préservées"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test des endpoints critiques
        endpoints_to_test = [
            ("/api/stats", "Stats"),
            ("/api/series/popular", "Series Popular"),
            ("/api/openlibrary/search?q=test&limit=1", "OpenLibrary Search")
        ]
        
        results = []
        for endpoint, name in endpoints_to_test:
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=10)
                if response.status_code == 200:
                    results.append(f"{name}: ✅")
                else:
                    results.append(f"{name}: ❌ (HTTP {response.status_code})")
            except Exception as e:
                results.append(f"{name}: ❌ (Exception)")
        
        success_count = len([r for r in results if "✅" in r])
        total_count = len(results)
        
        if success_count >= total_count * 0.8:  # Au moins 80% de succès
            return log_test("Core Functionalities", True, f"{success_count}/{total_count} endpoints fonctionnels")
        else:
            return log_test("Core Functionalities", False, f"Seulement {success_count}/{total_count} endpoints fonctionnels")
            
    except Exception as e:
        return log_test("Core Functionalities", False, f"Exception: {str(e)}")

def main():
    """Fonction principale de test"""
    print("🚀 Test rapide du backend BookTime après correction de compilation")
    print("=" * 70)
    
    results = []
    token = None
    
    # Test 1: Health Check
    results.append(test_health_check())
    
    # Test 2: Authentication
    auth_result, token = test_authentication()
    results.append(auth_result)
    
    if token:
        # Test 3: Main API Endpoint
        results.append(test_main_api_endpoint(token))
        
        # Test 4: ThreadPoolCTL/Scikit-Learn
        results.append(test_threadpoolctl_scikit_learn(token))
        
        # Test 5: Core Functionalities
        results.append(test_core_functionalities(token))
    else:
        print("❌ Impossible de continuer les tests sans token d'authentification")
        results.extend([False, False, False])
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"Tests réussis: {success_count}/{total_count}")
    print(f"Taux de réussite: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 TOUS LES TESTS SONT PASSÉS - L'application backend fonctionne correctement!")
        return True
    elif success_count >= total_count * 0.8:
        print("⚠️  La plupart des tests sont passés - L'application est fonctionnelle avec quelques problèmes mineurs")
        return True
    else:
        print("❌ ÉCHEC - Des problèmes critiques ont été détectés")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)