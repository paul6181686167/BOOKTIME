"""Origines autorisées à appeler l'API (CORS), source unique pour le middleware et les erreurs.

Avant : toute adresse `*.vercel.app` était acceptée, avec envoi des identifiants. N'importe qui
peut publier un site sur vercel.app : il aurait pu appeler l'API au nom d'un utilisateur
connecté (surtout avec le cookie de session). On n'accepte plus que :
  - une liste explicite d'origines (production, développement, application Android) ;
  - les déploiements de prévisualisation de TON compte Vercel (suffixe d'équipe
    `-paul6181686167s-projects.vercel.app`, impossible à usurper par un autre compte) ;
  - les origines ajoutées par les variables d'environnement CORS_ORIGINS (liste) et
    CORS_ORIGIN_REGEX (expression régulière complète, optionnelle).
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

STATIC_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Accès LAN (autre PC sur le même Wi-Fi)
    "http://192.168.1.167:3000",
    # Application Android (Capacitor) : la WebView sert le bundle depuis https://localhost
    "https://localhost",
    "http://localhost",
    "capacitor://localhost",
    # Déploiements Vercel
    "https://booktime-fawn.vercel.app",
    "https://booktime-sg59.vercel.app",
    "https://booktime.vercel.app",
    "https://1571571761761571.vercel.app",
    "https://changelog-reader-9.preview.emergentagent.com",
]

# Prévisualisations / alias de branche du compte Vercel du projet (suffixe d'équipe propre)
TEAM_PREVIEW_REGEX = r"^https://[a-z0-9-]+-paul6181686167s-projects\.vercel\.app$"

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
ALLOWED_HEADERS = [
    "Authorization",
    "Content-Type",
    "Accept",
    "Accept-Language",
    "X-Requested-With",
    "Cache-Control",
]


def get_cors_origins() -> List[str]:
    origins = list(STATIC_ORIGINS)
    env_origins = os.environ.get("CORS_ORIGINS", "")
    origins.extend(o.strip() for o in env_origins.split(",") if o.strip() and o.strip() != "*")
    return list(dict.fromkeys(origins))


def get_origin_regex() -> str:
    """Expression régulière (une seule) acceptée par le middleware Starlette."""
    extra = os.environ.get("CORS_ORIGIN_REGEX", "").strip()
    if extra:
        return f"(?:{TEAM_PREVIEW_REGEX})|(?:{extra})"
    return TEAM_PREVIEW_REGEX


def is_origin_allowed(origin: Optional[str]) -> bool:
    if not origin:
        return False
    if origin in get_cors_origins():
        return True
    try:
        return re.match(get_origin_regex(), origin, re.IGNORECASE) is not None
    except re.error:
        return origin in get_cors_origins()


def cors_headers_for(origin: Optional[str]) -> Dict[str, str]:
    """En-têtes CORS pour les réponses d'erreur : vides si l'origine n'est pas autorisée."""
    if not is_origin_allowed(origin):
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }
