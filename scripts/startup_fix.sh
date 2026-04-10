#!/bin/bash
# Script exécuté au démarrage pour s'assurer de la bonne configuration

# Attendre que les services soient prêts
sleep 15

# Vérifier et corriger la configuration
/app/scripts/configure_preview.sh

# Logs
echo "[$(date)] Startup configuration completed" >> /var/log/booktime_startup.log
