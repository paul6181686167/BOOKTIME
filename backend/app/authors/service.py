"""
Fiches auteurs persistées (cache Mongo), miroir de l'enrichissement livres.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from ..database.connection import (
    authors_collection,
    books_collection,
    series_library_collection,
)

logger = logging.getLogger(__name__)

CACHE_TTL = timedelta(days=30)
MAX_ENSURE_PER_CALL = 12


def normalize_author_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def _serialize_model(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, list):
        return [_serialize_model(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize_model(v) for k, v in obj.items()}
    return obj


def get_cached_author(name: str) -> Optional[dict]:
    key = normalize_author_name(name)
    if not key:
        return None
    doc = authors_collection.find_one({"name_normalized": key}, {"_id": 0})
    return doc if isinstance(doc, dict) else None


def is_fresh(doc: Optional[dict]) -> bool:
    if not doc:
        return False
    enriched_at = doc.get("enriched_at")
    if not enriched_at:
        return False
    try:
        if isinstance(enriched_at, str):
            enriched_at = datetime.fromisoformat(enriched_at.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        return datetime.utcnow() - enriched_at < CACHE_TTL
    except Exception:
        return False


def author_fiche_ready(doc: Optional[dict]) -> bool:
    """Une fiche est « créée » si bio/photo ou œuvres sont présentes."""
    if not doc:
        return False
    if doc.get("bio") or doc.get("photo_url") or doc.get("image_url"):
        return True
    if doc.get("series") or doc.get("individual_books"):
        return True
    if doc.get("wikidata_qid") or doc.get("wikipedia_url"):
        return True
    return bool(doc.get("enriched_at"))


async def enrich_author_fiche(author_name: str, *, force: bool = False) -> dict:
    """
    Crée / met à jour la fiche auteur (Wikidata → Wikipedia → Open Library).
    """
    display_name = (author_name or "").strip()
    key = normalize_author_name(display_name)
    if not key or key in ("auteur inconnu", "unknown", "n/a"):
        return {"found": False, "name": display_name}

    existing = get_cached_author(display_name)
    if existing and is_fresh(existing) and author_fiche_ready(existing) and not force:
        return {**existing, "found": True, "from_cache": True}

    from ..wikidata.service import wikidata_service

    profile: dict[str, Any] = {
        "name": display_name,
        "name_normalized": key,
        "bio": None,
        "photo_url": None,
        "image_url": None,
        "birth_date": None,
        "death_date": None,
        "nationality": None,
        "occupation": [],
        "genres": [],
        "awards": [],
        "wikidata_qid": None,
        "wikipedia_url": None,
        "series": [],
        "individual_books": [],
        "total_series": 0,
        "total_individual_books": 0,
        "sources": {},
    }

    # 1) Wikidata profil + séries
    try:
        info = await wikidata_service.get_author_info(display_name)
        if info:
            dumped = _serialize_model(info) or {}
            profile.update(
                {
                    "name": dumped.get("name") or display_name,
                    "birth_date": dumped.get("birth_date"),
                    "death_date": dumped.get("death_date"),
                    "nationality": dumped.get("nationality"),
                    "occupation": dumped.get("occupation") or [],
                    "genres": dumped.get("genres") or [],
                    "awards": dumped.get("awards") or [],
                    "photo_url": dumped.get("image_url") or dumped.get("photo_url"),
                    "image_url": dumped.get("image_url") or dumped.get("photo_url"),
                    "wikipedia_url": dumped.get("wikipedia_url"),
                    "wikidata_qid": dumped.get("id"),
                }
            )
            profile["sources"]["wikidata_profile"] = True
    except Exception as exc:
        logger.debug("author info wikidata fail %s: %s", display_name, exc)

    try:
        series_result = await wikidata_service.get_author_series(display_name)
        individual = await wikidata_service.get_author_individual_books(display_name)
        series_list = []
        if series_result and getattr(series_result, "found", False):
            series_list = _serialize_model(series_result.series) or []
        indiv_list = _serialize_model(individual) or []
        if series_list or indiv_list:
            profile["series"] = series_list
            profile["individual_books"] = indiv_list
            profile["total_series"] = len(series_list)
            profile["total_individual_books"] = len(indiv_list)
            profile["sources"]["wikidata_works"] = True
    except Exception as exc:
        logger.debug("author works wikidata fail %s: %s", display_name, exc)

    # 2) Wikipedia bio si manquante
    if not profile.get("bio"):
        try:
            import httpx

            async with httpx.AsyncClient(timeout=8.0) as client:
                for lang in ("fr", "en"):
                    r = await client.get(
                        f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{display_name.replace(' ', '_')}"
                    )
                    if not r.is_success:
                        continue
                    data = r.json()
                    extract = (data.get("extract") or "").strip()
                    if len(extract) >= 40:
                        profile["bio"] = extract[:2000]
                        profile["sources"]["wikipedia"] = lang
                        if not profile.get("photo_url"):
                            thumb = (data.get("thumbnail") or {}).get("source")
                            if thumb:
                                profile["photo_url"] = thumb
                                profile["image_url"] = thumb
                        if not profile.get("wikipedia_url"):
                            profile["wikipedia_url"] = (data.get("content_urls") or {}).get(
                                "desktop", {}
                            ).get("page")
                        break
        except Exception as exc:
            logger.debug("author wikipedia fail %s: %s", display_name, exc)

    now = datetime.utcnow()
    doc = {
        **profile,
        "id": (existing or {}).get("id") or str(uuid.uuid4()),
        "enriched_at": now,
        "updated_at": now,
        "created_at": (existing or {}).get("created_at") or now,
    }

    try:
        authors_collection.update_one(
            {"name_normalized": key},
            {"$set": doc},
            upsert=True,
        )
    except Exception as exc:
        logger.warning("author upsert fail %s: %s", display_name, exc)

    return {**doc, "found": author_fiche_ready(doc), "from_cache": False}


def list_library_author_names(user_id: str) -> list[str]:
    """Auteurs distincts des livres (+ séries si champ author) de la biblio user."""
    names: list[str] = []
    seen: set[str] = set()
    try:
        pipeline = [
            {"$match": {"user_id": user_id, "author": {"$exists": True, "$nin": [None, ""]}}},
            {"$group": {"_id": "$author", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
            {"$limit": 80},
        ]
        for row in books_collection.aggregate(pipeline):
            raw = (row.get("_id") or "").strip()
            if not raw:
                continue
            # « A, B » → premier auteur principal
            primary = raw.split(",")[0].strip() if "," in raw else raw
            key = normalize_author_name(primary)
            if not key or key in seen or key in ("auteur inconnu", "unknown"):
                continue
            seen.add(key)
            names.append(primary)
    except Exception as exc:
        logger.warning("list library authors fail: %s", exc)

    try:
        for s in series_library_collection.find(
            {"user_id": user_id},
            {"_id": 0, "author": 1, "authors": 1},
        ).limit(80):
            raw = (s.get("author") or "").strip()
            if not raw and isinstance(s.get("authors"), list) and s["authors"]:
                raw = str(s["authors"][0] or "").strip()
            primary = raw.split(",")[0].strip() if raw else ""
            key = normalize_author_name(primary)
            if not key or key in seen or key in ("auteur inconnu", "unknown"):
                continue
            seen.add(key)
            names.append(primary)
    except Exception as exc:
        logger.debug("list series authors fail: %s", exc)

    return names


async def ensure_authors_from_library(
    user_id: str, *, limit: int = MAX_ENSURE_PER_CALL, force: bool = False
) -> dict:
    names = list_library_author_names(user_id)
    created = []
    skipped = []
    errors = []
    for name in names:
        if len(created) >= limit:
            skipped.extend(names[names.index(name) :])
            break
        cached = get_cached_author(name)
        if cached and is_fresh(cached) and author_fiche_ready(cached) and not force:
            skipped.append(name)
            continue
        try:
            doc = await enrich_author_fiche(name, force=force)
            if doc.get("found") or author_fiche_ready(doc):
                created.append(name)
            else:
                skipped.append(name)
        except Exception as exc:
            logger.debug("ensure author fail %s: %s", name, exc)
            errors.append(name)
    return {
        "ok": True,
        "total_library_authors": len(names),
        "ensured": created,
        "skipped": skipped,
        "errors": errors,
        "ensured_count": len(created),
    }
