"""
Session par cookie httpOnly (option, désactivée par défaut).

Le jeton de connexion est aujourd'hui conservé par le navigateur dans localStorage, donc
lisible par n'importe quel script de la page (faille XSS = vol de session). Avec
`AUTH_COOKIE_ENABLED=true`, le serveur dépose en plus le jeton dans un cookie `httpOnly`
que JavaScript ne peut pas lire, et l'accepte à la place de l'en-tête `Authorization`.

Le jeton reste renvoyé dans le corps de la réponse : l'application Android et les anciennes
versions du site continuent de fonctionner à l'identique.

Protection CSRF : un cookie est envoyé automatiquement par le navigateur, y compris depuis
un site tiers. Pour les requêtes qui modifient des données, on exige donc l'en-tête
`X-Requested-With: BookTime` ; un site tiers ne peut pas l'ajouter sans passer par une
requête « preflight » que la politique CORS (origines autorisées) refuse.

Variables d'environnement :
  AUTH_COOKIE_ENABLED   "true" pour activer (défaut : false)
  AUTH_COOKIE_NAME      nom du cookie (défaut : booktime_session)
  AUTH_COOKIE_SECURE    "true" (défaut) ; "false" uniquement en développement http
  AUTH_COOKIE_SAMESITE  "none" (défaut, front et API sur des domaines différents),
                        "lax" ou "strict" si les deux partagent le même site
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import HTTPException, Request, Response, status

CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "BookTime"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def cookie_auth_enabled() -> bool:
    return os.getenv("AUTH_COOKIE_ENABLED", "false").strip().lower() == "true"


def cookie_name() -> str:
    return os.getenv("AUTH_COOKIE_NAME", "booktime_session")


def _samesite() -> str:
    value = os.getenv("AUTH_COOKIE_SAMESITE", "none").strip().lower()
    return value if value in {"none", "lax", "strict"} else "none"


def _secure() -> bool:
    # SameSite=None exige Secure : sans lui, les navigateurs rejettent le cookie.
    if _samesite() == "none":
        return True
    return os.getenv("AUTH_COOKIE_SECURE", "true").strip().lower() != "false"


def set_auth_cookie(response: Response, token: str, max_age_seconds: int) -> None:
    """Dépose le jeton dans un cookie httpOnly (sans effet si l'option est désactivée)."""
    if not cookie_auth_enabled():
        return
    response.set_cookie(
        key=cookie_name(),
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        secure=_secure(),
        samesite=_samesite(),
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Supprime le cookie (toujours exécuté : sans danger même si l'option est désactivée)."""
    response.delete_cookie(
        key=cookie_name(),
        path="/",
        secure=_secure(),
        httponly=True,
        samesite=_samesite(),
    )


def token_from_cookie(request: Optional[Request]) -> Optional[str]:
    if request is None or not cookie_auth_enabled():
        return None
    return request.cookies.get(cookie_name()) or None


def enforce_csrf(request: Request) -> None:
    """Refuse une requête modifiante authentifiée par cookie sans l'en-tête de confiance."""
    if request.method.upper() in SAFE_METHODS:
        return
    if request.headers.get(CSRF_HEADER, "") != CSRF_VALUE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="En-tête de protection CSRF manquant",
        )
