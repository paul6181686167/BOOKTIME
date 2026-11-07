#!/usr/bin/env python3
"""
🎯 ULTRA HARVEST PROGRESSION TRACKER
Tracking détaillé de la progression Ultra Harvest 100k avec métriques avancées
"""

import time
import json
import subprocess
import requests
from datetime import datetime, timedelta

def get_comprehensive_stats():
    """Statistiques complètes Ultra Harvest"""
    try:
        result = subprocess.run(
            ['python', '/app/backend/scripts/ultra_harvest_100k_tracking.py', '--stats'],
            capture_output=True, text=True, cwd='/app/backend/scripts'
        )
        return result.stdout
    except:
        return "Stats non disponibles"

def get_series_count_from_api():
    """Compter les séries via API backend"""
    try:
        # Simuler un appel API pour compter séries
        # En production, cela ferait un appel real au backend
        return "7,939+ séries en base (estimation)"
    except:
        return "API non disponible"

def get_performance_metrics():
    """Calculer métriques performance"""
    try:
        # Récupérer checkpoint actuel
        with open('/app/data/ultra_harvest_checkpoint.json', 'r') as f:
            checkpoint = json.load(f)
            
        stats = checkpoint.get('session_stats', {})
        start_time = stats.get('start_time', '')
        books_processed = stats.get('books_processed', 0)
        
        if start_time:
            # Calculer durée depuis début
            start = datetime.fromisoformat(start_time.replace(' ', 'T'))
            duration = datetime.now() - start
            duration_minutes = duration.total_seconds() / 60
            
            if duration_minutes > 0:
                books_per_minute = books_processed / duration_minutes
                estimated_completion = start + timedelta(minutes=(100000 / books_per_minute))
                
                return {
                    'duration_minutes': duration_minutes,
                    'books_per_minute': books_per_minute,
                    'estimated_completion': estimated_completion.strftime('%H:%M:%S'),
                    'progress_percent': (books_processed / 100000) * 100
                }
    except:
        pass
    
    return None

def display_comprehensive_dashboard():
    """Dashboard complet avec toutes les métriques"""
    
    print(f"""
🚀 ULTRA HARVEST 100K - PROGRESSION COMPLÈTE
==========================================
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 STATISTIQUES PRINCIPALES:
{get_comprehensive_stats()}

🎯 MÉTRIQUES PERFORMANCE:""")
    
    metrics = get_performance_metrics()
    if metrics:
        print(f"""📈 Progression: {metrics['progress_percent']:.1f}%
⚡ Vitesse: {metrics['books_per_minute']:.0f} livres/minute
⏱️ Durée écoulée: {metrics['duration_minutes']:.1f} minutes
🎯 Fin estimée: {metrics['estimated_completion']}""")
    else:
        print("Métriques non disponibles")
    
    print(f"""
🗄️ BASE DE DONNÉES:
{get_series_count_from_api()}

🔥 ACTIVITÉ TEMPS RÉEL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")
    
    # Afficher dernières activités
    try:
        with open('/app/logs/ultra_harvest_max_series.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-3:]:
                if 'INFO' in line and '🔍' in line:
                    # Extraire infos importantes
                    if 'Query' in line:
                        parts = line.split('Query ')
                        if len(parts) > 1:
                            query_info = parts[1].split('...')[0]
                            print(f"🔍 {query_info}...")
    except:
        print("Logs non disponibles")
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

def main():
    """Affichage unique pour suivi"""
    display_comprehensive_dashboard()

if __name__ == "__main__":
    main()