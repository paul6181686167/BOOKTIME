#!/usr/bin/env python3
"""
🔄 MISE À JOUR SYSTÈME DÉTECTION SÉRIES
Integration des nouvelles séries Open Library dans le système de détection BOOKTIME

Fonctionnalités :
- Chargement des nouvelles séries depuis la base de données
- Mise à jour du fichier EXTENDED_SERIES_DATABASE JavaScript
- Synchronisation avec le système de détection frontend
- Validation et tests de cohérence
- Backup automatique avant mise à jour

Utilisation :
python update_series_detection.py
python update_series_detection.py --backup-only
python update_series_detection.py --validate
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import argparse
import logging
from typing import List, Dict, Set

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SeriesDetectionUpdater:
    """Mise à jour système de détection séries"""
    
    def __init__(self):
        self.data_dir = Path('/app/backend/data')
        self.frontend_dir = Path('/app/frontend/src/data')
        self.backup_dir = Path('/app/backups/series_detection')
        
        # Fichiers cibles
        self.json_series_file = self.data_dir / 'extended_series_database.json'
        self.js_series_file = self.frontend_dir / 'extendedSeriesDatabase.js'
        
        # Création dossiers
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> bool:
        """Création backup avant mise à jour"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = self.backup_dir / f"backup_{timestamp}"
            backup_subdir.mkdir(exist_ok=True)
            
            # Backup fichier JSON
            if self.json_series_file.exists():
                shutil.copy2(self.json_series_file, backup_subdir / 'extended_series_database.json')
                logger.info(f"Backup JSON créé: {backup_subdir}")
            
            # Backup fichier JS
            if self.js_series_file.exists():
                shutil.copy2(self.js_series_file, backup_subdir / 'extendedSeriesDatabase.js')
                logger.info(f"Backup JS créé: {backup_subdir}")
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur création backup: {str(e)}")
            return False
    
    def load_series_data(self) -> List[Dict]:
        """Chargement données séries depuis JSON"""
        try:
            if not self.json_series_file.exists():
                logger.warning("Fichier séries JSON non trouvé")
                return []
            
            with open(self.json_series_file, 'r', encoding='utf-8') as f:
                series_data = json.load(f)
            
            logger.info(f"Chargé {len(series_data)} séries depuis JSON")
            return series_data
        
        except Exception as e:
            logger.error(f"Erreur chargement séries: {str(e)}")
            return []
    
    def validate_series_data(self, series_data: List[Dict]) -> bool:
        """Validation structure des données séries"""
        required_fields = ['name', 'authors', 'category', 'volumes', 'keywords', 'variations']
        
        for i, series in enumerate(series_data):
            # Vérification champs requis
            for field in required_fields:
                if field not in series:
                    logger.error(f"Série {i}: Champ manquant '{field}'")
                    return False
            
            # Validation types
            if not isinstance(series['name'], str) or not series['name'].strip():
                logger.error(f"Série {i}: Nom invalide")
                return False
            
            if not isinstance(series['authors'], list) or not series['authors']:
                logger.error(f"Série {i}: Auteurs invalides")
                return False
            
            if series['category'] not in ['roman', 'bd', 'manga']:
                logger.error(f"Série {i}: Catégorie invalide '{series['category']}'")
                return False
            
            if not isinstance(series['volumes'], int) or series['volumes'] < 1:
                logger.error(f"Série {i}: Nombre de volumes invalide")
                return False
        
        logger.info(f"Validation réussie pour {len(series_data)} séries")
        return True
    
    def deduplicate_series(self, series_data: List[Dict]) -> List[Dict]:
        """Déduplication des séries par nom"""
        seen_names = set()
        deduplicated = []
        duplicates_count = 0
        
        for series in series_data:
            name_key = series['name'].lower().strip()
            
            if name_key not in seen_names:
                seen_names.add(name_key)
                deduplicated.append(series)
            else:
                duplicates_count += 1
                logger.debug(f"Doublon ignoré: {series['name']}")
        
        logger.info(f"Déduplication: {duplicates_count} doublons supprimés, {len(deduplicated)} séries uniques")
        return deduplicated
    
    def sort_series_data(self, series_data: List[Dict]) -> List[Dict]:
        """Tri des séries par catégorie puis par nom"""
        def sort_key(series):
            category_order = {'roman': 0, 'bd': 1, 'manga': 2}
            return (category_order.get(series['category'], 3), series['name'].lower())
        
        return sorted(series_data, key=sort_key)
    
    def generate_js_content(self, series_data: List[Dict]) -> str:
        """Génération contenu JavaScript pour le frontend"""
        
        # En-tête du fichier
        js_content = f"""/**
 * 🚀 EXTENDED SERIES DATABASE - BOOKTIME
 * Base de données étendue des séries populaires
 * 
 * Dernière mise à jour: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
 * Nombre de séries: {len(series_data)}
 * 
 * Généré automatiquement par: update_series_detection.py
 * Source: Open Library + base manuelle
 */

// Export pour modules ES6
export const EXTENDED_SERIES_DATABASE = [
"""
        
        # Génération des entrées
        for i, series in enumerate(series_data):
            js_content += "  {\n"
            js_content += f"    name: {json.dumps(series['name'], ensure_ascii=False)},\n"
            js_content += f"    authors: {json.dumps(series['authors'], ensure_ascii=False)},\n"
            js_content += f"    category: {json.dumps(series['category'])},\n"
            js_content += f"    volumes: {series['volumes']},\n"
            js_content += f"    keywords: {json.dumps(series['keywords'], ensure_ascii=False)},\n"
            js_content += f"    variations: {json.dumps(series['variations'], ensure_ascii=False)},\n"
            
            # Champs optionnels
            if series.get('first_published'):
                js_content += f"    first_published: {json.dumps(series['first_published'])},\n"
            
            if series.get('status'):
                js_content += f"    status: {json.dumps(series['status'])},\n"
            
            if series.get('description'):
                js_content += f"    description: {json.dumps(series['description'], ensure_ascii=False)},\n"
            
            if series.get('subjects'):
                js_content += f"    subjects: {json.dumps(series['subjects'], ensure_ascii=False)},\n"
            
            if series.get('languages'):
                js_content += f"    languages: {json.dumps(series['languages'])},\n"
            
            if series.get('translations'):
                js_content += f"    translations: {json.dumps(series['translations'], ensure_ascii=False)},\n"
            
            if series.get('source'):
                js_content += f"    source: {json.dumps(series['source'])},\n"
            
            # Fermeture objet
            js_content += "  }"
            
            # Virgule sauf pour le dernier élément
            if i < len(series_data) - 1:
                js_content += ","
            
            js_content += "\n"
        
        # Fermeture tableau et statistiques
        js_content += f"""];

// Statistiques base de données
export const SERIES_STATS = {{
  total_series: {len(series_data)},
  by_category: {{
    roman: {len([s for s in series_data if s['category'] == 'roman'])},
    bd: {len([s for s in series_data if s['category'] == 'bd'])},
    manga: {len([s for s in series_data if s['category'] == 'manga'])}
  }},
  total_volumes: {sum(s['volumes'] for s in series_data)},
  avg_volumes_per_series: {sum(s['volumes'] for s in series_data) / len(series_data):.1f},
  last_updated: "{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
}};

// Fonctions utilitaires
export const getSeriesByCategory = (category) => {{
  return EXTENDED_SERIES_DATABASE.filter(series => series.category === category);
}};

export const getSeriesByAuthor = (author) => {{
  return EXTENDED_SERIES_DATABASE.filter(series => 
    series.authors.some(a => a.toLowerCase().includes(author.toLowerCase()))
  );
}};

export const searchSeries = (query) => {{
  const queryLower = query.toLowerCase();
  return EXTENDED_SERIES_DATABASE.filter(series => 
    series.name.toLowerCase().includes(queryLower) ||
    series.authors.some(a => a.toLowerCase().includes(queryLower)) ||
    series.keywords.some(k => k.toLowerCase().includes(queryLower))
  );
}};

// Export par défaut
export default EXTENDED_SERIES_DATABASE;
"""
        
        return js_content
    
    def save_js_file(self, js_content: str) -> bool:
        """Sauvegarde fichier JavaScript"""
        try:
            with open(self.js_series_file, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            logger.info(f"Fichier JS sauvegardé: {self.js_series_file}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur sauvegarde JS: {str(e)}")
            return False
    
    def update_package_json(self) -> bool:
        """Mise à jour package.json si nécessaire"""
        try:
            package_file = Path('/app/frontend/package.json')
            if not package_file.exists():
                return True
            
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Vérification si mise à jour nécessaire
            # (pour l'instant, pas de modifications nécessaires)
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur mise à jour package.json: {str(e)}")
            return False
    
    def run_tests(self, series_data: List[Dict]) -> bool:
        """Tests de cohérence des données"""
        try:
            logger.info("🧪 Exécution tests de cohérence")
            
            # Test 1: Unicité des noms
            names = [s['name'] for s in series_data]
            if len(names) != len(set(names)):
                logger.error("Test échoué: Noms non uniques")
                return False
            
            # Test 2: Catégories valides
            valid_categories = {'roman', 'bd', 'manga'}
            for series in series_data:
                if series['category'] not in valid_categories:
                    logger.error(f"Test échoué: Catégorie invalide '{series['category']}'")
                    return False
            
            # Test 3: Auteurs non vides
            for series in series_data:
                if not series['authors'] or not all(a.strip() for a in series['authors']):
                    logger.error(f"Test échoué: Auteurs invalides pour '{series['name']}'")
                    return False
            
            # Test 4: Mots-clés cohérents
            for series in series_data:
                if len(series['keywords']) == 0:
                    logger.warning(f"Attention: Aucun mot-clé pour '{series['name']}'")
            
            # Test 5: Variations cohérentes
            for series in series_data:
                if len(series['variations']) == 0:
                    logger.warning(f"Attention: Aucune variation pour '{series['name']}'")
            
            logger.info("✅ Tous les tests de cohérence passés")
            return True
        
        except Exception as e:
            logger.error(f"Erreur tests: {str(e)}")
            return False
    
    def generate_report(self, series_data: List[Dict]) -> str:
        """Génération rapport de mise à jour"""
        report = f"""
🔄 RAPPORT MISE À JOUR SYSTÈME DÉTECTION SÉRIES
==============================================

📊 STATISTIQUES GLOBALES
- Nombre total de séries: {len(series_data)}
- Répartition par catégorie:
  • Romans: {len([s for s in series_data if s['category'] == 'roman'])}
  • BD: {len([s for s in series_data if s['category'] == 'bd'])}
  • Mangas: {len([s for s in series_data if s['category'] == 'manga'])}

📈 MÉTRIQUES CONTENU
- Total volumes: {sum(s['volumes'] for s in series_data)}
- Moyenne volumes/série: {sum(s['volumes'] for s in series_data) / len(series_data):.1f}
- Série avec le plus de volumes: {max(series_data, key=lambda s: s['volumes'])['name']} ({max(s['volumes'] for s in series_data)} volumes)

🔍 MOTS-CLÉS DÉTECTION
- Total mots-clés: {sum(len(s['keywords']) for s in series_data)}
- Moyenne mots-clés/série: {sum(len(s['keywords']) for s in series_data) / len(series_data):.1f}
- Total variations: {sum(len(s['variations']) for s in series_data)}

📚 TOP 10 SÉRIES PAR VOLUMES
"""
        
        top_series = sorted(series_data, key=lambda s: s['volumes'], reverse=True)[:10]
        for i, series in enumerate(top_series, 1):
            authors = ', '.join(series['authors'][:2])
            report += f"{i}. {series['name']} - {authors} ({series['volumes']} volumes, {series['category']})\n"
        
        report += f"""
🔄 MISE À JOUR EFFECTUÉE
- Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Fichier JS: {self.js_series_file}
- Fichier JSON: {self.json_series_file}
- Backup: {self.backup_dir}

🎯 IMPACT SUR DÉTECTION
- Séries automatiquement détectées: {len(series_data)}
- Livres individuels potentiellement masqués: Estimation basée sur mots-clés
- Amélioration expérience utilisateur: Moins de doublons livre/série

⚡ PERFORMANCE ATTENDUE
- Détection: <5ms par livre maintenue
- Masquage: Cohérent bibliothèque + recherche
- Cache: Rechargement automatique au redémarrage

🚀 PROCHAINES ÉTAPES
1. Redémarrage frontend pour prise en compte
2. Tests fonctionnels masquage intelligent
3. Vérification détection séries existantes
4. Surveillance logs détection automatique
"""
        
        return report
    
    def run_update(self, backup_only: bool = False, validate_only: bool = False) -> Dict:
        """Exécution mise à jour complète"""
        
        logger.info("🔄 Démarrage mise à jour système détection séries")
        
        # Création backup
        if not self.create_backup():
            return {'success': False, 'error': 'Échec création backup'}
        
        if backup_only:
            logger.info("✅ Backup uniquement - Terminé")
            return {'success': True, 'message': 'Backup créé avec succès'}
        
        # Chargement données
        series_data = self.load_series_data()
        if not series_data:
            return {'success': False, 'error': 'Aucune donnée série trouvée'}
        
        # Validation
        if not self.validate_series_data(series_data):
            return {'success': False, 'error': 'Validation des données échouée'}
        
        if validate_only:
            logger.info("✅ Validation uniquement - Terminé")
            return {'success': True, 'message': 'Validation réussie'}
        
        # Déduplication et tri
        series_data = self.deduplicate_series(series_data)
        series_data = self.sort_series_data(series_data)
        
        # Tests de cohérence
        if not self.run_tests(series_data):
            return {'success': False, 'error': 'Tests de cohérence échoués'}
        
        # Génération fichier JS
        js_content = self.generate_js_content(series_data)
        if not self.save_js_file(js_content):
            return {'success': False, 'error': 'Échec sauvegarde fichier JS'}
        
        # Mise à jour package.json
        if not self.update_package_json():
            return {'success': False, 'error': 'Échec mise à jour package.json'}
        
        # Génération rapport
        report = self.generate_report(series_data)
        
        # Sauvegarde rapport
        report_file = Path(f'/app/logs/series_update_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info("✅ Mise à jour système détection terminée avec succès")
        
        return {
            'success': True,
            'series_count': len(series_data),
            'js_file': str(self.js_series_file),
            'report_file': str(report_file),
            'backup_dir': str(self.backup_dir)
        }


def main():
    """Fonction principale CLI"""
    parser = argparse.ArgumentParser(description='Mise à jour système détection séries')
    parser.add_argument('--backup-only',
                       action='store_true',
                       help='Créer uniquement un backup')
    parser.add_argument('--validate',
                       action='store_true',
                       help='Valider uniquement les données')
    
    args = parser.parse_args()
    
    # Création dossiers
    Path('/app/logs').mkdir(exist_ok=True)
    
    # Exécution mise à jour
    updater = SeriesDetectionUpdater()
    result = updater.run_update(
        backup_only=args.backup_only,
        validate_only=args.validate
    )
    
    if result['success']:
        print(f"\n✅ MISE À JOUR RÉUSSIE")
        if 'series_count' in result:
            print(f"📊 Séries traitées: {result['series_count']}")
            print(f"📄 Fichier JS: {result['js_file']}")
            print(f"📋 Rapport: {result['report_file']}")
        print(f"💾 Backup: {result.get('backup_dir', 'Créé')}")
    else:
        print(f"\n❌ ERREUR: {result['error']}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())