# ==========================================
# BOOKTIME API - ARCHITECTURE HYBRIDE
# Phase 1.2: Transition vers architecture modulaire
# ==========================================

# Import de l'application modulaire
from app.main import app

# Import des composants existants pour préserver les 89 endpoints
from server_backup import *

# L'application est maintenant structurée en modules mais conserve
# tous les endpoints existants pour maintenir la compatibilité.
# 
# Architecture nouvelle:
# - /app/config.py : Configuration centralisée
# - /app/database.py : Connexions MongoDB
# - /app/models/ : Modèles Pydantic
# - /app/services/ : Logique métier
# - /app/routers/ : Endpoints organisés
# - /app/utils/ : Utilitaires (sécurité, helpers)
#
# Endpoints préservés: 89 endpoints complets

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)