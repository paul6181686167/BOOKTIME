#!/usr/bin/env python3
"""
Tests backend pour le système de chapitres individuels BOOKTIME
==============================================================

Tests complets des 10 nouveaux endpoints du système de chapitres :
1. GET /api/chapters/health - Health check du module chapters
2. GET /api/chapters/series/{series_name} - Récupérer chapitres d'une série  
3. POST /api/chapters/series/{series_name}/refresh - Forcer rafraîchissement données série
4. GET /api/chapters/releases/upcoming - Planning sorties à venir
5. GET /api/chapters/user/stats - Statistiques utilisateur chapitres
6. GET /api/chapters/search/{series_name} - Rechercher série dans APIs externes
7. POST /api/chapters/series/{series_name}/map-ids - Mapper série aux IDs externes
8. GET /api/chapters/integrations/status - Statut intégrations externes
9. PUT /api/chapters/predictions/config - Configuration prédictions
10. GET /api/chapters/debug/series/{series_name} - Debug données série

Série de test suggérée : "One Piece" (AniList ID 30013)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BACKEND_URL = "https://changelog-reader-9.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
TEST_SERIES = "One Piece"
TEST_USER_DATA = {
    "first_name": "Chapter",
    "last_name": "Tester"
}

class ChapterSystemTester:
    """Testeur pour le système de chapitres individuels"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user_token = None
        self.test_results = []
        self.start_time = time.time()
        
    def log_test(self, endpoint: str, method: str, status: str, details: str = "", response_time: float = 0):
        """Enregistre un résultat de test"""
        self.test_results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        })
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {method} {endpoint} - {status} ({response_time:.2f}s)")
        if details:
            print(f"   └─ {details}")
    
    def authenticate_user(self) -> bool:
        """Authentifie un utilisateur de test"""
        try:
            print("\n🔐 AUTHENTIFICATION UTILISATEUR")
            print("=" * 50)
            
            # Essayer de se connecter d'abord
            auth_url = f"{API_BASE}/auth/login"
            response = self.session.post(auth_url, json=TEST_USER_DATA, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("access_token")
                if self.user_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
                    print(f"✅ Utilisateur connecté: {TEST_USER_DATA['first_name']} {TEST_USER_DATA['last_name']}")
                    return True
            
            # Si la connexion échoue, essayer de créer l'utilisateur
            if response.status_code == 400:
                print("👤 Utilisateur non trouvé, création en cours...")
                register_url = f"{API_BASE}/auth/register"
                response = self.session.post(register_url, json=TEST_USER_DATA, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.user_token = data.get("access_token")
                    if self.user_token:
                        self.session.headers.update({"Authorization": f"Bearer {self.user_token}"})
                        print(f"✅ Utilisateur créé et authentifié: {TEST_USER_DATA['first_name']} {TEST_USER_DATA['last_name']}")
                        return True
            
            print(f"❌ Échec authentification: {response.status_code} - {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Erreur authentification: {str(e)}")
            return False
    
    def test_health_check(self) -> bool:
        """Test 1: GET /api/chapters/health - Health check du module chapters"""
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/chapters/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["status", "module", "features"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("/api/chapters/health", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                if data["status"] != "ok" or data["module"] != "chapters":
                    self.log_test("/api/chapters/health", "GET", "FAIL", 
                                f"Status: {data['status']}, Module: {data['module']}", response_time)
                    return False
                
                if "series_chapters" not in data["features"]:
                    self.log_test("/api/chapters/health", "GET", "FAIL", 
                                "Feature 'series_chapters' manquante", response_time)
                    return False
                
                self.log_test("/api/chapters/health", "GET", "PASS", 
                            f"Module chapters opérationnel avec {len(data['features'])} features", response_time)
                return True
            else:
                self.log_test("/api/chapters/health", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("/api/chapters/health", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_get_series_chapters(self) -> bool:
        """Test 2: GET /api/chapters/series/{series_name} - Récupérer chapitres d'une série"""
        try:
            start_time = time.time()
            url = f"{API_BASE}/chapters/series/{TEST_SERIES}"
            response = self.session.get(url, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["success", "data", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                if not data["success"]:
                    self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "FAIL", 
                                f"Success=False: {data.get('message', 'No message')}", response_time)
                    return False
                
                series_data = data["data"]
                if "series_name" not in series_data:
                    self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "FAIL", 
                                "Données série manquantes", response_time)
                    return False
                
                self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "PASS", 
                            f"Série '{series_data['series_name']}' récupérée", response_time)
                return True
                
            elif response.status_code == 404:
                # 404 acceptable si la série n'existe pas encore
                self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "PASS", 
                            f"Série non trouvée (404) - comportement attendu", response_time)
                return True
            else:
                self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"/api/chapters/series/{TEST_SERIES}", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_refresh_series_chapters(self) -> bool:
        """Test 3: POST /api/chapters/series/{series_name}/refresh - Forcer rafraîchissement"""
        try:
            start_time = time.time()
            url = f"{API_BASE}/chapters/series/{TEST_SERIES}/refresh"
            response = self.session.post(url, timeout=20)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test(f"/api/chapters/series/{TEST_SERIES}/refresh", "POST", "FAIL", 
                                f"Success=False: {data.get('message', 'No message')}", response_time)
                    return False
                
                self.log_test(f"/api/chapters/series/{TEST_SERIES}/refresh", "POST", "PASS", 
                            f"Rafraîchissement réussi: {data.get('message', '')}", response_time)
                return True
                
            elif response.status_code == 400:
                # 400 acceptable si impossible de rafraîchir
                self.log_test(f"/api/chapters/series/{TEST_SERIES}/refresh", "POST", "PASS", 
                            f"Rafraîchissement impossible (400) - comportement attendu", response_time)
                return True
            else:
                self.log_test(f"/api/chapters/series/{TEST_SERIES}/refresh", "POST", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"/api/chapters/series/{TEST_SERIES}/refresh", "POST", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_get_upcoming_releases(self) -> bool:
        """Test 4: GET /api/chapters/releases/upcoming - Planning sorties à venir"""
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/chapters/releases/upcoming", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["this_week", "next_week", "this_month"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("/api/chapters/releases/upcoming", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                # Vérifier que ce sont des listes
                for field in required_fields:
                    if not isinstance(data[field], list):
                        self.log_test("/api/chapters/releases/upcoming", "GET", "FAIL", 
                                    f"Champ '{field}' n'est pas une liste", response_time)
                        return False
                
                total_releases = len(data["this_week"]) + len(data["next_week"]) + len(data["this_month"])
                self.log_test("/api/chapters/releases/upcoming", "GET", "PASS", 
                            f"Planning récupéré: {total_releases} sorties prévues", response_time)
                return True
            else:
                self.log_test("/api/chapters/releases/upcoming", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("/api/chapters/releases/upcoming", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_get_user_stats(self) -> bool:
        """Test 5: GET /api/chapters/user/stats - Statistiques utilisateur chapitres"""
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/chapters/user/stats", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["success", "user_id", "stats"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("/api/chapters/user/stats", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                if not data["success"]:
                    self.log_test("/api/chapters/user/stats", "GET", "FAIL", 
                                "Success=False", response_time)
                    return False
                
                stats = data["stats"]
                expected_stats = ["chapters_read_this_week", "series_following", "predictions_accuracy"]
                missing_stats = [stat for stat in expected_stats if stat not in stats]
                
                if missing_stats:
                    self.log_test("/api/chapters/user/stats", "GET", "FAIL", 
                                f"Stats manquantes: {missing_stats}", response_time)
                    return False
                
                self.log_test("/api/chapters/user/stats", "GET", "PASS", 
                            f"Stats utilisateur: {len(stats)} métriques", response_time)
                return True
            else:
                self.log_test("/api/chapters/user/stats", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("/api/chapters/user/stats", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_search_series_in_apis(self) -> bool:
        """Test 6: GET /api/chapters/search/{series_name} - Rechercher série dans APIs externes"""
        try:
            start_time = time.time()
            url = f"{API_BASE}/chapters/search/{TEST_SERIES}"
            response = self.session.get(url, timeout=20)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["anilist_matches", "mangaupdates_matches", "confidence_scores"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"/api/chapters/search/{TEST_SERIES}", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                # Vérifier que ce sont des listes/dict
                if not isinstance(data["anilist_matches"], list):
                    self.log_test(f"/api/chapters/search/{TEST_SERIES}", "GET", "FAIL", 
                                "anilist_matches n'est pas une liste", response_time)
                    return False
                
                if not isinstance(data["confidence_scores"], dict):
                    self.log_test(f"/api/chapters/search/{TEST_SERIES}", "GET", "FAIL", 
                                "confidence_scores n'est pas un dict", response_time)
                    return False
                
                total_matches = len(data["anilist_matches"]) + len(data["mangaupdates_matches"])
                self.log_test(f"/api/chapters/search/{TEST_SERIES}", "GET", "PASS", 
                            f"Recherche réussie: {total_matches} résultats trouvés", response_time)
                return True
            else:
                self.log_test(f"/api/chapters/search/{TEST_SERIES}", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"/api/chapters/search/{TEST_SERIES}", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_map_series_ids(self) -> bool:
        """Test 7: POST /api/chapters/series/{series_name}/map-ids - Mapper série aux IDs externes"""
        try:
            start_time = time.time()
            url = f"{API_BASE}/chapters/series/{TEST_SERIES}/map-ids"
            
            # Données de test (One Piece sur AniList)
            mapping_data = {
                "anilist_id": 30013,
                "mangaupdates_id": 319
            }
            
            response = self.session.post(url, json=mapping_data, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test(f"/api/chapters/series/{TEST_SERIES}/map-ids", "POST", "FAIL", 
                                f"Success=False: {data.get('message', 'No message')}", response_time)
                    return False
                
                # Vérifier les IDs mappés
                mapped_ids = data.get("mapped_ids", {})
                if mapped_ids.get("anilist_id") != 30013:
                    self.log_test(f"/api/chapters/series/{TEST_SERIES}/map-ids", "POST", "FAIL", 
                                f"AniList ID incorrect: {mapped_ids.get('anilist_id')}", response_time)
                    return False
                
                self.log_test(f"/api/chapters/series/{TEST_SERIES}/map-ids", "POST", "PASS", 
                            f"Mapping réussi: AniList={mapped_ids.get('anilist_id')}, MU={mapped_ids.get('mangaupdates_id')}", response_time)
                return True
                
            elif response.status_code == 400:
                # 400 acceptable si mapping impossible
                self.log_test(f"/api/chapters/series/{TEST_SERIES}/map-ids", "POST", "PASS", 
                            f"Mapping impossible (400) - comportement attendu", response_time)
                return True
            else:
                self.log_test(f"/api/chapters/series/{TEST_SERIES}/map-ids", "POST", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"/api/chapters/series/{TEST_SERIES}/map-ids", "POST", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_get_integrations_status(self) -> bool:
        """Test 8: GET /api/chapters/integrations/status - Statut intégrations externes"""
        try:
            start_time = time.time()
            response = self.session.get(f"{API_BASE}/chapters/integrations/status", timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["success", "integrations"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test("/api/chapters/integrations/status", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                if not data["success"]:
                    self.log_test("/api/chapters/integrations/status", "GET", "FAIL", 
                                "Success=False", response_time)
                    return False
                
                integrations = data["integrations"]
                if not isinstance(integrations, dict):
                    self.log_test("/api/chapters/integrations/status", "GET", "FAIL", 
                                "integrations n'est pas un dict", response_time)
                    return False
                
                # Vérifier les intégrations attendues
                expected_integrations = ["anilist", "mangaupdates"]
                found_integrations = [name for name in expected_integrations if name in integrations]
                
                self.log_test("/api/chapters/integrations/status", "GET", "PASS", 
                            f"Statut intégrations: {len(found_integrations)} services vérifiés", response_time)
                return True
            else:
                self.log_test("/api/chapters/integrations/status", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("/api/chapters/integrations/status", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_update_predictions_config(self) -> bool:
        """Test 9: PUT /api/chapters/predictions/config - Configuration prédictions"""
        try:
            start_time = time.time()
            url = f"{API_BASE}/chapters/predictions/config"
            
            # Configuration de test
            config_data = {
                "enable_predictions": True,
                "confidence_threshold": 0.85
            }
            
            response = self.session.put(url, json=config_data, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("success"):
                    self.log_test("/api/chapters/predictions/config", "PUT", "FAIL", 
                                f"Success=False: {data.get('message', 'No message')}", response_time)
                    return False
                
                # Vérifier la configuration retournée
                config = data.get("config", {})
                if config.get("enable_predictions") != True:
                    self.log_test("/api/chapters/predictions/config", "PUT", "FAIL", 
                                f"enable_predictions incorrect: {config.get('enable_predictions')}", response_time)
                    return False
                
                if config.get("confidence_threshold") != 0.85:
                    self.log_test("/api/chapters/predictions/config", "PUT", "FAIL", 
                                f"confidence_threshold incorrect: {config.get('confidence_threshold')}", response_time)
                    return False
                
                self.log_test("/api/chapters/predictions/config", "PUT", "PASS", 
                            f"Configuration mise à jour: predictions={config.get('enable_predictions')}, threshold={config.get('confidence_threshold')}", response_time)
                return True
            else:
                self.log_test("/api/chapters/predictions/config", "PUT", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("/api/chapters/predictions/config", "PUT", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_debug_series_data(self) -> bool:
        """Test 10: GET /api/chapters/debug/series/{series_name} - Debug données série"""
        try:
            start_time = time.time()
            url = f"{API_BASE}/chapters/debug/series/{TEST_SERIES}"
            response = self.session.get(url, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifications de structure
                required_fields = ["success", "debug_info"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "FAIL", 
                                f"Champs manquants: {missing_fields}", response_time)
                    return False
                
                if not data["success"]:
                    self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "FAIL", 
                                "Success=False", response_time)
                    return False
                
                debug_info = data["debug_info"]
                if "series_name" not in debug_info:
                    self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "FAIL", 
                                "series_name manquant dans debug_info", response_time)
                    return False
                
                if debug_info["series_name"] != TEST_SERIES:
                    self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "FAIL", 
                                f"series_name incorrect: {debug_info['series_name']}", response_time)
                    return False
                
                cache_status = debug_info.get("cache_status", "unknown")
                chapters_count = debug_info.get("chapters_count", 0)
                
                self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "PASS", 
                            f"Debug réussi: cache={cache_status}, chapitres={chapters_count}", response_time)
                return True
            else:
                self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "FAIL", 
                            f"Status code: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test(f"/api/chapters/debug/series/{TEST_SERIES}", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def test_authentication_required(self) -> bool:
        """Test que l'authentification est requise pour les endpoints protégés"""
        try:
            # Sauvegarder le token actuel
            current_token = self.session.headers.get("Authorization")
            
            # Supprimer l'authentification
            if "Authorization" in self.session.headers:
                del self.session.headers["Authorization"]
            
            # Tester un endpoint protégé
            response = self.session.get(f"{API_BASE}/chapters/series/{TEST_SERIES}", timeout=10)
            
            # Restaurer l'authentification
            if current_token:
                self.session.headers["Authorization"] = current_token
            
            # Accepter 401 ou 403 comme codes d'erreur valides pour l'authentification
            if response.status_code in [401, 403]:
                self.log_test("Authentication Required", "GET", "PASS", 
                            f"Authentification correctement requise (code: {response.status_code})", 0)
                return True
            else:
                self.log_test("Authentication Required", "GET", "FAIL", 
                            f"Status code: {response.status_code} (attendu: 401 ou 403)", 0)
                return False
                
        except Exception as e:
            self.log_test("Authentication Required", "GET", "FAIL", f"Exception: {str(e)}", 0)
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests du système de chapitres"""
        print("\n🧪 TESTS BACKEND - SYSTÈME CHAPITRES INDIVIDUELS BOOKTIME")
        print("=" * 70)
        print(f"📍 Backend URL: {BACKEND_URL}")
        print(f"🎯 Série de test: {TEST_SERIES}")
        print(f"👤 Utilisateur test: {TEST_USER_DATA['first_name']} {TEST_USER_DATA['last_name']}")
        print()
        
        # Authentification
        if not self.authenticate_user():
            return {"success": False, "error": "Échec authentification"}
        
        print("\n🔍 TESTS DES ENDPOINTS CHAPITRES")
        print("=" * 50)
        
        # Liste des tests à exécuter
        tests = [
            ("Health Check", self.test_health_check),
            ("Get Series Chapters", self.test_get_series_chapters),
            ("Refresh Series Chapters", self.test_refresh_series_chapters),
            ("Get Upcoming Releases", self.test_get_upcoming_releases),
            ("Get User Stats", self.test_get_user_stats),
            ("Search Series in APIs", self.test_search_series_in_apis),
            ("Map Series IDs", self.test_map_series_ids),
            ("Get Integrations Status", self.test_get_integrations_status),
            ("Update Predictions Config", self.test_update_predictions_config),
            ("Debug Series Data", self.test_debug_series_data),
            ("Authentication Required", self.test_authentication_required)
        ]
        
        passed = 0
        failed = 0
        total_response_time = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: EXCEPTION - {str(e)}")
                failed += 1
        
        # Calcul du temps de réponse moyen
        if self.test_results:
            total_response_time = sum(r["response_time"] for r in self.test_results if r["response_time"] > 0)
            avg_response_time = total_response_time / len([r for r in self.test_results if r["response_time"] > 0])
        else:
            avg_response_time = 0
        
        total_time = time.time() - self.start_time
        
        print("\n📊 RÉSULTATS FINAUX")
        print("=" * 40)
        print(f"✅ Tests réussis: {passed}")
        print(f"❌ Tests échoués: {failed}")
        print(f"📈 Taux de succès: {(passed/(passed+failed))*100:.1f}%")
        print(f"⏱️  Temps total: {total_time:.2f}s")
        print(f"⚡ Temps de réponse moyen: {avg_response_time:.2f}s")
        
        # Vérification des performances
        performance_ok = avg_response_time < 2.0
        if performance_ok:
            print("🚀 Performance: EXCELLENTE (< 2s par endpoint)")
        else:
            print(f"⚠️  Performance: LENTE ({avg_response_time:.2f}s par endpoint)")
        
        # Résumé des problèmes
        failed_tests = [r for r in self.test_results if r["status"] == "FAIL"]
        if failed_tests:
            print("\n❌ TESTS ÉCHOUÉS:")
            for test in failed_tests:
                print(f"   • {test['method']} {test['endpoint']}: {test['details']}")
        
        success = failed == 0
        if success:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
            print("✅ Le système de chapitres individuels est opérationnel")
        else:
            print(f"\n⚠️  {failed} TEST(S) ONT ÉCHOUÉ")
            print("❌ Le système de chapitres nécessite des corrections")
        
        return {
            "success": success,
            "passed": passed,
            "failed": failed,
            "total_time": total_time,
            "avg_response_time": avg_response_time,
            "performance_ok": performance_ok,
            "test_results": self.test_results
        }


def main():
    """Point d'entrée principal"""
    tester = ChapterSystemTester()
    results = tester.run_all_tests()
    
    # Code de sortie
    exit_code = 0 if results["success"] else 1
    exit(exit_code)


if __name__ == "__main__":
    main()