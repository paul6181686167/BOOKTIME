"""Fonctions pures du module d'administration (sans accès base de données)."""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Set

ONLINE_WINDOW_MINUTES = 15
MAX_BAN_REASON = 200


def admin_emails(raw: Optional[str] = None) -> Set[str]:
    """Emails administrateurs, lus dans la variable d'environnement ADMIN_EMAILS (séparés par des virgules)."""
    value = os.environ.get("ADMIN_EMAILS", "") if raw is None else raw
    return {part.strip().lower() for part in value.split(",") if part.strip()}


def is_admin(doc: Optional[dict], allowed: Optional[Set[str]] = None) -> bool:
    """Un utilisateur est administrateur si son email est autorisé ou si `is_admin` est vrai en base.

    Sans configuration, personne n'est administrateur.
    """
    if not doc:
        return False
    if doc.get("is_admin") is True:
        return True
    emails = admin_emails() if allowed is None else allowed
    return str(doc.get("email") or "").strip().lower() in emails


def to_naive_utc(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    return None


def bucket_by_day(dates: Iterable[Any], days: int, today: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Compte des dates par jour sur les `days` derniers jours (aujourd'hui inclus), du plus ancien au plus récent."""
    end = (today or datetime.utcnow()).date()
    counts = {end - timedelta(days=offset): 0 for offset in range(days)}
    for value in dates:
        dt = to_naive_utc(value)
        if dt and dt.date() in counts:
            counts[dt.date()] += 1
    return [{"date": day.isoformat(), "count": counts[day]} for day in sorted(counts)]


def is_online(last_seen: Any, now: Optional[datetime] = None, window: int = ONLINE_WINDOW_MINUTES) -> bool:
    """Vrai si l'activité date de moins de `window` minutes."""
    dt = to_naive_utc(last_seen)
    if not dt:
        return False
    return ((now or datetime.utcnow()) - dt) <= timedelta(minutes=window)


def clean_reason(value: Any) -> str:
    return " ".join(str(value or "").split())[:MAX_BAN_REASON]
