"""
Catalogue global de livres — endpoint de découverte.
Sert les livres depuis MongoDB (books_catalog) ou depuis le fichier JSON local
si MongoDB est vide ou inaccessible.
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict
import re
import json
from pathlib import Path
from functools import lru_cache

from ..database.connection import client
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

_DATA_DIR         = Path(__file__).resolve().parent.parent.parent / "data"
_JSON_CACHE_PATH  = _DATA_DIR / "catalog_cache.json"
_MANGA_BD_PATH    = _DATA_DIR / "manga_bd_cache.json"


@lru_cache(maxsize=1)
def _load_main_cache() -> List[Dict]:
    """Charge le catalogue principal (romans essentiellement)."""
    if not _JSON_CACHE_PATH.exists():
        return []
    try:
        with open(_JSON_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


@lru_cache(maxsize=1)
def _load_manga_bd_cache() -> List[Dict]:
    """Charge le catalogue manga/BD secondaire (Jikan + Google Books)."""
    if not _MANGA_BD_PATH.exists():
        return []
    try:
        with open(_MANGA_BD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _load_json_cache() -> List[Dict]:
    """Retourne la fusion des deux caches (mis en mémoire individuellement)."""
    return _load_main_cache() + _load_manga_bd_cache()


def _get_catalog():
    """Retourne la collection books_catalog (lecture seule)."""
    return client.booktime.books_catalog


def _catalog_has_data() -> bool:
    """Vérifie si la collection MongoDB est peuplée."""
    try:
        return client.booktime.books_catalog.count_documents({}) > 0
    except Exception:
        return False


# ─── Routes ───────────────────────────────────────────────────────────────────

def _filter_json(books: List[Dict], category: Optional[str]) -> List[Dict]:
    """Filtre une liste JSON par catégorie."""
    if not category or category == "all":
        return books
    if category == "graphic_novel":
        return [b for b in books if b.get("category") in ("manga", "bd")]
    return [b for b in books if b.get("category") == category]


@router.get("/popular")
async def get_popular_books(
    category: Optional[str] = None,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Retourne des livres populaires (MongoDB ou JSON local en fallback)."""

    if _catalog_has_data():
        # ── MongoDB ───────────────────────────────────────────────────────────
        catalog = _get_catalog()
        query: dict = {}
        if category and category != "all":
            query["category"] = {"$in": ["manga", "bd"]} if category == "graphic_novel" else category
        try:
            docs = list(catalog.find(query, {"_id": 0}).sort("popularity_score", -1).skip(offset).limit(limit))
            total = catalog.count_documents(query)
            return {"books": docs, "total": total, "offset": offset, "limit": limit}
        except Exception:
            pass

    # ── Fallback JSON local ───────────────────────────────────────────────────
    all_books = _load_json_cache()
    filtered = _filter_json(all_books, category)
    filtered.sort(key=lambda b: b.get("popularity_score", 0), reverse=True)
    page = filtered[offset: offset + limit]
    return {"books": page, "total": len(filtered), "offset": offset, "limit": limit}


@router.get("/search")
async def search_catalog(
    q: str = Query(..., min_length=2),
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Recherche dans le catalogue (MongoDB ou JSON local)."""

    if _catalog_has_data():
        catalog = _get_catalog()
        query: dict = {}
        if category and category != "all":
            query["category"] = {"$in": ["manga", "bd"]} if category == "graphic_novel" else category
        # Full-text
        try:
            text_query = {**query, "$text": {"$search": q}}
            docs = list(catalog.find(text_query, {"_id": 0, "score": {"$meta": "textScore"}}).sort([("score", {"$meta": "textScore"})]).limit(limit))
            if docs:
                return {"books": docs, "source": "full_text"}
        except Exception:
            pass
        # Regex
        pattern = re.compile(re.escape(q), re.IGNORECASE)
        try:
            docs = list(catalog.find({**query, "$or": [{"title": pattern}, {"author": pattern}]}, {"_id": 0}).sort("popularity_score", -1).limit(limit))
            return {"books": docs, "source": "regex"}
        except Exception:
            pass

    # Fallback JSON
    q_lower = q.lower()
    all_books = _load_json_cache()
    filtered = _filter_json(all_books, category)
    matched = [b for b in filtered if q_lower in b.get("title", "").lower() or q_lower in b.get("author", "").lower()]
    matched.sort(key=lambda b: b.get("popularity_score", 0), reverse=True)
    return {"books": matched[:limit], "source": "json_cache"}


@router.get("/stats")
async def get_catalog_stats(current_user: dict = Depends(get_current_user)):
    """Statistiques du catalogue."""
    if _catalog_has_data():
        try:
            catalog = _get_catalog()
            total = catalog.count_documents({})
            return {
                "total": total,
                "roman": catalog.count_documents({"category": "roman"}),
                "manga": catalog.count_documents({"category": "manga"}),
                "bd":    catalog.count_documents({"category": "bd"}),
                "ready": total > 0,
                "source": "mongodb",
            }
        except Exception:
            pass
    # Fallback JSON (fusion des deux caches)
    main_books = _load_main_cache()
    mb_books   = _load_manga_bd_cache()
    books = main_books + mb_books
    from collections import Counter
    cats = Counter(b.get("category", "roman") for b in books)
    return {
        "total": len(books),
        "roman": cats.get("roman", 0),
        "manga": cats.get("manga", 0),
        "bd":    cats.get("bd", 0),
        "ready": len(books) > 0,
        "source": "json_cache",
        "sources_detail": {
            "catalog_cache": len(main_books),
            "manga_bd_cache": len(mb_books),
        },
    }
