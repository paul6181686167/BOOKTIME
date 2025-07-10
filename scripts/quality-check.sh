#!/bin/bash

# Script de vérification qualité pour BOOKTIME
# Phase 4 - Outils de qualité et métriques

set -e

echo "🔍 BOOKTIME - Vérification Qualité"
echo "================================="

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Compteurs
TOTAL_CHECKS=0
PASSED_CHECKS=0

check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if eval "$1"; then
        log_success "$2"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        log_error "$2"
        return 1
    fi
}

echo ""
log_info "1. Vérification de la structure du projet..."

check "[ -f /app/backend/server.py ]" "✓ Backend principal existe"
check "[ -f /app/frontend/src/App.js ]" "✓ Frontend principal existe"
check "[ -d /app/backend/tests ]" "✓ Dossier tests backend existe"
check "[ -d /app/frontend/src/__tests__ ]" "✓ Dossier tests frontend existe"
check "[ -f /app/playwright.config.js ]" "✓ Configuration Playwright existe"

echo ""
log_info "2. Vérification des dépendances..."

check "cd /app/backend && python -c 'import pytest, httpx, faker'" "✓ Dépendances tests backend installées"
check "cd /app && yarn list @testing-library/react > /dev/null 2>&1" "✓ Dépendances tests frontend installées"
check "cd /app && yarn list @playwright/test > /dev/null 2>&1" "✓ Playwright installé"

echo ""
log_info "3. Vérification de la qualité du code..."

# Lint frontend
if cd /app && yarn lint > /dev/null 2>&1; then
    log_success "✓ Linting frontend réussi"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "✗ Erreurs de linting frontend détectées"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

# Build frontend
if cd /app && yarn build > /dev/null 2>&1; then
    log_success "✓ Build frontend réussi"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    log_error "✗ Erreurs de build frontend"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo ""
log_info "4. Vérification de la configuration des tests..."

check "[ -f /app/backend/pytest.ini ]" "✓ Configuration pytest existe"
check "[ -f /app/frontend/src/setupTests.js ]" "✓ Configuration Jest existe"
check "grep -q 'collectCoverageFrom' /app/package.json" "✓ Configuration couverture frontend"
check "grep -q 'cov-fail-under=80' /app/backend/pytest.ini" "✓ Seuil couverture backend configuré"

echo ""
log_info "5. Vérification des tests existants..."

BACKEND_TESTS=$(find /app/backend/tests -name "test_*.py" | wc -l)
FRONTEND_TESTS=$(find /app/frontend/src -name "*.test.js" | wc -l)
E2E_TESTS=$(find /app/e2e -name "*.spec.js" | wc -l)

check "[ $BACKEND_TESTS -ge 3 ]" "✓ Tests backend suffisants ($BACKEND_TESTS fichiers)"
check "[ $FRONTEND_TESTS -ge 3 ]" "✓ Tests frontend suffisants ($FRONTEND_TESTS fichiers)"
check "[ $E2E_TESTS -ge 3 ]" "✓ Tests E2E suffisants ($E2E_TESTS fichiers)"

echo ""
log_info "6. Vérification des scripts d'automatisation..."

check "[ -f /app/scripts/test-all.sh ]" "✓ Script de tests complets existe"
check "[ -x /app/scripts/test-all.sh ]" "✓ Script de tests exécutable"
check "[ -f /app/.github/workflows/tests.yml ]" "✓ Pipeline CI/CD configuré"

echo ""
log_info "7. Métriques de qualité..."

# Compter les lignes de code
BACKEND_LOC=$(find /app/backend -name "*.py" -not -path "*/tests/*" -exec wc -l {} + | tail -1 | awk '{print $1}')
FRONTEND_LOC=$(find /app/frontend/src -name "*.js" -not -path "*/__tests__/*" -not -name "*.test.js" -exec wc -l {} + | tail -1 | awk '{print $1}')
TEST_LOC=$(find /app -name "test_*.py" -o -name "*.test.js" -o -name "*.spec.js" | xargs wc -l | tail -1 | awk '{print $1}')

log_info "Backend LOC: $BACKEND_LOC"
log_info "Frontend LOC: $FRONTEND_LOC"
log_info "Tests LOC: $TEST_LOC"

# Ratio de tests
TOTAL_LOC=$((BACKEND_LOC + FRONTEND_LOC))
if [ $TOTAL_LOC -gt 0 ]; then
    TEST_RATIO=$((TEST_LOC * 100 / TOTAL_LOC))
    log_info "Ratio tests/code: ${TEST_RATIO}%"
    
    check "[ $TEST_RATIO -ge 15 ]" "✓ Ratio tests/code acceptable (≥15%)"
fi

echo ""
echo "========================================="
echo "📊 RÉSUMÉ DE LA VÉRIFICATION QUALITÉ"
echo "========================================="
echo "Vérifications réussies: $PASSED_CHECKS/$TOTAL_CHECKS"

PERCENTAGE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
echo "Pourcentage de réussite: $PERCENTAGE%"

if [ $PERCENTAGE -ge 90 ]; then
    log_success "🎉 Excellente qualité! Phase 4 prête!"
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠️  Qualité acceptable mais améliorations possibles${NC}"
else
    log_error "❌ Qualité insuffisante, corrections nécessaires"
    exit 1
fi

echo ""
log_info "Phase 4 - Tests et Qualité: Configuration validée ✅"