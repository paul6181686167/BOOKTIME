#!/bin/bash

# 🚀 Script de configuration rapide pour déploiement BOOKTIME

echo "🚀 Configuration du déploiement BOOKTIME..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "backend/server.py" ]; then
    echo "❌ Erreur: Exécutez ce script depuis la racine du projet BOOKTIME"
    exit 1
fi

echo "✅ Structure du projet détectée"

# Créer .gitignore si il n'existe pas
if [ ! -f ".gitignore" ]; then
    echo "📝 Création du .gitignore..."
    cat > .gitignore << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Runtime data
pids/
*.pid
*.seed

# Coverage directory used by tools like istanbul
coverage/

# Environment variables
.env.local
.env.production
.env.development.local
.env.test.local

# Build outputs
build/
dist/
.next/
.vercel/

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
tmp/
temp/
EOF
    echo "✅ .gitignore créé"
else
    echo "✅ .gitignore existe déjà"
fi

# Vérifier les dépendances frontend
echo "📦 Vérification des dépendances frontend..."
cd frontend
if [ ! -f "yarn.lock" ]; then
    echo "🔧 Installation des dépendances avec yarn..."
    yarn install
    echo "✅ Dépendances installées"
else
    echo "✅ Dépendances déjà installées"
fi
cd ..

# Test build frontend
echo "🏗️  Test du build frontend..."
cd frontend
if yarn build > /dev/null 2>&1; then
    echo "✅ Build frontend réussi"
    rm -rf build
else
    echo "❌ Erreur lors du build frontend"
    echo "💡 Vérifiez les erreurs avec: cd frontend && yarn build"
fi
cd ..

# Test backend
echo "🐍 Test du backend..."
cd backend
if python -c "import server; print('Backend OK')" > /dev/null 2>&1; then
    echo "✅ Backend testé avec succès"
else
    echo "❌ Erreur backend - vérifiez les dépendances Python"
    echo "💡 Installez avec: cd backend && pip install -r requirements.txt"
fi
cd ..

# Initialiser Git si nécessaire
if [ ! -d ".git" ]; then
    echo "📂 Initialisation du repository Git..."
    git init
    git add .
    git commit -m "🎉 Initial commit - BOOKTIME ready for deployment"
    echo "✅ Repository Git initialisé"
    echo "💡 Connectez votre repository GitHub avec:"
    echo "   git remote add origin https://github.com/VOTRE-USERNAME/VOTRE-REPO.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
else
    echo "✅ Repository Git déjà configuré"
fi

echo ""
echo "🎉 Configuration terminée !"
echo ""
echo "📋 Prochaines étapes :"
echo "1. Pushez votre code sur GitHub"
echo "2. Suivez le guide DEPLOYMENT.md"
echo "3. Configurez Railway (backend)"
echo "4. Configurez Vercel (frontend)"
echo "5. Configurez MongoDB Atlas"
echo ""
echo "⏱️  Temps estimé : 15-20 minutes"
echo "📖 Guide complet : DEPLOYMENT.md"