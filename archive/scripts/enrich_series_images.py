#!/usr/bin/env python3
"""
Script d'enrichissement d'images pour les séries BOOKTIME
Utilise Open Library API pour obtenir des images de couverture
"""
import asyncio
import json
import sys
import os

# Ajouter le chemin backend au PYTHONPATH
sys.path.append('/app/backend')

from app.series.image_service import image_service

async def test_single_series():
    """Tester l'enrichissement d'une série unique"""
    print("🧪 Test enrichissement série unique...")
    
    test_series = {
        "name": "Harry Potter",
        "authors": ["J.K. Rowling"],
        "category": "roman",
        "volumes": 7
    }
    
    enriched = await image_service.enrich_series_with_image(test_series)
    
    print(f"✅ Série testée: {enriched['name']}")
    print(f"📸 Image trouvée: {'✅ Oui' if enriched.get('cover_url') else '❌ Non'}")
    if enriched.get('cover_url'):
        print(f"🔗 URL: {enriched['cover_url']}")
    
    return enriched

async def test_popular_series():
    """Tester l'enrichissement des séries populaires"""
    print("\n🎯 Test enrichissement séries populaires...")
    
    popular_series = [
        {
            "name": "Harry Potter",
            "authors": ["J.K. Rowling"],
            "category": "roman",
            "volumes": 7
        },
        {
            "name": "Le Seigneur des Anneaux",
            "authors": ["J.R.R. Tolkien"],
            "category": "roman",
            "volumes": 3
        },
        {
            "name": "One Piece",
            "authors": ["Eiichiro Oda"],
            "category": "manga",
            "volumes": 108
        },
        {
            "name": "Dragon Ball",
            "authors": ["Akira Toriyama"],
            "category": "manga",
            "volumes": 42
        },
        {
            "name": "Astérix",
            "authors": ["René Goscinny", "Albert Uderzo"],
            "category": "bd",
            "volumes": 39
        }
    ]
    
    print(f"📚 Enrichissement de {len(popular_series)} séries populaires...")
    enriched_series = await image_service.batch_enrich_series(popular_series, max_concurrent=3)
    
    # Afficher les résultats
    found_images = 0
    for series in enriched_series:
        has_image = bool(series.get('cover_url'))
        if has_image:
            found_images += 1
        
        print(f"📖 {series['name']}: {'✅' if has_image else '❌'}")
        if has_image:
            print(f"   🔗 {series['cover_url']}")
    
    print(f"\n📊 Résumé: {found_images}/{len(enriched_series)} séries avec images ({found_images/len(enriched_series)*100:.1f}%)")
    
    return enriched_series

async def enrich_sample_database():
    """Enrichir un échantillon de la base de données"""
    print("\n🗄️ Test enrichissement échantillon base de données...")
    
    database_path = "/app/backend/data/extended_series_database.json"
    
    if not os.path.exists(database_path):
        print(f"❌ Base de données non trouvée: {database_path}")
        return None
    
    # Enrichir un petit échantillon
    try:
        result = await image_service.enrich_series_database(
            database_path,
            output_path="/app/backend/data/series_sample_enriched.json",
            sample_size=20
        )
        
        print(f"✅ Échantillon enrichi:")
        print(f"   📊 {result['enriched_count']}/{result['total_processed']} avec images")
        print(f"   📈 Taux de succès: {result['success_rate']*100:.1f}%")
        print(f"   💾 Sauvegardé: {result['output_file']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur enrichissement échantillon: {e}")
        return None

async def get_vision_expert_images():
    """Obtenir des images via vision_expert_agent pour test"""
    print("\n🎨 Test vision_expert_agent (placeholder)...")
    
    # Pour l'instant, on simule juste l'appel
    test_series = {
        "name": "Test Series",
        "category": "roman"
    }
    
    result = await image_service.get_placeholder_image_from_vision_expert(
        test_series["name"], 
        test_series["category"]
    )
    
    print(f"📸 Vision expert result: {result or 'None (placeholder)'}")
    return result

async def main():
    """Fonction principale de test"""
    print("🚀 BOOKTIME - Test d'enrichissement d'images pour séries")
    print("=" * 60)
    
    try:
        # Test 1: Série unique
        await test_single_series()
        
        # Test 2: Séries populaires
        await test_popular_series()
        
        # Test 3: Échantillon base de données
        await enrich_sample_database()
        
        # Test 4: Vision expert (placeholder)
        await get_vision_expert_images()
        
        print("\n✅ Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        raise
    finally:
        # Fermer la session aiohttp
        await image_service.close()

if __name__ == "__main__":
    asyncio.run(main())