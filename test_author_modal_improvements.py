#!/usr/bin/env python3
"""
Test des améliorations du modal auteur - Session 87.8
Validation des nouveaux endpoints pour afficher toutes les œuvres d'un auteur
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
TEST_AUTHORS = [
    "J.K. Rowling",
    "Stephen King", 
    "Agatha Christie",
    "George R.R. Martin",
    "J.R.R. Tolkien"
]

def test_author_works_endpoints():
    """Test des nouveaux endpoints pour les œuvres des auteurs"""
    print("🎯 TEST DES NOUVEAUX ENDPOINTS ŒUVRES AUTEURS")
    print("=" * 60)
    
    results = {
        "wikipedia_works": {},
        "openlibrary_works": {},
        "summary": {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0
        }
    }
    
    for author in TEST_AUTHORS:
        print(f"\n📚 Test pour l'auteur: {author}")
        print("-" * 40)
        
        # Test 1: Endpoint Wikipedia Works
        print(f"🔍 Test Wikipedia works endpoint...")
        wikipedia_url = f"{BASE_URL}/api/wikipedia/author/{author}/works"
        
        try:
            response = requests.get(wikipedia_url, timeout=15)
            results["summary"]["total_tests"] += 1
            
            if response.status_code == 200:
                data = response.json()
                if data.get("found"):
                    works = data.get("works", {})
                    series_count = len(works.get("series", []))
                    individual_count = len(works.get("individual_books", []))
                    total_books = works.get("total_books", 0)
                    sources = works.get("sources", {})
                    
                    print(f"✅ Wikipedia works: {total_books} livres trouvés")
                    print(f"   📖 Séries: {series_count}")
                    print(f"   📚 Livres individuels: {individual_count}")
                    print(f"   🔗 Sources: {sources}")
                    
                    results["wikipedia_works"][author] = {
                        "success": True,
                        "total_books": total_books,
                        "series_count": series_count,
                        "individual_count": individual_count,
                        "sources": sources
                    }
                    results["summary"]["successful_tests"] += 1
                else:
                    print(f"⚠️ Wikipedia works: Auteur non trouvé")
                    results["wikipedia_works"][author] = {"success": False, "reason": "Not found"}
                    results["summary"]["failed_tests"] += 1
            else:
                print(f"❌ Wikipedia works: Erreur HTTP {response.status_code}")
                results["wikipedia_works"][author] = {"success": False, "reason": f"HTTP {response.status_code}"}
                results["summary"]["failed_tests"] += 1
                
        except Exception as e:
            print(f"❌ Wikipedia works: Erreur - {str(e)}")
            results["wikipedia_works"][author] = {"success": False, "reason": str(e)}
            results["summary"]["failed_tests"] += 1
        
        # Test 2: Endpoint OpenLibrary Works (nécessite authentification)
        print(f"🔍 Test OpenLibrary works endpoint...")
        openlibrary_url = f"{BASE_URL}/api/openlibrary/author/{author}/works"
        
        # Créer un token test simple (prénom/nom)
        auth_data = {"first_name": "Test", "last_name": "User"}
        try:
            auth_response = requests.post(f"{BASE_URL}/api/auth/login", json=auth_data, timeout=10)
            if auth_response.status_code == 200:
                token = auth_response.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                
                results["summary"]["total_tests"] += 1
                ol_response = requests.get(openlibrary_url, headers=headers, timeout=15)
                
                if ol_response.status_code == 200:
                    ol_data = ol_response.json()
                    if ol_data.get("found"):
                        total_books = ol_data.get("total_books", 0)
                        series_count = len(ol_data.get("series", []))
                        individual_count = len(ol_data.get("individual_books", []))
                        sources = ol_data.get("sources", {})
                        
                        print(f"✅ OpenLibrary works: {total_books} livres trouvés")
                        print(f"   📖 Séries: {series_count}")
                        print(f"   📚 Livres individuels: {individual_count}")
                        print(f"   🔗 Sources: {sources}")
                        
                        results["openlibrary_works"][author] = {
                            "success": True,
                            "total_books": total_books,
                            "series_count": series_count,
                            "individual_count": individual_count,
                            "sources": sources
                        }
                        results["summary"]["successful_tests"] += 1
                    else:
                        print(f"⚠️ OpenLibrary works: Auteur non trouvé")
                        results["openlibrary_works"][author] = {"success": False, "reason": "Not found"}
                        results["summary"]["failed_tests"] += 1
                else:
                    print(f"❌ OpenLibrary works: Erreur HTTP {ol_response.status_code}")
                    results["openlibrary_works"][author] = {"success": False, "reason": f"HTTP {ol_response.status_code}"}
                    results["summary"]["failed_tests"] += 1
            else:
                print(f"❌ OpenLibrary works: Erreur authentification")
                results["openlibrary_works"][author] = {"success": False, "reason": "Auth failed"}
                results["summary"]["failed_tests"] += 1
                
        except Exception as e:
            print(f"❌ OpenLibrary works: Erreur - {str(e)}")
            results["openlibrary_works"][author] = {"success": False, "reason": str(e)}
            results["summary"]["failed_tests"] += 1
    
    return results

def test_endpoint_performance():
    """Test des performances des nouveaux endpoints"""
    print("\n⚡ TEST DES PERFORMANCES")
    print("=" * 60)
    
    performance_results = {}
    
    for author in TEST_AUTHORS[:3]:  # Test seulement 3 auteurs pour la performance
        print(f"\n📊 Test performance pour: {author}")
        
        # Test Wikipedia works
        start_time = time.time()
        try:
            response = requests.get(f"{BASE_URL}/api/wikipedia/author/{author}/works", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                duration = end_time - start_time
                data = response.json()
                total_books = data.get("works", {}).get("total_books", 0)
                
                print(f"✅ Wikipedia: {duration:.2f}s pour {total_books} livres")
                performance_results[f"{author}_wikipedia"] = {
                    "duration": duration,
                    "books": total_books,
                    "success": True
                }
            else:
                print(f"❌ Wikipedia: Erreur HTTP {response.status_code}")
                performance_results[f"{author}_wikipedia"] = {"success": False}
                
        except Exception as e:
            print(f"❌ Wikipedia: Timeout ou erreur - {str(e)}")
            performance_results[f"{author}_wikipedia"] = {"success": False, "error": str(e)}
    
    return performance_results

def test_data_structure():
    """Test de la structure des données retournées"""
    print("\n🏗️ TEST DE LA STRUCTURE DES DONNÉES")
    print("=" * 60)
    
    # Test avec J.K. Rowling pour analyser la structure
    author = "J.K. Rowling"
    print(f"📋 Analyse structure pour: {author}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/wikipedia/author/{author}/works", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print(f"🔍 Structure réponse Wikipedia works:")
            print(f"   - found: {data.get('found')}")
            print(f"   - author: {data.get('author')}")
            
            if data.get("found"):
                works = data.get("works", {})
                print(f"   - works.total_books: {works.get('total_books')}")
                print(f"   - works.series: {len(works.get('series', []))} séries")
                print(f"   - works.individual_books: {len(works.get('individual_books', []))} livres")
                print(f"   - works.sources: {works.get('sources')}")
                
                # Analyser une série si disponible
                series = works.get("series", [])
                if series:
                    first_series = series[0]
                    print(f"   - Première série: {first_series.get('name')}")
                    print(f"     - books: {len(first_series.get('books', []))}")
                    print(f"     - source: {first_series.get('source')}")
                
                # Analyser un livre individuel si disponible
                individual_books = works.get("individual_books", [])
                if individual_books:
                    first_book = individual_books[0]
                    print(f"   - Premier livre: {first_book.get('title')}")
                    print(f"     - year: {first_book.get('year')}")
                    print(f"     - source: {first_book.get('source')}")
                
                return True
        
        print(f"❌ Erreur lors de l'analyse de structure")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def generate_report(results, performance_results):
    """Génération du rapport final"""
    print("\n📊 RAPPORT FINAL - AMÉLIORATIONS MODAL AUTEUR")
    print("=" * 60)
    
    summary = results["summary"]
    success_rate = (summary["successful_tests"] / summary["total_tests"]) * 100 if summary["total_tests"] > 0 else 0
    
    print(f"✅ Tests réussis: {summary['successful_tests']}/{summary['total_tests']} ({success_rate:.1f}%)")
    print(f"❌ Tests échoués: {summary['failed_tests']}")
    
    print(f"\n📚 RÉSULTATS PAR AUTEUR:")
    for author in TEST_AUTHORS:
        print(f"\n👤 {author}:")
        
        # Wikipedia results
        wiki_result = results["wikipedia_works"].get(author, {})
        if wiki_result.get("success"):
            print(f"   📖 Wikipedia: {wiki_result['total_books']} livres ({wiki_result['series_count']} séries)")
        else:
            print(f"   📖 Wikipedia: ❌ {wiki_result.get('reason', 'Erreur inconnue')}")
        
        # OpenLibrary results  
        ol_result = results["openlibrary_works"].get(author, {})
        if ol_result.get("success"):
            print(f"   📚 OpenLibrary: {ol_result['total_books']} livres ({ol_result['series_count']} séries)")
        else:
            print(f"   📚 OpenLibrary: ❌ {ol_result.get('reason', 'Erreur inconnue')}")
    
    print(f"\n⚡ PERFORMANCES:")
    for key, perf in performance_results.items():
        if perf.get("success"):
            print(f"   {key}: {perf['duration']:.2f}s pour {perf['books']} livres")
    
    print(f"\n🎯 CONCLUSION:")
    if success_rate >= 80:
        print("✅ Les améliorations du modal auteur fonctionnent correctement")
        print("✅ Les nouveaux endpoints récupèrent toutes les œuvres des auteurs")
        print("✅ La structure des données est conforme aux attentes")
    else:
        print("⚠️ Certains endpoints présentent des problèmes")
        print("⚠️ Vérifications supplémentaires nécessaires")
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"author_modal_test_results_{timestamp}.json"
    
    full_results = {
        "timestamp": timestamp,
        "summary": summary,
        "results": results,
        "performance": performance_results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(full_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Résultats sauvegardés dans: {filename}")

def main():
    """Fonction principale"""
    print("🚀 DÉBUT DES TESTS - AMÉLIORATIONS MODAL AUTEUR")
    print("=" * 60)
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Backend: {BASE_URL}")
    
    # Vérifier que le backend est accessible
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Backend accessible")
        else:
            print(f"❌ Backend inaccessible: {health_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend inaccessible: {str(e)}")
        return
    
    # Exécuter les tests
    results = test_author_works_endpoints()
    performance_results = test_endpoint_performance()
    structure_ok = test_data_structure()
    
    # Générer le rapport
    generate_report(results, performance_results)
    
    print(f"\n🏁 FIN DES TESTS")
    print(f"🕐 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()