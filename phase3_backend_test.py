#!/usr/bin/env python3
"""
BOOKTIME - Test des fonctionnalités Phase 3.4 et 3.5
- Phase 3.4: Recommandations Avancées avec IA/ML
- Phase 3.5: Intégrations Externes
"""
import requests
import json
import sys
import time
import random
from datetime import datetime

# Configuration
API_BASE_URL = "https://06ad0466-f8dc-45df-9572-d7f90595d8b4.preview.emergentagent.com/api"
TOKEN = None
USER_ID = None

# Couleurs pour la console
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Statistiques des tests
tests_run = 0
tests_passed = 0
tests_failed = 0

def print_header(text):
    """Affiche un en-tête de section"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}== {text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")

def print_subheader(text):
    """Affiche un sous-en-tête"""
    print(f"\n{BLUE}-- {text} --{RESET}\n")

def print_result(success, message):
    """Affiche le résultat d'un test"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1
    
    if success:
        tests_passed += 1
        print(f"{GREEN}✓ SUCCÈS:{RESET} {message}")
    else:
        tests_failed += 1
        print(f"{RED}✗ ÉCHEC:{RESET} {message}")

def print_info(message):
    """Affiche une information"""
    print(f"{YELLOW}ℹ INFO:{RESET} {message}")

def print_summary():
    """Affiche un résumé des tests"""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}== RÉSUMÉ DES TESTS{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"Tests exécutés: {tests_run}")
    print(f"{GREEN}Tests réussis: {tests_passed}{RESET}")
    print(f"{RED}Tests échoués: {tests_failed}{RESET}")
    print(f"Taux de réussite: {(tests_passed / tests_run * 100) if tests_run > 0 else 0:.2f}%")

