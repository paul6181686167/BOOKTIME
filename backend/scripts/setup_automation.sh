#!/bin/bash
"""
🎯 CONFIGURATION SYSTÈME AUTOMATISATION SÉRIES
Script de configuration et d'aide pour l'automatisation Open Library

Utilisation :
./setup_automation.sh
"""

# Configuration initiale
echo "🚀 CONFIGURATION SYSTÈME AUTOMATISATION SÉRIES OPEN LIBRARY"
echo "============================================================="

# Création dossiers nécessaires
echo "📁 Création des dossiers..."
mkdir -p /app/backend/data
mkdir -p /app/frontend/src/data
mkdir -p /app/logs
mkdir -p /app/reports
mkdir -p /app/backups/series_detection

# Permissions scripts
echo "🔐 Configuration des permissions..."
chmod +x /app/backend/scripts/*.py

# Vérification dépendances Python
echo "🐍 Vérification dépendances Python..."
python3 -c "import aiohttp, asyncio, json, pathlib" 2>/dev/null && echo "✅ Dépendances OK" || echo "❌ Dépendances manquantes"

# Affichage des commandes disponibles
echo ""
echo "🎯 COMMANDES DISPONIBLES"
echo "========================"
echo ""
echo "1. 🔍 RÉCUPÉRATION AUTOMATIQUE"
echo "   cd /app/backend/scripts"
echo "   python series_automation_pipeline.py --quick --limit=10"
echo "   python series_automation_pipeline.py --full --limit=50"
echo ""
echo "2. 👥 RÉCUPÉRATION PAR AUTEURS"
echo "   python series_automation_pipeline.py --mode=authors --limit=30"
echo ""
echo "3. 🏷️ RÉCUPÉRATION PAR CATÉGORIES"
echo "   python series_automation_pipeline.py --mode=categories --limit=40"
echo ""
echo "4. 🧪 VALIDATION SYSTÈME"
echo "   python update_series_detection.py --validate"
echo ""
echo "5. 💾 BACKUP MANUEL"
echo "   python update_series_detection.py --backup-only"
echo ""
echo "6. 🎯 DÉMONSTRATION COMPLÈTE"
echo "   python demo_automation.py"
echo ""
echo "📊 STATISTIQUES ET SURVEILLANCE"
echo "==============================="
echo ""
echo "• Voir séries actuelles:"
echo "  jq '. | length' /app/backend/data/extended_series_database.json"
echo ""
echo "• Voir logs récents:"
echo "  tail -20 /app/logs/open_library_auto.log"
echo ""
echo "• Voir rapports:"
echo "  ls -la /app/reports/"
echo ""
echo "• Voir backups:"
echo "  ls -la /app/backups/series_detection/"
echo ""
echo "🚀 PRÊT À UTILISER !"
echo "Commencez par: python demo_automation.py"