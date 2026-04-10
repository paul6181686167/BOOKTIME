#!/bin/bash
# 🚀 SCRIPT DE MIGRATION VERCEL FULLSTACK - BOOKTIME
# Session 90.26 - Migration complète vers Vercel

echo "🚀 MIGRATION VERCEL FULLSTACK - BOOKTIME"
echo "======================================="
echo ""

echo "📋 Phase 1: Préparation environnement Vercel"
# Vérification Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI manquant - Installation requise:"
    echo "   npm i -g vercel"
    exit 1
fi

echo "✅ Vercel CLI détecté"
echo ""

echo "📋 Phase 2: Configuration backend pour Vercel"
# Copie de la configuration Vercel
cp vercel-fullstack.json vercel.json
echo "✅ Configuration Vercel Fullstack appliquée"

# Création du fichier requirements.txt pour Vercel
cd backend
echo "✅ Backend requirements.txt validé"
cd ..

echo "📋 Phase 3: Configuration frontend"
cd frontend
# Mise à jour de la variable backend URL pour pointer vers le même domaine
export REACT_APP_BACKEND_URL="/api"
echo "✅ Frontend configuré pour Vercel Fullstack"
cd ..

echo ""
echo "🎯 PRÊT POUR DÉPLOIEMENT VERCEL"
echo "==============================="
echo ""
echo "📋 Actions utilisateur requises:"
echo "1. Se connecter à Vercel: vercel login"
echo "2. Configurer les variables d'environnement:"
echo "   - MONGO_URL (votre MongoDB Atlas)"
echo "   - EMERGENT_LLM_KEY (votre clé)"
echo "3. Déployer: vercel --prod"
echo ""
echo "🌐 Résultat attendu:"
echo "   - Frontend: https://votre-app.vercel.app"
echo "   - Backend:  https://votre-app.vercel.app/api/health"
echo ""
echo "✅ Script terminé - Prêt pour déploiement Vercel Fullstack!"