def make_request(method, endpoint, data=None, params=None, files=None, expected_status=200):
    """Effectue une requête à l'API"""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {}
    
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    if files:
        # Ne pas définir Content-Type pour les requêtes multipart/form-data
        response = requests.request(
            method, 
            url, 
            files=files,
            headers=headers,
            params=params
        )
    else:
        headers["Content-Type"] = "application/json"
        response = requests.request(
            method, 
            url, 
            json=data, 
            headers=headers,
            params=params
        )
    
    success = response.status_code == expected_status
    
    if not success:
        print(f"{RED}Réponse HTTP {response.status_code}:{RESET}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    
    return success, response

def login():
    """Authentification à l'API"""
    print_subheader("Authentification")
    
    # Données de test
    login_data = {
        "username": "testuser",
        "password": "testpassword",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Tentative de connexion
    success, response = make_request("POST", "auth/login", login_data)
    
    if success:
        data = response.json()
        if "access_token" in data:
            global TOKEN, USER_ID
            TOKEN = data["access_token"]
            USER_ID = data.get("user", {}).get("id")
            print_result(True, f"Authentification réussie. Token obtenu.")
            return True
        else:
            print_result(False, "Token non trouvé dans la réponse.")
            return False
    else:
        # Tentative d'inscription si la connexion échoue
        print_info("Tentative d'inscription...")
        register_data = {
            "username": "testuser",
            "password": "testpassword",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        reg_success, reg_response = make_request("POST", "auth/register", register_data, expected_status=201)
        
        if reg_success:
            print_result(True, "Inscription réussie. Tentative de connexion...")
            return login()
        else:
            print_result(False, "Échec de l'inscription et de la connexion.")
            return False

def test_health_endpoints():
    """Teste les endpoints de santé"""
    print_subheader("Endpoints de santé")
    
    # Test de l'endpoint de santé principal
    success, response = make_request("GET", "health")
    print_result(success, "Endpoint de santé principal")
    
    # Test de l'endpoint de santé des recommandations avancées
    success, response = make_request("GET", "recommendations/advanced/health")
    print_result(success, "Endpoint de santé des recommandations avancées")
    
    # Test de l'endpoint de santé des intégrations
    success, response = make_request("GET", "integrations/health")
    print_result(success, "Endpoint de santé des intégrations")

def test_advanced_recommendations():
    """Teste les endpoints de recommandations avancées"""
    print_header("PHASE 3.4 - RECOMMANDATIONS AVANCÉES")
    
    # Test des recommandations contextuelles
    print_subheader("Recommandations contextuelles")
    
    context = {
        "time_of_day": "evening",
        "mood": "relaxed",
        "available_time": 60,
        "location": "home",
        "social_context": "alone",
        "weather": "unknown",
        "reading_goal": "entertainment"
    }
    
    success, response = make_request("POST", "recommendations/advanced/contextual", data=context)
    
    if success:
        data = response.json()
        recommendations = data.get("data", {}).get("recommendations", [])
        print_result(True, f"Récupération de {len(recommendations)} recommandations contextuelles")
        
        if recommendations:
            print_info(f"Exemple de recommandation: {recommendations[0].get('book', {}).get('title', 'N/A')}")
    else:
        print_result(False, "Échec de récupération des recommandations contextuelles")
    
    # Test des recommandations sociales
    print_subheader("Recommandations sociales")
    
    success, response = make_request("GET", "recommendations/advanced/social", params={"limit": 10})
    
    if success:
        data = response.json()
        recommendations = data.get("data", {}).get("recommendations", [])
        print_result(True, f"Récupération de {len(recommendations)} recommandations sociales")
        
        if recommendations:
            print_info(f"Exemple de recommandation: {recommendations[0].get('book', {}).get('title', 'N/A')}")
    else:
        print_result(False, "Échec de récupération des recommandations sociales")
    
    # Test du profil utilisateur avancé
    print_subheader("Profil utilisateur avancé")
    
    success, response = make_request("GET", "recommendations/advanced/user-profile/advanced")
    
    if success:
        data = response.json()
        user_profile = data.get("data", {})
        print_result(True, "Récupération du profil utilisateur avancé")
        
        if user_profile:
            print_info(f"Vitesse de lecture: {user_profile.get('reading_velocity', 'N/A')} livres/mois")
            print_info(f"Clusters comportementaux: {user_profile.get('behavioral_insights', {}).get('behavioral_clusters', [])}")
    else:
        print_result(False, "Échec de récupération du profil utilisateur avancé")
    
    # Test des statistiques ML
    print_subheader("Statistiques ML")
    
    success, response = make_request("GET", "recommendations/advanced/stats/ml")
    
    if success:
        data = response.json()
        ml_stats = data.get("data", {})
        print_result(True, "Récupération des statistiques ML")
        
        if ml_stats:
            models_status = ml_stats.get("models_status", {})
            for model, status in models_status.items():
                print_info(f"Modèle {model}: {'Chargé' if status.get('loaded') else 'Non chargé'}")
    else:
        print_result(False, "Échec de récupération des statistiques ML")
    
    # Test de prédiction de rating
    print_subheader("Prédiction de rating")
    
    # Récupérer un livre pour tester la prédiction
    success, response = make_request("GET", "books", params={"limit": 1})
    
    if success:
        books = response.json()
        if isinstance(books, list) and len(books) > 0:
            book_id = books[0].get("_id") or books[0].get("id")
            
            if book_id:
                success, response = make_request("GET", "recommendations/advanced/ml/predict-rating", params={"book_id": book_id})
                
                if success:
                    data = response.json()
                    prediction = data.get("data", {})
                    print_result(True, f"Prédiction de rating pour le livre {book_id}")
                    
                    if prediction:
                        print_info(f"Rating prédit: {prediction.get('predicted_rating', 'N/A')}")
                        print_info(f"Confiance: {prediction.get('confidence', 'N/A')}")
                else:
                    print_result(False, "Échec de prédiction de rating")
            else:
                print_result(False, "Impossible de trouver un ID de livre pour tester la prédiction")
        else:
            print_result(False, "Aucun livre trouvé pour tester la prédiction")
    else:
        print_result(False, "Échec de récupération des livres pour tester la prédiction")

def test_external_integrations():
    """Teste les endpoints d'intégrations externes"""
    print_header("PHASE 3.5 - INTÉGRATIONS EXTERNES")
    
    # Test de recherche Google Books
    print_subheader("Recherche Google Books")
    
    search_terms = ["Harry Potter", "Dune", "Foundation", "Neuromancer"]
    search_term = random.choice(search_terms)
    
    success, response = make_request("GET", "integrations/google-books/search", params={"query": search_term, "max_results": 5})
    
    if success:
        data = response.json()
        books = data.get("data", {}).get("books", [])
        print_result(True, f"Recherche Google Books pour '{search_term}': {len(books)} résultats")
        
        if books:
            print_info(f"Premier résultat: {books[0].get('title', 'N/A')} par {books[0].get('author', 'N/A')}")
            
            # Test de récupération des détails d'un livre
            if "google_id" in books[0]:
                volume_id = books[0]["google_id"]
                
                success, response = make_request("GET", f"integrations/google-books/details/{volume_id}")
                
                if success:
                    data = response.json()
                    book_details = data.get("data", {}).get("book", {})
                    print_result(True, f"Récupération des détails du livre {volume_id}")
                    
                    if book_details:
                        print_info(f"Titre: {book_details.get('title', 'N/A')}")
                        print_info(f"Auteur: {book_details.get('author', 'N/A')}")
                else:
                    print_result(False, "Échec de récupération des détails du livre")
    else:
        print_result(False, f"Échec de recherche Google Books pour '{search_term}'")
    
    # Test de recherche combinée
    print_subheader("Recherche combinée")
    
    success, response = make_request("GET", "integrations/combined-search", params={
        "query": search_term,
        "sources": "google_books",
        "max_results_per_source": 5
    })
    
    if success:
        data = response.json()
        books = data.get("data", {}).get("books", [])
        print_result(True, f"Recherche combinée pour '{search_term}': {len(books)} résultats")
        
        if books:
            print_info(f"Premier résultat: {books[0].get('title', 'N/A')} par {books[0].get('author', 'N/A')}")
    else:
        print_result(False, f"Échec de recherche combinée pour '{search_term}'")
    
    # Test des statistiques d'intégrations
    print_subheader("Statistiques d'intégrations")
    
    success, response = make_request("GET", "integrations/stats")
    
    if success:
        data = response.json()
        stats = data.get("data", {})
        print_result(True, "Récupération des statistiques d'intégrations")
        
        if stats:
            integrations = stats.get("supported_integrations", [])
            print_info(f"Intégrations supportées: {len(integrations)}")
            
            for integration in integrations:
                print_info(f"- {integration.get('name', 'N/A')} ({integration.get('type', 'N/A')}): {integration.get('status', 'N/A')}")
    else:
        print_result(False, "Échec de récupération des statistiques d'intégrations")

def main():
    """Fonction principale"""
    print_header("TESTS BOOKTIME - PHASE 3.4 & 3.5")
    
    # Authentification
    if not login():
        print(f"{RED}Impossible de continuer sans authentification.{RESET}")
        return 1
    
    # Test des endpoints de santé
    test_health_endpoints()
    
    # Test des recommandations avancées
    test_advanced_recommendations()
    
    # Test des intégrations externes
    test_external_integrations()
    
    # Affichage du résumé
    print_summary()
    
    return 0 if tests_failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())