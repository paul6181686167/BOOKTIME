from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Request, Response
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets
import re
import base64
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import bcrypt
from ..models.user import UserAuth, RegisterRequest
from ..security.cookies import clear_auth_cookie, set_auth_cookie
from ..database.connection import users_collection, db
from ..admin.helpers import is_admin
from ..friends.identity import clean_username
from ..security.jwt import (
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REMEMBER_ME_EXPIRE_MINUTES,
    SESSION_EXPIRE_MINUTES,
)
from ..security.rate_limit import RateLimiter, client_ip, ip_rate_limit, rate_limiting_enabled
from ..utils.timeutils import utcnow
import logging

logger = logging.getLogger(__name__)


def _token_ttl_minutes(remember_me: bool = True) -> int:
    """Durée de session : longue par défaut (rester connecté)."""
    if remember_me:
        return REMEMBER_ME_EXPIRE_MINUTES or ACCESS_TOKEN_EXPIRE_MINUTES
    return SESSION_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=254)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., max_length=200)
    new_password: str = Field(..., max_length=256)


def _frontend_base_url() -> str:
    return (
        os.environ.get("FRONTEND_URL")
        or os.environ.get("PUBLIC_FRONTEND_URL")
        or "https://booktime-sg59.vercel.app"
    ).rstrip("/")


def _smtp_configured() -> bool:
    return bool(
        os.environ.get("SMTP_USER", "").strip()
        and os.environ.get("SMTP_PASSWORD", "").strip()
    )


def _resend_configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY", "").strip())


def _email_configured() -> bool:
    return _resend_configured() or _smtp_configured()


def _reset_email_html(reset_url: str) -> str:
    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
      <h2 style="color:#166534">Réinitialisation de mot de passe</h2>
      <p>Bonjour,</p>
      <p>Vous avez demandé à réinitialiser votre mot de passe Booktime.</p>
      <p>Cliquez sur le bouton ci-dessous (valable <strong>1 heure</strong>) :</p>
      <a href="{reset_url}" style="display:inline-block;padding:12px 24px;background:#16a34a;color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;margin:16px 0">
        Réinitialiser mon mot de passe
      </a>
      <p style="color:#666;font-size:13px">Si vous n'avez pas fait cette demande, ignorez cet email.</p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="color:#999;font-size:12px">L'équipe Booktime</p>
    </body></html>
    """


def _send_via_resend(to_email: str, reset_url: str) -> None:
    """Envoi via l'API Resend (https://resend.com)."""
    import requests

    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    from_raw = (
        os.environ.get("FROM_EMAIL")
        or os.environ.get("RESEND_FROM")
        or "Booktime <onboarding@resend.dev>"
    ).strip()
    from_email = from_raw if "<" in from_raw else f"Booktime <{from_raw}>"

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_email,
            "to": [to_email],
            "subject": "Réinitialisation de votre mot de passe Booktime",
            "html": _reset_email_html(reset_url),
        },
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Resend HTTP {response.status_code}: {response.text[:300]}")


def _send_via_smtp(to_email: str, reset_url: str) -> None:
    """Envoi via SMTP (Gmail, Outlook, etc.)."""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    from_email = (os.environ.get("FROM_EMAIL") or smtp_user).strip()

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP_USER et SMTP_PASSWORD non configurés")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Réinitialisation de votre mot de passe Booktime"
    msg["From"] = f"Booktime <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(_reset_email_html(reset_url), "html"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())


def _send_reset_email(to_email: str, reset_token: str, frontend_url: str):
    """Envoie l'email de réinitialisation (Resend prioritaire, sinon SMTP)."""
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    if _resend_configured():
        _send_via_resend(to_email, reset_url)
        return
    if _smtp_configured():
        _send_via_smtp(to_email, reset_url)
        return
    raise ValueError(
        "Aucun service e-mail configuré (RESEND_API_KEY ou SMTP_USER/SMTP_PASSWORD)"
    )


MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # limite de bcrypt : au-delà, la bibliothèque lève une erreur


def _password_problem(password: str) -> Optional[str]:
    """Message d'erreur si le mot de passe ne respecte pas les règles, sinon None."""
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères."
    if len((password or "").encode("utf-8")) > MAX_PASSWORD_BYTES:
        return "Le mot de passe est trop long (72 octets maximum)."
    return None


