#!/usr/bin/env python3
"""
🎯 ORCHESTRATEUR AUTOMATISATION SÉRIES OPEN LIBRARY
Pipeline complète d'automatisation pour BOOKTIME

Fonctionnalités :
- Exécution automatique récupération séries Open Library
- Mise à jour système de détection
- Redémarrage services si nécessaire
- Validation end-to-end
- Rapport consolidé

Utilisation :
python series_automation_pipeline.py
python series_automation_pipeline.py --quick --limit=20
python series_automation_pipeline.py --full --limit=100
python series_automation_pipeline.py --test-only
"""

import asyncio
import subprocess
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SeriesAutomationPipeline:
    """Pipeline complète d'automatisation séries"""
    
    def __init__(self):
        self.scripts_dir = Path('/app/backend/scripts')
        self.logs_dir = Path('/app/logs')
        self.reports_dir = Path('/app/reports')
        
        # Création dossiers
        self.logs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        self.pipeline_stats = {
            'start_time': datetime.now(),
            'steps_completed': 0,
            'total_steps': 5,
            'errors': [],
            'series_added': 0,
            'series_updated': 0
        }
    
    def log_step(self, step_name: str, success: bool, details: str = ""):
        """Logging étape pipeline"""
        self.pipeline_stats['steps_completed'] += 1
        status = "✅" if success else "❌"
        
        logger.info(f"{status} [{self.pipeline_stats['steps_completed']}/{self.pipeline_stats['total_steps']}] {step_name}")
        
        if details:
            logger.info(f"   {details}")
        
        if not success:
            self.pipeline_stats['errors'].append(f"{step_name}: {details}")
    
    async def step_1_fetch_series(self, mode: str = 'popular', limit: int = 50) -> Dict:
        """Étape 1: Récupération séries Open Library"""
        logger.info("🔍 ÉTAPE 1: Récupération séries Open Library")
        
        try:
            # Exécution script récupération
            cmd = [
                sys.executable,
                str(self.scripts_dir / 'open_library_series_auto.py'),
                '--mode', mode,
                '--limit', str(limit)
            ]
            
            logger.info(f"Commande: {' '.join(cmd)}")
            
            # Exécution avec capture sortie
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Parsing résultat depuis stdout
                output = stdout.decode('utf-8')
                
                # Extraction métriques (parsing basique)
                series_added = 0
                duplicates_skipped = 0
                
                lines = output.split('\n')
                for line in lines:
                    if 'Séries ajoutées:' in line:
                        try:
                            series_added = int(line.split(':')[1].strip())
                        except:
                            pass
                    elif 'Doublons ignorés:' in line:
                        try:
                            duplicates_skipped = int(line.split(':')[1].strip())
                        except:
                            pass
                
                self.pipeline_stats['series_added'] = series_added
                self.log_step("Récupération séries Open Library", True, 
                             f"{series_added} séries ajoutées, {duplicates_skipped} doublons ignorés")
                
                return {
                    'success': True,
                    'series_added': series_added,
                    'duplicates_skipped': duplicates_skipped,
                    'output': output
                }
            
            else:
                error_msg = stderr.decode('utf-8')
                self.log_step("Récupération séries Open Library", False, 
                             f"Code erreur: {process.returncode}, {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'return_code': process.returncode
                }
        
        except Exception as e:
            self.log_step("Récupération séries Open Library", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def step_2_update_detection(self) -> Dict:
        """Étape 2: Mise à jour système détection"""
        logger.info("🔄 ÉTAPE 2: Mise à jour système détection")
        
        try:
            # Exécution script mise à jour
            cmd = [
                sys.executable,
                str(self.scripts_dir / 'update_series_detection.py')
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                # Parsing résultat
                series_count = 0
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Séries traitées:' in line:
                        try:
                            series_count = int(line.split(':')[1].strip())
                        except:
                            pass
                
                self.pipeline_stats['series_updated'] = series_count
                self.log_step("Mise à jour système détection", True,
                             f"{series_count} séries dans le système")
                
                return {
                    'success': True,
                    'series_count': series_count,
                    'output': result.stdout
                }
            
            else:
                self.log_step("Mise à jour système détection", False,
                             f"Code erreur: {result.returncode}, {result.stderr}")
                
                return {
                    'success': False,
                    'error': result.stderr,
                    'return_code': result.returncode
                }
        
        except Exception as e:
            self.log_step("Mise à jour système détection", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def step_3_restart_services(self) -> Dict:
        """Étape 3: Redémarrage services"""
        logger.info("🔄 ÉTAPE 3: Redémarrage services")
        
        try:
            # Redémarrage frontend pour prise en compte nouvelles séries
            cmd = ['sudo', 'supervisorctl', 'restart', 'frontend']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log_step("Redémarrage services", True,
                             "Frontend redémarré avec succès")
                return {'success': True, 'output': result.stdout}
            
            else:
                self.log_step("Redémarrage services", False,
                             f"Erreur redémarrage: {result.stderr}")
                return {'success': False, 'error': result.stderr}
        
        except Exception as e:
            self.log_step("Redémarrage services", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def step_4_validate_integration(self) -> Dict:
        """Étape 4: Validation intégration"""
        logger.info("🧪 ÉTAPE 4: Validation intégration")
        
        try:
            # Vérification fichiers générés
            js_file = Path('/app/frontend/src/data/extendedSeriesDatabase.js')
            json_file = Path('/app/backend/data/extended_series_database.json')
            
            if not js_file.exists():
                self.log_step("Validation intégration", False,
                             "Fichier JS manquant")
                return {'success': False, 'error': 'Fichier JS manquant'}
            
            if not json_file.exists():
                self.log_step("Validation intégration", False,
                             "Fichier JSON manquant")
                return {'success': False, 'error': 'Fichier JSON manquant'}
            
            # Vérification contenu JS
            with open(js_file, 'r', encoding='utf-8') as f:
                js_content = f.read()
            
            if 'EXTENDED_SERIES_DATABASE' not in js_content:
                self.log_step("Validation intégration", False,
                             "Contenu JS invalide")
                return {'success': False, 'error': 'Contenu JS invalide'}
            
            # Vérification contenu JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if not isinstance(json_data, list) or len(json_data) == 0:
                self.log_step("Validation intégration", False,
                             "Données JSON invalides")
                return {'success': False, 'error': 'Données JSON invalides'}
            
            # Validation structure
            required_fields = ['name', 'authors', 'category', 'volumes']
            for series in json_data[:5]:  # Vérification échantillon
                for field in required_fields:
                    if field not in series:
                        self.log_step("Validation intégration", False,
                                     f"Champ manquant: {field}")
                        return {'success': False, 'error': f'Champ manquant: {field}'}
            
            self.log_step("Validation intégration", True,
                         f"Fichiers validés: {len(json_data)} séries")
            
            return {
                'success': True,
                'series_count': len(json_data),
                'js_file_size': js_file.stat().st_size,
                'json_file_size': json_file.stat().st_size
            }
        
        except Exception as e:
            self.log_step("Validation intégration", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def step_5_generate_report(self, step_results: List[Dict]) -> Dict:
        """Étape 5: Génération rapport final"""
        logger.info("📊 ÉTAPE 5: Génération rapport final")
        
        try:
            # Compilation statistiques
            total_series = self.pipeline_stats['series_added']
            total_updated = self.pipeline_stats['series_updated']
            duration = datetime.now() - self.pipeline_stats['start_time']
            
            # Génération rapport
            report = f"""
🎯 RAPPORT PIPELINE AUTOMATISATION SÉRIES OPEN LIBRARY
======================================================

📊 RÉSUMÉ EXÉCUTION
- Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Durée totale: {duration}
- Étapes complétées: {self.pipeline_stats['steps_completed']}/{self.pipeline_stats['total_steps']}
- Statut: {'✅ SUCCÈS' if len(self.pipeline_stats['errors']) == 0 else '❌ ERREURS'}

🔢 STATISTIQUES SÉRIES
- Nouvelles séries ajoutées: {total_series}
- Séries totales dans système: {total_updated}
- Doublons ignorés: {step_results[0].get('duplicates_skipped', 0) if step_results else 0}

📋 DÉTAIL ÉTAPES
"""
            
            # Détail des étapes
            step_names = [
                "Récupération séries Open Library",
                "Mise à jour système détection",
                "Redémarrage services",
                "Validation intégration",
                "Génération rapport final"
            ]
            
            for i, (step_name, step_result) in enumerate(zip(step_names, step_results)):
                status = "✅" if step_result.get('success', False) else "❌"
                report += f"{i+1}. {status} {step_name}\n"
                
                if not step_result.get('success', False):
                    report += f"   Erreur: {step_result.get('error', 'Inconnue')}\n"
            
            # Erreurs
            if self.pipeline_stats['errors']:
                report += f"\n❌ ERREURS RENCONTRÉES ({len(self.pipeline_stats['errors'])})\n"
                for error in self.pipeline_stats['errors']:
                    report += f"- {error}\n"
            
            # Prochaines étapes
            report += f"""
🚀 PROCHAINES ÉTAPES
- Tester fonctionnalités masquage intelligent
- Vérifier détection automatique séries
- Surveiller logs détection
- Planifier prochaine exécution automatisation

📁 FICHIERS GÉNÉRÉS
- Données JSON: /app/backend/data/extended_series_database.json
- Système JS: /app/frontend/src/data/extendedSeriesDatabase.js
- Logs: /app/logs/
- Rapports: /app/reports/

⚡ PERFORMANCE
- Séries par minute: {total_series / max(1, duration.total_seconds() / 60):.1f}
- Efficacité: {(total_series / max(1, total_series + step_results[0].get('duplicates_skipped', 0))) * 100:.1f}% (nouvelles/total)
"""
            
            # Sauvegarde rapport
            report_file = self.reports_dir / f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.log_step("Génération rapport final", True,
                         f"Rapport sauvegardé: {report_file}")
            
            return {
                'success': True,
                'report_file': str(report_file),
                'report_content': report
            }
        
        except Exception as e:
            self.log_step("Génération rapport final", False, str(e))
            return {'success': False, 'error': str(e)}
    
    async def run_pipeline(self, mode: str = 'popular', limit: int = 50, test_only: bool = False) -> Dict:
        """Exécution pipeline complète"""
        
        logger.info("🚀 DÉMARRAGE PIPELINE AUTOMATISATION SÉRIES")
        logger.info(f"Mode: {mode}, Limit: {limit}, Test: {test_only}")
        
        step_results = []
        
        # Étape 1: Récupération séries
        if not test_only:
            result_1 = await self.step_1_fetch_series(mode, limit)
            step_results.append(result_1)
            
            if not result_1['success']:
                logger.error("❌ Échec étape 1 - Arrêt pipeline")
                return {'success': False, 'error': 'Échec récupération séries'}
        
        else:
            # Mode test - simulation
            self.log_step("Récupération séries Open Library (TEST)", True, "Mode test activé")
            step_results.append({'success': True, 'test_mode': True})
        
        # Étape 2: Mise à jour détection
        result_2 = self.step_2_update_detection()
        step_results.append(result_2)
        
        if not result_2['success']:
            logger.error("❌ Échec étape 2 - Arrêt pipeline")
            return {'success': False, 'error': 'Échec mise à jour détection'}
        
        # Étape 3: Redémarrage services
        result_3 = self.step_3_restart_services()
        step_results.append(result_3)
        
        if not result_3['success']:
            logger.warning("⚠️ Échec étape 3 - Continuation pipeline")
        
        # Étape 4: Validation
        result_4 = self.step_4_validate_integration()
        step_results.append(result_4)
        
        if not result_4['success']:
            logger.error("❌ Échec étape 4 - Arrêt pipeline")
            return {'success': False, 'error': 'Échec validation'}
        
        # Étape 5: Rapport
        result_5 = self.step_5_generate_report(step_results)
        step_results.append(result_5)
        
        # Résultat final
        success = all(r['success'] for r in step_results)
        
        if success:
            logger.info("🎉 PIPELINE TERMINÉ AVEC SUCCÈS")
        else:
            logger.error("❌ PIPELINE TERMINÉ AVEC ERREURS")
        
        return {
            'success': success,
            'step_results': step_results,
            'total_duration': datetime.now() - self.pipeline_stats['start_time'],
            'series_added': self.pipeline_stats['series_added'],
            'series_updated': self.pipeline_stats['series_updated'],
            'errors': self.pipeline_stats['errors']
        }


async def main():
    """Fonction principale CLI"""
    parser = argparse.ArgumentParser(description='Pipeline automatisation séries')
    parser.add_argument('--mode',
                       choices=['popular', 'authors', 'categories'],
                       default='popular',
                       help='Mode de récupération')
    parser.add_argument('--limit',
                       type=int,
                       default=50,
                       help='Nombre maximum de séries')
    parser.add_argument('--quick',
                       action='store_true',
                       help='Exécution rapide (limit=20)')
    parser.add_argument('--full',
                       action='store_true',
                       help='Exécution complète (limit=100)')
    parser.add_argument('--test-only',
                       action='store_true',
                       help='Mode test sans récupération')
    
    args = parser.parse_args()
    
    # Ajustement limite selon mode
    if args.quick:
        args.limit = 20
    elif args.full:
        args.limit = 100
    
    # Création pipeline
    pipeline = SeriesAutomationPipeline()
    
    # Exécution
    result = await pipeline.run_pipeline(
        mode=args.mode,
        limit=args.limit,
        test_only=args.test_only
    )
    
    # Affichage résultat
    if result['success']:
        print(f"\n🎉 PIPELINE RÉUSSI")
        print(f"📊 Séries ajoutées: {result['series_added']}")
        print(f"🔄 Séries dans système: {result['series_updated']}")
        print(f"⏱️ Durée: {result['total_duration']}")
        
        if result['step_results'] and result['step_results'][-1]['success']:
            print(f"📋 Rapport: {result['step_results'][-1]['report_file']}")
    
    else:
        print(f"\n❌ PIPELINE ÉCHOUÉ")
        print(f"🚨 Erreurs: {len(result['errors'])}")
        for error in result['errors']:
            print(f"   - {error}")
        
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))