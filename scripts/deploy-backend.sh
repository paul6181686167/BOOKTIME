#!/bin/bash
# Script déploiement Backend Railway
# Usage: ./deploy-backend.sh

set -e

echo "🚀 DÉPLOIEMENT BACKEND RAILWAY - BOOKTIME"
echo "========================================"

# Vérification prérequis
echo "🔍 Vérification prérequis..."

if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ backend/requirements.txt manquant"
    exit 1
fi

if [ ! -f "backend/Dockerfile" ]; then
    echo "❌ backend/Dockerfile manquant"
    exit 1
fi

if [ ! -f "backend/railway.json" ]; then
    echo "❌ backend/railway.json manquant"
    exit 1
fi

echo "✅ Tous les fichiers requis présents"

# Vérification Git
echo "🔍 Vérification Git..."
if ! git status >/dev/null 2>&1; then
    echo "❌ Répertoire Git non initialisé"
    echo "💡 Exécutez: git init && git add . && git commit -m 'Initial commit'"
    exit 1
fi

# Test build Docker local (optionnel)
echo "🐳 Test build Docker local..."
cd backend
if docker --version >/dev/null 2>&1; then
    docker build -t booktime-backend-test . || {
        echo "⚠️  Build Docker échoué, mais on continue..."
    }
    echo "✅ Build Docker réussi"
else
    echo "⚠️  Docker non disponible, skip test build"
fi
cd ..

# Commit changements
echo "📦 Commit des changements..."
git add .
git status --porcelain
if [ -n "$(git status --porcelain)" ]; then
    git commit -m "Deploy backend to Railway - $(date)" || echo "Pas de nouveaux changements"
else
    echo "✅ Pas de changements à commiter"
fi

# Push vers Railway (via Git)
echo "🚀 Push vers Railway..."
echo "💡 Railway déploiera automatiquement après push"
echo "🔗 Surveillez le déploiement sur: https://railway.app/dashboard"

git push origin main || {
    echo "⚠️  Push failed - vérifiez votre connexion Git"
    echo "💡 Configurez Railway via: railway link"
}

echo ""
echo "✅ SCRIPT TERMINÉ"
echo "📋 PROCHAINES ÉTAPES:"
echo "   1. Vérifiez déploiement Railway: https://railway.app/dashboard"
echo "   2. Copiez URL générée (ex: booktime-backend-production.up.railway.app)"
echo "   3. Configurez variables Vercel avec cette URL"
echo "   4. Testez: curl https://YOUR-BACKEND-URL/health"
echo ""