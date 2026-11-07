#!/usr/bin/env python3
"""
📊 TABLEAU DE BORD ULTRA HARVEST 100K COMPLET
Dashboard avancé avec métriques en temps réel, progression et estimations
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
import os
import subprocess

def clear_screen():
    """Efface l'écran"""
    os.system('clear')

def get_process_status():
    """Vérifie si Ultra Harvest est actif"""
    try:
        result = subprocess.run(['pgrep', '-f', 'ultra_harvest_100k_tracking'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def get_ultra_harvest_metrics():
    """Récupère toutes les métriques Ultra Harvest"""
    
    db_file = "/app/data/ultra_harvest_tracking.db"
    
    metrics = {
        'status': 'NOT_STARTED',
        'books_analyzed': 0,
        'series_detected': 0,
        'detection_rate': 0,
        'progress_percent': 0,
        'rate_per_minute': 0,
        'estimated_completion': 'Calculating...',
        'top_series': [],
        'recent_books': [],
        'strategies': {}
    }
    
    if not os.path.exists(db_file):
        return metrics
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Comptes principaux
        cursor.execute('SELECT COUNT(*) FROM analyzed_books')
        metrics['books_analyzed'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM analyzed_books WHERE series_detected = 1')
        metrics['series_detected'] = cursor.fetchone()[0]
        
        # Taux de détection
        if metrics['books_analyzed'] > 0:
            metrics['detection_rate'] = (metrics['series_detected'] / metrics['books_analyzed']) * 100
        
        # Progression vers 100K
        metrics['progress_percent'] = (metrics['books_analyzed'] / 100000) * 100
        
        # Calcul de la vitesse (dernière heure)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM analyzed_books 
            WHERE analysis_date > ?
        """, (one_hour_ago,))
        books_last_hour = cursor.fetchone()[0]
        metrics['rate_per_minute'] = books_last_hour / 60
        
        # Estimation temps restant
        if metrics['rate_per_minute'] > 0:
            remaining_books = 100000 - metrics['books_analyzed']
            minutes_remaining = remaining_books / metrics['rate_per_minute']
            completion_time = datetime.now() + timedelta(minutes=minutes_remaining)
            metrics['estimated_completion'] = completion_time.strftime('%H:%M:%S')
        
        # Top séries détectées
        cursor.execute("""
            SELECT series_name, COUNT(*) as count 
            FROM analyzed_books 
            WHERE series_detected = 1 AND series_name IS NOT NULL
            GROUP BY series_name 
            ORDER BY count DESC 
            LIMIT 5
        """)
        metrics['top_series'] = cursor.fetchall()
        
        # Livres récents
        cursor.execute("""
            SELECT title, author, series_name, confidence_score 
            FROM analyzed_books 
            ORDER BY id DESC 
            LIMIT 3
        """)
        metrics['recent_books'] = cursor.fetchall()
        
        # Métriques par source/stratégie
        cursor.execute("""
            SELECT source_strategy, COUNT(*) as count 
            FROM analyzed_books 
            WHERE source_strategy IS NOT NULL
            GROUP BY source_strategy 
            ORDER BY count DESC 
            LIMIT 3
        """)
        metrics['strategies'] = dict(cursor.fetchall())
        
        metrics['status'] = 'RUNNING'
        
        conn.close()
        
    except Exception as e:
        metrics['status'] = f'ERROR: {str(e)}'
    
    return metrics

def get_series_database_info():
    """Info sur la base de séries"""
    
    series_file = "/app/backend/data/extended_series_database.json"
    
    if not os.path.exists(series_file):
        return {"total": 0, "categories": {}}
    
    with open(series_file, 'r', encoding='utf-8') as f:
        series_data = json.load(f)
    
    categories = {}
    for serie in series_data:
        cat = serie.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "total": len(series_data),
        "categories": categories
    }

def display_dashboard():
    """Affiche le tableau de bord complet"""
    
    clear_screen()
    
    # Header
    print("🚀 ULTRA HARVEST 100K - DASHBOARD COMPLET")
    print("=" * 70)
    print(f"🕒 Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Statut processus
    process_active = get_process_status()
    status_icon = "🟢" if process_active else "🔴"
    print(f"{status_icon} Processus Ultra Harvest: {'ACTIF' if process_active else 'ARRÊTÉ'}")
    
    # Métriques principales
    metrics = get_ultra_harvest_metrics()
    
    print(f"\n📊 PROGRESSION ULTRA HARVEST 100K")
    print("-" * 50)
    print(f"📚 Livres analysés: {metrics['books_analyzed']:,}")
    print(f"🎯 Séries détectées: {metrics['series_detected']:,}")
    print(f"📈 Taux détection: {metrics['detection_rate']:.1f}%")
    print(f"📊 Progression: {metrics['progress_percent']:.2f}% vers 100K")
    
    # Barre de progression visuelle
    if metrics['progress_percent'] > 0:
        bar_length = 40
        filled_length = int(bar_length * metrics['progress_percent'] / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"[{bar}] {metrics['progress_percent']:.1f}%")
    
    print(f"\n⚡ PERFORMANCE TEMPS RÉEL")
    print("-" * 30)
    print(f"📈 Vitesse: {metrics['rate_per_minute']:.1f} livres/minute")
    print(f"⏰ Fin estimée: {metrics['estimated_completion']}")
    
    # Top séries
    if metrics['top_series']:
        print(f"\n🏆 TOP SÉRIES DÉTECTÉES")
        print("-" * 25)
        for i, (series, count) in enumerate(metrics['top_series'], 1):
            print(f"  {i}. {series[:30]}: {count} livres")
    
    # Stratégies actives
    if metrics['strategies']:
        print(f"\n🎯 STRATÉGIES ACTIVES")
        print("-" * 20)
        for strategy, count in list(metrics['strategies'].items())[:3]:
            pct = (count / metrics['books_analyzed'] * 100) if metrics['books_analyzed'] > 0 else 0
            print(f"  ├── {strategy}: {count:,} ({pct:.1f}%)")
    
    # Base de séries actuelle
    series_info = get_series_database_info()
    print(f"\n📚 BASE DE SÉRIES ACTUELLE")
    print("-" * 28)
    print(f"Total séries: {series_info['total']:,}")
    for cat, count in sorted(series_info['categories'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / series_info['total'] * 100) if series_info['total'] > 0 else 0
        print(f"  ├── {cat}: {count:,} ({pct:.1f}%)")
    
    # Livres récents
    if metrics['recent_books']:
        print(f"\n📖 DERNIERS LIVRES ANALYSÉS")
        print("-" * 30)
        for title, author, series, confidence in metrics['recent_books']:
            series_info = f" → {series}" if series else ""
            conf_info = f" ({confidence}%)" if confidence else ""
            print(f"  ├── {title[:30]}... by {author[:20]}{series_info}{conf_info}")
    
    # Estimations finales
    if metrics['books_analyzed'] > 0 and metrics['rate_per_minute'] > 0:
        remaining = 100000 - metrics['books_analyzed']
        hours_remaining = (remaining / metrics['rate_per_minute']) / 60
        
        print(f"\n🎯 ESTIMATIONS FINALES")
        print("-" * 20)
        print(f"📊 Livres restants: {remaining:,}")
        print(f"⏱️ Temps restant: {hours_remaining:.1f} heures")
        
        # Projection séries
        projected_series = int((metrics['series_detected'] / metrics['books_analyzed']) * 100000)
        print(f"🎯 Séries projetées (100K): ~{projected_series:,}")
    
    print(f"\n💡 Appuyez sur Ctrl+C pour quitter le monitoring")

def main():
    """Boucle principale de monitoring"""
    
    try:
        while True:
            display_dashboard()
            time.sleep(30)  # Mise à jour toutes les 30 secondes
            
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard fermé par l'utilisateur")
        
        # Résumé final
        metrics = get_ultra_harvest_metrics()
        print(f"\n📊 RÉSUMÉ FINAL ULTRA HARVEST 100K:")
        print(f"├── 📚 Livres analysés: {metrics['books_analyzed']:,}")
        print(f"├── 🎯 Séries détectées: {metrics['series_detected']:,}")
        print(f"├── 📈 Taux détection: {metrics['detection_rate']:.1f}%")
        print(f"└── 📊 Progression: {metrics['progress_percent']:.2f}%")

if __name__ == "__main__":
    main()