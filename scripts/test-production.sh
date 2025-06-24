#!/bin/bash

# 🧪 Script de test pour l'environnement de production

echo "🧪 Test de l'environnement de production BOOKTIME..."

# Configuration
BACKEND_URL=${1:-"http://localhost:8001"}
FRONTEND_URL=${2:-"http://localhost:3000"}

echo "🔍 Test du backend : $BACKEND_URL"
echo "🔍 Test du frontend : $FRONTEND_URL"

# Test de connectivité backend
echo "📡 Test de connectivité backend..."
if curl -s "$BACKEND_URL" > /dev/null; then
    echo "✅ Backend accessible"
    
    # Test API welcome
    WELCOME_MSG=$(curl -s "$BACKEND_URL" | grep -o '"message":"[^"]*"')
    if [[ $WELCOME_MSG == *"BOOKTIME"* ]]; then
        echo "✅ API BOOKTIME détectée"
    else
        echo "⚠️  Message d'accueil inattendu"
    fi
    
    # Test endpoint /api/books
    echo "📚 Test de l'endpoint /api/books..."
    BOOKS_RESPONSE=$(curl -s "$BACKEND_URL/api/books")
    if [[ $BOOKS_RESPONSE == "["* ]]; then
        echo "✅ Endpoint /api/books fonctionne"
    else
        echo "❌ Erreur sur /api/books"
        echo "Response: $BOOKS_RESPONSE"
    fi
    
    # Test endpoint /api/stats
    echo "📊 Test de l'endpoint /api/stats..."
    STATS_RESPONSE=$(curl -s "$BACKEND_URL/api/stats")
    if [[ $STATS_RESPONSE == *"total_books"* ]]; then
        echo "✅ Endpoint /api/stats fonctionne"
    else
        echo "❌ Erreur sur /api/stats"
    fi
    
else
    echo "❌ Backend non accessible à $BACKEND_URL"
    echo "💡 Vérifiez que le backend est démarré"
fi

echo ""

# Test de connectivité frontend
echo "🌐 Test de connectivité frontend..."
if curl -s "$FRONTEND_URL" > /dev/null; then
    echo "✅ Frontend accessible"
    
    # Vérifier le titre de la page
    PAGE_TITLE=$(curl -s "$FRONTEND_URL" | grep -o '<title>[^<]*</title>')
    if [[ $PAGE_TITLE == *"BOOKTIME"* || $PAGE_TITLE == *"React"* ]]; then
        echo "✅ Page frontend chargée"
    else
        echo "⚠️  Titre de page inattendu: $PAGE_TITLE"
    fi
    
else
    echo "❌ Frontend non accessible à $FRONTEND_URL"
    echo "💡 Vérifiez que le frontend est démarré"
fi

echo ""

# Test de l'intégration frontend-backend
echo "🔗 Test d'intégration frontend-backend..."
if [ "$FRONTEND_URL" != "http://localhost:3000" ]; then
    echo "📱 Test sur URL de production..."
    
    # Vérifier que le frontend peut atteindre le backend
    # (Ce test nécessiterait du JavaScript côté navigateur)
    echo "💡 Test d'intégration à effectuer manuellement :"
    echo "   1. Ouvrez $FRONTEND_URL"
    echo "   2. Ouvrez les DevTools (F12)"
    echo "   3. Vérifiez qu'aucune erreur CORS n'apparaît"
    echo "   4. Testez l'ajout d'un livre"
else
    echo "🏠 Environnement local détecté"
fi

echo ""
echo "📋 Résumé des tests :"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "💡 Pour tester en production :"
echo "   ./scripts/test-production.sh https://votre-backend.railway.app https://votre-frontend.vercel.app"