import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from ..database.connection import users_collection

load_dotenv()

# Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
# Par défaut 60 jours (session longue). « Rester connecté » → 90 jours.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "86400"))
REMEMBER_ME_EXPIRE_MINUTES = int(os.getenv("REMEMBER_ME_EXPIRE_MINUTES", "129600"))  # 90 jours
SESSION_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", "1440"))  # 1 jour sans remember me

# Security
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Creer un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return str(encoded_jwt) if isinstance(encoded_jwt, bytes) else encoded_jwt

LAST_SEEN_INTERVAL_SECONDS = 300


def should_touch_last_seen(last_seen, now, interval=LAST_SEEN_INTERVAL_SECONDS) -> bool:
    """Vrai si la dernière activité est absente ou trop ancienne pour être réécrite."""
    if not isinstance(last_seen, datetime):
        return True
    return (now - last_seen).total_seconds() >= interval


def _touch_last_seen(user: dict) -> None:
    """Note la dernière activité (au plus une écriture toutes les 5 min par utilisateur)."""
    now = datetime.utcnow()
    if not should_touch_last_seen(user.get("last_seen"), now):
        return
    try:
        users_collection.update_one({"id": user.get("id")}, {"$set": {"last_seen": now}})
    except Exception:
        # Un échec d'écriture ne doit jamais bloquer une requête authentifiée.
        pass


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtenir l'utilisateur actuel à partir du token JWT"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
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
        if user.get("banned"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Compte suspendu"
            )
        _touch_last_seen(user)
        return user
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )