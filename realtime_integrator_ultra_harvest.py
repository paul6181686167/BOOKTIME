#!/usr/bin/env python3
"""
🔄 INTÉGRATEUR TEMPS RÉEL ULTRA HARVEST → BOOKTIME
Capture et intègre les nouvelles séries au fur et à mesure de leur détection
"""

import sqlite3
import json
import os
import time
from datetime import datetime

def get_current_ultra_harvest_stats():
    """Statistiques actuelles Ultra Harvest"""
    
    db_file = "/app/data/ultra_harvest_tracking.db"
    
    if not os.path.exists(db_file):
        return None
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Stats principales
    cursor.execute('SELECT COUNT(*) FROM analyzed_books')
    total_books = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM analyzed_books WHERE series_detected = 1')
    series_books = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT series_name) FROM analyzed_books WHERE series_detected = 1 AND series_name IS NOT NULL')
    unique_series = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_books': total_books,
        'series_books': series_books,
        'unique_series': unique_series,
        'detection_rate': (series_books / total_books * 100) if total_books > 0 else 0
    }

def scan_for_emerging_series():
    """Scan pour nouvelles séries émergentes avec critères très permissifs"""
    
    db_file = "/app/data/ultra_harvest_tracking.db"
    series_file = "/app/backend/data/extended_series_database.json"
    
    # Charger base existante
    if os.path.exists(series_file):
        with open(series_file, 'r', encoding='utf-8') as f:
            existing_series = json.load(f)
        existing_names = {s.get('name', '').lower().strip() for s in existing_series}
    else:
        existing_names = set()
    
    if not os.path.exists(db_file):
        return []
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Recherche avec critères très permissifs pour nouvelles séries
    cursor.execute('''
        SELECT series_name, COUNT(*) as volume_count,
               AVG(confidence_score) as avg_confidence,
               GROUP_CONCAT(DISTINCT author) as authors,
               MAX(title) as sample_title,
               MIN(analysis_date) as first_detection
        FROM analyzed_books 
        WHERE series_detected = 1 
          AND series_name IS NOT NULL 
          AND confidence_score > 60
        GROUP BY series_name
        HAVING COUNT(*) >= 2
        ORDER BY MIN(analysis_date) DESC, AVG(confidence_score) DESC
        LIMIT 50
    ''')
    
    emerging_series = []
    
    for row in cursor.fetchall():
        series_name, volume_count, avg_confidence, authors, sample_title, first_detection = row
        
        clean_name = series_name.strip()
        name_lower = clean_name.lower()
        
        # Vérifier si vraiment nouveau
        if name_lower in existing_names:
            continue
        
        # Critères de base
        if len(clean_name) < 3 or len(clean_name) > 60:
            continue
        
        # Filtres qualité modérés (plus permissifs)
        problematic_terms = [
            'student edition', 'teacher edition', 'textbook', 'coursebook',
            'academic', 'university press', 'cookbook', 'recipe'
        ]
        
        if any(term in name_lower for term in problematic_terms):
            continue
        
        # Déterminer catégorie intelligemment
        category = "roman"  # Par défaut
        
        # Détection manga (patterns étendus)
        manga_patterns = [
            'naruto', 'bleach', 'one piece', 'dragon ball', 'fullmetal alchemist',
            'death note', 'attack on titan', 'demon slayer', 'my hero academia',
            'tokyo ghoul', 'hunter x hunter', 'jojo', 'slam dunk'
        ]
        
        if any(pattern in name_lower for pattern in manga_patterns):
            category = "manga"
        
        # Détection BD
        bd_patterns = [
            'tintin', 'asterix', 'gaston', 'spirou', 'lucky luke', 'thorgal',
            'bd', 'bande dessinee', 'comic'
        ]
        
        if any(pattern in name_lower for pattern in bd_patterns):
            category = "bd"
        
        # Créer entrée série
        serie_entry = {
            "name": clean_name,
            "category": category,
            "score": max(60, int(avg_confidence)),  # Score minimum 60
            "keywords": [clean_name.lower().replace(',', '').strip()],
            "authors": [authors.split(",")[0].strip()] if authors else ["Unknown"],
            "variations": [clean_name, clean_name.replace(',', '').strip()],
            "volumes": volume_count,
            "languages": ["fr", "en"],
            "description": f"Série émergente détectée par Ultra Harvest - {volume_count} volumes",
            "first_published": 2020,  # Supposer récent
            "status": "ongoing",
            "source": "ultra_harvest_100k_emerging",
            "detection_date": datetime.now().isoformat(),
            "first_detection": first_detection,
            "ultra_harvest_confidence": avg_confidence,
            "sample_title": sample_title
        }
        
        emerging_series.append(serie_entry)
    
    conn.close()
    return emerging_series

