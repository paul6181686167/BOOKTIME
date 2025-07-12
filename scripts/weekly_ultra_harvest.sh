#!/bin/bash
"""
🚀 ULTRA HARVEST WEEKLY PRODUCTION
Script cron pour Ultra Harvest automatique en production
Exécution hebdomadaire avec rate limiting respectueux
"""

echo "🚀 ULTRA HARVEST WEEKLY PRODUCTION - $(date)"
echo "=============================================="

# Configuration production
PRODUCTION_TARGET=1000
RATE_LIMIT=0.5
MAX_API_CALLS=100
LOG_DIR="/app/logs"
DATA_DIR="/app/data"
SCRIPTS_DIR="/app/backend/scripts"

# Création dossiers si nécessaires
mkdir -p "$LOG_DIR" "$DATA_DIR"

# Fichier log avec timestamp
LOG_FILE="$LOG_DIR/ultra_harvest_weekly_$(date +%Y%m%d_%H%M%S).log"

echo "📋 Configuration Production:"
echo "  🎯 Target: $PRODUCTION_TARGET livres"
echo "  ⏱️ Rate limit: ${RATE_LIMIT}s entre requêtes"
echo "  🔢 Max API calls: $MAX_API_CALLS"
echo "  📄 Log: $LOG_FILE"
echo "=============================================="

# Vérification qu'aucun Ultra Harvest n'est déjà en cours
if pgrep -f "ultra_harvest_100k_tracking.py" > /dev/null; then
    echo "⚠️ Ultra Harvest déjà en cours d'exécution"
    echo "⏹️ Abandon pour éviter doublons"
    exit 1
fi

# Vérification prérequis
if [ ! -f "$SCRIPTS_DIR/ultra_harvest_100k_tracking.py" ]; then
    echo "❌ Script Ultra Harvest non trouvé: $SCRIPTS_DIR/ultra_harvest_100k_tracking.py"
    exit 1
fi

# Sauvegarde base données avant exécution (sécurité)
if [ -f "$DATA_DIR/ultra_harvest_tracking.db" ]; then
    cp "$DATA_DIR/ultra_harvest_tracking.db" "$DATA_DIR/ultra_harvest_tracking_backup_$(date +%Y%m%d).db"
    echo "💾 Backup base données créé"
fi

# Exécution Ultra Harvest avec configuration production
echo "🚀 Démarrage Ultra Harvest Production..."
cd "$SCRIPTS_DIR"

# Commande avec tous les paramètres production
python ultra_harvest_100k_tracking.py \
    --target "$PRODUCTION_TARGET" \
    2>&1 | tee "$LOG_FILE"

# Vérification résultat
HARVEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $HARVEST_EXIT_CODE -eq 0 ]; then
    echo "✅ Ultra Harvest Weekly réussi!"
    
    # Statistiques post-exécution
    echo "📊 Statistiques finales:"
    python ultra_harvest_100k_tracking.py --stats | tee -a "$LOG_FILE"
    
    # Nettoyage logs anciens (garde 30 derniers jours)
    find "$LOG_DIR" -name "ultra_harvest_weekly_*.log" -mtime +30 -delete
    
    # Nettoyage backups anciens (garde 7 derniers jours)
    find "$DATA_DIR" -name "ultra_harvest_tracking_backup_*.db" -mtime +7 -delete
    
    echo "🧹 Nettoyage logs/backups anciens effectué"
    
else
    echo "❌ Ultra Harvest Weekly échoué (code: $HARVEST_EXIT_CODE)"
    echo "📋 Consulter log pour détails: $LOG_FILE"
fi

echo "=============================================="
echo "🏁 Ultra Harvest Weekly terminé - $(date)"
echo "📊 Code sortie: $HARVEST_EXIT_CODE"
echo "📄 Log complet: $LOG_FILE"
echo "=============================================="

exit $HARVEST_EXIT_CODE