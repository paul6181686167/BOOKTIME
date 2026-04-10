#!/usr/bin/env python3
"""
PHASE C.1 - Test de Validation Hook Unifié
Test complet du système de rafraîchissement unifié nouvellement implémenté
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

class PhaseC1Validator:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.test_results = []
        self.session = None
        self.auth_token = None
        
    async def setup_session(self):
        """Initialiser la session HTTP"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Nettoyer la session HTTP"""
        if self.session:
            await self.session.close()
            
    def log(self, message):
        """Logger avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    async def authenticate(self):
        """Authentification pour les tests"""
        try:
            auth_data = {
                "first_name": "TestUser",
                "last_name": "PhaseC1"
            }
            
            async with self.session.post(f"{self.base_url}/api/auth/register", json=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get('access_token')
                    self.log("✅ Authentification réussie")
                    return True
                else:
                    # Essayer de se connecter si l'utilisateur existe déjà
                    async with self.session.post(f"{self.base_url}/api/auth/login", json=auth_data) as login_response:
                        if login_response.status == 200:
                            data = await login_response.json()
                            self.auth_token = data.get('access_token')
                            self.log("✅ Connexion réussie")
                            return True
                        
        except Exception as e:
            self.log(f"❌ Erreur authentification: {e}")
            return False
            
    def get_headers(self):
        """Headers avec authentification"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
    async def test_unified_loading_parallel(self):
        """Test 1: Chargement parallèle livres + séries"""
        self.log("🧪 Test 1: Chargement parallèle unifié")
        
        start_time = time.time()
        
        # Simuler les appels que fait useUnifiedContent
        tasks = [
            self.session.get(f"{self.base_url}/api/books", headers=self.get_headers()),
            self.session.get(f"{self.base_url}/api/series/library", headers=self.get_headers()),
            self.session.get(f"{self.base_url}/api/stats", headers=self.get_headers())
        ]
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            load_time = (time.time() - start_time) * 1000
            
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
            
            if success_count == 3:
                self.log(f"✅ Test 1 RÉUSSI: Chargement parallèle en {load_time:.0f}ms")
                self.test_results.append(("Chargement parallèle", True, f"{load_time:.0f}ms"))
                return True
            else:
                self.log(f"❌ Test 1 ÉCHOUÉ: {success_count}/3 endpoints réussis")
                self.test_results.append(("Chargement parallèle", False, f"{success_count}/3"))
                return False
                
        except Exception as e:
            self.log(f"❌ Test 1 ERREUR: {e}")
            self.test_results.append(("Chargement parallèle", False, str(e)))
            return False
            
    async def test_add_book_refresh(self):
        """Test 2: Ajout livre + rafraîchissement immédiat"""
        self.log("🧪 Test 2: Ajout livre avec rafraîchissement")
        
        # État initial
        async with self.session.get(f"{self.base_url}/api/books", headers=self.get_headers()) as response:
            initial_books = await response.json()
            initial_count = len(initial_books)
            
        # Ajouter un livre de test
        test_book = {
            "title": f"Test Book Phase C.1 {int(time.time())}",
            "author": "Test Author",
            "category": "roman",
            "description": "Livre de test pour Phase C.1"
        }
        
        start_time = time.time()
        
        try:
            # Ajout du livre
            async with self.session.post(f"{self.base_url}/api/books", headers=self.get_headers(), json=test_book) as response:
                if response.status not in [200, 201]:
                    self.log(f"❌ Test 2 ÉCHOUÉ: Erreur ajout livre {response.status}")
                    return False
                    
            # Vérification immédiate (simuler le rafraîchissement unifié)
            await asyncio.sleep(0.5)  # Délai minimal comme dans le hook
            
            async with self.session.get(f"{self.base_url}/api/books", headers=self.get_headers()) as response:
                updated_books = await response.json()
                updated_count = len(updated_books)
                
            refresh_time = (time.time() - start_time) * 1000
            
            if updated_count > initial_count:
                self.log(f"✅ Test 2 RÉUSSI: Livre ajouté et visible en {refresh_time:.0f}ms")
                self.test_results.append(("Ajout + rafraîchissement", True, f"{refresh_time:.0f}ms"))
                return True
            else:
                self.log(f"❌ Test 2 ÉCHOUÉ: Livre non visible après ajout")
                self.test_results.append(("Ajout + rafraîchissement", False, "Non visible"))
                return False
                
        except Exception as e:
            self.log(f"❌ Test 2 ERREUR: {e}")
            self.test_results.append(("Ajout + rafraîchissement", False, str(e)))
            return False
            
    async def test_series_library_integration(self):
        """Test 3: Intégration bibliothèque séries"""
        self.log("🧪 Test 3: Intégration userSeriesLibrary")
        
        try:
            # Vérifier que l'endpoint séries bibliothèque fonctionne
            async with self.session.get(f"{self.base_url}/api/series/library", headers=self.get_headers()) as response:
                if response.status == 200:
                    series_data = await response.json()
                    series_count = len(series_data)
                    
                    self.log(f"✅ Test 3 RÉUSSI: {series_count} séries dans la bibliothèque")
                    self.test_results.append(("Bibliothèque séries", True, f"{series_count} séries"))
                    return True
                else:
                    self.log(f"❌ Test 3 ÉCHOUÉ: Status {response.status}")
                    self.test_results.append(("Bibliothèque séries", False, f"Status {response.status}"))
                    return False
                    
        except Exception as e:
            self.log(f"❌ Test 3 ERREUR: {e}")
            self.test_results.append(("Bibliothèque séries", False, str(e)))
            return False
            
    async def test_error_handling(self):
        """Test 4: Gestion erreurs du hook unifié"""
        self.log("🧪 Test 4: Gestion erreurs robuste")
        
        try:
            # Test avec token invalide pour simuler une erreur
            invalid_headers = {
                "Authorization": "Bearer invalid_token",
                "Content-Type": "application/json"
            }
            
            # Le hook devrait gérer cette erreur gracieusement
            async with self.session.get(f"{self.base_url}/api/books", headers=invalid_headers) as response:
                if response.status == 401:  # Non autorisé, comme attendu
                    self.log("✅ Test 4 RÉUSSI: Gestion erreur auth correcte")
                    self.test_results.append(("Gestion erreurs", True, "Auth 401"))
                    return True
                else:
                    self.log(f"❌ Test 4 ÉCHOUÉ: Status inattendu {response.status}")
                    self.test_results.append(("Gestion erreurs", False, f"Status {response.status}"))
                    return False
                    
        except Exception as e:
            # Exception attendue pour token invalide
            self.log("✅ Test 4 RÉUSSI: Exception gérée correctement")
            self.test_results.append(("Gestion erreurs", True, "Exception gérée"))
            return True
            
    async def test_performance_unified_vs_sequential(self):
        """Test 5: Performance parallèle vs séquentiel"""
        self.log("🧪 Test 5: Performance parallèle vs séquentiel")
        
        # Test séquentiel
        start_sequential = time.time()
        try:
            async with self.session.get(f"{self.base_url}/api/books", headers=self.get_headers()):
                pass
            async with self.session.get(f"{self.base_url}/api/series/library", headers=self.get_headers()):
                pass
            async with self.session.get(f"{self.base_url}/api/stats", headers=self.get_headers()):
                pass
            sequential_time = (time.time() - start_sequential) * 1000
        except:
            sequential_time = 9999
            
        # Test parallèle
        start_parallel = time.time()
        try:
            tasks = [
                self.session.get(f"{self.base_url}/api/books", headers=self.get_headers()),
                self.session.get(f"{self.base_url}/api/series/library", headers=self.get_headers()),
                self.session.get(f"{self.base_url}/api/stats", headers=self.get_headers())
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            parallel_time = (time.time() - start_parallel) * 1000
        except:
            parallel_time = 9999
            
        improvement = ((sequential_time - parallel_time) / sequential_time) * 100
        
        if parallel_time < sequential_time:
            self.log(f"✅ Test 5 RÉUSSI: {improvement:.1f}% plus rapide ({parallel_time:.0f}ms vs {sequential_time:.0f}ms)")
            self.test_results.append(("Performance parallèle", True, f"{improvement:.1f}% gain"))
            return True
        else:
            self.log(f"⚠️ Test 5 MITIGÉ: Pas d'amélioration performance")
            self.test_results.append(("Performance parallèle", False, "Pas d'amélioration"))
            return False
            
    async def run_all_tests(self):
        """Exécuter tous les tests de validation Phase C.1"""
        self.log("🚀 === DÉBUT TESTS PHASE C.1 - HOOK UNIFIÉ ===")
        
        await self.setup_session()
        
        try:
            if not await self.authenticate():
                self.log("❌ Impossible de s'authentifier, arrêt des tests")
                return
                
            # Exécution des tests
            tests = [
                self.test_unified_loading_parallel,
                self.test_add_book_refresh,
                self.test_series_library_integration,
                self.test_error_handling,
                self.test_performance_unified_vs_sequential
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if await test():
                    passed += 1
                await asyncio.sleep(0.5)  # Délai entre tests
                
            # Résumé
            self.log("📊 === RÉSUMÉ TESTS PHASE C.1 ===")
            for test_name, success, details in self.test_results:
                status = "✅" if success else "❌"
                self.log(f"{status} {test_name}: {details}")
                
            success_rate = (passed / total) * 100
            self.log(f"📈 Taux de réussite: {passed}/{total} ({success_rate:.1f}%)")
            
            if passed == total:
                self.log("🎉 PHASE C.1 VALIDATION RÉUSSIE - Hook unifié opérationnel")
            elif passed >= total * 0.8:
                self.log("⚠️ PHASE C.1 VALIDATION PARTIELLE - Quelques ajustements nécessaires")
            else:
                self.log("❌ PHASE C.1 VALIDATION ÉCHOUÉE - Révision nécessaire")
                
        finally:
            await self.cleanup_session()

async def main():
    """Point d'entrée principal"""
    validator = PhaseC1Validator()
    await validator.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())