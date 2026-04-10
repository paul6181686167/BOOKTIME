#!/usr/bin/env python3
"""
💾 EXTRACTEUR SÉRIES DÉTECTÉES ULTRA HARVEST
Script pour extraire et sauvegarder les séries détectées en cours d'analyse
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import argparse

def extract_detected_series():
    """Extraire séries détectées de la base SQLite"""
    db_path = Path('/app/data/ultra_harvest_tracking.db')
    
    if not db_path.exists():
        print("❌ Base de données tracking non trouvée")
        return []
    
    with sqlite3.connect(db_path) as conn:
        # Récupérer toutes les séries détectées
        cursor = conn.execute("""
            SELECT 
                series_name,
                author,
                COUNT(*) as volume_count,
                AVG(confidence_score) as avg_confidence,
                source_strategy,
                MIN(analysis_date) as first_detection
            FROM analyzed_books 
            WHERE series_detected = 1 AND series_name IS NOT NULL
            GROUP BY series_name, author
            HAVING COUNT(*) >= 2  -- Au moins 2 volumes
            ORDER BY avg_confidence DESC, volume_count DESC
        """)
        
        detected_series = cursor.fetchall()
        
        print(f"🔍 Trouvé {len(detected_series)} séries uniques dans la base tracking")
        return detected_series

def smart_categorize_series(series_name, author):
    """Catégorisation intelligente basée sur nom/auteur"""
    name_lower = series_name.lower()
    author_lower = author.lower() if author != "Unknown" else ""
    
    # Patterns manga
    manga_indicators = ['manga', 'anime', 'light novel', 'ln', 'vol.', 'tome']
    japanese_names = ['akira', 'hiroshi', 'takeshi', 'kenji', 'yuki', 'masashi', 'naoki', 'oda', 'toriyama', 'kishimoto']
    
    if (any(indicator in name_lower for indicator in manga_indicators) or
        any(jp_name in author_lower for jp_name in japanese_names)):
        return 'manga'
    
    # Patterns BD
    bd_indicators = ['comic', 'bd', 'bande dessinée', 'astérix', 'tintin', 'lucky luke']
    if any(indicator in name_lower for indicator in bd_indicators):
        return 'bd'
    
    return 'roman'

def generate_series_keywords(name, author):
    """Génération keywords intelligents"""
    keywords = []
    
    # Base nom
    base_name = name.lower().strip()
    keywords.append(base_name)
    
    # Variations
    keywords.extend([
        f"{base_name} series",
        f"{base_name} saga",
        f"the {base_name}"
    ])
    
    # Auteur si pertinent
    if author != "Unknown" and len(author.split()) <= 3:
        author_last = author.split()[-1].lower()
        if len(author_last) > 2:
            keywords.append(author_last)
    
    return keywords[:8]

def create_series_entry(series_data):
    """Créer entrée série format BOOKTIME"""
    series_name, author, volume_count, avg_confidence, source_strategy, first_detection = series_data
    
    # Catégorisation
    category = smart_categorize_series(series_name, author)
    
    # Keywords
    keywords = generate_series_keywords(series_name, author)
    
    # Variations titre
    variations = [
        series_name,
        f"The {series_name}",
        f"{series_name} Series"
    ]
    
    return {
        "name": series_name,
        "authors": [author] if author != "Unknown" else [],
        "category": category,
        "volumes": int(volume_count),
        "keywords": keywords,
        "variations": variations,
        "exclusions": ["anthology", "collection", "omnibus"],
        "source": "ultra_harvest_intermediate_save",
        "confidence_score": int(avg_confidence or 75),
        "auto_generated": True,
        "detection_date": datetime.now().isoformat(),
        "ultra_harvest_info": {
            "volume_count": int(volume_count),
            "avg_confidence": float(avg_confidence or 75),
            "source_strategy": source_strategy,
            "first_detection": first_detection
        }
    }

def save_series_to_booktime(new_series, dry_run=False):
    """Sauvegarder séries dans BOOKTIME"""
    series_path = Path('/app/backend/data/extended_series_database.json')
    
    # Charger séries existantes
    if series_path.exists():
        with open(series_path, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []
    
    # Éviter doublons
    existing_names = {series['name'].lower() for series in existing_data}
    
    unique_new_series = []
    for series in new_series:
        if series['name'].lower() not in existing_names:
            unique_new_series.append(series)
    
    print(f"📊 Nouvelles séries uniques: {len(unique_new_series)}")
    
    if dry_run:
        print("🔍 MODE DRY-RUN - Aucune sauvegarde effectuée")
        return len(unique_new_series)
    
    # Ajout nouvelles séries
    existing_data.extend(unique_new_series)
    
    # Backup sécurisé
    backup_path = Path(f'/app/backups/series_detection/backup_intermediate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(backup_path, 'w') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    # Sauvegarde principale
    with open(series_path, 'w') as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 {len(unique_new_series)} nouvelles séries sauvegardées")
    print(f"📚 Total séries BOOKTIME: {len(existing_data)}")
    print(f"🔄 Backup créé: {backup_path}")
    
    return len(unique_new_series)

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Extracteur Séries Ultra Harvest")
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation sans sauvegarde')
    parser.add_argument('--min-confidence', type=int, default=70, help='Score confiance minimum')
    parser.add_argument('--min-volumes', type=int, default=2, help='Nombre minimum de volumes')
    
    args = parser.parse_args()
    
    print("💾 EXTRACTEUR SÉRIES DÉTECTÉES ULTRA HARVEST")
    print("=" * 50)
    print(f"🎯 Confiance minimum: {args.min_confidence}%")
    print(f"📚 Volumes minimum: {args.min_volumes}")
    print(f"🔍 Mode: {'DRY-RUN' if args.dry_run else 'SAUVEGARDE'}")
    print()
    
    # Extraction séries
    detected_series = extract_detected_series()
    
    if not detected_series:
        print("❌ Aucune série détectée")
        return
    
    # Filtrage et conversion
    valid_series = []
    
    for series_data in detected_series:
        series_name, author, volume_count, avg_confidence, source_strategy, first_detection = series_data
        
        # Filtres qualité
        if (avg_confidence >= args.min_confidence and 
            volume_count >= args.min_volumes and
            len(series_name) >= 3):
            
            series_entry = create_series_entry(series_data)
            valid_series.append(series_entry)
    
    print(f"✅ Séries validées: {len(valid_series)} / {len(detected_series)}")
    
    if valid_series:
        # Top 10 séries par confiance
        print("\n🏆 TOP 10 SÉRIES DÉTECTÉES:")
        print("-" * 80)
        print(f"{'Série':<30} {'Auteur':<20} {'Vol.':<5} {'Conf.':<6} {'Catégorie':<8}")
        print("-" * 80)
        
        for i, series in enumerate(valid_series[:10]):
            print(f"{series['name'][:29]:<30} {series['authors'][0][:19] if series['authors'] else 'N/A':<20} "
                  f"{series['volumes']:<5} {series['confidence_score']:<6} {series['category']:<8}")
        
        # Sauvegarde
        print()
        saved_count = save_series_to_booktime(valid_series, args.dry_run)
        
        if not args.dry_run:
            print(f"\n🎉 SUCCÈS! {saved_count} nouvelles séries ajoutées à BOOKTIME!")
    else:
        print("❌ Aucune série valide trouvée")

if __name__ == "__main__":
    main()