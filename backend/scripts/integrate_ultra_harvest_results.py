#!/usr/bin/env python3
"""
🔧 INTÉGRATION RÉSULTATS ULTRA HARVEST 100K
Script pour intégrer les séries détectées par l'Ultra Harvest dans la base principale
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Set
import re

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_tracking_data():
    """Charger données depuis base SQLite tracking"""
    db_path = Path('/app/data/ultra_harvest_tracking.db')
    
    if not db_path.exists():
        logger.error(f"❌ Base de données tracking non trouvée: {db_path}")
        return []
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Récupérer tous les livres avec séries détectées
            cursor = conn.execute("""
                SELECT open_library_key, title, author, series_name, confidence_score, 
                       processing_time_ms, source_strategy, isbn, publication_year
                FROM analyzed_books 
                WHERE series_detected = 1 AND series_name IS NOT NULL
                ORDER BY series_name, title
            """)
            
            books_data = cursor.fetchall()
            logger.info(f"📚 {len(books_data)} livres avec séries détectées récupérés")
            
            return books_data
            
    except Exception as e:
        logger.error(f"❌ Erreur lecture base tracking: {e}")
        return []

def group_books_by_series(books_data):
    """Grouper livres par série détectée"""
    series_candidates = defaultdict(lambda: {
        'books': [],
        'authors': set(),
        'confidence_scores': [],
        'detection_patterns': set(),
        'publication_years': [],
        'isbns': []
    })
    
    for book in books_data:
        (ol_key, title, author, series_name, confidence, processing_time, 
         strategy, isbn, pub_year) = book
        
        # Clé unique pour la série
        series_key = (series_name.strip(), author.strip() if author else "Unknown")
        
        series_candidates[series_key]['books'].append({
            'ol_key': ol_key,
            'title': title,
            'author': author,
            'isbn': isbn,
            'publication_year': pub_year
        })
        
        if author:
            series_candidates[series_key]['authors'].add(author)
        
        series_candidates[series_key]['confidence_scores'].append(confidence)
        series_candidates[series_key]['detection_patterns'].add(strategy)
        
        if pub_year:
            series_candidates[series_key]['publication_years'].append(pub_year)
        
        if isbn:
            series_candidates[series_key]['isbns'].append(isbn)
    
    logger.info(f"🎯 {len(series_candidates)} séries candidates identifiées")
    return series_candidates

def validate_and_create_series(series_candidates):
    """Valider et créer entrées série"""
    valid_series = []
    
    for (series_name, author), data in series_candidates.items():
        # Critères validation
        has_multiple_books = len(data['books']) >= 2
        good_confidence = max(data['confidence_scores']) >= 70  # Seuil plus bas pour récupérer plus
        meaningful_name = len(series_name) >= 3 and not series_name.isdigit()
        
        if has_multiple_books and good_confidence and meaningful_name:
            # Catégorisation intelligente
            category = categorize_series(data['books'])
            
            # Génération keywords
            keywords = generate_series_keywords(series_name, author, data['books'])
            
            # Variations titre
            variations = generate_title_variations(series_name)
            
            series_entry = {
                "name": series_name,
                "authors": list(data['authors']),
                "category": category,
                "volumes": len(data['books']),
                "keywords": keywords,
                "variations": variations,
                "exclusions": ["anthology", "collection", "omnibus", "complete"],
                "source": "ultra_harvest_100k",
                "confidence_score": max(data['confidence_scores']),
                "auto_generated": True,
                "detection_date": datetime.now().isoformat(),
                "ultra_harvest_info": {
                    "books_analyzed": len(data['books']),
                    "detection_patterns": list(data['detection_patterns']),
                    "avg_confidence": sum(data['confidence_scores']) / len(data['confidence_scores']),
                    "isbn_samples": data['isbns'][:3],
                    "publication_years": list(set(data['publication_years']))
                }
            }
            
            valid_series.append(series_entry)
    
    logger.info(f"✅ {len(valid_series)} séries validées pour intégration")
    return valid_series

def categorize_series(books):
    """Catégorisation intelligente série"""
    # Analyse titres pour indices catégorie
    all_titles = ' '.join([book['title'].lower() for book in books])
    
    # Détection manga
    manga_indicators = ['manga', 'anime', 'light novel', 'vol.', 'tome', 'naruto', 'one piece', 'dragon ball']
    if any(indicator in all_titles for indicator in manga_indicators):
        return 'manga'
    
    # Détection BD
    bd_indicators = ['astérix', 'tintin', 'spirou', 'gaston', 'bd', 'bande dessinée', 'comic']
    if any(indicator in all_titles for indicator in bd_indicators):
        return 'bd'
    
    # Par défaut: roman
    return 'roman'

def generate_series_keywords(series_name, author, books):
    """Génération mots-clés série"""
    keywords = []
    
    # Mots du titre série
    series_words = re.findall(r'\b\w{3,}\b', series_name.lower())
    keywords.extend(series_words)
    
    # Mots de l'auteur
    if author and author != "Unknown":
        author_words = re.findall(r'\b\w{3,}\b', author.lower())
        keywords.extend(author_words)
    
    # Mots fréquents dans titres
    all_titles = ' '.join([book['title'].lower() for book in books])
    title_words = re.findall(r'\b\w{4,}\b', all_titles)
    
    # Compter fréquence
    word_count = defaultdict(int)
    for word in title_words:
        word_count[word] += 1
    
    # Ajouter mots fréquents
    frequent_words = [word for word, count in word_count.items() if count >= 2]
    keywords.extend(frequent_words[:5])
    
    # Nettoyer et dédupliquer
    keywords = list(set([k for k in keywords if len(k) >= 3]))
    
    return keywords[:10]  # Limite à 10 mots-clés

def generate_title_variations(series_name):
    """Génération variations titre"""
    variations = [series_name]
    
    # Variations ponctuation
    variations.append(series_name.replace(':', ''))
    variations.append(series_name.replace(' - ', ' '))
    
    # Variations articles
    if series_name.startswith('The '):
        variations.append(series_name[4:])
    elif series_name.startswith('Les '):
        variations.append(series_name[4:])
    
    return list(set(variations))

def load_existing_series():
    """Charger séries existantes"""
    series_path = Path('/app/backend/data/extended_series_database.json')
    
    if not series_path.exists():
        logger.warning("⚠️ Fichier séries existant non trouvé, création nouveau")
        return []
    
    try:
        with open(series_path, 'r') as f:
            existing_series = json.load(f)
        
        logger.info(f"📚 {len(existing_series)} séries existantes chargées")
        return existing_series
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture séries existantes: {e}")
        return []

def integrate_new_series(new_series, existing_series):
    """Intégrer nouvelles séries en évitant doublons"""
    # Créer index séries existantes
    existing_names = {series['name'].lower() for series in existing_series}
    
    # Filtrer nouvelles séries
    unique_new_series = []
    for series in new_series:
        if series['name'].lower() not in existing_names:
            unique_new_series.append(series)
    
    logger.info(f"🆕 {len(unique_new_series)} nouvelles séries uniques à ajouter")
    
    # Combiner toutes les séries
    all_series = existing_series + unique_new_series
    
    return all_series, unique_new_series

def save_integrated_database(all_series):
    """Sauvegarder base de données intégrée"""
    series_path = Path('/app/backend/data/extended_series_database.json')
    
    # Backup de sécurité
    if series_path.exists():
        backup_path = Path(f'/app/backups/series_detection/backup_before_ultra_harvest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(series_path, 'r') as f_src, open(backup_path, 'w') as f_dst:
            f_dst.write(f_src.read())
        
        logger.info(f"💾 Backup créé: {backup_path}")
    
    # Sauvegarde base intégrée
    try:
        with open(series_path, 'w') as f:
            json.dump(all_series, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Base de données mise à jour: {len(all_series)} séries totales")
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde: {e}")
        raise

def main():
    """Fonction principale intégration"""
    logger.info("🚀 DÉMARRAGE INTÉGRATION ULTRA HARVEST 100K")
    
    try:
        # 1. Charger données tracking
        books_data = load_tracking_data()
        if not books_data:
            logger.error("❌ Aucune donnée à intégrer")
            return
        
        # 2. Grouper par séries
        series_candidates = group_books_by_series(books_data)
        
        # 3. Valider et créer séries
        new_series = validate_and_create_series(series_candidates)
        
        if not new_series:
            logger.warning("⚠️ Aucune série valide détectée")
            return
        
        # 4. Charger séries existantes
        existing_series = load_existing_series()
        
        # 5. Intégrer nouvelles séries
        all_series, unique_new = integrate_new_series(new_series, existing_series)
        
        # 6. Sauvegarder base intégrée
        save_integrated_database(all_series)
        
        # 7. Résultats finaux
        logger.info(f"""
✅ INTÉGRATION ULTRA HARVEST TERMINÉE !
======================================
📚 Livres analysés: {len(books_data):,}
🎯 Séries candidates: {len(series_candidates):,}
✅ Séries validées: {len(new_series):,}
🆕 Nouvelles ajoutées: {len(unique_new):,}
📊 Total base: {len(all_series):,}
======================================
""")
        
    except Exception as e:
        logger.error(f"❌ Erreur intégration: {e}")
        raise

if __name__ == "__main__":
    main()