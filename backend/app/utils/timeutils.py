"""Heure UTC sans la dépréciation de `datetime.utcnow()`.

MongoDB (pymongo sans `tz_aware`) renvoie des datetimes naïfs en UTC : on garde donc le même
format pour que les comparaisons avec les dates déjà stockées continuent de fonctionner.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Maintenant, en UTC, sans fuseau attaché (équivalent de l'ancien `datetime.utcnow()`)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_epoch(value: datetime) -> int:
    """Secondes Unix d'un datetime naïf considéré comme UTC (ou d'un datetime avec fuseau)."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp())
