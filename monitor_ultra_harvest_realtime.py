#!/usr/bin/env python3
"""
📊 MONITOR ULTRA HARVEST 100K EN TEMPS RÉEL
Surveillance avancée du processus avec métriques détaillées
"""

import json
import time
from pathlib import Path
from datetime import datetime
import subprocess

def get_ultra_harvest_stats():
    """Récupération statistiques Ultra Harvest en cours"""
    
    # Vérifier processus actif
    try:
        result = subprocess.run(['pgrep', '-f', 'ultra_harvest_100k_tracking.py'], 
                              capture_output=True, text=True)
        pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
        active_processes = len([pid for pid in pids if pid])
    except:
        active_processes = 0
    
    # Checkpoint données
    checkpoint_path = Path('/app/data/ultra_harvest_checkpoint.json')
    checkpoint_data = {}
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
        except:
            pass
    
    # Logs récents
    log_path = Path('/app/logs/ultra_harvest_max_70.log')
    recent_logs = []
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-10:]  # 10 dernières lignes
        except:
            pass
    
    return {
        'active_processes': active_processes,
        'checkpoint': checkpoint_data,
        'recent_logs': recent_logs,
        'timestamp': datetime.now().isoformat()
    }

def format_progress(stats):
    """Formatage affichage progression"""
    
    if stats['active_processes'] == 0:
        return "❌ Aucun processus Ultra Harvest actif"
    
    checkpoint = stats.get('checkpoint', {})
    session_stats = checkpoint.get('session_stats', {})
    
    if not session_stats:
        return "⏳ Ultra Harvest démarré, en attente de données..."
    
    books_processed = session_stats.get('books_processed', 0)
    new_series_count = checkpoint.get('new_series_count', 0)
    strategies_completed = session_stats.get('strategies_completed', 0)
    start_time = session_stats.get('start_time')
    
    # Calcul temps écoulé
    elapsed_str = "N/A"
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            elapsed = (datetime.now() - start_dt.replace(tzinfo=None)).total_seconds()
            elapsed_str = f"{elapsed/60:.1f} min"
        except:
            pass
    
    return f"""
🚀 ULTRA HARVEST 100K - PROGRESSION TEMPS RÉEL
===============================================
📊 Processus actifs: {stats['active_processes']}
📚 Livres analysés: {books_processed:,}
🎯 Nouvelles séries détectées: {new_series_count}
🔧 Stratégies terminées: {strategies_completed}
⏱️ Temps écoulé: {elapsed_str}
📅 Dernière mise à jour: {checkpoint.get('timestamp', 'N/A')}
===============================================
"""

def show_recent_activity(stats):
    """Affichage activité récente"""
    
    logs = stats.get('recent_logs', [])
    if not logs:
        return "ℹ️ Aucune activité récente dans les logs"
    
    activity = "🔍 ACTIVITÉ RÉCENTE:\n"
    for i, log_line in enumerate(logs[-5:], 1):  # 5 dernières lignes
        activity += f"{i}. {log_line.strip()}\n"
    
    return activity

def main():
    """Monitoring principal"""
    
    print("🚀 DÉMARRAGE MONITORING ULTRA HARVEST 100K")
    print("==========================================")
    
    try:
        while True:
            stats = get_ultra_harvest_stats()
            
            # Effacer écran
            print("\033[2J\033[H")
            
            # Affichage progression
            print(format_progress(stats))
            
            # Activité récente
            print(show_recent_activity(stats))
            
            # Instructions
            print("💡 Appuyez sur Ctrl+C pour arrêter le monitoring")
            print("📋 Logs complets: /app/logs/ultra_harvest_max_70.log")
            
            # Si plus de processus actif
            if stats['active_processes'] == 0:
                print("\n🏁 Ultra Harvest terminé!")
                break
            
            # Attendre 10 secondes
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring arrêté par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur monitoring: {e}")

if __name__ == "__main__":
    main()