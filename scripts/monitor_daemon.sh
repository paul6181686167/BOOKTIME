#!/bin/bash
# Démon de surveillance BOOKTIME - Vérifie périodiquement et corrige automatiquement

INTERVAL=600  # 10 minutes
LOG_FILE="/var/log/booktime_monitor.log"

log_monitor() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] MONITOR: $1" >> "$LOG_FILE"
}

# Boucle de surveillance
while true; do
    log_monitor "🔍 Début cycle surveillance"
    
    # Exécution health check
    if /app/scripts/health_check.sh >> "$LOG_FILE" 2>&1; then
        log_monitor "✅ Health check OK"
    else
        log_monitor "⚠️ Health check échoué - Tentative correction automatique"
        /app/scripts/configure_preview.sh >> "$LOG_FILE" 2>&1
        
        # Re-test après correction
        if /app/scripts/health_check.sh >> "$LOG_FILE" 2>&1; then
            log_monitor "✅ Problème corrigé avec succès"
        else
            log_monitor "❌ Correction automatique échouée"
        fi
    fi
    
    log_monitor "😴 Attente $INTERVAL secondes..."
    sleep $INTERVAL
done
