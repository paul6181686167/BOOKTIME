#!/bin/bash
# Wrapper pour health check via cron
cd /app
/app/scripts/health_check.sh >> /var/log/booktime_cron.log 2>&1

# Si le health check échoue, tenter de résoudre automatiquement
if [ $? -ne 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CRON: Health check failed - Attempting auto-fix" >> /var/log/booktime_cron.log
    /app/scripts/configure_preview.sh >> /var/log/booktime_cron.log 2>&1
fi
