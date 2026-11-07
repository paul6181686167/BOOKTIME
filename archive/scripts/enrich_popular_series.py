#!/usr/bin/env python3
"""
Script d'enrichissement automatique des séries populaires avec images
Met à jour directement la base de données avec les URLs d'images trouvées
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Ajouter le chemin backend au PYTHONPATH
sys.path.append('/app/backend')

from app.series.image_service import image_service

async def enrich_popular_series_in_database():
    """Enrichir les séries populaires dans la base de données"""
    print("🎯 Enrichissement des séries populaires avec images")
    print("=" * 60)
    
    database_path = "/app/backend/data/extended_series_database.json"
    
    if not os.path.exists(database_path):
        print(f"❌ Base de données non trouvée: {database_path}")
        return
    
    # Charger la base de données
    with open(database_path, 'r', encoding='utf-8') as f:
        series_database = json.load(f)
    
    print(f"📚 Base de données chargée: {len(series_database)} séries")
    
    # Définir les séries populaires prioritaires
    popular_series_names = [
        "Harry Potter",
        "Le Seigneur des Anneaux", 
        "One Piece",
        "Naruto",
        "Dragon Ball",
        "Astérix",
        "Tintin",
        "Game of Thrones",
        "Fullmetal Alchemist",
        "Death Note",
        "My Hero Academia",
        "Attack On Titan",
        "Demon Slayer",
        "Lucky Luke",
        "Spirou et Fantasio",
        "Thorgal",
        "InuYasha",
        "Slam Dunk"
    ]
    
    print(f"🎯 Ciblage de {len(popular_series_names)} séries populaires...")
    
    # Trouver et enrichir les séries populaires
    enriched_count = 0
    updated_series = []
    
    for i, series in enumerate(series_database):
        series_name = series.get('name', '')
        
        # Vérifier si c'est une série populaire
        is_popular = any(
            popular_name.lower() in series_name.lower() or 
            series_name.lower() in popular_name.lower()
            for popular_name in popular_series_names
        )
        
        if is_popular and not series.get('cover_url'):
            print(f"\n📖 Enrichissement de '{series_name}'...")
            
            try:
                # Enrichir avec image
                enriched_series = await image_service.enrich_series_with_image(series)
                
                if enriched_series.get('cover_url'):
                    # Ajouter métadonnées d'enrichissement
                    enriched_series['image_enriched'] = True
                    enriched_series['image_enriched_date'] = datetime.utcnow().isoformat()
                    enriched_series['image_source'] = 'openlibrary'
                    
                    # Remplacer dans la base
                    series_database[i] = enriched_series
                    enriched_count += 1
                    updated_series.append(series_name)
                    
                    print(f"   ✅ Image trouvée: {enriched_series['cover_url']}")
                else:
                    print(f"   ❌ Aucune image trouvée")
                    
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        # Affichage du progrès
        if (i + 1) % 1000 == 0:
            print(f"📊 Progression: {i + 1}/{len(series_database)} séries traitées")
    
    # Sauvegarder la base mise à jour
    if enriched_count > 0:
        backup_path = database_path.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        # Créer une sauvegarde
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(series_database, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Sauvegarde créée: {backup_path}")
        
        # Sauvegarder la version enrichie
        with open(database_path, 'w', encoding='utf-8') as f:
            json.dump(series_database, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Base de données mise à jour: {database_path}")
    
    # Résumé
    print(f"\n📊 RÉSUMÉ ENRICHISSEMENT:")
    print(f"   🎯 Séries populaires ciblées: {len(popular_series_names)}")
    print(f"   ✅ Séries enrichies: {enriched_count}")
    print(f"   📝 Séries mises à jour: {', '.join(updated_series[:10])}")
    if len(updated_series) > 10:
        print(f"   ... et {len(updated_series) - 10} autres")
    
    return {
        'enriched_count': enriched_count,
        'updated_series': updated_series,
        'total_series': len(series_database)
    }

async def main():
    """Fonction principale"""
    try:
        result = await enrich_popular_series_in_database()
        print(f"\n🎉 Enrichissement terminé avec succès!")
        print(f"   📈 {result['enriched_count']} séries populaires enrichies")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'enrichissement: {e}")
        raise
    finally:
        await image_service.close()

if __name__ == "__main__":
    asyncio.run(main())