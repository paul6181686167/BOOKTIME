"""Fonctions pures du module amis (sans accès base de données, donc testables)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException

MAX_MESSAGE_CHARS = 1000
MAX_SEARCH_RESULTS = 15

_BOOK_TEXT_LIMITS = {
    "title": 200,
    "author": 200,
    "category": 30,
    "ol_key": 60,
    "isbn": 20,
    "note": 300,
}


def pair_key(user_a: str, user_b: str) -> str:
    """Clé de conversation identique dans les deux sens."""
    first, second = sorted([str(user_a), str(user_b)])
    return f"{first}|{second}"


def iso(value: Any) -> Optional[str]:
    """Date ISO 8601 en UTC (suffixe Z), ou None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        text = value.isoformat()
        return text if text.endswith("Z") or "+" in text[10:] else text + "Z"
    return str(value)


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Lit une date ISO renvoyée par `iso` (naïve, en UTC)."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def display_label(doc: Optional[dict]) -> str:
    """Nom affiché : nom choisi, sinon partie locale de l'email."""
    doc = doc or {}
    name = str(doc.get("display_name") or "").strip()
    if name:
        return name
    email = str(doc.get("email") or "")
    return email.split("@")[0] if email else "Lecteur"


def clean_book_ref(book: Any) -> Optional[Dict[str, str]]:
    """Valide un livre recommandé dans un message. Retourne None si aucun livre."""
    if not book:
        return None
    if not isinstance(book, dict):
        raise HTTPException(status_code=400, detail="Livre recommandé invalide.")
    out: Dict[str, str] = {}
    for field, limit in _BOOK_TEXT_LIMITS.items():
        value = " ".join(str(book.get(field) or "").split())
        out[field] = value[:limit]
    if not out["title"]:
        raise HTTPException(status_code=400, detail="Le livre recommandé doit avoir un titre.")
    cover = str(book.get("cover_url") or "").strip()
    out["cover_url"] = cover[:500] if re.match(r"^https?://", cover, re.I) else ""
    return out


def clean_message(text: Any, book: Any) -> Dict[str, Any]:
    """Valide le contenu d'un message : texte et/ou livre recommandé."""
    clean_text = str(text or "").replace("\r\n", "\n").strip()
    if len(clean_text) > MAX_MESSAGE_CHARS:
        raise HTTPException(
            status_code=400,
            detail=f"Message trop long ({MAX_MESSAGE_CHARS} caractères maximum).",
        )
    book_ref = clean_book_ref(book)
    if not clean_text and not book_ref:
        raise HTTPException(status_code=400, detail="Message vide.")
    return {"text": clean_text, "book": book_ref}


def search_filter(query: str, exclude_id: str) -> Optional[Dict[str, Any]]:
    """Filtre Mongo de recherche d'un lecteur.

    Une adresse email exacte retrouve le compte ; sinon on cherche dans le nom affiché.
    Les emails ne sont jamais cherchés par fragment pour ne pas exposer les comptes.
    """
    q = (query or "").strip()
    # Les lecteurs qui ont désactivé « apparaître dans la recherche » restent introuvables
    # Un compte banni n'apparaît plus non plus.
    visible = {"settings.discoverable": {"$ne": False}, "banned": {"$ne": True}}
    if "@" in q:
        return {"email": q.lower(), "id": {"$ne": exclude_id}, **visible}
    if len(q) < 2:
        return None
    return {
        "display_name": {"$regex": re.escape(q), "$options": "i"},
        "id": {"$ne": exclude_id},
        **visible,
    }
