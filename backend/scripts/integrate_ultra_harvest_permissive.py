#!/usr/bin/env python3
"""
🔧 INTÉGRATION ULTRA HARVEST - CRITÈRES AJUSTÉS POUR MAXIMUM RÉCUPÉRATION
Script optimisé pour capturer le maximum de nouvelles séries avec critères assouplis
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

def load_tracking_data_enhanced():
    """Charger données avec analyse détaillée"""
    db_path = Path('/app/data/ultra_harvest_tracking.db')
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Récupérer TOUS les livres avec séries détectées (critères assouplis)
            cursor = conn.execute("""
                SELECT open_library_key, title, author, series_name, confidence_score, 
                       processing_time_ms, source_strategy, isbn, publication_year
                FROM analyzed_books 
                WHERE series_detected = 1 AND series_name IS NOT NULL
                AND series_name != '' AND length(series_name) >= 3
                ORDER BY series_name, title
            """)
            
            books_data = cursor.fetchall()
            logger.info(f"📚 {len(books_data)} livres avec séries détectées récupérés (critères assouplis)")
            
            return books_data
            
    except Exception as e:
        logger.error(f"❌ Erreur lecture base tracking: {e}")
        return []

def group_books_by_series_enhanced(books_data):
    """Grouper livres par série avec critères assouplis"""
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
        
        # Nettoyage nom série
        clean_series_name = series_name.strip()
        clean_author = author.strip() if author else "Unknown"
        
        # Clé unique pour la série
        series_key = (clean_series_name, clean_author)
        
        series_candidates[series_key]['books'].append({
            'ol_key': ol_key,
            'title': title,
            'author': author,
            'isbn': isbn,
            'publication_year': pub_year,
            'confidence': confidence
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

def validate_and_create_series_permissive(series_candidates):
    """Validation avec critères très permissifs pour maximiser récupération"""
    valid_series = []
    stats = {
        'total_candidates': len(series_candidates),
        'single_book_accepted': 0,
        'multi_book_high_conf': 0,
        'multi_book_low_conf': 0,
        'rejected_short_name': 0,
        'rejected_low_conf_single': 0
    }
    
    for (series_name, author), data in series_candidates.items():
        book_count = len(data['books'])
        max_confidence = max(data['confidence_scores'])
        avg_confidence = sum(data['confidence_scores']) / len(data['confidence_scores'])
        
        # Critères TRÈS permissifs
        meaningful_name = len(series_name) >= 3 and not series_name.isdigit()
        
        # Règles d'acceptation assouplies
        accepted = False
        reason = ""
        
        if not meaningful_name:
            stats['rejected_short_name'] += 1
            continue
        
        if book_count >= 2:
            if max_confidence >= 50:  # Seuil baissé de 70 à 50
                accepted = True
                if max_confidence >= 70:
                    stats['multi_book_high_conf'] += 1
                    reason = "multi_book_high_confidence"
                else:
                    stats['multi_book_low_conf'] += 1
                    reason = "multi_book_medium_confidence"
        
        elif book_count == 1:
            if max_confidence >= 80:  # Seuil élevé pour livres uniques
                accepted = True
                stats['single_book_accepted'] += 1
                reason = "single_book_high_confidence"
            else:
                stats['rejected_low_conf_single'] += 1
                continue
        
        if accepted:
            # Catégorisation intelligente
            category = categorize_series_enhanced(data['books'])
            
            # Génération keywords
            keywords = generate_series_keywords_enhanced(series_name, author, data['books'])
            
            # Variations titre
            variations = generate_title_variations_enhanced(series_name)
            
            series_entry = {
                "name": series_name,
                "authors": list(data['authors']),
                "category": category,
                "volumes": book_count,
                "keywords": keywords,
                "variations": variations,
                "exclusions": ["anthology", "collection", "omnibus", "complete"],
                "source": "ultra_harvest_100k_permissive",
                "confidence_score": max_confidence,
                "avg_confidence": avg_confidence,
                "validation_reason": reason,
                "auto_generated": True,
                "detection_date": datetime.now().isoformat(),
                "ultra_harvest_info": {
                    "books_analyzed": len(data['books']),
                    "detection_patterns": list(data['detection_patterns']),
                    "avg_confidence": avg_confidence,
                    "isbn_samples": data['isbns'][:3],
                    "publication_years": list(set(data['publication_years']))
                }
            }
            
            valid_series.append(series_entry)
    
    logger.info(f"✅ {len(valid_series)} séries validées avec critères permissifs")
    logger.info(f"📊 Statistiques validation:")
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")
    
    return valid_series, stats

def categorize_series_enhanced(books):
    """Catégorisation améliorée avec plus de patterns"""
    all_titles = ' '.join([book['title'].lower() for book in books])
    
    # Détection manga (patterns étendus)
    manga_indicators = [
        'manga', 'anime', 'light novel', 'vol.', 'tome', 'naruto', 'one piece', 
        'dragon ball', 'bleach', 'fullmetal', 'berserk', 'attack on titan',
        'my hero academia', 'demon slayer', 'jujutsu kaisen', 'chainsaw man',
        'japanese', 'shonen', 'shojo', 'seinen', 'josei'
    ]
    if any(indicator in all_titles for indicator in manga_indicators):
        return 'manga'
    
    # Détection BD (patterns étendus)
    bd_indicators = [
        'astérix', 'tintin', 'spirou', 'gaston', 'thorgal', 'lucky luke',
        'bd', 'bande dessinée', 'comic', 'blake et mortimer', 'yoko tsuno',
        'largo winch', 'tuniques bleues', 'schtroumpfs', 'marsupilami'
    ]
    if any(indicator in all_titles for indicator in bd_indicators):
        return 'bd'
    
    # Par défaut: roman
    return 'roman'

def generate_series_keywords_enhanced(series_name, author, books):
    """Génération mots-clés améliorée"""
    keywords = []
    
    # Mots du titre série (nettoyés)
    series_words = re.findall(r'\b\w{3,}\b', series_name.lower())
    keywords.extend(series_words)
    
    # Mots de l'auteur
    if author and author != "Unknown":
        author_words = re.findall(r'\b\w{3,}\b', author.lower())
        keywords.extend(author_words)
    
    # Mots fréquents dans titres
    all_titles = ' '.join([book['title'].lower() for book in books])
    title_words = re.findall(r'\b\w{4,}\b', all_titles)
    
    # Compter fréquence et ajouter mots fréquents
    word_count = defaultdict(int)
    for word in title_words:
        if word not in ['volume', 'tome', 'book', 'part', 'chapter']:
            word_count[word] += 1
    
    frequent_words = [word for word, count in word_count.items() if count >= 2]
    keywords.extend(frequent_words[:8])
    
    # Nettoyer et dédupliquer
    keywords = list(set([k for k in keywords if len(k) >= 3 and k.isalpha()]))
    
    return keywords[:12]  # Limite étendue à 12 mots-clés

def generate_title_variations_enhanced(series_name):
    """Génération variations étendues"""
    variations = [series_name]
    
    # Variations ponctuation
    variations.append(series_name.replace(':', ''))
    variations.append(series_name.replace(' - ', ' '))
    variations.append(series_name.replace('.', ''))
    variations.append(series_name.replace(',', ''))
    
    # Variations articles
    if series_name.startswith('The '):
        variations.append(series_name[4:])
    elif series_name.startswith('Les '):
        variations.append(series_name[4:])
    elif series_name.startswith('La '):
        variations.append(series_name[3:])
    elif series_name.startswith('Le '):
        variations.append(series_name[3:])
    
    # Variations espaces/tirets
    variations.append(series_name.replace(' ', '-'))
    variations.append(series_name.replace('-', ' '))
    
    return list(set([v for v in variations if len(v) >= 3]))

def load_existing_series_with_analysis():
    """Charger séries existantes avec analyse détaillée"""
    series_path = Path('/app/backend/data/extended_series_database.json')
    
    try:
        with open(series_path, 'r') as f:
            existing_series = json.load(f)
        
        # Créer index détaillé
        existing_index = {}
        existing_names_lower = set()
        
        for series in existing_series:
            name_lower = series['name'].lower().strip()
            existing_names_lower.add(name_lower)
            existing_index[name_lower] = series
        
        logger.info(f"📚 {len(existing_series)} séries existantes chargées")
        logger.info(f"📊 {len(existing_names_lower)} noms uniques (après normalisation)")
        
        return existing_series, existing_index, existing_names_lower
        
    except Exception as e:
        logger.error(f"❌ Erreur lecture séries existantes: {e}")
        return [], {}, set()

def integrate_new_series_detailed(new_series, existing_index, existing_names_lower):
    """Intégration avec analyse détaillée des rejets/acceptations"""
    unique_new_series = []
    duplicate_analysis = []
    
    for series in new_series:
        series_name_lower = series['name'].lower().strip()
        
        if series_name_lower not in existing_names_lower:
            unique_new_series.append(series)
        else:
            # Analyser le doublon pour documentation
            existing_series = existing_index[series_name_lower]
            duplicate_analysis.append({
                'new_name': series['name'],
                'existing_name': existing_series['name'],
                'new_confidence': series['confidence_score'],
                'new_volumes': series['volumes'],
                'existing_volumes': existing_series.get('volumes', 'N/A'),
                'new_source': series['source']
            })
    
    logger.info(f"🆕 {len(unique_new_series)} nouvelles séries uniques à ajouter")
    logger.info(f"🔄 {len(duplicate_analysis)} doublons détectés et ignorés")
    
    return unique_new_series, duplicate_analysis

def save_detailed_report(stats, duplicate_analysis, unique_new_series):
    """Sauvegarder rapport détaillé de l'opération"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "operation": "ultra_harvest_integration_permissive",
        "validation_stats": stats,
        "duplicates_found": len(duplicate_analysis),
        "new_series_added": len(unique_new_series),
        "duplicate_samples": duplicate_analysis[:20],  # Échantillon de doublons
        "new_series_samples": [
            {
                "name": s['name'],
                "category": s['category'],
                "volumes": s['volumes'],
                "confidence": s['confidence_score'],
                "reason": s['validation_reason']
            }
            for s in unique_new_series[:20]
        ]
    }
    
    report_path = Path(f'/app/reports/ultra_harvest_integration_permissive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 Rapport détaillé sauvegardé: {report_path}")
    return report_path

def main():
    """Fonction principale avec critères permissifs"""
    logger.info("🚀 DÉMARRAGE INTÉGRATION ULTRA HARVEST - CRITÈRES PERMISSIFS")
    
    try:
        # 1. Charger données tracking (critères assouplis)
        books_data = load_tracking_data_enhanced()
        if not books_data:
            logger.error("❌ Aucune donnée à intégrer")
            return
        
        # 2. Grouper par séries
        series_candidates = group_books_by_series_enhanced(books_data)
        
        # 3. Valider avec critères permissifs
        new_series, validation_stats = validate_and_create_series_permissive(series_candidates)
        
        if not new_series:
            logger.warning("⚠️ Aucune série valide détectée")
            return
        
        # 4. Charger séries existantes avec analyse
        existing_series, existing_index, existing_names_lower = load_existing_series_with_analysis()
        
        # 5. Intégrer avec analyse détaillée
        unique_new, duplicate_analysis = integrate_new_series_detailed(
            new_series, existing_index, existing_names_lower
        )
        
        # 6. Sauvegarder rapport avant modification
        report_path = save_detailed_report(validation_stats, duplicate_analysis, unique_new)
        
        if unique_new:
            # 7. Combiner et sauvegarder
            all_series = existing_series + unique_new
            
            # Backup sécurisé
            series_path = Path('/app/backend/data/extended_series_database.json')
            backup_path = Path(f'/app/backups/series_detection/backup_before_permissive_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(series_path, 'r') as f_src, open(backup_path, 'w') as f_dst:
                f_dst.write(f_src.read())
            
            # Sauvegarde base intégrée
            with open(series_path, 'w') as f:
                json.dump(all_series, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Backup créé: {backup_path}")
            logger.info(f"✅ Base de données mise à jour: {len(all_series)} séries totales")
        
        # 8. Résultats finaux détaillés
        logger.info(f"""
✅ INTÉGRATION PERMISSIVE TERMINÉE !
====================================
📚 Livres analysés: {len(books_data):,}
🎯 Séries candidates: {len(series_candidates):,}
✅ Séries validées: {len(new_series):,}
🆕 Nouvelles uniques: {len(unique_new):,}
🔄 Doublons ignorés: {len(duplicate_analysis):,}
📊 Total base finale: {len(existing_series) + len(unique_new):,}
📄 Rapport détaillé: {report_path}
====================================
""")
        
        # Afficher échantillon nouvelles séries
        if unique_new:
            logger.info("🆕 ÉCHANTILLON NOUVELLES SÉRIES AJOUTÉES:")
            for i, series in enumerate(unique_new[:10]):
                logger.info(f"   {i+1:2d}. {series['name']} ({series['category']}, {series['volumes']} vol, conf:{series['confidence_score']:.0f})")
        
    except Exception as e:
        logger.error(f"❌ Erreur intégration: {e}")
        raise

if __name__ == "__main__":
    main()