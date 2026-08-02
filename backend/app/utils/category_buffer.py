"""
Mémoire tampon des catégories vérifiées (titre+auteur → roman|bd|manga).

- RAM (session serveur) pour accès rapide
- Persistance MongoDB `category_buffer` quand disponible
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from .category_detect import coerce_category, normalize_category_key

logger = logging.getLogger("booktime.category_buffer")

# Mémoire tampon process
_BUFFER: dict[str, dict[str, Any]] = {}


def _collection():
    try:
        from ..db_config import database

        if database.is_mock_mode():
            return None
        db = database.db
        if db is None:
            return None
        return db["category_buffer"]
    except Exception:
        return None


def get_cached_category(title: str, author: str = "") -> Optional[str]:
    key = normalize_category_key(title, author)
    if not key or key == "|":
        return None
    hit = _BUFFER.get(key)
    if hit and hit.get("category") in ("roman", "bd", "manga"):
        return hit["category"]
    col = _collection()
    if col is None:
        return None
    try:
        doc = col.find_one({"key": key}, {"category": 1})
        if doc and doc.get("category") in ("roman", "bd", "manga"):
            _BUFFER[key] = {
                "category": doc["category"],
                "source": doc.get("source", "mongo"),
                "updated_at": doc.get("updated_at"),
            }
            return doc["category"]
    except Exception as exc:
        logger.debug("Lecture tampon catégorie échouée: %s", exc)
    return None


def set_cached_category(
    title: str,
    author: str = "",
    *,
    category: str,
    source: str = "heuristic",
    meta: Optional[dict] = None,
) -> str:
    cat = coerce_category(category)
    key = normalize_category_key(title, author)
    if not key or key == "|":
        return cat
    now = datetime.now(timezone.utc)
    entry = {
        "key": key,
        "title": (title or "").strip(),
        "author": (author or "").strip(),
        "category": cat,
        "source": source,
        "updated_at": now,
        "meta": meta or {},
    }
    _BUFFER[key] = entry
    col = _collection()
    if col is not None:
        try:
            col.update_one({"key": key}, {"$set": entry}, upsert=True)
        except Exception as exc:
            logger.debug("Écriture tampon catégorie échouée: %s", exc)
    return cat


def buffer_stats() -> dict[str, Any]:
    return {"memory_entries": len(_BUFFER)}


def clear_memory_buffer() -> None:
    _BUFFER.clear()
