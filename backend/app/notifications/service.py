"""
Notifications utilisateur (collection `notifications`).

Utilisé par le job "prochaines sorties" pour signaler une sortie devenue
disponible. Canal in-app persistant ; l'e-mail est best-effort (uniquement si un
serveur SMTP est configuré via les variables d'environnement).
"""

from __future__ import annotations

import logging
import os
import smtplib
import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any, Optional

from ..database.connection import db

logger = logging.getLogger(__name__)


def _coll():
    return db.notifications


def create_notification(
    user_id: str,
    *,
    title: str,
    body: str = "",
    type: str = "upcoming_release",
    data: Optional[dict[str, Any]] = None,
    dedup_key: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Crée une notification in-app. `dedup_key` évite les doublons (une même sortie
    ne notifie qu'une fois par utilisateur).
    """
    try:
        if dedup_key:
            existing = _coll().find_one({"user_id": user_id, "dedup_key": dedup_key}, {"_id": 0, "id": 1})
            if existing:
                return None
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": type,
            "title": title,
            "body": body,
            "data": data or {},
            "dedup_key": dedup_key,
            "read": False,
            "created_at": datetime.now(timezone.utc),
        }
        _coll().insert_one(doc)
        doc.pop("_id", None)
        return doc
    except Exception as exc:  # pragma: no cover
        logger.warning("Création notification échouée : %s", exc)
        return None


def list_notifications(user_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    try:
        cursor = _coll().find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)
    except Exception as exc:  # pragma: no cover
        logger.debug("Lecture notifications échouée : %s", exc)
        return []


def unread_count(user_id: str) -> int:
    try:
        return _coll().count_documents({"user_id": user_id, "read": {"$ne": True}})
    except Exception:  # pragma: no cover
        return 0


def mark_read(user_id: str, notif_id: str) -> bool:
    try:
        res = _coll().update_one(
            {"user_id": user_id, "id": notif_id}, {"$set": {"read": True}}
        )
        return getattr(res, "modified_count", 0) > 0
    except Exception:  # pragma: no cover
        return False


def mark_all_read(user_id: str) -> int:
    """Marque toutes les notifications non lues comme lues (compatible mock)."""
    count = 0
    try:
        for n in _coll().find({"user_id": user_id, "read": {"$ne": True}}, {"_id": 0, "id": 1}):
            if mark_read(user_id, n.get("id")):
                count += 1
    except Exception:  # pragma: no cover
        pass
    return count


# ── E-mail best-effort ────────────────────────────────────────────────────────

def _smtp_config() -> Optional[dict[str, Any]]:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")).strip(),
        "use_tls": os.getenv("SMTP_TLS", "true").lower() != "false",
    }


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Envoie un e-mail si un SMTP est configuré ; sinon no-op silencieux."""
    cfg = _smtp_config()
    if not cfg or not to_email:
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = cfg["from"] or cfg["user"]
        msg["To"] = to_email
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
            if cfg["use_tls"]:
                server.starttls()
            if cfg["user"]:
                server.login(cfg["user"], cfg["password"])
            server.sendmail(msg["From"], [to_email], msg.as_string())
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("Envoi e-mail échoué : %s", exc)
        return False