def _require_valid_password(password: str) -> None:
    problem = _password_problem(password)
    if problem:
        raise HTTPException(status_code=400, detail=problem)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    data = (plain or "").encode("utf-8")
    if len(data) > MAX_PASSWORD_BYTES:
        return False  # bcrypt 5 lève une erreur au-delà de 72 octets : ce ne peut pas être le bon mot de passe
    return bcrypt.checkpw(data, hashed.encode("utf-8"))


# Hash factice : on fait toujours un calcul bcrypt, même si le compte n'existe pas, pour que le
# temps de réponse ne révèle pas quelles adresses sont inscrites.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt()).decode("utf-8")


def _hash_reset_token(token: str) -> str:
    """Seule l'empreinte du jeton est stockée : une fuite de la base ne donne pas de liens valides."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --- limitation de débit -----------------------------------------------------
_login_ip_limit = ip_rate_limit("login", 40, 900)
_register_ip_limit = ip_rate_limit("register", 10, 3600, "Trop d'inscriptions depuis cette connexion. Réessaie plus tard.")
_forgot_ip_limit = ip_rate_limit("forgot", 8, 3600, "Trop de demandes. Réessaie plus tard.")
_reset_ip_limit = ip_rate_limit("reset", 20, 3600)
# Échecs de connexion par adresse e-mail : bloque le brute-force d'un compte précis
_login_failures = RateLimiter(8, 900, "Trop d'échecs de connexion. Réessaie dans quelques minutes.")
_forgot_by_email = RateLimiter(3, 3600)
# Échecs de vérification du mot de passe actuel (changement / suppression) par utilisateur
_password_failures = RateLimiter(6, 900, "Trop de tentatives. Réessaie dans quelques minutes.")


@router.post("/register", dependencies=[Depends(_register_ip_limit)])
def register(user_data: RegisterRequest, response: Response):
    """Enregistrer un nouvel utilisateur (email + mot de passe + acceptation des CGU)"""
    if not user_data.accept_terms:
        raise HTTPException(
            status_code=400,
            detail="Tu dois accepter les conditions générales d'utilisation pour créer un compte.",
        )
    _require_valid_password(user_data.password)
    email_lower = user_data.email.lower().strip()
    existing_user = users_collection.find_one({"email": email_lower})

    if existing_user:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email")

    user_id = str(uuid.uuid4())
    password_hash = _hash_password(user_data.password)
    user = {
        "id": user_id,
        "email": email_lower,
        "password_hash": password_hash,
        "created_at": utcnow(),
        "terms_accepted_at": utcnow(),
        "terms_version": (user_data.terms_version or "").strip() or None,
    }

    users_collection.insert_one(user)

    access_token_expires = timedelta(minutes=_token_ttl_minutes(True))
    access_token = create_access_token(data={"sub": user_id}, expires_delta=access_token_expires)
    set_auth_cookie(response, access_token, int(access_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email_lower},
    }


@router.post("/login", dependencies=[Depends(_login_ip_limit)])
def login(user_data: UserAuth, response: Response):
    """Connexion (email + mot de passe)"""
    email_lower = user_data.email.lower().strip()
    limits_on = rate_limiting_enabled()
    if limits_on:
        _login_failures.raise_if_blocked(email_lower)
    user = users_collection.find_one({"email": email_lower}, {"_id": 0})

    stored_hash = (user or {}).get("password_hash", "")
    password_ok = _verify_password(user_data.password, stored_hash or _DUMMY_HASH) and bool(user and stored_hash)
    if not password_ok:
        if limits_on:
            _login_failures.hit(email_lower)
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")

    if user.get("banned"):
        raise HTTPException(status_code=403, detail="Ce compte a été suspendu.")

    if limits_on:
        _login_failures.reset(email_lower)

    access_token_expires = timedelta(
        minutes=_token_ttl_minutes(bool(user_data.remember_me))
    )
    access_token = create_access_token(data={"sub": user["id"]}, expires_delta=access_token_expires)
    set_auth_cookie(response, access_token, int(access_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], **public_profile(user)},
    }

@router.post("/logout")
def logout(response: Response):
    """Déconnexion : supprime le cookie de session httpOnly (le jeton localStorage est effacé côté appli)."""
    clear_auth_cookie(response)
    return {"success": True}


def _send_reset_email_safely(to_email: str, reset_token: str, frontend_url: str) -> None:
    """Envoi en tâche de fond : un échec est journalisé mais n'est jamais montré au client
    (réponse et délai identiques que le compte existe ou non)."""
    try:
        _send_reset_email(to_email, reset_token, frontend_url)
    except Exception as e:
        logger.error("[EMAIL] Erreur envoi email reset: %s", e)


_FORGOT_RESPONSE = {
    "message": "Si cet email existe, un lien de réinitialisation a été envoyé.",
    "delivery": "email",
}


@router.post("/forgot-password", dependencies=[Depends(_forgot_ip_limit)])
def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Envoie un e-mail de réinitialisation (Resend ou SMTP requis).

    La réponse est identique que le compte existe ou non (pas d'énumération d'adresses)."""
    email_lower = data.email.lower().strip()

    # Configuration serveur : même réponse pour tout le monde, donc sans fuite sur les comptes
    if not _email_configured():
        raise HTTPException(
            status_code=503,
            detail="Envoi d'e-mail indisponible pour le moment. Réessaie plus tard.",
        )
    if rate_limiting_enabled():
        if _forgot_by_email.blocked(email_lower):
            return dict(_FORGOT_RESPONSE)  # silencieux : ne pas révéler le blocage
        _forgot_by_email.hit(email_lower)

    user = users_collection.find_one({"email": email_lower}, {"_id": 0})
    if not user:
        return dict(_FORGOT_RESPONSE)

    reset_token = secrets.token_urlsafe(32)
    expires_at = utcnow() + timedelta(hours=1)

    users_collection.update_one(
        {"email": email_lower},
        {"$set": {"reset_token": _hash_reset_token(reset_token), "reset_token_expires": expires_at}}
    )

    background_tasks.add_task(_send_reset_email_safely, email_lower, reset_token, _frontend_base_url())
    return dict(_FORGOT_RESPONSE)


