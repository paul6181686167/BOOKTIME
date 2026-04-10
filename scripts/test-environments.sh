#!/bin/bash
# Script tests multi-environnements BOOKTIME
# Usage: ./test-environments.sh

set -e

echo "🧪 TESTS MULTI-ENVIRONNEMENTS BOOKTIME"
echo "======================================"

# Configuration URLs
VERCEL_URL="https://booktime-sg59-git-main-paul6181686167s-projects.vercel.app"
EMERGENT_URL="https://changelog-reader-9.preview.emergentagent.com"
RAILWAY_URL=${1:-"https://booktime-backend-production.up.railway.app"}
LOCAL_URL="http://localhost:8001"

echo "🔗 URLs de test:"
echo "   Vercel:   $VERCEL_URL"
echo "   Emergent: $EMERGENT_URL" 
echo "   Railway:  $RAILWAY_URL"
echo "   Local:    $LOCAL_URL"
echo ""

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local endpoint=$3
    local expected=$4
    
    echo "🔍 Test $name: $url$endpoint"
    
    if command -v curl >/dev/null 2>&1; then
        response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$url$endpoint" 2>/dev/null || echo "ERROR")
        
        if [[ "$response" == *"HTTPSTATUS:200"* ]]; then
            echo "✅ $name OK"
            if [[ "$response" == *"$expected"* ]]; then
                echo "   ✅ Response contains: $expected"
            else
                echo "   ⚠️  Response unexpected"
            fi
        else
            echo "❌ $name FAILED"
            echo "   Response: $response"
        fi
    else
        echo "⚠️  curl not available, skipping $name"
    fi
    echo ""
}

# Tests Backend Railway
echo "🚂 TESTS BACKEND RAILWAY"
echo "------------------------"
test_endpoint "Health" "$RAILWAY_URL" "/health" "\"status\":\"ok\""
test_endpoint "Deployment" "$RAILWAY_URL" "/api/deployment-status" "\"status\":\"deployed\""
test_endpoint "Auth Register" "$RAILWAY_URL" "/api/auth/register" "POST"

# Tests Frontend Vercel
echo "🌐 TESTS FRONTEND VERCEL"  
echo "-----------------------"
test_endpoint "Homepage" "$VERCEL_URL" "/" "BookTime"
test_endpoint "Static" "$VERCEL_URL" "/static/css" "404"  # Normal pour CSS

# Tests Preview Emergent
echo "🔬 TESTS PREVIEW EMERGENT"
echo "------------------------"
test_endpoint "Homepage" "$EMERGENT_URL" "/" "BookTime"
test_endpoint "Health" "$EMERGENT_URL" "/health" "\"status\":\"ok\""

# Tests Local (si disponible)
echo "💻 TESTS LOCAL (si disponible)"
echo "-----------------------------"
if curl -s "http://localhost:8001/health" >/dev/null 2>&1; then
    test_endpoint "Local Health" "$LOCAL_URL" "/health" "\"status\":\"ok\""
    echo "✅ Local backend accessible"
else
    echo "⚠️  Local backend non accessible (normal si arrêté)"
fi

if curl -s "http://localhost:3000" >/dev/null 2>&1; then
    test_endpoint "Local Frontend" "http://localhost:3000" "/" "BookTime"
    echo "✅ Local frontend accessible"
else
    echo "⚠️  Local frontend non accessible (normal si arrêté)"
fi

# Résumé
echo ""
echo "📊 RÉSUMÉ TESTS"
echo "==============="
echo "✅ = Service opérationnel"
echo "❌ = Service défaillant" 
echo "⚠️  = Service optionnel/attendu"
echo ""
echo "🎯 ARCHITECTURE PRODUCTION:"
echo "   Frontend Vercel → Backend Railway → Database Atlas"
echo ""
echo "🔧 ARCHITECTURE DEVELOPMENT:"
echo "   Frontend Local → Backend Local → Database Local/Atlas"
echo ""
echo "🔬 ARCHITECTURE PREVIEW:"
echo "   Frontend+Backend Emergent → Database Local/Atlas"
echo ""

# Instructions finales
echo "📋 PROCHAINS TESTS MANUELS:"
echo "1. 🌐 Ouvrir: $VERCEL_URL"
echo "2. 👤 Tester création compte + connexion"
echo "3. 📚 Tester ajout livre + recherche"  
echo "4. 📊 Vérifier statistiques + navigation"
echo "5. 🔄 Tester dans Chrome + Firefox + Mobile"
echo ""
echo "✅ Tests automatiques terminés!"
echo ""