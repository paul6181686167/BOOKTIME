"""Messages d'erreur renvoyés au client.

Ne jamais renvoyer `str(exc)` tel quel : il peut contenir des chemins, des requêtes, des URL
internes ou des identifiants. On journalise le détail côté serveur et on ne montre le détail
au client qu'en développement explicite (ENVIRONMENT=development).
"""
from __future__ import annotations

import logging

from ..config import is_development

logger = logging.getLogger("booktime.errors")


def public_error(exc: BaseException, message: str = "Une erreur est survenue") -> str:
    """Texte à mettre dans `detail=` d'une HTTPException : générique en production."""
    message = (message or "Une erreur est survenue").rstrip(" :")
    logger.error("%s : %s", message, exc, exc_info=exc)
    if is_development():
        return f"{message} : {exc}"
    return message
