#!/usr/bin/env python3
"""
🔧 INTÉGRATION SÉRIES ULTRA HARVEST EN ATTENTE
Script pour identifier et intégrer les séries détectées mais pas encore ajoutées
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import hashlib

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_current_series():
    """Charger la base actuelle des séries"""
    series_db_path = Path('/app/backend/data/extended_series_database.json')
    
    try:
        with open(series_db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {series['name'].lower().strip() for series in data}
    except Exception as e:
        logger.error(f"❌ Erreur lecture base séries: {e}")
        return set()

def load_ultra_harvest_backups():
    """Charger toutes les données des backups Ultra Harvest récents"""
    backup_dir = Path('/app/backups/series_detection')
    ultra_harvest_files = [
        'backup_ultra_harvest_20250712_100905.json',
        'backup_ultra_harvest_20250712_102352.json',
        'backup_20250712_013649_mega_harvest.json',
        'backup_20250712_114252_mega_expansion.json',
        'backup_20250712_113447_mega_expansion.json',
        'backup_20250712_114505_ultra_expansion.json',
        'backup_20250712_113650_ultra_expansion.json'
    ]
    
    all_series = []
    
    for filename in ultra_harvest_files:
        file_path = backup_dir / filename
        if file_path.exists():
            try:
                logger.info(f"📁 Traitement {filename}...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Filtrer les séries valides seulement
                        valid_series = [s for s in data if 'name' in s and len(s.get('name', '').strip()) >= 3]
                        all_series.extend(valid_series)
                        logger.info(f"📁 {filename}: {len(valid_series)} séries valides chargées")
                    else:
                        logger.warning(f"⚠️ Format inattendu dans {filename}")
            except Exception as e:
                logger.error(f"❌ Erreur lecture {filename}: {e}")
    
    return all_series

def identify_new_series(all_harvest_series, current_series):
    """Identifier les nouvelles séries non encore intégrées"""
    new_series = []
    duplicates = 0
    
    for series in all_harvest_series:
        if 'name' in series:
            series_name = series['name'].lower().strip()
            
            # Filtrer les séries déjà présentes
            if series_name not in current_series:
                # Vérifications qualité basiques
                if (len(series_name) >= 3 and 
                    series_name not in ['', 'unknown', 'n/a'] and
                    not series_name.startswith('error')):
                    new_series.append(series)
                    current_series.add(series_name)  # Éviter doublons internes
                else:
                    logger.debug(f"🚫 Série rejetée (qualité): {series_name}")
            else:
                duplicates += 1
    
    logger.info(f"🆕 {len(new_series)} nouvelles séries identifiées")
    logger.info(f"🔄 {duplicates} doublons évités")
    
    return new_series

def enhance_series_metadata(new_series):
    """Améliorer les métadonnées des nouvelles séries"""
    enhanced_series = []
    
    for series in new_series:
        enhanced = series.copy()
        
        # Valeurs par défaut si manquantes
        if 'category' not in enhanced:
            enhanced['category'] = 'roman'  # Défaut
        
        if 'volumes' not in enhanced:
            enhanced['volumes'] = 1
            
        if 'confidence' not in enhanced:
            enhanced['confidence'] = 80
            
        if 'source' not in enhanced:
            enhanced['source'] = 'ultra_harvest_pending'
            
        # Timestamp ajout
        enhanced['date_added'] = datetime.now().isoformat()
        
        # Génération ID unique
        series_id = hashlib.md5(
            f"{enhanced['name']}_{enhanced.get('category', 'roman')}".encode()
        ).hexdigest()[:12]
        enhanced['id'] = series_id
        
        enhanced_series.append(enhanced)
    
    return enhanced_series

def save_expanded_database(current_data, new_series):
    """Sauvegarder la base étendue avec nouvelles séries"""
    
    # Backup de sécurité
    backup_path = f"/app/backups/series_detection/backup_before_pending_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Backup sauvegardé: {backup_path}")
    except Exception as e:
        logger.error(f"❌ Erreur backup: {e}")
        return False
    
    # Extension base avec nouvelles séries
    extended_database = current_data + new_series
    
    # Sauvegarde base étendue
    db_path = Path('/app/backend/data/extended_series_database.json')
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(extended_database, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Base étendue sauvegardée: {len(extended_database)} séries totales")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde: {e}")
        return False

def generate_integration_report(new_series):
    """Générer rapport d'intégration"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'operation': 'pending_series_integration',
        'new_series_added': len(new_series),
        'categories_breakdown': defaultdict(int),
        'sample_series': new_series[:20] if new_series else []
    }
    
    # Analyse par catégorie
    for series in new_series:
        category = series.get('category', 'unknown')
        report['categories_breakdown'][category] += 1
    
    # Sauvegarde rapport
    report_path = f"/app/reports/pending_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 Rapport généré: {report_path}")
    except Exception as e:
        logger.error(f"❌ Erreur rapport: {e}")
    
    return report

def main():
    """Processus principal d'intégration"""
    logger.info("🚀 DÉMARRAGE INTÉGRATION SÉRIES EN ATTENTE")
    
    # 1. Charger base actuelle
    logger.info("📚 Chargement base séries actuelle...")
    current_series_names = load_current_series()
    logger.info(f"📊 {len(current_series_names)} séries actuellement en base")
    
    # Charger données complètes pour extension
    try:
        with open('/app/backend/data/extended_series_database.json', 'r', encoding='utf-8') as f:
            current_data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Erreur chargement données complètes: {e}")
        return False
    
    # 2. Charger données Ultra Harvest
    logger.info("🔍 Chargement données Ultra Harvest...")
    all_harvest_series = load_ultra_harvest_backups()
    logger.info(f"📊 {len(all_harvest_series)} séries dans backups Ultra Harvest")
    
    # 3. Identifier nouvelles séries
    logger.info("🆕 Identification nouvelles séries...")
    new_series = identify_new_series(all_harvest_series, current_series_names)
    
    if not new_series:
        logger.info("✅ Aucune nouvelle série à intégrer - Base à jour")
        return True
    
    # 4. Améliorer métadonnées
    logger.info("🔧 Amélioration métadonnées...")
    enhanced_series = enhance_series_metadata(new_series)
    
    # 5. Sauvegarder base étendue
    logger.info("💾 Sauvegarde base étendue...")
    if save_expanded_database(current_data, enhanced_series):
        # 6. Générer rapport
        logger.info("📊 Génération rapport...")
        report = generate_integration_report(enhanced_series)
        
        logger.info("="*60)
        logger.info("🎯 INTÉGRATION RÉUSSIE !")
        logger.info(f"📈 {len(enhanced_series)} nouvelles séries ajoutées")
        logger.info(f"📚 {len(current_data) + len(enhanced_series)} séries totales en base")
        logger.info("="*60)
        
        return True
    else:
        logger.error("❌ Échec sauvegarde")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)