#!/bin/bash
# Script de configuration automatique pour environnement Preview Emergent
# Résout définitivement le problème de création de compte en configurant l'URL backend correcte

set -e

echo "🔧 Configuration automatique Preview Emergent - Résolution définitive problème création compte"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Détection URL Preview Emergent
detect_preview_url() {
    log "🔍 Détection URL Preview Emergent..."
    
    # Méthode 1: Variable d'environnement preview_endpoint
    if [ ! -z "$preview_endpoint" ]; then
        PREVIEW_URL="$preview_endpoint"
        log "✅ URL Preview détectée via variable env: $PREVIEW_URL"
        return 0
    fi
    
    # Méthode 2: Recherche dans /proc/self/environ
    PREVIEW_URL=$(grep -ao 'preview_endpoint=[^[:space:]]*' /proc/self/environ 2>/dev/null | cut -d'=' -f2 || true)
    if [ ! -z "$PREVIEW_URL" ]; then
        log "✅ URL Preview détectée via /proc/environ: $PREVIEW_URL"
        return 0
    fi
    
    # Méthode 3: Recherche dans les variables système
    PREVIEW_URL=$(env | grep -i preview | grep -o 'https://[^[:space:]]*\.preview\.emergentagent\.com' | head -n1 || true)
    if [ ! -z "$PREVIEW_URL" ]; then
        log "✅ URL Preview détectée via env grep: $PREVIEW_URL"
        return 0
    fi
    
    log "❌ Aucune URL Preview détectée - utilisation localhost par défaut"
    PREVIEW_URL="http://localhost:8001"
    return 1
}

# Configuration frontend .env
configure_frontend() {
    log "⚙️ Configuration frontend .env..."
    
    # Backup de l'ancien fichier si existe
    if [ -f "/app/frontend/.env" ]; then
        cp "/app/frontend/.env" "/app/frontend/.env.backup.$(date +%s)"
        log "💾 Backup ancien .env créé"
    fi
    
    # Création nouveau fichier .env
    cat > /app/frontend/.env << EOF
# Configuration automatique Preview Emergent - $(date)
# URL Backend - Detectée automatiquement pour résoudre problème création compte
REACT_APP_BACKEND_URL=$PREVIEW_URL

# Configuration réseau pour accès externe
HOST=0.0.0.0
DANGEROUSLY_DISABLE_HOST_CHECK=true

# Configuration générée automatiquement par configure_preview.sh
# NE PAS MODIFIER MANUELLEMENT - Utiliser le script pour les mises à jour
EOF

    log "✅ Fichier /app/frontend/.env configuré avec URL: $PREVIEW_URL"
}

# Test connectivité API
test_api_connectivity() {
    log "🧪 Test connectivité API backend..."
    
    # Test health endpoint
    if curl -s --max-time 10 "$PREVIEW_URL/health" > /dev/null 2>&1; then
        log "✅ API Health accessible: $PREVIEW_URL/health"
    else
        log "⚠️ API Health inaccessible: $PREVIEW_URL/health"
    fi
    
    # Test register endpoint
    REGISTER_TEST=$(curl -s --max-time 10 -X POST "$PREVIEW_URL/api/auth/register" \
        -H "Content-Type: application/json" \
        -d '{"first_name": "Test", "last_name": "Script"}' || echo "ERROR")
    
    if [[ "$REGISTER_TEST" == *"access_token"* ]]; then
        log "✅ API Register fonctionnelle: $PREVIEW_URL/api/auth/register"
        return 0
    else
        log "❌ API Register non accessible: $PREVIEW_URL/api/auth/register"
        return 1
    fi
}

# Redémarrage services
restart_services() {
    log "🔄 Redémarrage services avec nouvelle configuration..."
    
    # Redémarrage frontend avec nouvelle config
    sudo supervisorctl restart frontend
    sleep 3
    
    # Vérification statut
    STATUS=$(sudo supervisorctl status frontend | grep RUNNING || echo "FAILED")
    if [[ "$STATUS" == *"RUNNING"* ]]; then
        log "✅ Frontend redémarré avec succès"
    else
        log "❌ Erreur redémarrage frontend"
        return 1
    fi
}

# Validation finale
validate_solution() {
    log "✨ Validation finale solution..."
    
    # Vérifier fichier .env
    if [ -f "/app/frontend/.env" ] && grep -q "$PREVIEW_URL" "/app/frontend/.env"; then
        log "✅ Fichier .env correctement configuré"
    else
        log "❌ Erreur configuration .env"
        return 1
    fi
    
    # Vérifier services
    FRONTEND_STATUS=$(sudo supervisorctl status frontend)
    if [[ "$FRONTEND_STATUS" == *"RUNNING"* ]]; then
        log "✅ Service frontend opérationnel"
    else
        log "❌ Service frontend non opérationnel"
        return 1
    fi
    
    log "🎉 Solution définitive appliquée avec succès !"
    log "📋 URL Backend configurée: $PREVIEW_URL"
    log "📋 Fichier .env: /app/frontend/.env"
    log "📋 Services: Frontend RUNNING"
    
    return 0
}

# Exécution du script
main() {
    log "🚀 Début configuration automatique Preview Emergent"
    
    # Étapes de configuration
    if detect_preview_url; then
        configure_frontend
        
        if test_api_connectivity; then
            restart_services
            
            if validate_solution; then
                log "✅ SUCCÈS - Problème création compte résolu définitivement"
                echo "Configuration terminée avec succès. URL Backend: $PREVIEW_URL"
                exit 0
            else
                log "❌ ÉCHEC - Validation finale"
                exit 1
            fi
        else
            log "⚠️ API non accessible - Configuration appliquée mais à vérifier"
            restart_services
            log "⚠️ Veuillez vérifier manuellement la connectivité"
            exit 2
        fi
    else
        log "⚠️ URL Preview non détectée - Configuration localhost appliquée"
        configure_frontend
        restart_services
        log "⚠️ Configuration par défaut appliquée - À adapter si nécessaire"
        exit 3
    fi
}

# Lancement du script
main "$@"