#!/usr/bin/env python3
"""
📊 MONITEUR ULTRA HARVEST 100K EN TEMPS RÉEL
Surveillance continue avec métriques détaillées et tableau de bord
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
import os

def get_ultra_harvest_stats():
    """Récupère les statistiques actuelles de l'Ultra Harvest"""
    
    # Fichier de tracking SQLite
    db_file = "/app/backend/scripts/ultra_harvest_tracking.db"
    
    stats = {
        'books_analyzed': 0,
        'series_detected': 0,
        'progress_percent': 0,
        'rate_books_per_min': 0,
        'rate_series_per_min': 0,
        'estimated_completion': 'Calculating...',
        'status': 'Unknown'
    }
    
    try:
        if os.path.exists(db_file):
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Compter les livres analysés
            cursor.execute("SELECT COUNT(*) FROM analyzed_books")
            stats['books_analyzed'] = cursor.fetchone()[0]
            
            # Compter les séries détectées  
            cursor.execute("SELECT COUNT(*) FROM detected_series")
            stats['series_detected'] = cursor.fetchone()[0]
            
            # Calculer progression vers 100K
            target = 100000
            stats['progress_percent'] = (stats['books_analyzed'] / target) * 100
            
            # Calculer les taux (dernière heure)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            one_hour_ago_str = one_hour_ago.isoformat()
            
            cursor.execute("""
                SELECT COUNT(*) FROM analyzed_books 
                WHERE timestamp > ?
            """, (one_hour_ago_str,))
            books_last_hour = cursor.fetchone()[0]
            stats['rate_books_per_min'] = books_last_hour / 60
            
            cursor.execute("""
                SELECT COUNT(*) FROM detected_series 
                WHERE detection_date > ?
            """, (one_hour_ago_str,))
            series_last_hour = cursor.fetchone()[0]
            stats['rate_series_per_min'] = series_last_hour / 60
            
            conn.close()
            
            # Estimation temps restant
            if stats['rate_books_per_min'] > 0:
                remaining_books = target - stats['books_analyzed']
                minutes_remaining = remaining_books / stats['rate_books_per_min']
                completion_time = datetime.now() + timedelta(minutes=minutes_remaining)
                stats['estimated_completion'] = completion_time.strftime('%H:%M:%S')
            
            stats['status'] = 'RUNNING'
        else:
            stats['status'] = 'NOT_STARTED'
            
    except Exception as e:
        stats['status'] = f'ERROR: {str(e)}'
    
    return stats

def check_process_status():
    """Vérifie si le processus Ultra Harvest est actif"""
    try:
        import subprocess
        result = subprocess.run(['pgrep', '-f', 'ultra_harvest_100k_tracking'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def display_dashboard():
    """Affiche le tableau de bord en temps réel"""
    
    # Clear screen
    os.system('clear')
    
    print("🚀 ULTRA HARVEST 100K - MONITORING EN TEMPS RÉEL")
    print("=" * 60)
    
    # Vérifier statut processus
    process_active = check_process_status()
    status_icon = "🟢" if process_active else "🔴"
    print(f"{status_icon} Processus: {'ACTIF' if process_active else 'ARRÊTÉ'}")
    
    # Statistiques détaillées
    stats = get_ultra_harvest_stats()
    
    print(f"\n📊 PROGRESSION GLOBALE")
    print(f"├── 📚 Livres analysés: {stats['books_analyzed']:,}")
    print(f"├── 🎯 Séries détectées: {stats['series_detected']:,}")
    print(f"├── 📈 Progression: {stats['progress_percent']:.2f}% vers 100K")
    print(f"└── 🎛️ Statut: {stats['status']}")
    
    print(f"\n⚡ PERFORMANCE TEMPS RÉEL")
    print(f"├── 📚 Livres/minute: {stats['rate_books_per_min']:.1f}")
    print(f"├── 🎯 Séries/minute: {stats['rate_series_per_min']:.1f}")
    print(f"└── ⏰ Fin estimée: {stats['estimated_completion']}")
    
    # Taux de détection
    if stats['books_analyzed'] > 0:
        detection_rate = (stats['series_detected'] / stats['books_analyzed']) * 100
        print(f"\n🎯 EFFICACITÉ DÉTECTION")
        print(f"└── 📊 Taux détection: {detection_rate:.1f}%")
    
    # Barre de progression visuelle
    if stats['progress_percent'] > 0:
        bar_length = 40
        filled_length = int(bar_length * stats['progress_percent'] / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"\n📊 PROGRESSION VISUELLE")
        print(f"[{bar}] {stats['progress_percent']:.1f}%")
    
    print(f"\n🕒 Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
    print("\n💡 Appuyez sur Ctrl+C pour quitter le monitoring")

def main():
    """Boucle principale de monitoring"""
    
    try:
        while True:
            display_dashboard()
            time.sleep(30)  # Mise à jour toutes les 30 secondes
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring arrêté par l'utilisateur")
        
        # Afficher résumé final
        stats = get_ultra_harvest_stats()
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"├── 📚 Livres analysés: {stats['books_analyzed']:,}")
        print(f"├── 🎯 Séries détectées: {stats['series_detected']:,}")
        print(f"└── 📈 Progression: {stats['progress_percent']:.2f}%")

if __name__ == "__main__":
    main()