def integrate_emerging_series(emerging_series):
    """Intègre les séries émergentes dans BookTime"""
    
    if not emerging_series:
        return 0
    
    series_file = "/app/backend/data/extended_series_database.json"
    
    # Backup
    backup_file = f"/app/backend/data/extended_series_database_backup_emerging_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Charger base existante
    if os.path.exists(series_file):
        with open(series_file, 'r', encoding='utf-8') as f:
            existing_series = json.load(f)
    else:
        existing_series = []
    
    # Sauvegarde
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(existing_series, f, ensure_ascii=False, indent=2)
    
    # Ajouter séries émergentes
    updated_series = existing_series + emerging_series
    
    # Sauvegarder
    with open(series_file, 'w', encoding='utf-8') as f:
        json.dump(updated_series, f, ensure_ascii=False, indent=2)
    
    return len(emerging_series)

def main():
    """Monitoring et intégration en temps réel"""
    
    print("🔄 INTÉGRATEUR TEMPS RÉEL ULTRA HARVEST → BOOKTIME")
    print("=" * 65)
    
    total_integrated = 0
    last_check_books = 0
    
    try:
        while True:
            # Stats actuelles
            stats = get_current_ultra_harvest_stats()
            
            if stats:
                print(f"\\n🚀 ULTRA HARVEST - {datetime.now().strftime('%H:%M:%S')}")
                print(f"├── 📚 Livres analysés: {stats['total_books']:,}")
                print(f"├── 🎯 Avec séries: {stats['series_books']:,}")
                print(f"├── ✨ Séries uniques: {stats['unique_series']:,}")
                print(f"└── 📊 Taux détection: {stats['detection_rate']:.1f}%")
                
                # Chercher nouvelles séries si progression
                if stats['total_books'] > last_check_books + 1000:  # Chaque 1000 livres
                    print(f"\\n🔍 Scan nouvelles séries émergentes...")
                    
                    emerging = scan_for_emerging_series()
                    
                    if emerging:
                        print(f"✨ {len(emerging)} nouvelles séries émergentes trouvées!")
                        
                        # Afficher top 5
                        for i, serie in enumerate(emerging[:5], 1):
                            print(f"  {i}. {serie['name'][:35]:<35} | {serie['category']:<6} | {serie['volumes']:2d} vol | {serie['score']:2d}%")
                        
                        if len(emerging) > 5:
                            print(f"     ... et {len(emerging) - 5} autres")
                        
                        # Intégrer
                        integrated = integrate_emerging_series(emerging)
                        total_integrated += integrated
                        
                        print(f"✅ {integrated} séries intégrées à BookTime!")
                        
                    else:
                        print(f"ℹ️ Aucune nouvelle série émergente")
                    
                    last_check_books = stats['total_books']
                
                print(f"💫 Total intégré: {total_integrated} séries")
            
            else:
                print(f"⏸️ Ultra Harvest en attente...")
            
            print("-" * 65)
            
            # Attendre 2 minutes
            time.sleep(120)
            
    except KeyboardInterrupt:
        print(f"\\n👋 Intégrateur temps réel arrêté")
        print(f"📊 Total intégré: {total_integrated} nouvelles séries")

if __name__ == "__main__":
    main()