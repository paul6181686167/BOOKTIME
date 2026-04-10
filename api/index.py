"""
BOOKTIME API COMPLÈTE POUR VERCEL SERVERLESS
Point d'entrée principal: importe et expose l'API complète
"""

# Import de l'API complète depuis main.py
from .main import app

# Export pour Vercel
__all__ = ["app"]