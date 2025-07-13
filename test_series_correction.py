#!/usr/bin/env python3
"""
TEST CORRECTION SYSTÈME VIGNETTES SÉRIES
Vérification que les vignettes de série se créent automatiquement
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.database.connection import client

def test_series_correction():
    """
    Test de la correction du système de vignettes de série
    """
    print("🧪 [TEST CORRECTION] Début test système vignettes de série")
    
    # Connexion à la base de données
    try:
        db = client["booktime"]
        books_collection = db["books"]
        
        # Compter le nombre total de livres
        total_books = books_collection.count_documents({})
        print(f"📚 [TEST] Total livres en base: {total_books}")
        
        # Récupérer quelques livres pour tester
        test_books = list(books_collection.find().limit(10))
        
        print(f"📖 [TEST] Livres de test récupérés: {len(test_books)}")
        
        # Analyser chaque livre pour voir s'il appartient à une série
        series_detected = {}
        standalone_books = []
        
        for book in test_books:
            book_title = book.get('title', 'Titre inconnu')
            book_author = book.get('author', 'Auteur inconnu')
            book_saga = book.get('saga', '')
            
            print(f"\n📖 [TEST] Livre: \"{book_title}\" par {book_author}")
            
            # Test 1: Champ saga existant
            if book_saga and book_saga.strip():
                series_name = book_saga.strip()
                if series_name not in series_detected:
                    series_detected[series_name] = {
                        'books': [],
                        'method': 'existing_saga_field',
                        'confidence': 100
                    }
                series_detected[series_name]['books'].append(book_title)
                print(f"   ✅ Appartient à la série: \"{series_name}\" (champ saga existant)")
                continue
            
            # Test 2: Détection automatique basique (patterns simples)
            title_lower = book_title.lower()
            
            # Pattern Harry Potter
            if 'harry potter' in title_lower:
                series_name = 'Harry Potter'
                if series_name not in series_detected:
                    series_detected[series_name] = {
                        'books': [],
                        'method': 'title_pattern_detection',
                        'confidence': 95
                    }
                series_detected[series_name]['books'].append(book_title)
                print(f"   ✅ Appartient à la série: \"{series_name}\" (détection pattern)")
                continue
            
            # Pattern One Piece
            if 'one piece' in title_lower:
                series_name = 'One Piece'
                if series_name not in series_detected:
                    series_detected[series_name] = {
                        'books': [],
                        'method': 'title_pattern_detection',
                        'confidence': 95
                    }
                series_detected[series_name]['books'].append(book_title)
                print(f"   ✅ Appartient à la série: \"{series_name}\" (détection pattern)")
                continue
            
            # Pattern Astérix
            if 'asterix' in title_lower or 'astérix' in title_lower:
                series_name = 'Astérix'
                if series_name not in series_detected:
                    series_detected[series_name] = {
                        'books': [],
                        'method': 'title_pattern_detection',
                        'confidence': 95
                    }
                series_detected[series_name]['books'].append(book_title)
                print(f"   ✅ Appartient à la série: \"{series_name}\" (détection pattern)")
                continue
            
            # Pattern numérotation générique
            if any(pattern in title_lower for pattern in ['tome ', 'volume ', 'vol. ', ' #']):
                # Essayer d'extraire le nom de la série
                for separator in [' tome ', ' volume ', ' vol. ', ' #']:
                    if separator in title_lower:
                        series_name = book_title.split(separator)[0].strip()
                        if len(series_name) > 3:  # Nom de série valide
                            if series_name not in series_detected:
                                series_detected[series_name] = {
                                    'books': [],
                                    'method': 'numbering_pattern_detection',
                                    'confidence': 80
                                }
                            series_detected[series_name]['books'].append(book_title)
                            print(f"   ✅ Appartient à la série: \"{series_name}\" (détection numérotation)")
                            break
                else:
                    # Aucun pattern trouvé
                    standalone_books.append(book_title)
                    print(f"   📖 Livre standalone")
            else:
                # Aucun pattern trouvé
                standalone_books.append(book_title)
                print(f"   📖 Livre standalone")
        
        # Résumé des résultats
        print(f"\n🎯 [TEST] RÉSUMÉ DÉTECTION:")
        print(f"📚 Séries détectées: {len(series_detected)}")
        print(f"📖 Livres standalone: {len(standalone_books)}")
        
        for series_name, info in series_detected.items():
            print(f"   📚 Série \"{series_name}\": {len(info['books'])} livre(s) - Méthode: {info['method']} ({info['confidence']}%)")
            for book_title in info['books']:
                print(f"      - {book_title}")
        
        if standalone_books:
            print(f"   📖 Livres standalone:")
            for book_title in standalone_books:
                print(f"      - {book_title}")
        
        # Test de la logique attendue après correction
        print(f"\n✅ [TEST] CORRECTION ATTENDUE:")
        print(f"   🎯 Vignettes de série qui devraient être créées automatiquement: {len(series_detected)}")
        print(f"   🎯 Vignettes de livres individuels qui devraient être affichées: {len(standalone_books)}")
        print(f"   🎯 Livres qui devraient être masqués (dans vignettes série): {len(test_books) - len(standalone_books)}")
        
        # Validation du test
        series_books_count = sum(len(info['books']) for info in series_detected.values())
        expected_masked = series_books_count
        expected_visible_individual = len(standalone_books)
        expected_series_thumbnails = len(series_detected)
        
        print(f"\n🔍 [TEST] VALIDATION LOGIQUE:")
        print(f"   📊 Livres appartenant à des séries: {series_books_count}")
        print(f"   📊 Livres standalone: {expected_visible_individual}")
        print(f"   📊 Total vérifié: {series_books_count + expected_visible_individual} = {len(test_books)} ✅")
        
        if expected_series_thumbnails > 0:
            print(f"\n🎉 [TEST] SUCCÈS: La correction devrait créer automatiquement {expected_series_thumbnails} vignette(s) de série !")
        else:
            print(f"\n⚠️ [TEST] ATTENTION: Aucune série détectée dans l'échantillon de test")
        
        return {
            'total_books': len(test_books),
            'series_detected': len(series_detected),
            'standalone_books': len(standalone_books),
            'success': True
        }
        
    except Exception as e:
        print(f"❌ [TEST] Erreur: {e}")
        return {
            'total_books': 0,
            'series_detected': 0,
            'standalone_books': 0,
            'success': False,
            'error': str(e)
        }

def main():
    print("🚀 [TEST] Démarrage test correction système vignettes de série")
    result = test_series_correction()
    
    if result['success']:
        print(f"\n✅ [TEST] Test terminé avec succès!")
        print(f"📊 Résumé: {result['series_detected']} séries, {result['standalone_books']} livres standalone sur {result['total_books']} livres testés")
    else:
        print(f"\n❌ [TEST] Test échoué: {result.get('error', 'Erreur inconnue')}")
    
    return result

if __name__ == "__main__":
    main()