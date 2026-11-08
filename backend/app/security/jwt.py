import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REMEMBER_ME_EXPIRE_MINUTES,
    SESSION_EXPIRE_MINUTES,
)
from ..database.connection import users_collection
from ..utils.timeutils import utcnow, to_epoch
from .cookies import enforce_csrf, token_from_cookie

# Security
# auto_error=False : le jeton peut aussi venir du cookie httpOnly (voir cookies.py)
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Creer un token JWT (avec sa date d'émission, utilisée pour révoquer après un changement de mot de passe)"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return str(encoded_jwt) if isinstance(encoded_jwt, bytes) else encoded_jwt


def token_revoked(payload: dict, user: dict) -> bool:
    """Vrai si le jeton a été émis avant le dernier changement de mot de passe du compte.

    Les jetons sont sans état : sans cette vérification, un jeton volé resterait valable
    jusqu'à son expiration (60 à 90 jours) même après un changement ou une réinitialisation
    du mot de passe. Les comptes qui n'ont jamais changé de mot de passe ne sont pas concernés.
    """
    changed_at = user.get("password_changed_at")
    if not isinstance(changed_at, datetime):
        return False
    issued_at = payload.get("iat")
    if not isinstance(issued_at, (int, float)):
        return True  # ancien jeton sans date d'émission, compte dont le mot de passe a changé
    return issued_at < to_epoch(changed_at)


LAST_SEEN_INTERVAL_SECONDS = 300


def should_touch_last_seen(last_seen, now, interval=LAST_SEEN_INTERVAL_SECONDS) -> bool:
    """Vrai si la dernière activité est absente ou trop ancienne pour être réécrite."""
    if not isinstance(last_seen, datetime):
        return True
    return (now - last_seen).total_seconds() >= interval


def _touch_last_seen(user: dict) -> None:
    """Note la dernière activité (au plus une écriture toutes les 5 min par utilisateur)."""
    now = utcnow()
    if not should_touch_last_seen(user.get("last_seen"), now):
        return
    try:
        users_collection.update_one({"id": user.get("id")}, {"$set": {"last_seen": now}})
    except Exception:
        # Un échec d'écriture ne doit jamais bloquer une requête authentifiée.
        pass


def _extract_token(credentials: Optional[HTTPAuthorizationCredentials], request: Optional[Request]) -> str:
    """Jeton de l'en-tête Authorization, sinon du cookie httpOnly (si activé, avec contrôle CSRF)."""
    if credentials is not None and credentials.credentials:
        return credentials.credentials
    cookie_token = token_from_cookie(request)
    if cookie_token:
        enforce_csrf(request)
        return cookie_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None,
):
    """Obtenir l'utilisateur actuel à partir du token JWT (en-tête Bearer ou cookie httpOnly)"""
    token = _extract_token(credentials, request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # La photo de profil (data URL) n'est pas chargée à chaque requête : /api/auth/me la renvoie.
    user = users_collection.find_one(
        {"id": user_id}, {"_id": 0, "password_hash": 0, "avatar_url": 0}
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if token_revoked(payload, user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée : reconnecte-toi."
        )
    if user.get("banned"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte suspendu"
        )
    _touch_last_seen(user)
    return user
