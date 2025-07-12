#!/usr/bin/env python3
"""
📊 MONITORING ULTRA HARVEST PRODUCTION
Script de surveillance et validation des exécutions Ultra Harvest automatiques
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/ultra_harvest_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraHarvestMonitor:
    """Monitoring et validation Ultra Harvest production"""
    
    def __init__(self):
        self.db_path = Path('/app/data/ultra_harvest_tracking.db')
        self.logs_dir = Path('/app/logs')
        self.sessions_file = Path('/app/data/ultra_harvest_sessions.json')
        
    def check_database_health(self):
        """Vérification santé base de données tracking"""
        try:
            if not self.db_path.exists():
                logger.warning("⚠️ Base données tracking introuvable")
                return {
                    'status': 'warning',
                    'message': 'Base données tracking non initialisée',
                    'recommendations': ['Lancer Ultra Harvest pour initialiser']
                }
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_books,
                        COUNT(CASE WHEN series_detected = 1 THEN 1 END) as series_found,
                        MAX(analysis_date) as last_analysis
                    FROM analyzed_books
                """)
                
                result = cursor.fetchone()
                total_books, series_found, last_analysis = result
                
                detection_rate = (series_found / total_books * 100) if total_books > 0 else 0
                
                # Analyse temporelle
                if last_analysis:
                    last_date = datetime.fromisoformat(last_analysis.replace('Z', '+00:00').replace('+00:00', ''))
                    days_since = (datetime.now() - last_date).days
                else:
                    days_since = float('inf')
                
                # Détermination statut
                if days_since > 10:
                    status = 'error'
                    message = f"Aucune analyse depuis {days_since} jours"
                elif days_since > 7:
                    status = 'warning' 
                    message = f"Dernière analyse il y a {days_since} jours"
                elif detection_rate < 1:
                    status = 'warning'
                    message = f"Taux détection très bas: {detection_rate:.1f}%"
                else:
                    status = 'success'
                    message = "Base données saine"
                
                return {
                    'status': status,
                    'message': message,
                    'metrics': {
                        'total_books': total_books,
                        'series_found': series_found, 
                        'detection_rate': detection_rate,
                        'days_since_last': days_since,
                        'last_analysis': last_analysis
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification DB: {e}")
            return {
                'status': 'error',
                'message': f'Erreur base données: {str(e)}',
                'recommendations': ['Vérifier intégrité base données']
            }
    
    def check_recent_logs(self):
        """Analyse logs récents pour détecter problèmes"""
        try:
            # Chercher logs Ultra Harvest récents (7 derniers jours)
            recent_logs = []
            for log_file in self.logs_dir.glob("ultra_harvest_weekly_*.log"):
                if log_file.stat().st_mtime > (datetime.now() - timedelta(days=7)).timestamp():
                    recent_logs.append(log_file)
            
            if not recent_logs:
                return {
                    'status': 'warning',
                    'message': 'Aucun log Ultra Harvest récent trouvé',
                    'recommendations': ['Vérifier exécution cron job']
                }
            
            # Analyse du log le plus récent
            latest_log = max(recent_logs, key=lambda f: f.stat().st_mtime)
            
            with open(latest_log, 'r') as f:
                log_content = f.read()
            
            # Recherche patterns succès/échec
            success_patterns = [
                "✅ ULTRA HARVEST RÉUSSI",
                "ULTRA HARVEST 100K TERMINÉ",
                "success: True"
            ]
            
            error_patterns = [
                "❌ ERREUR",
                "ERROR",
                "FAILED",
                "Exception",
                "success: False"
            ]
            
            has_success = any(pattern in log_content for pattern in success_patterns)
            has_errors = any(pattern in log_content for pattern in error_patterns)
            
            if has_success and not has_errors:
                status = 'success'
                message = f"Dernière exécution réussie ({latest_log.name})"
            elif has_errors:
                status = 'error'
                message = f"Erreurs détectées dans {latest_log.name}"
            else:
                status = 'warning'
                message = f"Statut exécution unclear dans {latest_log.name}"
            
            return {
                'status': status,
                'message': message,
                'latest_log': str(latest_log),
                'log_analysis': {
                    'has_success_indicators': has_success,
                    'has_error_indicators': has_errors,
                    'log_size_kb': latest_log.stat().st_size // 1024
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse logs: {e}")
            return {
                'status': 'error',
                'message': f'Erreur analyse logs: {str(e)}'
            }
    
    def check_cron_schedule(self):
        """Vérification configuration cron (approximative)"""
        try:
            # Vérifier si script weekly existe et est exécutable
            weekly_script = Path('/app/scripts/weekly_ultra_harvest.sh')
            
            if not weekly_script.exists():
                return {
                    'status': 'error',
                    'message': 'Script weekly Ultra Harvest introuvable',
                    'recommendations': ['Installer script weekly_ultra_harvest.sh']
                }
            
            if not weekly_script.stat().st_mode & 0o111:
                return {
                    'status': 'warning', 
                    'message': 'Script weekly non exécutable',
                    'recommendations': ['chmod +x /app/scripts/weekly_ultra_harvest.sh']
                }
            
            return {
                'status': 'success',
                'message': 'Script weekly disponible et exécutable',
                'script_path': str(weekly_script)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erreur vérification cron: {str(e)}'
            }
    
    def generate_weekly_report(self):
        """Génération rapport hebdomadaire complet"""
        logger.info("📊 Génération rapport monitoring Ultra Harvest")
        
        # Collecte toutes les vérifications
        db_check = self.check_database_health()
        logs_check = self.check_recent_logs()
        cron_check = self.check_cron_schedule()
        
        # Statut global
        all_statuses = [db_check['status'], logs_check['status'], cron_check['status']]
        
        if 'error' in all_statuses:
            global_status = 'error'
        elif 'warning' in all_statuses:
            global_status = 'warning'
        else:
            global_status = 'success'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'global_status': global_status,
            'checks': {
                'database': db_check,
                'logs': logs_check,
                'cron': cron_check
            },
            'summary': {
                'total_books_analyzed': db_check.get('metrics', {}).get('total_books', 0),
                'total_series_found': db_check.get('metrics', {}).get('series_found', 0),
                'detection_rate': db_check.get('metrics', {}).get('detection_rate', 0),
                'days_since_last_run': db_check.get('metrics', {}).get('days_since_last', 0)
            }
        }
        
        # Sauvegarde rapport
        report_file = Path(f'/app/logs/ultra_harvest_weekly_report_{datetime.now().strftime("%Y%m%d")}.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Affichage console
        self._print_report(report)
        
        return report
    
    def _print_report(self, report):
        """Affichage rapport formaté"""
        status_emoji = {
            'success': '✅',
            'warning': '⚠️', 
            'error': '❌'
        }
        
        global_emoji = status_emoji.get(report['global_status'], '❓')
        
        print(f"""
📊 RAPPORT MONITORING ULTRA HARVEST PRODUCTION
=============================================
{global_emoji} Statut Global: {report['global_status'].upper()}
📅 Timestamp: {report['timestamp']}

🗄️ Base de Données:
   {status_emoji.get(report['checks']['database']['status'], '❓')} {report['checks']['database']['message']}
   📚 Livres analysés: {report['summary']['total_books_analyzed']:,}
   🎯 Séries trouvées: {report['summary']['total_series_found']:,} 
   📈 Taux détection: {report['summary']['detection_rate']:.1f}%

📋 Logs d'Exécution:
   {status_emoji.get(report['checks']['logs']['status'], '❓')} {report['checks']['logs']['message']}

⏰ Configuration Cron:
   {status_emoji.get(report['checks']['cron']['status'], '❓')} {report['checks']['cron']['message']}

📊 RÉSUMÉ:
   📅 Dernière exécution: {report['summary']['days_since_last_run']} jour(s)
   📈 Performance: {'EXCELLENT' if report['summary']['detection_rate'] > 5 else 'CORRECT' if report['summary']['detection_rate'] > 1 else 'À AMÉLIORER'}
   🎯 Recommandation: {'Fonctionnement optimal' if report['global_status'] == 'success' else 'Vérifications requises'}
=============================================
""")

def main():
    """Point d'entrée monitoring"""
    monitor = UltraHarvestMonitor()
    
    try:
        report = monitor.generate_weekly_report()
        
        # Exit code basé sur statut global
        exit_codes = {
            'success': 0,
            'warning': 1,
            'error': 2
        }
        
        exit_code = exit_codes.get(report['global_status'], 3)
        
        if exit_code > 0:
            logger.warning(f"⚠️ Monitoring détecté problèmes (exit code: {exit_code})")
        else:
            logger.info("✅ Monitoring Ultra Harvest: Tout OK")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"❌ Erreur monitoring: {e}")
        return 3

if __name__ == "__main__":
    exit(main())