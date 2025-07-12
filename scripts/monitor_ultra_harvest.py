#!/usr/bin/env python3
"""
📊 MONITORING ULTRA HARVEST 100K
Script de monitoring temps réel avec dashboard interactif
"""

import sqlite3
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse

class UltraHarvestMonitor:
    """Moniteur temps réel Ultra Harvest 100K"""
    
    def __init__(self):
        self.db_path = Path('/app/data/ultra_harvest_tracking.db')
        self.log_path = Path('/app/logs/ultra_harvest_100k_main.log')
        self.pid_path = Path('/app/data/ultra_harvest_pid.txt')
    
    def get_current_stats(self):
        """Récupérer statistiques actuelles"""
        if not self.db_path.exists():
            return None
        
        with sqlite3.connect(self.db_path) as conn:
            # Stats générales
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_analyzed,
                    COUNT(CASE WHEN series_detected = 1 THEN 1 END) as series_found,
                    COUNT(DISTINCT source_strategy) as strategies_used,
                    AVG(processing_time_ms) as avg_processing_time,
                    MAX(analysis_date) as last_analysis,
                    MIN(analysis_date) as first_analysis
                FROM analyzed_books
            """)
            
            general_stats = cursor.fetchone()
            
            # Stats par stratégie
            cursor = conn.execute("""
                SELECT 
                    source_strategy,
                    COUNT(*) as books_count,
                    COUNT(CASE WHEN series_detected = 1 THEN 1 END) as series_count,
                    AVG(confidence_score) as avg_confidence
                FROM analyzed_books 
                WHERE source_strategy IS NOT NULL
                GROUP BY source_strategy
                ORDER BY books_count DESC
            """)
            
            strategy_stats = cursor.fetchall()
            
            # Stats temporelles (dernières 5 minutes)
            five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
            cursor = conn.execute("""
                SELECT COUNT(*) as recent_books
                FROM analyzed_books 
                WHERE analysis_date > ?
            """, (five_min_ago,))
            
            recent_stats = cursor.fetchone()
            
        return {
            'general': general_stats,
            'strategies': strategy_stats,
            'recent': recent_stats
        }
    
    def get_process_status(self):
        """Vérifier statut processus"""
        if not self.pid_path.exists():
            return {'running': False, 'pid': None}
        
        try:
            with open(self.pid_path, 'r') as f:
                pid = int(f.read().strip())
            
            # Vérifier si processus existe
            try:
                os.kill(pid, 0)
                return {'running': True, 'pid': pid}
            except OSError:
                return {'running': False, 'pid': pid, 'status': 'terminated'}
                
        except Exception:
            return {'running': False, 'pid': None, 'status': 'error'}
    
    def get_log_tail(self, lines=10):
        """Récupérer fin des logs"""
        if not self.log_path.exists():
            return []
        
        try:
            with open(self.log_path, 'r') as f:
                return f.readlines()[-lines:]
        except Exception:
            return []
    
    def calculate_eta(self, stats):
        """Calculer ETA basé sur progression"""
        if not stats or not stats['general']:
            return None
        
        total_analyzed = stats['general'][0]
        if total_analyzed == 0:
            return None
        
        # Estimer basé sur les 5 dernières minutes
        recent_books = stats['recent'][0] if stats['recent'] else 0
        if recent_books == 0:
            return None
        
        books_per_minute = recent_books / 5
        remaining_books = 100000 - total_analyzed
        
        if books_per_minute > 0:
            eta_minutes = remaining_books / books_per_minute
            eta_time = datetime.now() + timedelta(minutes=eta_minutes)
            return {
                'eta_minutes': eta_minutes,
                'eta_time': eta_time.strftime('%H:%M:%S'),
                'rate_per_minute': books_per_minute
            }
        
        return None
    
    def display_dashboard(self):
        """Afficher dashboard temps réel"""
        os.system('clear')
        
        print("📊 ULTRA HARVEST 100K - DASHBOARD TEMPS RÉEL")
        print("=" * 60)
        print(f"🕐 Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # Statut processus
        process_status = self.get_process_status()
        if process_status['running']:
            print(f"🟢 Processus: ACTIF (PID: {process_status['pid']})")
        else:
            print(f"🔴 Processus: ARRÊTÉ (PID: {process_status.get('pid', 'N/A')})")
        print()
        
        # Statistiques générales
        stats = self.get_current_stats()
        if stats and stats['general']:
            total, series, strategies, avg_time, last, first = stats['general']
            
            progress = (total / 100000) * 100
            detection_rate = (series / total * 100) if total > 0 else 0
            
            print("📊 PROGRESSION GLOBALE")
            print("-" * 30)
            print(f"📚 Livres analysés: {total:,} / 100,000 ({progress:.1f}%)")
            print(f"🎯 Séries détectées: {series:,}")
            print(f"📈 Taux détection: {detection_rate:.1f}%")
            print(f"🔧 Stratégies utilisées: {strategies}")
            print(f"⚡ Temps moyen/livre: {avg_time:.1f}ms")
            print()
            
            # Barre de progression ASCII
            bar_length = 40
            filled_length = int(bar_length * progress // 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f"Progress: |{bar}| {progress:.1f}%")
            print()
            
            # ETA
            eta = self.calculate_eta(stats)
            if eta:
                print("⏰ ESTIMATION TEMPS RESTANT")
                print("-" * 30)
                print(f"🕐 ETA: {eta['eta_time']}")
                print(f"⚡ Vitesse: {eta['rate_per_minute']:.1f} livres/min")
                print(f"⏱️ Temps restant: {eta['eta_minutes']:.0f} minutes")
                print()
        
        # Stats par stratégie
        if stats and stats['strategies']:
            print("🎯 PERFORMANCE PAR STRATÉGIE")
            print("-" * 50)
            print(f"{'Stratégie':<25} {'Livres':<8} {'Séries':<8} {'Taux':<8}")
            print("-" * 50)
            
            for strategy, books, series, confidence in stats['strategies'][:10]:
                rate = (series / books * 100) if books > 0 else 0
                strategy_short = strategy[:24] if strategy else "N/A"
                print(f"{strategy_short:<25} {books:<8} {series:<8} {rate:<7.1f}%")
            print()
        
        # Logs récents
        recent_logs = self.get_log_tail(5)
        if recent_logs:
            print("📋 LOGS RÉCENTS")
            print("-" * 40)
            for line in recent_logs:
                clean_line = line.strip()
                if clean_line:
                    # Simplifier l'affichage des logs
                    if "PROGRESSION GLOBALE" in clean_line:
                        print(f"📊 {clean_line.split('📊')[-1].strip()}")
                    elif "terminée:" in clean_line:
                        print(f"✅ {clean_line.split('✅')[-1].strip()}")
                    elif "ERROR" in clean_line:
                        print(f"❌ {clean_line}")
        
        print()
        print("⌨️  Commandes: [q]uitter | [r]afraîchir | [s]tats détaillées")
    
    def run_interactive(self):
        """Mode interactif avec rafraîchissement"""
        import sys
        import select
        import tty
        import termios
        
        print("🚀 Démarrage monitoring interactif...")
        print("⌨️  Appuyez sur 'q' pour quitter, 'r' pour rafraîchir")
        print()
        
        # Configuration terminal pour lecture non-bloquante
        old_settings = termios.tcgetattr(sys.stdin)
        tty.cbreak(sys.stdin.fileno())
        
        try:
            while True:
                self.display_dashboard()
                
                # Attendre 10 secondes ou input utilisateur
                ready, _, _ = select.select([sys.stdin], [], [], 10)
                
                if ready:
                    char = sys.stdin.read(1)
                    if char.lower() == 'q':
                        break
                    elif char.lower() == 'r':
                        continue
                    elif char.lower() == 's':
                        self.show_detailed_stats()
                        input("\nAppuyez sur Entrée pour continuer...")
                        
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        print("\n👋 Monitoring terminé!")
    
    def show_detailed_stats(self):
        """Afficher statistiques détaillées"""
        os.system('clear')
        print("📊 STATISTIQUES DÉTAILLÉES ULTRA HARVEST 100K")
        print("=" * 60)
        
        stats = self.get_current_stats()
        if not stats:
            print("❌ Aucune donnée disponible")
            return
        
        # Toutes les stratégies
        if stats['strategies']:
            print("\n🎯 TOUTES LES STRATÉGIES")
            print("-" * 80)
            print(f"{'Stratégie':<30} {'Livres':<10} {'Séries':<10} {'Taux':<10} {'Confiance':<10}")
            print("-" * 80)
            
            for strategy, books, series, confidence in stats['strategies']:
                rate = (series / books * 100) if books > 0 else 0
                print(f"{strategy:<30} {books:<10} {series:<10} {rate:<9.1f}% {confidence or 0:<9.1f}")
        
        # Analyse temporelle
        if self.db_path.exists():
            with sqlite3.connect(self.db_path) as conn:
                # Analyse par heure
                cursor = conn.execute("""
                    SELECT 
                        substr(analysis_date, 1, 13) as hour,
                        COUNT(*) as books_count,
                        COUNT(CASE WHEN series_detected = 1 THEN 1 END) as series_count
                    FROM analyzed_books
                    GROUP BY substr(analysis_date, 1, 13)
                    ORDER BY hour DESC
                    LIMIT 24
                """)
                
                hourly_stats = cursor.fetchall()
                
                if hourly_stats:
                    print("\n⏰ ANALYSE TEMPORELLE (24 dernières heures)")
                    print("-" * 50)
                    print(f"{'Heure':<15} {'Livres':<10} {'Séries':<10} {'Taux':<10}")
                    print("-" * 50)
                    
                    for hour, books, series in hourly_stats:
                        rate = (series / books * 100) if books > 0 else 0
                        hour_display = hour.replace('T', ' ') + ":00"
                        print(f"{hour_display:<15} {books:<10} {series:<10} {rate:<9.1f}%")

def main():
    """Point d'entrée monitoring"""
    parser = argparse.ArgumentParser(description="Monitoring Ultra Harvest 100K")
    parser.add_argument('--once', action='store_true', help='Affichage unique')
    parser.add_argument('--detailed', action='store_true', help='Stats détaillées')
    parser.add_argument('--json', action='store_true', help='Sortie JSON')
    
    args = parser.parse_args()
    
    monitor = UltraHarvestMonitor()
    
    if args.json:
        stats = monitor.get_current_stats()
        process = monitor.get_process_status()
        eta = monitor.calculate_eta(stats)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'process': process,
            'stats': stats,
            'eta': eta
        }
        
        print(json.dumps(result, indent=2, default=str))
        
    elif args.detailed:
        monitor.show_detailed_stats()
        
    elif args.once:
        monitor.display_dashboard()
        
    else:
        monitor.run_interactive()

if __name__ == "__main__":
    main()