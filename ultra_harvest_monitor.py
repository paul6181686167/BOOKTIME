#!/usr/bin/env python3
"""
🚀 ULTRA HARVEST MONITOR - DASHBOARD TEMPS RÉEL
Monitoring complet de l'Ultra Harvest 100k AutoExpansion OpenLibrary
"""

import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

def get_ultra_harvest_stats():
    """Récupérer statistiques Ultra Harvest en temps réel"""
    try:
        result = subprocess.run(
            ['python', '/app/backend/scripts/ultra_harvest_100k_tracking.py', '--stats'],
            capture_output=True, text=True, cwd='/app/backend/scripts'
        )
        return result.stdout
    except:
        return "Erreur récupération stats"

def get_process_count():
    """Compter processus actifs"""
    try:
        processes = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        ultra_count = processes.stdout.count('ultra_harvest')
        expansion_count = processes.stdout.count('expansion_optimizer')
        integrate_count = processes.stdout.count('integrate_ultra_harvest')
        return ultra_count, expansion_count, integrate_count
    except:
        return 0, 0, 0

def get_log_tail(log_file, lines=5):
    """Récupérer les dernières lignes d'un log"""
    try:
        result = subprocess.run(['tail', f'-n{lines}', log_file], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Log non disponible"

def display_dashboard():
    """Afficher dashboard monitoring"""
    ultra_count, expansion_count, integrate_count = get_process_count()
    
    print(f"""
🚀 ULTRA HARVEST 100K - DASHBOARD TEMPS RÉEL
============================================
⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 PROCESSUS ACTIFS:
   🎯 Ultra Harvest 100K: {ultra_count} processus
   ⚡ Expansion Optimizer: {expansion_count} processus  
   🔄 Auto-Intégration: {integrate_count} processus

📈 STATISTIQUES ULTRA HARVEST:
{get_ultra_harvest_stats()}

🔍 DERNIÈRES ACTIVITÉS:
━━━━━━━━━━━━━━━━━━━━━━━━━
Ultra Harvest (Principal):
{get_log_tail('/app/logs/ultra_harvest_max_series.log', 3)}

━━━━━━━━━━━━━━━━━━━━━━━━━
Expansion Optimizer:
{get_log_tail('/app/logs/expansion_optimizer_max.log', 2)}

━━━━━━━━━━━━━━━━━━━━━━━━━
Auto-Intégration:
{get_log_tail('/app/logs/auto_integrate_series.log', 2)}

🎯 DONNÉES DISPONIBLES:
━━━━━━━━━━━━━━━━━━━━━━━━━""")
    
    # Afficher données checkpoint si disponible
    checkpoint_file = Path('/app/data/ultra_harvest_checkpoint.json')
    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                stats = checkpoint.get('session_stats', {})
                print(f"""📚 Livres traités: {stats.get('books_processed', 0):,}
🆕 Séries détectées: {stats.get('series_detected', 0):,}
📞 Appels API: {stats.get('api_calls_made', 0):,}
🔧 Stratégies: {stats.get('strategies_completed', 0)}/15
⏰ Dernière maj: {stats.get('last_checkpoint', 'N/A')}""")
        except:
            print("Checkpoint non lisible")
    
    print("\n" + "="*50 + "\n")

def main():
    """Monitoring en continu"""
    print("🚀 DÉMARRAGE MONITORING ULTRA HARVEST 100K")
    print("Appuyez sur Ctrl+C pour arrêter")
    
    try:
        while True:
            display_dashboard()
            time.sleep(30)  # Actualisation toutes les 30 secondes
            
    except KeyboardInterrupt:
        print("\n⏹️ Monitoring arrêté par l'utilisateur")

if __name__ == "__main__":
    main()