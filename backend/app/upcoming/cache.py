"""
Cache par utilisateur des "prochaines sorties" (collection `upcoming_cache`).

Évite de retaper Wikidata / Google Books à chaque ouverture du panneau. La
fraîcheur est vérifiée en Python (pas d'index TTL Mongo) pour rester compatible
avec le mode mock. Sert aussi de mémoire au job planifié (ids déjà notifiés).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..database.connection import db

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = int(os.getenv("UPCOMING_CACHE_TTL_HOURS", "6"))
# Incrémenter après tout changement de règles de filtrage pour invalider
# les payloads obsolètes encore dans la TTL (sinon le panneau sert l'ancienne liste).
CACHE_LOGIC_VERSION = int(os.getenv("UPCOMING_CACHE_LOGIC_VERSION", "2"))


def _coll():
    return db.upcoming_cache


def get_cached(user_id: str, *, max_age_hours: int = CACHE_TTL_HOURS) -> Optional[dict[str, Any]]:
    """Retourne le payload en cache s'il est encore frais, sinon None."""
    try:
        doc = _coll().find_one({"user_id": user_id}, {"_id": 0})
    except Exception as exc:  # pragma: no cover
        logger.debug("Lecture cache upcoming échouée : %s", exc)
        return None
    if not doc or "payload" not in doc:
        return None
    if int(doc.get("logic_version") or 0) != CACHE_LOGIC_VERSION:
        return None
    updated = doc.get("updated_at")
    if isinstance(updated, str):
        try:
            updated = datetime.fromisoformat(updated)
        except ValueError:
            updated = None
    if not isinstance(updated, datetime):
        return None
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - updated > timedelta(hours=max_age_hours):
        return None
    payload = doc["payload"]
    payload["cached"] = True
    return payload


def set_cached(
    user_id: str,
    payload: Optional[dict[str, Any]] = None,
    *,
    notified_ids: Optional[list[str]] = None,
) -> None:
    """Met à jour le cache (payload et/ou liste des ids déjà notifiés)."""
    update: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc),
        "logic_version": CACHE_LOGIC_VERSION,
    }
    if payload is not None:
        stored = {k: v for k, v in payload.items() if k != "cached"}
        update["payload"] = stored
    if notified_ids is not None:
        update["notified_ids"] = list(notified_ids)
    try:
        _coll().update_one({"user_id": user_id}, {"$set": update}, upsert=True)
    except Exception as exc:  # pragma: no cover
        logger.debug("Écriture cache upcoming échouée : %s", exc)


def get_notified_ids(user_id: str) -> set[str]:
    try:
        doc = _coll().find_one({"user_id": user_id}, {"_id": 0, "notified_ids": 1})
    except Exception:  # pragma: no cover
        return set()
    ids = (doc or {}).get("notified_ids") or []
    return set(ids) if isinstance(ids, list) else set()
