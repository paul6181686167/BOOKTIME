# Dépendances partagées pour BOOKTIME.
#
# L'authentification a une seule implémentation (security/jwt.py), réexportée ici pour
# compatibilité. Les anciens utilitaires de pagination / validation / recherche de ce fichier
# n'étaient plus utilisés par aucune route et ont été supprimés (leur recherche par regex ne
# protégeait pas les caractères spéciaux).
from .security.jwt import create_access_token, get_current_user, security  # noqa: F401

__all__ = ["create_access_token", "get_current_user", "security"]
