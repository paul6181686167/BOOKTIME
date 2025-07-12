#!/bin/bash
"""
🚀 LANCEUR ULTRA HARVEST 100K 
Script de lancement pour mega harvest avec 100,000 livres
"""

echo "🚀 DÉMARRAGE ULTRA HARVEST 100K avec TRACKING COMPLET"
echo "======================================================"
echo "🎯 Objectif: 100,000 livres à analyser"
echo "📊 15+ stratégies ultra-sophistiquées"
echo "🗄️ Tracking SQLite + JSON persistant"
echo "⏰ Démarrage: $(date)"
echo "======================================================"

# Création des dossiers nécessaires
mkdir -p /app/logs /app/data /app/backups/series_detection

# Lancement du script principal avec nohup pour persistence
cd /app/backend/scripts

nohup python ultra_harvest_100k_tracking.py --target 100000 > /app/logs/ultra_harvest_100k_main.log 2>&1 &

HARVEST_PID=$!
echo "🔢 PID du processus: $HARVEST_PID"
echo $HARVEST_PID > /app/data/ultra_harvest_pid.txt

echo "🎯 Ultra Harvest 100K lancé en arrière-plan!"
echo "📋 Logs disponibles dans: /app/logs/ultra_harvest_100k_main.log"
echo "📊 Statistiques: python ultra_harvest_100k_tracking.py --stats"
echo "🔍 Suivi progression: tail -f /app/logs/ultra_harvest_100k_main.log"

echo ""
echo "⚡ COMMANDES UTILES:"
echo "==================="
echo "📊 Voir stats:      cd /app/backend/scripts && python ultra_harvest_100k_tracking.py --stats"
echo "📋 Voir logs:       tail -f /app/logs/ultra_harvest_100k_main.log"
echo "🔍 Voir progression: tail -n 50 /app/logs/ultra_harvest_100k_main.log | grep 'PROGRESSION GLOBALE'"
echo "⏹️ Arrêter:         kill \$(cat /app/data/ultra_harvest_pid.txt)"
echo "==================="