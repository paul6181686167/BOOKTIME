#!/usr/bin/env python3
"""
Test d'enrichissement des images de séries
Teste le système Open Library optimisé
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

from app.series.image_service import SeriesImageService

async def test_series_images():
    """Tester l'enrichissement d'images pour des séries populaires"""
    
    # Créer le service
    service = SeriesImageService()
    
    # Séries de test populaires
    test_series = [
        {
            'name': 'Harry Potter',
            'authors': ['J.K. Rowling'],
            'category': 'roman'
        },
        {
            'name': 'One Piece',
            'authors': ['Eiichiro Oda'],
            'category': 'manga'
        },
        {
            'name': 'Astérix',
            'authors': ['René Goscinny', 'Albert Uderzo'],
            'category': 'bd'
        },
        {
            'name': 'Le Seigneur des Anneaux',
            'authors': ['J.R.R. Tolkien'],
            'category': 'roman'
        },
        {
            'name': 'Dragon Ball',
            'authors': ['Akira Toriyama'],
            'category': 'manga'
        }
    ]
    
    print("🔍 TEST D'ENRICHISSEMENT D'IMAGES DE SÉRIES")
    print("=" * 50)
    
    results = []
    
    for i, series in enumerate(test_series, 1):
        print(f"\n📚 Test {i}/{len(test_series)}: {series['name']}")
        print(f"   Auteur(s): {', '.join(series['authors'])}")
        print(f"   Catégorie: {series['category']}")
        
        try:
            # Enrichir la série
            enriched = await service.enrich_series_with_image(series.copy())
            
            # Vérifier le résultat
            if enriched.get('cover_url'):
                print(f"   ✅ IMAGE TROUVÉE: {enriched['cover_url']}")
                print(f"   📊 Source: {enriched.get('image_source', 'unknown')}")
                results.append({
                    'series': series['name'],
                    'success': True,
                    'url': enriched['cover_url']
                })
            else:
                print(f"   ❌ Aucune image trouvée")
                results.append({
                    'series': series['name'],
                    'success': False,
                    'url': None
                })
                
        except Exception as e:
            print(f"   ⚠️ ERREUR: {e}")
            results.append({
                'series': series['name'],
                'success': False,
                'error': str(e)
            })
    
    # Fermer la session
    await service.close()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Succès: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"❌ Échecs: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)")
    
    if successful:
        print(f"\n✅ SÉRIES AVEC IMAGES:")
        for result in successful:
            print(f"   📚 {result['series']}: {result['url']}")
    
    if failed:
        print(f"\n❌ SÉRIES SANS IMAGES:")
        for result in failed:
            error_msg = result.get('error', 'Aucune image trouvée')
            print(f"   📚 {result['series']}: {error_msg}")
    
    return len(successful) > 0

if __name__ == "__main__":
    print("🚀 Démarrage du test d'enrichissement d'images...")
    success = asyncio.run(test_series_images())
    
    if success:
        print("\n🎉 TEST RÉUSSI: Au moins une image a été trouvée!")
        sys.exit(0)
    else:
        print("\n⚠️ TEST ÉCHOUÉ: Aucune image trouvée")
        sys.exit(1)