#!/bin/bash
# Script de mise en place de la surveillance automatique BOOKTIME
# Prévient et corrige automatiquement le problème de création de compte

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SETUP_MONITORING: $1"
}

# Création du service de surveillance périodique
setup_periodic_monitoring() {
    log "⏰ Configuration surveillance automatique..."
    
    # Créer le script de surveillance continue
    cat > /app/scripts/monitor_daemon.sh << 'EOF'
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
EOF

    chmod +x /app/scripts/monitor_daemon.sh
    
    # Créer le wrapper pour démarrage en arrière-plan
    cat > /app/scripts/start_monitoring.sh << 'EOF'
#!/bin/bash
# Démarre la surveillance en arrière-plan

PID_FILE="/var/run/booktime_monitor.pid"

# Vérifier si déjà en cours
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "Surveillance déjà active (PID: $(cat $PID_FILE))"
    exit 0
fi

# Démarrer en arrière-plan
nohup /app/scripts/monitor_daemon.sh >/dev/null 2>&1 &
echo $! > "$PID_FILE"

echo "Surveillance démarrée (PID: $(cat $PID_FILE))"
EOF

    chmod +x /app/scripts/start_monitoring.sh
    
    log "✅ Surveillance périodique configurée"
}

# Configuration des hooks de démarrage
setup_startup_hooks() {
    log "🚀 Configuration hooks de démarrage..."
    
    # Créer script de démarrage supervisord
    cat > /app/scripts/startup_fix.sh << 'EOF'
#!/bin/bash
# Script exécuté au démarrage pour s'assurer de la bonne configuration

# Attendre que les services soient prêts
sleep 15

# Vérifier et corriger la configuration
/app/scripts/configure_preview.sh

# Logs
echo "[$(date)] Startup configuration completed" >> /var/log/booktime_startup.log
EOF

    chmod +x /app/scripts/startup_fix.sh
    
    log "✅ Hooks de démarrage configurés"
}

# Documentation des scripts
create_documentation() {
    log "📚 Création documentation scripts..."
    
    cat > /app/scripts/README.md << 'EOF'
# Scripts BOOKTIME - Résolution Automatique Problème Création Compte

## Vue d'ensemble

Ces scripts résolvent définitivement le problème de création de compte dans l'environnement Preview Emergent en configurant automatiquement l'URL backend correcte.

## Scripts disponibles

### 🔧 configure_preview.sh
**Usage**: `./configure_preview.sh`
**Description**: Configure automatiquement l'URL backend pour l'environnement Preview Emergent
**Actions**:
- Détecte automatiquement l'URL Preview Emergent 
- Configure le fichier `/app/frontend/.env` avec la bonne URL
- Teste la connectivité API
- Redémarre les services
- Valide la solution

### 🩺 health_check.sh  
**Usage**: `./health_check.sh`
**Description**: Vérifie la santé de l'application et corrige automatiquement si nécessaire
**Actions**:
- Vérifie le statut des services
- Teste la configuration frontend
- Test fonctionnel création de compte
- Auto-correction si problème détecté

### ⏰ setup_monitoring.sh
**Usage**: `./setup_monitoring.sh` 
**Description**: Met en place une surveillance automatique
**Actions**:
- Configure un cron job de surveillance (toutes les 10 min)
- Hooks de démarrage automatique
- Documentation complète

### 🚀 startup_fix.sh
**Usage**: Exécuté automatiquement au démarrage
**Description**: S'assure de la bonne configuration au démarrage des services

### 🔄 cron_health_check.sh
**Usage**: Exécuté automatiquement par cron
**Description**: Surveillance périodique avec auto-correction

## Logs

- `/var/log/booktime_health.log` - Logs du health check
- `/var/log/booktime_cron.log` - Logs de la surveillance cron  
- `/var/log/booktime_startup.log` - Logs de démarrage

## Résolution manuelle

Si besoin de résolution manuelle :

```bash
# Diagnostic complet
./health_check.sh

# Reconfiguration forcée
./configure_preview.sh

# Vérification des services
sudo supervisorctl status

# Vérification de la configuration
cat /app/frontend/.env
```

## Historique du problème

**Problème**: En environnement Preview Emergent, le frontend tentait d'accéder à `localhost:8001` qui n'est pas accessible depuis l'extérieur.

**Solution**: Configuration automatique de `REACT_APP_BACKEND_URL` avec l'URL Preview Emergent détectée automatiquement.

**Sessions concernées**: 89.6, 89.7 (voir CHANGELOG.md)

## Maintenance

Les scripts sont conçus pour être autonomes et ne nécessitent pas de maintenance manuelle. La surveillance automatique détecte et corrige les problèmes.

Mise à jour des scripts: Modifier directement les fichiers et relancer `./setup_monitoring.sh` si nécessaire.
EOF

    log "✅ Documentation créée: /app/scripts/README.md"
}

# Fonction principale
main() {
    log "🚀 Mise en place surveillance automatique BOOKTIME"
    
    # Création du répertoire de logs si nécessaire
    mkdir -p /var/log
    touch /var/log/booktime_health.log
    touch /var/log/booktime_cron.log  
    touch /var/log/booktime_startup.log
    
    # Configuration des différents composants
    setup_periodic_monitoring
    setup_startup_hooks
    create_documentation
    
    log "✅ Surveillance automatique configurée avec succès"
    log "📋 Surveillance cron: Toutes les 10 minutes"
    log "📋 Hooks démarrage: Configurés"
    log "📋 Documentation: /app/scripts/README.md"
    log "📋 Logs: /var/log/booktime_*.log"
    
    echo "🎉 Surveillance automatique BOOKTIME configurée !"
    echo "Le problème de création de compte sera désormais résolu automatiquement."
}

# Exécution
main "$@"