@router.post("/reset-password", dependencies=[Depends(_reset_ip_limit)])
def reset_password(data: ResetPasswordRequest):
    """Réinitialiser le mot de passe avec le token reçu par email."""
    _require_valid_password(data.new_password)

    token_hash = _hash_reset_token(data.token)
    user = users_collection.find_one({"reset_token": token_hash}, {"_id": 0})

    if not user:
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré.")

    expires_at = user.get("reset_token_expires")
    if expires_at is not None and getattr(expires_at, "tzinfo", None) is not None:
        expires_at = expires_at.replace(tzinfo=None)
    if not expires_at or utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Ce lien a expiré. Faites une nouvelle demande.")

    new_hash = _hash_password(data.new_password)
    users_collection.update_one(
        {"reset_token": token_hash},
        {
            # password_changed_at révoque toutes les sessions ouvertes avant la réinitialisation
            "$set": {"password_hash": new_hash, "password_changed_at": utcnow()},
            "$unset": {"reset_token": "", "reset_token_expires": ""},
        },
    )

    return {"message": "Mot de passe réinitialisé avec succès."}


PROFILE_FIELDS = ("display_name", "bio", "avatar_url", "username")
MAX_DISPLAY_NAME = 40
MAX_BIO = 300
# Photo redimensionnée côté application (~256 px) : quelques dizaines de Ko en base64.
MAX_AVATAR_CHARS = 150_000
_AVATAR_RE = re.compile(r"^data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/]+={0,2})$")


def public_profile(doc: dict) -> dict:
    """Champs de profil exposés au client (valeurs vides plutôt qu'absentes)."""
    doc = doc or {}
    return {
        "display_name": doc.get("display_name") or "",
        "bio": doc.get("bio") or "",
        "avatar_url": doc.get("avatar_url") or "",
        "username": doc.get("username") or "",
    }


