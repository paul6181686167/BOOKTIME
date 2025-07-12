#!/usr/bin/env python3
"""
🔄 INTÉGRATEUR INTELLIGENT ULTRA HARVEST → BOOKTIME
Ajoute automatiquement les nouvelles séries de qualité à BookTime
"""

import sqlite3
import json
import os
import time
from datetime import datetime
from collections import defaultdict

def load_booktime_series():
    """Charge la base BookTime actuelle"""
    series_file = "/app/backend/data/extended_series_database.json"
    
    if os.path.exists(series_file):
        with open(series_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_ultra_harvest_candidates():
    """Récupère les meilleures candidates Ultra Harvest"""
    
    db_file = "/app/data/ultra_harvest_tracking.db"
    
    if not os.path.exists(db_file):
        return []
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Critères plus permissifs pour voir plus de résultats
    cursor.execute("""
        SELECT series_name, COUNT(*) as volume_count,
               AVG(confidence_score) as avg_confidence,
               GROUP_CONCAT(DISTINCT author) as authors,
               MAX(title) as sample_title
        FROM analyzed_books 
        WHERE series_detected = 1 
          AND series_name IS NOT NULL 
          AND confidence_score > 60
        GROUP BY series_name
        HAVING COUNT(*) >= 2
        ORDER BY AVG(confidence_score) DESC, COUNT(*) DESC
        LIMIT 100
    """)
    
    candidates = []
    for row in cursor.fetchall():
        series_name, volume_count, avg_confidence, authors, sample_title = row
        
        # Nettoyer le nom
        clean_name = series_name.strip()
        if len(clean_name) < 3:
            continue
        
        # Déterminer la catégorie
        category = "roman"  # Par défaut
        name_lower = clean_name.lower()
        sample_lower = (sample_title or "").lower()
        
        # Détection manga
        if any(word in name_lower or word in sample_lower for word in [
            "manga", "naruto", "bleach", "one piece", "dragon ball", "fullmetal alchemist",
            "death note", "attack on titan", "demon slayer", "my hero academia"
        ]):
            category = "manga"
        
        # Détection BD
        elif any(word in name_lower or word in sample_lower for word in [
            "tintin", "asterix", "gaston", "spirou", "bd", "comic", "bande dessinee"
        ]):
            category = "bd"
        
        candidate = {
            "name": clean_name,
            "category": category,
            "score": int(avg_confidence),
            "keywords": [clean_name.lower()],
            "authors": [authors.split(",")[0].strip()] if authors else [],
            "variations": [clean_name],
            "volumes": volume_count,
            "languages": ["fr", "en"],
            "description": f"Série détectée par Ultra Harvest avec {volume_count} volumes",
            "first_published": 2000,
            "status": "ongoing",
            "source": "ultra_harvest_100k_intelligent",
            "detection_date": datetime.now().isoformat(),
            "ultra_harvest_confidence": avg_confidence,
            "sample_title": sample_title
        }
        
        candidates.append(candidate)
    
    conn.close()
    return candidates

def filter_quality_series(candidates, existing_series):
    """Filtre les séries de haute qualité vraiment nouvelles"""
    
    existing_names = {s.get("name", "").lower().strip() for s in existing_series}
    quality_series = []
    
    for candidate in candidates:
        name = candidate["name"]
        name_lower = name.lower()
        
        # Déjà existe ?
        if name_lower in existing_names:
            continue
        
        # Filtres qualité stricts
        
        # 1. Exclure termes problématiques
        problematic_terms = [
            "student edition", "teacher", "textbook", "manual", "guide", 
            "handbook", "cookbook", "academic", "university", "collection",
            "anthology", "best of", "selected works", "complete", "integral"
        ]
        
        if any(term in name_lower for term in problematic_terms):
            continue
        
        # 2. Minimum qualité
        if candidate["score"] < 75 or candidate["volumes"] < 3:
            continue
        
        # 3. Longueur nom raisonnable
        if len(name) < 3 or len(name) > 50:
            continue
        
        # 4. Éviter noms trop génériques
        generic_terms = ["book", "tome", "volume", "part", "chapter", "episode"]
        if name_lower in generic_terms:
            continue
        
        quality_series.append(candidate)
    
    return quality_series

def integrate_series_to_booktime(new_series):
    """Intègre les nouvelles séries dans BookTime"""
    
    if not new_series:
        return 0
    
    # Backup base actuelle
    series_file = "/app/backend/data/extended_series_database.json"
    backup_file = f"/app/backend/data/extended_series_database_backup_ultra_harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    existing_series = load_booktime_series()
    
    # Sauvegarde
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(existing_series, f, ensure_ascii=False, indent=2)
    
    # Ajouter nouvelles séries
    updated_series = existing_series + new_series
    
    # Sauvegarder
    with open(series_file, 'w', encoding='utf-8') as f:
        json.dump(updated_series, f, ensure_ascii=False, indent=2)
    
    return len(new_series)

def display_integration_status():
    """Affiche le statut d'intégration"""
    
    print(f"🔄 INTÉGRATION ULTRA HARVEST → BOOKTIME")
    print(f"{'='*55}")
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    # Charger base actuelle
    existing_series = load_booktime_series()
    print(f"📚 Base BookTime actuelle: {len(existing_series):,} séries")
    
    # Analyser candidates Ultra Harvest
    candidates = get_ultra_harvest_candidates()
    print(f"🔍 Candidates Ultra Harvest: {len(candidates)} séries")
    
    # Filtrer qualité
    quality_series = filter_quality_series(candidates, existing_series)
    print(f"✨ Séries qualité à ajouter: {len(quality_series)}")
    
    if quality_series:
        print(f"\n🎯 NOUVELLES SÉRIES DE QUALITÉ:")
        for i, serie in enumerate(quality_series[:10], 1):
            print(f"  {i:2d}. {serie['name'][:35]:<35} | {serie['category']:<6} | {serie['volumes']:2d} vol | {serie['score']:2d}%")
        
        if len(quality_series) > 10:
            print(f"     ... et {len(quality_series) - 10} autres séries de qualité")
        
        # Intégrer
        integrated = integrate_series_to_booktime(quality_series)
        print(f"\n✅ {integrated} nouvelles séries intégrées à BookTime!")
        print(f"📊 Total séries BookTime: {len(existing_series) + integrated:,}")
        
        return integrated
    else:
        print("\nℹ️ Aucune nouvelle série de qualité suffisante trouvée")
        return 0

def main():
    """Intégration continue avec affichage détaillé"""
    
    print("🚀 DÉMARRAGE INTÉGRATEUR INTELLIGENT ULTRA HARVEST")
    print("=" * 60)
    
    total_integrated = 0
    
    try:
        while True:
            new_count = display_integration_status()
            total_integrated += new_count
            
            print(f"\n💫 Total intégré cette session: {total_integrated} séries")
            print("-" * 60)
            
            # Attendre 3 minutes
            time.sleep(180)
            
    except KeyboardInterrupt:
        print(f"\n👋 Intégrateur arrêté")
        print(f"📊 Total intégré: {total_integrated} nouvelles séries")

if __name__ == "__main__":
    # Exécution unique pour voir l'état
    display_integration_status()