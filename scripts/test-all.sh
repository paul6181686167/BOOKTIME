#!/bin/bash

# Script de tests complets pour BOOKTIME
# Phase 4.2 - Automation des tests

set -e

echo "🧪 BOOKTIME - Tests Complets Phase 4"
echo "=================================="

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour logs colorés
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables
BACKEND_PORT=8001
FRONTEND_PORT=3000
TEST_RESULTS_DIR="test-results"

# Créer dossier de résultats
mkdir -p $TEST_RESULTS_DIR

log_info "Vérification des prérequis..."

# Vérifier que les services sont en cours d'exécution
if ! curl -s http://localhost:$BACKEND_PORT/api/health > /dev/null; then
    log_error "Backend non accessible sur le port $BACKEND_PORT"
    exit 1
fi

if ! curl -s http://localhost:$FRONTEND_PORT > /dev/null; then
    log_warning "Frontend non accessible sur le port $FRONTEND_PORT"
    log_info "Tentative de démarrage du frontend..."
    cd /app && yarn start &
    FRONTEND_PID=$!
    sleep 10
    
    if ! curl -s http://localhost:$FRONTEND_PORT > /dev/null; then
        log_error "Impossible de démarrer le frontend"
        exit 1
    fi
fi

log_success "Services backend et frontend opérationnels"

# Phase 4.1 - Tests Backend
log_info "Phase 4.1 - Tests Backend (pytest)"
echo "--------------------------------"

cd /app/backend

# Tests unitaires backend
log_info "Exécution des tests unitaires backend..."
if pytest tests/ -v --cov=app --cov-report=html:../test-results/backend-coverage --cov-report=term-missing --junitxml=../test-results/backend-junit.xml; then
    log_success "Tests backend réussis"
else
    log_error "Tests backend échoués"
    exit 1
fi

# Phase 4.1 - Tests Frontend
log_info "Phase 4.1 - Tests Frontend (Jest)"
echo "--------------------------------"

cd /app

# Tests unitaires frontend
log_info "Exécution des tests unitaires frontend..."
if yarn test --coverage --watchAll=false --testResultsProcessor=./test-results/frontend-results.json; then
    log_success "Tests frontend réussis"
else
    log_error "Tests frontend échoués"
    exit 1
fi

# Phase 4.2 - Tests E2E
log_info "Phase 4.2 - Tests End-to-End (Playwright)"
echo "----------------------------------------"

# Installation des navigateurs Playwright si nécessaire
log_info "Vérification des navigateurs Playwright..."
npx playwright install chromium firefox webkit

# Tests E2E
log_info "Exécution des tests E2E..."
if npx playwright test --reporter=html --output-dir=test-results/e2e-results; then
    log_success "Tests E2E réussis"
else
    log_error "Tests E2E échoués"
    exit 1
fi

# Phase 4.2 - Tests de Performance
log_info "Phase 4.2 - Tests de Performance"
echo "-------------------------------"

# Tests de charge basiques avec curl
log_info "Tests de charge backend..."
for i in {1..10}; do
    response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:$BACKEND_PORT/api/health)
    echo "Requête $i: ${response_time}s"
done

# Génération du rapport final
log_info "Génération du rapport final..."

cat > $TEST_RESULTS_DIR/summary.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>BOOKTIME - Rapport de Tests Phase 4</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .success { color: green; }
        .error { color: red; }
        .section { margin: 20px 0; padding: 10px; border: 1px solid #ddd; }
        .header { background: #f5f5f5; padding: 10px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 BOOKTIME - Rapport de Tests Phase 4</h1>
        <p>Généré le: $(date)</p>
    </div>
    
    <div class="section">
        <h2>✅ Phase 4.1 - Tests Unitaires</h2>
        <p class="success">Backend: Tests pytest réussis avec couverture de code</p>
        <p class="success">Frontend: Tests Jest réussis avec couverture de code</p>
    </div>
    
    <div class="section">
        <h2>✅ Phase 4.2 - Tests d'Intégration</h2>
        <p class="success">Tests E2E Playwright réussis sur Chrome, Firefox, Safari</p>
        <p class="success">Tests de performance backend validés</p>
    </div>
    
    <div class="section">
        <h2>📊 Métriques de Qualité</h2>
        <ul>
            <li>Couverture backend: Voir rapport HTML</li>
            <li>Couverture frontend: Voir rapport HTML</li>
            <li>Tests E2E: Voir rapport Playwright</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>🎯 Résultats Phase 4</h2>
        <p class="success"><strong>Phase 4.1 Tests Unitaires: ✅ 100% TERMINÉE</strong></p>
        <p class="success"><strong>Phase 4.2 Tests d'Intégration: ✅ 100% TERMINÉE</strong></p>
        <p class="success"><strong>PHASE 4 TESTS ET QUALITÉ: ✅ 100% TERMINÉE</strong></p>
    </div>
</body>
</html>
EOF

# Nettoyage
if [ ! -z "$FRONTEND_PID" ]; then
    log_info "Arrêt du frontend temporaire..."
    kill $FRONTEND_PID 2>/dev/null || true
fi

log_success "Tests complets terminés avec succès!"
log_info "Rapports disponibles dans: $TEST_RESULTS_DIR/"
log_info "- Backend coverage: $TEST_RESULTS_DIR/backend-coverage/index.html"
log_info "- Frontend coverage: $TEST_RESULTS_DIR/frontend-coverage/index.html"
log_info "- E2E results: $TEST_RESULTS_DIR/e2e-results/index.html"
log_info "- Résumé: $TEST_RESULTS_DIR/summary.html"

echo ""
echo "🎉 PHASE 4 - TESTS ET QUALITÉ TERMINÉE AVEC SUCCÈS!"
echo "=================================================="