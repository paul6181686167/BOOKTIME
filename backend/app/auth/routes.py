from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import bcrypt
from ..models.user import UserAuth
from ..database.connection import users_collection, db
from ..security.jwt import (
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REMEMBER_ME_EXPIRE_MINUTES,
    SESSION_EXPIRE_MINUTES,
)


def _token_ttl_minutes(remember_me: bool = True) -> int:
    """Durée de session : longue par défaut (rester connecté)."""
    if remember_me:
        return REMEMBER_ME_EXPIRE_MINUTES or ACCESS_TOKEN_EXPIRE_MINUTES
    return SESSION_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


@router.post("/register")
async def register(user_data: UserAuth):
    """Enregistrer un nouvel utilisateur (email + mot de passe)"""
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
        "created_at": datetime.utcnow(),
    }

    users_collection.insert_one(user)

    access_token_expires = timedelta(minutes=_token_ttl_minutes(True))
    access_token = create_access_token(data={"sub": user_id}, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": email_lower},
    }


@router.post("/login")
async def login(user_data: UserAuth):
    """Connexion (email + mot de passe)"""
    email_lower = user_data.email.lower().strip()
    user = users_collection.find_one({"email": email_lower}, {"_id": 0})

    if not user:
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")

    if not _verify_password(user_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")

    access_token_expires = timedelta(
        minutes=_token_ttl_minutes(bool(user_data.remember_me))
    )
    access_token = create_access_token(data={"sub": user["id"]}, expires_delta=access_token_expires)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"]},
    }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Envoie un e-mail de réinitialisation (Resend ou SMTP requis)."""
    email_lower = data.email.lower().strip()
    user = users_collection.find_one({"email": email_lower}, {"_id": 0})

    # Message générique si le compte n'existe pas (pas d'énumération d'emails)
    if not user:
        return {
            "message": "Si cet email existe, un lien de réinitialisation a été envoyé.",
            "delivery": "none",
        }

    if not _email_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Envoi d'e-mail non configuré sur le serveur. "
                "Ajoute RESEND_API_KEY (recommandé) ou SMTP_USER + SMTP_PASSWORD sur Render."
            ),
        )

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    users_collection.update_one(
        {"email": email_lower},
        {"$set": {"reset_token": reset_token, "reset_token_expires": expires_at}}
    )

    frontend_url = _frontend_base_url()

    try:
        _send_reset_email(email_lower, reset_token, frontend_url)
    except Exception as e:
        print(f"[EMAIL] Erreur envoi email reset: {e}")
        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible d'envoyer l'e-mail. Vérifie RESEND_API_KEY ou "
                "SMTP_USER / SMTP_PASSWORD (mot de passe d'application Gmail) sur Render."
            ),
        )

    return {
        "message": "Si cet email existe, un lien de réinitialisation a été envoyé.",
        "delivery": "email",
    }


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Réinitialiser le mot de passe avec le token reçu par email."""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 6 caractères.")

    user = users_collection.find_one({"reset_token": data.token}, {"_id": 0})

    if not user:
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré.")

    expires_at = user.get("reset_token_expires")
    if expires_at is not None and getattr(expires_at, "tzinfo", None) is not None:
        expires_at = expires_at.replace(tzinfo=None)
    if not expires_at or datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="Ce lien a expiré. Faites une nouvelle demande.")

    new_hash = _hash_password(data.new_password)
    users_collection.update_one(
        {"reset_token": data.token},
        {"$set": {"password_hash": new_hash}, "$unset": {"reset_token": "", "reset_token_expires": ""}}
    )

    return {"message": "Mot de passe réinitialisé avec succès."}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur actuel"""
    return current_user


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
    password: str


@router.delete("/me")
async def delete_account(
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

    if not _verify_password(data.password, stored.get("password_hash", "")):
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

    users_collection.delete_one({"id": user_id})

    return {"message": "Compte supprimé définitivement.", "deleted": deleted}