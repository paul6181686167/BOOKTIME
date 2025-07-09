# Auth Dependencies
"""
Réexportation des fonctions d'authentification pour compatibilité
avec la structure modulaire du projet.
"""

from ..security.jwt import get_current_user

# Réexportation pour compatibilité avec les imports existants
__all__ = ["get_current_user"]