#!/usr/bin/env python3
"""
🔄 INTÉGRATION AUTOMATIQUE ULTRA HARVEST EN TEMPS RÉEL
Intègre automatiquement les nouvelles séries détectées par Ultra Harvest
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import os
from collections import defaultdict

def load_existing_series():
    """Charge la base de séries existante"""
    series_file = "/app/backend/data/extended_series_database.json"
    
    if os.path.exists(series_file):
        with open(series_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_new_series_from_tracking():
    """Récupère les nouvelles séries depuis la base tracking"""
    
    db_file = "/app/data/ultra_harvest_tracking.db"
    
    if not os.path.exists(db_file):
        return []
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Récupérer toutes les séries détectées avec confiance > 80
    cursor.execute("""
        SELECT DISTINCT series_name, COUNT(*) as volume_count,
               AVG(confidence_score) as avg_confidence,
               GROUP_CONCAT(DISTINCT author) as authors
        FROM analyzed_books 
        WHERE series_detected = 1 
          AND series_name IS NOT NULL 
          AND confidence_score > 80
        GROUP BY series_name
        HAVING COUNT(*) >= 2
        ORDER BY COUNT(*) DESC
    """)
    
    new_series = []
    for row in cursor.fetchall():
        series_name, volume_count, avg_confidence, authors = row
        
        # Nettoyer le nom de série
        clean_name = series_name.strip()
        if len(clean_name) < 3:  # Ignore séries avec noms trop courts
            continue
            
        # Déterminer la catégorie (approximation basée sur les patterns)
        category = "roman"  # Par défaut
        if any(word in clean_name.lower() for word in ["manga", "naruto", "one piece", "dragon ball"]):
            category = "manga"
        elif any(word in clean_name.lower() for word in ["bd", "comic", "tintin", "asterix"]):
            category = "bd"
        
        # Créer l'entrée série
        serie_entry = {
            "name": clean_name,
            "category": category,
            "score": int(avg_confidence),
            "keywords": [clean_name.lower()],
            "authors": [authors.split(",")[0].strip()] if authors else [],
            "variations": [clean_name],
            "volumes": volume_count,
            "languages": ["fr", "en"],
            "description": f"Série détectée par Ultra Harvest avec {volume_count} volumes",
            "first_published": 2000,  # Approximation
            "status": "ongoing",
            "source": "ultra_harvest_100k_auto",
            "detection_date": datetime.now().isoformat(),
            "ultra_harvest_confidence": avg_confidence
        }
        
        new_series.append(serie_entry)
    
    conn.close()
    return new_series

def filter_unique_series(new_series, existing_series):
    """Filtre les séries vraiment nouvelles"""
    
    existing_names = {s.get("name", "").lower() for s in existing_series}
    unique_series = []
    
    for serie in new_series:
        if serie["name"].lower() not in existing_names:
            # Vérifications qualité supplémentaires
            name = serie["name"]
            
            # Exclure termes problématiques
            if any(term in name.lower() for term in [
                "student edition", "teacher", "textbook", "manual", 
                "guide", "handbook", "cookbook", "academic"
            ]):
                continue
                
            # Minimum de qualité
            if serie["score"] >= 85 and serie["volumes"] >= 2:
                unique_series.append(serie)
    
    return unique_series

def integrate_new_series():
    """Intègre les nouvelles séries dans la base"""
    
    print(f"🔄 INTÉGRATION AUTOMATIQUE - {datetime.now().strftime('%H:%M:%S')}")
    
    # Charger base existante
    existing_series = load_existing_series()
    print(f"📚 Base actuelle: {len(existing_series)} séries")
    
    # Récupérer nouvelles séries
    new_series = get_new_series_from_tracking()
    print(f"🆕 Nouvelles détections: {len(new_series)} séries candidates")
    
    # Filtrer pour ne garder que les vraiment nouvelles
    unique_series = filter_unique_series(new_series, existing_series)
    print(f"✨ Séries uniques à ajouter: {len(unique_series)}")
    
    if unique_series:
        # Backup de la base actuelle
        backup_file = f"/app/backend/data/extended_series_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, ensure_ascii=False, indent=2)
        
        # Ajouter les nouvelles séries
        updated_series = existing_series + unique_series
        
        # Sauvegarder la base mise à jour
        series_file = "/app/backend/data/extended_series_database.json"
        with open(series_file, 'w', encoding='utf-8') as f:
            json.dump(updated_series, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(unique_series)} nouvelles séries intégrées!")
        print(f"📚 Total séries: {len(updated_series)}")
        
        # Afficher les nouvelles séries ajoutées
        for i, serie in enumerate(unique_series[:5], 1):
            print(f"  {i}. {serie['name']} ({serie['category']}) - {serie['volumes']} volumes")
        
        if len(unique_series) > 5:
            print(f"  ... et {len(unique_series) - 5} autres séries")
    
    else:
        print("ℹ️ Aucune nouvelle série unique à intégrer")
    
    return len(unique_series)

def main():
    """Intégration continue toutes les 2 minutes"""
    
    print("🚀 DÉMARRAGE INTÉGRATION AUTOMATIQUE ULTRA HARVEST")
    print("=" * 60)
    
    integration_count = 0
    
    try:
        while True:
            new_count = integrate_new_series()
            integration_count += new_count
            
            print(f"💫 Total intégré cette session: {integration_count} séries")
            print("-" * 60)
            
            # Attendre 2 minutes
            time.sleep(120)
            
    except KeyboardInterrupt:
        print(f"\n👋 Intégration automatique arrêtée")
        print(f"📊 Total intégré: {integration_count} nouvelles séries")

if __name__ == "__main__":
    main()