def clean_profile_update(data: dict) -> dict:
    """Valide et nettoie les champs de profil reçus. Lève HTTPException 400 si invalide."""
    out = {}
    if "username" in data:
        out["username"] = clean_username(data["username"])
    if "display_name" in data:
        name = " ".join(str(data["display_name"] or "").split())
        if len(name) > MAX_DISPLAY_NAME:
            raise HTTPException(
                status_code=400, detail=f"Le nom ne peut pas dépasser {MAX_DISPLAY_NAME} caractères."
            )
        out["display_name"] = name
    if "bio" in data:
        bio = str(data["bio"] or "").replace("\r\n", "\n").strip()
        if len(bio) > MAX_BIO:
            raise HTTPException(
                status_code=400, detail=f"La biographie ne peut pas dépasser {MAX_BIO} caractères."
            )
        out["bio"] = bio
    if "avatar_url" in data:
        avatar = str(data["avatar_url"] or "").strip()
        if avatar:
            if len(avatar) > MAX_AVATAR_CHARS:
                raise HTTPException(status_code=400, detail="Photo trop volumineuse.")
            match = _AVATAR_RE.match(avatar)
            if not match:
                raise HTTPException(
                    status_code=400, detail="Format de photo non pris en charge (JPEG, PNG ou WebP)."
                )
            try:
                base64.b64decode(match.group(2), validate=True)
            except Exception:
                raise HTTPException(status_code=400, detail="Photo illisible.")
        out["avatar_url"] = avatar
    return out


SETTINGS_DEFAULTS = {
    "discoverable": True,  # apparaître dans la recherche de lecteurs
    "share_favorites": True,  # livres préférés visibles par les amis
    "share_reviews": True,  # notes et avis visibles par les amis
    "share_reading": True,  # lectures en cours visibles par les amis
}

def public_settings(doc: Optional[dict]) -> dict:
    """Réglages de l'utilisateur, complétés par les valeurs par défaut."""
    stored = (doc or {}).get("settings") or {}
    return {key: bool(stored.get(key, default)) for key, default in SETTINGS_DEFAULTS.items()}


def clean_settings_update(data: dict) -> dict:
    """Ne garde que les réglages connus, qui doivent être des booléens."""
    out = {}
    for key, value in (data or {}).items():
        if key not in SETTINGS_DEFAULTS:
            raise HTTPException(status_code=400, detail=f"Réglage inconnu : {key}")
        if not isinstance(value, bool):
            raise HTTPException(status_code=400, detail=f"Valeur invalide pour {key}.")
        out[key] = value
    return out


class SettingsUpdateRequest(BaseModel):
    discoverable: Optional[bool] = None
    share_favorites: Optional[bool] = None
    share_reviews: Optional[bool] = None
    share_reading: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., max_length=256)
    new_password: str = Field(..., max_length=256)


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    # Chaîne vide = retirer la photo
    avatar_url: Optional[str] = None
    # Pseudo unique, sans « @ » ; chaîne vide = retirer le pseudo
    username: Optional[str] = None


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur actuel (profil et photo inclus)."""
    stored = users_collection.find_one(
        {"id": current_user.get("id")}, {"_id": 0, "password_hash": 0}
    )
    return {
        **current_user,
        **public_profile(stored or current_user),
        "settings": public_settings(stored or current_user),
        # Affiche le lien « Administration » dans les paramètres (le contrôle réel est côté serveur)
        "is_admin": is_admin(stored or current_user),
    }


@router.put("/me/settings")
def update_my_settings(
    payload: SettingsUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Met à jour les réglages de confidentialité."""
    updates = clean_settings_update(payload.model_dump(exclude_unset=True, exclude_none=True))
    if not updates:
        raise HTTPException(status_code=400, detail="Aucun réglage à mettre à jour.")
    users_collection.update_one(
        {"id": current_user.get("id")},
        {"$set": {f"settings.{key}": value for key, value in updates.items()}},
    )
    stored = users_collection.find_one({"id": current_user.get("id")}, {"_id": 0}) or {}
    return {"success": True, "settings": public_settings(stored)}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    """Change le mot de passe après vérification de l'ancien.

    Les sessions ouvertes avant le changement (autres appareils, jeton volé) sont révoquées ;
    un nouveau jeton est renvoyé pour que l'appareil courant reste connecté."""
    user_id = current_user.get("id")
    limits_on = rate_limiting_enabled()
    if limits_on:
        _password_failures.raise_if_blocked(f"change:{user_id}")
    stored = users_collection.find_one({"id": user_id})
    if not stored or not _verify_password(payload.current_password, stored.get("password_hash", "")):
        if limits_on:
            _password_failures.hit(f"change:{user_id}")
        raise HTTPException(status_code=401, detail="Mot de passe actuel incorrect.")
    problem = _password_problem(payload.new_password)
    if problem:
        raise HTTPException(status_code=400, detail=problem)
    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=400, detail="Le nouveau mot de passe doit être différent de l'ancien."
        )
    users_collection.update_one(
        {"id": user_id},
        {"$set": {"password_hash": _hash_password(payload.new_password), "password_changed_at": utcnow()}},
    )
    if limits_on:
        _password_failures.reset(f"change:{user_id}")

    ttl = timedelta(minutes=_token_ttl_minutes(True))
    access_token = create_access_token(data={"sub": user_id}, expires_delta=ttl)
    set_auth_cookie(response, access_token, int(ttl.total_seconds()))
    return {"success": True, "access_token": access_token, "token_type": "bearer"}


