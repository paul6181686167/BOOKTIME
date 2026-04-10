#!/bin/bash
# Script de vérification santé application BOOKTIME
# Vérifie automatiquement la configuration et corrige si nécessaire

set -e

# Configuration
LOG_FILE="/var/log/booktime_health.log"
CONFIG_SCRIPT="/app/scripts/configure_preview.sh"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] HEALTH_CHECK: $1" | tee -a "$LOG_FILE"
}

# Vérification configuration frontend
check_frontend_config() {
    log "🔍 Vérification configuration frontend..."
    
    if [ ! -f "/app/frontend/.env" ]; then
        log "❌ Fichier .env manquant - Reconfiguration nécessaire"
        return 1
    fi
    
    # Vérifier si utilise localhost (problématique en preview)
    if grep -q "localhost:8001" /app/frontend/.env; then
        # Vérifier si on est en environnement preview
        if [ ! -z "$(env | grep preview_endpoint)" ]; then
            log "❌ Configuration localhost détectée en environnement preview"
            return 1
        fi
    fi
    
    log "✅ Configuration frontend OK"
    return 0
}

# Test création compte
test_account_creation() {
    log "🧪 Test création compte..."
    
    # Lire URL backend depuis .env
    BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2)
    
    # Test API register
    TEST_RESULT=$(curl -s --max-time 10 -X POST "$BACKEND_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"first_name\": \"Health\", \"last_name\": \"Check$(date +%s)\"}" || echo "ERROR")
    
    if [[ "$TEST_RESULT" == *"access_token"* ]]; then
        log "✅ Création compte fonctionnelle"
        return 0
    else
        log "❌ Création compte échoue: $TEST_RESULT"
        return 1
    fi
}

# Correction automatique
auto_fix() {
    log "🔧 Correction automatique..."
    
    if [ -x "$CONFIG_SCRIPT" ]; then
        log "📋 Exécution script de configuration automatique..."
        "$CONFIG_SCRIPT"
        
        # Attendre que les services redémarrent
        sleep 10
        
        log "✅ Correction appliquée"
        return 0
    else
        log "❌ Script de configuration non disponible: $CONFIG_SCRIPT"
        return 1
    fi
}

# Vérification services
check_services() {
    log "🔍 Vérification statut services..."
    
    BACKEND_STATUS=$(sudo supervisorctl status backend | grep RUNNING || echo "FAILED")
    FRONTEND_STATUS=$(sudo supervisorctl status frontend | grep RUNNING || echo "FAILED")
    MONGODB_STATUS=$(sudo supervisorctl status mongodb | grep RUNNING || echo "FAILED")
    
    if [[ "$BACKEND_STATUS" == *"RUNNING"* ]] && \
       [[ "$FRONTEND_STATUS" == *"RUNNING"* ]] && \
       [[ "$MONGODB_STATUS" == *"RUNNING"* ]]; then
        log "✅ Tous les services sont opérationnels"
        return 0
    else
        log "❌ Un ou plusieurs services ne fonctionnent pas"
        log "Backend: $BACKEND_STATUS"
        log "Frontend: $FRONTEND_STATUS"  
        log "MongoDB: $MONGODB_STATUS"
        return 1
    fi
}

# Fonction principale
main() {
    log "🩺 Début vérification santé BOOKTIME"
    
    # Vérifier services d'abord
    if ! check_services; then
        log "⚠️ Services non opérationnels - Tentative redémarrage"
        sudo supervisorctl restart all
        sleep 5
        
        if ! check_services; then
            log "❌ Impossible de redémarrer les services"
            exit 1
        fi
    fi
    
    # Vérifier configuration
    if ! check_frontend_config; then
        log "⚠️ Configuration problématique - Correction automatique"
        if auto_fix; then
            log "✅ Configuration corrigée"
        else
            log "❌ Impossible de corriger automatiquement"
            exit 1
        fi
    fi
    
    # Test fonctionnel
    if test_account_creation; then
        log "✅ SUCCÈS - Application BOOKTIME entièrement fonctionnelle"
        echo "SUCCESS: BOOKTIME operational - Account creation working"
        exit 0
    else
        log "❌ Test création compte échoue - Tentative correction"
        if auto_fix && test_account_creation; then
            log "✅ Problème corrigé après reconfiguration"
            echo "SUCCESS: BOOKTIME operational after fix"
            exit 0
        else
            log "❌ ÉCHEC - Impossible de résoudre le problème automatiquement"
            echo "FAILED: Manual intervention required"
            exit 1
        fi
    fi
}

# Exécution si appelé directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi