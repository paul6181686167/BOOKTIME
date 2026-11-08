"""
Catalogue global de livres — endpoint de découverte.
Sert les livres depuis MongoDB (books_catalog) ou depuis le fichier JSON local
si MongoDB est vide ou inaccessible.
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional, List, Dict
import re
import json
from pathlib import Path
from functools import lru_cache

import uuid
from pydantic import BaseModel, Field

from datetime import datetime, timezone

from ..database.connection import client, books_collection, series_library_collection
from ..library.series_library_helpers import series_library_duplicate_query
from ..models.book import BookCreate
from ..security.jwt import get_current_user
from ..utils.errors import public_error
from ..utils.timeutils import utcnow
from ..utils.validation import validate_category
from . import expanded as expanded_fiches

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

_DATA_DIR         = Path(__file__).resolve().parent.parent.parent / "data"
_JSON_CACHE_PATH  = _DATA_DIR / "catalog_cache.json"
_MANGA_BD_PATH    = _DATA_DIR / "manga_bd_cache.json"
_ONBOARDING_PATH  = _DATA_DIR / "onboarding_catalog.json"

# Œuvres d'accueil qui sont des séries (pas un livre unique à la couverture unique)
_ONBOARDING_SERIES = {
    "one piece": {
        "volumes": 112,
        "first_published": "1997",
        "publisher": "Glénat",
        "series_status": "ongoing",
    },
    "asterix": {
        "volumes": 40,
        "first_published": "1959",
        "publisher": "Albert René",
        "series_status": "ongoing",
    },
    "tintin": {
        "volumes": 24,
        "first_published": "1929",
        "publisher": "Casterman",
        "series_status": "completed",
    },
}


def _norm_onboarding_title(title: str) -> str:
    s = (title or "").strip().lower()
    for src, dst in (("é", "e"), ("è", "e"), ("ê", "e"), ("ë", "e")):
        s = s.replace(src, dst)
    return s


def _onboarding_series_meta(work: dict) -> Optional[Dict]:
    return _ONBOARDING_SERIES.get(_norm_onboarding_title(work.get("title") or ""))


def _annotate_onboarding_work(work: dict) -> dict:
    out = dict(work)
    meta = _onboarding_series_meta(work)
    if meta:
        out["kind"] = "series"
        out["volumes"] = meta["volumes"]
        out["first_published"] = meta["first_published"]
        out["publisher"] = meta["publisher"]
        out["series_status"] = meta["series_status"]
    return out


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
def get_popular_books(
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


@lru_cache(maxsize=1)
def _load_onboarding() -> List[Dict]:
    """Charge la sélection éditoriale d'oeuvres de l'écran d'accueil."""
    if not _ONBOARDING_PATH.exists():
        return []
    try:
        with open(_ONBOARDING_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("works", [])
    except Exception:
        return []


@router.get("/onboarding")
def get_onboarding_works(
    group: str = "roman",
    current_user: dict = Depends(get_current_user),
):
    """
    Oeuvres proposées à un nouvel utilisateur pour constituer sa bibliothèque
    (« coche ce que tu as déjà lu »). `group` : « roman » ou « graphic_novel ».
    """
    if group not in ("roman", "graphic_novel"):
        raise HTTPException(status_code=400, detail="Catégorie invalide")
    works = [_annotate_onboarding_work(w) for w in _load_onboarding() if w.get("group") == group]
    genres: List[str] = []
    for w in works:
        if w.get("genre") and w["genre"] not in genres:
            genres.append(w["genre"])
    return {"works": works, "genres": genres, "total": len(works)}


class OnboardingSelection(BaseModel):
    ids: List[str] = Field(default_factory=list, max_length=500)


@router.post("/onboarding")
def add_onboarding_works(
    selection: OnboardingSelection,
    current_user: dict = Depends(get_current_user),
):
    """
    Ajoute à la bibliothèque les oeuvres cochées « déjà lues » sur l'écran d'accueil.

    Seuls les identifiants du catalogue éditorial sont acceptés : titre, auteur et
    couverture viennent du serveur. Les livres sont marqués « terminé » sans date
    de fin (ils ont été lus avant l'inscription : objectifs et calendrier restent exacts).
    """
    by_id = {w["id"]: w for w in _load_onboarding() if w.get("id")}
    wanted = [by_id[i] for i in dict.fromkeys(selection.ids) if i in by_id]
    if not wanted:
        return {"added": 0, "skipped": 0}

    existing = {
        (b.get("title") or "").strip().lower()
        for b in books_collection.find({"user_id": current_user["id"]}, {"title": 1, "_id": 0})
    }
    existing_series = {
        (s.get("series_name") or s.get("name") or "").strip().lower()
        for s in series_library_collection.find(
            {"user_id": current_user["id"]}, {"series_name": 1, "name": 1, "_id": 0}
        )
    }

    added = 0
    skipped = 0
    for w in wanted:
        key = w["title"].strip().lower()
        series_meta = _onboarding_series_meta(w)
        if series_meta:
            if key in existing_series:
                skipped += 1
                continue
            n_vol = int(series_meta["volumes"])
            volumes = [
                {
                    "volume_number": i,
                    "volume_title": f"{w['title']} - Tome {i}",
                    "is_read": True,
                    "date_read": None,
                }
                for i in range(1, n_vol + 1)
            ]
            series = {
                "id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "series_name": w["title"],
                "name": w["title"],
                "authors": [w.get("author") or "Auteur inconnu"],
                "category": validate_category(w.get("category") or "roman"),
                "volumes": volumes,
                "total_volumes": n_vol,
                "cover_image_url": w.get("cover_url") or "",
                "first_published": series_meta["first_published"],
                "publisher": series_meta["publisher"],
                "series_status": series_meta.get("series_status") or "completed",
                "description_fr": "",
                "added_via": "onboarding",
                "category_verified": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            try:
                if series_library_collection.find_one(
                    series_library_duplicate_query(current_user["id"], w["title"])
                ):
                    skipped += 1
                    existing_series.add(key)
                    continue
                series_library_collection.insert_one(series)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=public_error(e, "Erreur lors de l'ajout des séries"),
                )
            existing_series.add(key)
            added += 1
            continue
        if key in existing:
            skipped += 1
            continue
        data = BookCreate(
            title=w["title"],
            author=w.get("author") or "",
            category=w.get("category") or "roman",
            status="completed",
            cover_url=w.get("cover_url") or "",
            genre=w.get("genre") or "",
            ol_key=w.get("ol_key"),
        ).model_dump()
        book = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["id"],
            **data,
            "category": validate_category(data["category"]),
            "date_added": utcnow(),
            "date_started": None,
            "date_completed": None,
            "added_via": "onboarding",
            # catégorie fixée à la main dans le catalogue éditorial : pas de reclassification automatique
            "category_verified": True,
        }
        try:
            books_collection.insert_one(book)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=public_error(e, "Erreur lors de l'ajout des livres"),
            )
        existing.add(key)
        added += 1
    return {"added": added, "skipped": skipped}


@router.get("/search")
def search_catalog(
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
def get_catalog_stats(current_user: dict = Depends(get_current_user)):
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
                "expanded_fiches": expanded_fiches.stats(),
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
        "expanded_fiches": expanded_fiches.stats(),
    }


@router.get("/expanded")
def get_expanded_fiches(current_user: dict = Depends(get_current_user)):
    """Noyau curé : 50 000 fiches tomes (overlay riche ~103 séries en plus)."""
    return expanded_fiches.catalog_payload()


@router.get("/expanded/search")
def search_expanded_fiches(
    q: str = Query(..., min_length=2, max_length=200),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Recherche dans le catalogue étendu (nom de série ou titre de tome)."""
    return {"results": expanded_fiches.search_series(q, limit=limit), "query": q}