@router.put("/me/profile")
def update_my_profile(
    payload: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Met à jour le nom affiché, la biographie et la photo de profil."""
    sent = payload.model_dump(exclude_unset=True)
    updates = clean_profile_update(sent)
    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour.")

    me = current_user.get("id")
    operation: dict = {}
    if "username" in updates:
        username = updates.pop("username")
        if username:
            taken = users_collection.find_one({"username": username, "id": {"$ne": me}}, {"id": 1})
            if taken:
                raise HTTPException(status_code=409, detail="Ce pseudo est déjà pris.")
            updates["username"] = username
        else:
            operation["$unset"] = {"username": ""}
    if updates:
        operation["$set"] = updates
    users_collection.update_one({"id": me}, operation)
    try:
        # Garde-fou contre deux inscriptions simultanées du même pseudo (sans effet s'il existe déjà)
        users_collection.create_index("username", unique=True, sparse=True)
    except Exception:
        pass
    stored = users_collection.find_one({"id": me}, {"_id": 0}) or {}
    return {"success": True, "profile": public_profile(stored)}


# Collections portant des documents rattachés à un utilisateur via user_id.
# Toute nouvelle collection utilisateur doit être ajoutée ici, sans quoi des
# données orphelines survivraient à la suppression du compte.
_USER_DATA_COLLECTIONS = (
    "books",
    "series_library",
    "notifications",
    "upcoming_cache",
    "user_profiles",
    "follows",
    "social_activities",
    "social_comments",
    "social_likes",
    "book_lists",
    "book_recommendations",
    "social_notifications",
)


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., max_length=256)


@router.delete("/me")
def delete_account(
    data: DeleteAccountRequest,
    current_user: dict = Depends(get_current_user),
):
    """Supprimer définitivement le compte et toutes les données associées.

    Exigé par Google Play pour toute application permettant la création d'un
    compte. Le mot de passe est redemandé car l'action est irréversible.
    """
    user_id = current_user.get("id")
    stored = users_collection.find_one({"id": user_id})
    if not stored:
        raise HTTPException(status_code=404, detail="Compte introuvable.")

    limits_on = rate_limiting_enabled()
    if limits_on:
        _password_failures.raise_if_blocked(f"delete:{user_id}")
    if not _verify_password(data.password, stored.get("password_hash", "")):
        if limits_on:
            _password_failures.hit(f"delete:{user_id}")
        raise HTTPException(status_code=401, detail="Mot de passe incorrect.")

    deleted = {}
    for name in _USER_DATA_COLLECTIONS:
        try:
            result = db[name].delete_many({"user_id": user_id})
            if result.deleted_count:
                deleted[name] = result.deleted_count
        except Exception:
            # Une collection absente ne doit pas empêcher la suppression du compte.
            continue

    # Le follow social référence l'utilisateur par les deux extrémités.
    try:
        db["follows"].delete_many({"following_id": user_id})
    except Exception:
        pass

    # Amis : demandes et messages référencent l'utilisateur par l'une ou l'autre extrémité.
    for name, fields in (
        ("friendships", ("requester_id", "addressee_id")),
        ("friend_messages", ("sender_id", "recipient_id")),
    ):
        try:
            db[name].delete_many({"$or": [{f: user_id} for f in fields]})
        except Exception:
            continue

    users_collection.delete_one({"id": user_id})

    return {"message": "Compte supprimé définitivement.", "deleted": deleted}