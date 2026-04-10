#!/usr/bin/env python3
"""
Test de validation - Finalisation de l'algorithme de recherche avancé
Tests des scénarios critiques de tolérance orthographique et priorisation
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
TEST_SCENARIOS = [
    # Scénarios tolérance orthographique critiques
    ("herry potter", "Harry Potter - Distance Levenshtein: 1"),
    ("astérics", "Astérix - Correspondance phonétique"),
    ("one pece", "One Piece - Distance Levenshtein: 1"),
    ("seigneur anneaux", "Le Seigneur des Anneaux - Correspondance partielle"),
    ("game of throne", "Game of Thrones - Variations linguistiques"),
    
    # Scénarios exacts
    ("harry potter", "Harry Potter - Correspondance exacte"),
    ("astérix", "Astérix - Correspondance exacte"),
    ("one piece", "One Piece - Correspondance exacte"),
    
    # Scénarios partiels
    ("attack titan", "Attack on Titan - Mots partiels"),
    ("attaque titans", "Attaque des Titans - Correspondance française")
]

def test_search_optimization():
    """Test de l'algorithme de recherche optimisé"""
    
    print("🔍 Test de Finalisation - Algorithme de Recherche Avancé")
    print("="*60)
    
    results = []
    
    for query, expected in TEST_SCENARIOS:
        print(f"\n🧪 Test: '{query}' (attendu: {expected})")
        
        try:
            # Test recherche Open Library
            response = requests.get(
                f"{BACKEND_URL}/api/openlibrary/search",
                params={"q": query, "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyser les résultats
                series_detected = False
                series_first = False
                top_results = data.get('books', [])[:3]
                
                print(f"   📊 {len(top_results)} résultats reçus")
                
                for i, book in enumerate(top_results):
                    title = book.get('title', 'Sans titre')[:50]
                    is_series = book.get('isSeriesCard', False)
                    score = book.get('relevanceScore', book.get('confidence', 0))
                    
                    if is_series:
                        series_detected = True
                        if i == 0:
                            series_first = True
                    
                    badge = "📚 SÉRIE" if is_series else "📖 LIVRE"
                    print(f"   {i+1}. {badge}: {title} - Score: {score}")
                
                # Validation des critères
                success = True
                success_details = []
                
                if series_detected:
                    success_details.append("✅ Série détectée")
                    if series_first:
                        success_details.append("✅ Série en position #1")
                    else:
                        success_details.append("⚠️ Série non prioritaire")
                        success = False
                else:
                    success_details.append("❌ Aucune série détectée")
                    success = False
                
                print(f"   Résultat: {' | '.join(success_details)}")
                
                results.append({
                    'query': query,
                    'expected': expected,
                    'success': success,
                    'series_detected': series_detected,
                    'series_first': series_first,
                    'results_count': len(top_results)
                })
                
            else:
                print(f"   ❌ Erreur API: {response.status_code}")
                results.append({
                    'query': query,
                    'expected': expected,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
            results.append({
                'query': query,
                'expected': expected,
                'success': False,
                'error': str(e)
            })
        
        time.sleep(0.5)  # Éviter surcharge API
    
    # Rapport final
    print("\n" + "="*60)
    print("📋 RAPPORT FINAL - Algorithme de Recherche Avancé")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    total_tests = len(results)
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"🎯 Taux de réussite: {success_count}/{total_tests} ({success_rate:.1f}%)")
    print(f"✅ Tests réussis: {success_count}")
    print(f"❌ Tests échoués: {total_tests - success_count}")
    
    # Détail des échecs
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"\n⚠️ Tests échoués:")
        for test in failed_tests:
            reason = test.get('error', 'Série non détectée ou non prioritaire')
            print(f"   - '{test['query']}': {reason}")
    
    # Validation globale
    if success_rate >= 80:
        print(f"\n🎉 ALGORITHME VALIDÉ - Performance excellente ({success_rate:.1f}%)")
        return True
    elif success_rate >= 60:
        print(f"\n⚠️ ALGORITHME ACCEPTABLE - Performance correcte ({success_rate:.1f}%)")
        return True
    else:
        print(f"\n❌ ALGORITHME À AMÉLIORER - Performance insuffisante ({success_rate:.1f}%)")
        return False

if __name__ == "__main__":
    success = test_search_optimization()
    exit(0 if success else 1)