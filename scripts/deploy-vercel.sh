#!/bin/bash
# Script configuration Frontend Vercel
# Usage: ./deploy-vercel.sh <BACKEND_URL>

set -e

echo "🚀 CONFIGURATION FRONTEND VERCEL - BOOKTIME"
echo "==========================================="

# Validation argument
BACKEND_URL=$1
if [ -z "$BACKEND_URL" ]; then
    echo "❌ Usage: ./deploy-vercel.sh <BACKEND_URL>"
    echo "💡 Exemple: ./deploy-vercel.sh https://booktime-backend-production.up.railway.app"
    exit 1
fi

echo "🔗 Backend URL: $BACKEND_URL"

# Vérification répertoire frontend
if [ ! -f "frontend/package.json" ]; then
    echo "❌ frontend/package.json manquant"
    exit 1
fi

cd frontend

# Test build local
echo "🔨 Test build local..."
if [ ! -d "node_modules" ]; then
    echo "📦 Installation dépendances..."
    npm install || yarn install
fi

# Configuration variable temporaire pour build test
export REACT_APP_BACKEND_URL=$BACKEND_URL
export REACT_APP_ENVIRONMENT=production

echo "🔨 Build de test..."
npm run build || {
    echo "❌ Build échoué"
    exit 1
}
echo "✅ Build local réussi"

# Instructions Vercel Dashboard
echo ""
echo "✅ BUILD TEST RÉUSSI"
echo "📋 CONFIGURATION VERCEL DASHBOARD:"
echo ""
echo "1. 🌐 Allez sur: https://vercel.com/dashboard"
echo "2. 📁 Sélectionnez votre projet: booktime-sg59"
echo "3. ⚙️  Allez dans Settings → Environment Variables"
echo "4. ➕ Ajoutez ces variables:"
echo ""
echo "   REACT_APP_BACKEND_URL = $BACKEND_URL"
echo "   REACT_APP_ENVIRONMENT = production"
echo ""
echo "5. 🚀 Allez dans Deployments → Redeploy latest"
echo "6. ✅ Testez création compte sur: https://booktime-sg59-git-main-paul6181686167s-projects.vercel.app"
echo ""

# Test connectivité backend
echo "🔍 Test connectivité backend..."
if command -v curl >/dev/null 2>&1; then
    echo "Testing: $BACKEND_URL/health"
    curl -s "$BACKEND_URL/health" | head -200 || echo "⚠️  Backend non accessible (normal si pas encore déployé)"
else
    echo "⚠️  curl non disponible, skip test connectivité"
fi

cd ..

echo ""
echo "✅ CONFIGURATION PRÊTE"
echo "🎯 Configurez maintenant Vercel Dashboard avec les variables ci-dessus"
echo ""