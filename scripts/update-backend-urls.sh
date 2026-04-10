#!/bin/bash

# Script pour mettre à jour tous les fichiers frontend
# Remplace process.env.REACT_APP_BACKEND_URL par API_BASE_URL depuis config/environment.js
# PARTIE AGENT - Finalisation configuration multi-environnement

echo "🔧 MISE À JOUR CONFIGURATION BACKEND URLs - PARTIE AGENT"
echo "==========================================================="

FRONTEND_DIR="/app/frontend/src"
FILES_UPDATED=0

# Fonction pour mettre à jour un fichier
update_file() {
    local file="$1"
    local relative_path="$2"
    
    echo "🔍 Vérification: $relative_path"
    
    # Vérifier si le fichier contient l'ancien pattern
    if grep -q "process\.env\.REACT_APP_BACKEND_URL.*localhost:8001" "$file"; then
        echo "  📝 Mise à jour nécessaire..."
        
        # Calculer le bon chemin d'import selon la profondeur
        local depth=$(echo "$relative_path" | tr '/' '\n' | wc -l)
        local import_path=""
        
        if [[ "$relative_path" =~ ^components/ ]]; then
            import_path="../config/environment"
        elif [[ "$relative_path" =~ ^components/.+/ ]]; then
            import_path="../../config/environment"  
        elif [[ "$relative_path" =~ ^services/ ]]; then
            import_path="../config/environment"
        else
            import_path="./config/environment"
        fi
        
        # Faire une copie de sauvegarde
        cp "$file" "$file.backup"
        
        # 1. Ajouter l'import en haut du fichier (après autres imports React/bibliothèques)
        if ! grep -q "import.*API_BASE_URL.*from.*config/environment" "$file"; then
            # Trouver la ligne après les derniers imports
            local last_import_line=$(grep -n "^import\|^const.*require" "$file" | tail -1 | cut -d: -f1)
            if [ -n "$last_import_line" ]; then
                sed -i "${last_import_line}a\\import { API_BASE_URL } from '$import_path';" "$file"
            else
                # Si pas d'imports, ajouter au début
                sed -i "1i\\import { API_BASE_URL } from '$import_path';" "$file"
            fi
        fi
        
        # 2. Remplacer les occurrences de process.env.REACT_APP_BACKEND_URL
        sed -i 's/process\.env\.REACT_APP_BACKEND_URL || .*http:\/\/localhost:8001.*/API_BASE_URL/g' "$file"
        sed -i 's/const backendUrl = process\.env\.REACT_APP_BACKEND_URL || .*http:\/\/localhost:8001.*/const backendUrl = API_BASE_URL;/g' "$file"
        
        # 3. Cas spéciaux pour certains patterns
        sed -i 's/\${process\.env\.REACT_APP_BACKEND_URL}/\${API_BASE_URL}/g' "$file"
        
        echo "  ✅ Fichier mis à jour"
        FILES_UPDATED=$((FILES_UPDATED + 1))
    else
        echo "  ➡️  Déjà à jour"
    fi
}

# Parcourir tous les fichiers .js dans src/
echo "📂 Parcours des fichiers JavaScript..."

find "$FRONTEND_DIR" -name "*.js" -type f | while read -r file; do
    # Calculer le chemin relatif depuis src/
    relative_path=$(realpath --relative-to="$FRONTEND_DIR" "$file")
    
    # Exclure certains fichiers
    if [[ "$relative_path" =~ ^config/environment\.js$ ]] || 
       [[ "$relative_path" =~ ^setupTests\.js$ ]] ||
       [[ "$relative_path" =~ ^.*\.test\.js$ ]] || 
       [[ "$relative_path" =~ ^.*\.spec\.js$ ]]; then
        continue
    fi
    
    update_file "$file" "$relative_path"
done

echo ""
echo "📊 RÉSUMÉ MISE À JOUR"
echo "===================="
echo "✅ Fichiers mis à jour: $FILES_UPDATED"
echo "🔧 Configuration: API_BASE_URL depuis config/environment.js"
echo "🌍 Multi-environnement: Local/Vercel/Emergent/Railway"
echo ""
echo "🎯 PARTIE AGENT - CONFIGURATION BACKEND URLs TERMINÉE !"
echo ""

# Test de validation
echo "🧪 VALIDATION CONFIGURATION"
echo "============================"

# Compter les fichiers qui utilisent encore l'ancien pattern
OLD_PATTERN_COUNT=$(find "$FRONTEND_DIR" -name "*.js" -type f -exec grep -l "process\.env\.REACT_APP_BACKEND_URL.*localhost:8001" {} \; | wc -l)
NEW_PATTERN_COUNT=$(find "$FRONTEND_DIR" -name "*.js" -type f -exec grep -l "API_BASE_URL.*from.*config/environment" {} \; | wc -l)

echo "❌ Fichiers avec ancien pattern: $OLD_PATTERN_COUNT"
echo "✅ Fichiers avec nouveau pattern: $NEW_PATTERN_COUNT"

if [ "$OLD_PATTERN_COUNT" -eq 0 ]; then
    echo ""
    echo "🎉 SUCCÈS - TOUS LES FICHIERS MIGRÉS VERS LA NOUVELLE CONFIGURATION !"
    echo "🚀 PARTIE AGENT 100% TERMINÉE - PRÊT POUR PARTIE UTILISATEUR"
else
    echo ""
    echo "⚠️  ATTENTION - $OLD_PATTERN_COUNT fichiers nécessitent encore une mise à jour manuelle"
    echo "📋 Liste des fichiers restants:"
    find "$FRONTEND_DIR" -name "*.js" -type f -exec grep -l "process\.env\.REACT_APP_BACKEND_URL.*localhost:8001" {} \;
fi

echo ""