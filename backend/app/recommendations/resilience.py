"""Recommandations « à toute épreuve » : cache, délai maximal et repli local.

Les recommandations dépendent d'Open Library / Google Books, parfois très lents (ou en panne).
Sans garde-fou, la page « Découvrir » tourne pendant tout le délai du client (45 s) puis n'affiche
rien. Ici :

- un délai maximal côté serveur (inférieur à celui du client) ;
- un cache mémoire par utilisateur (« Rafraîchir » force la régénération) ;
- en cas d'échec ou de résultat vide : on ressert la dernière liste connue, sinon une sélection
  locale (catalogue éditorial livré avec l'application), jamais une page vide.
"""
from __future__ import annotations

import asyncio
import logging
import os
import random
import re
import time
import unicodedata
from typing import Dict, List, Optional, Tuple

from app.utils.timeutils import utcnow

logger = logging.getLogger(__name__)

PERSONALIZED_TTL = 15 * 60          # une liste fraîche est réutilisée 15 min
POPULAR_TTL = 60 * 60
STALE_MAX_AGE = 24 * 60 * 60        # une liste plus ancienne ne sert plus de repli
_MAX_ENTRIES = 500

_cache: Dict[str, Tuple[float, Dict]] = {}


def _timeout(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def personalized_timeout() -> float:
    return _timeout("RECO_PERSONALIZED_TIMEOUT", 28.0)


def popular_timeout() -> float:
    return _timeout("RECO_POPULAR_TIMEOUT", 14.0)


def clear_cache(user_id: Optional[str] = None) -> None:
    """Vide le cache (tout, ou les entrées d'un utilisateur)."""
    if user_id is None:
        _cache.clear()
        return
    for key in [k for k in _cache if k.startswith(f"perso:{user_id}:")]:
        _cache.pop(key, None)


def _store(key: str, payload: Dict) -> None:
    if len(_cache) >= _MAX_ENTRIES:
        oldest = sorted(_cache.items(), key=lambda kv: kv[1][0])[: _MAX_ENTRIES // 5]
        for old_key, _ in oldest:
            _cache.pop(old_key, None)
    _cache[key] = (time.monotonic(), payload)


def _lookup(key: str, max_age: float) -> Optional[Dict]:
    entry = _cache.get(key)
    if not entry:
        return None
    stamp, payload = entry
    if time.monotonic() - stamp > max_age:
        return None
    return payload


def _has_items(payload: Optional[Dict]) -> bool:
    return bool(payload and payload.get("recommendations"))


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _local_pool() -> List[Dict]:
    """Sélection éditoriale livrée avec l'application (toujours disponible, hors ligne)."""
    from app.catalog.routes import _load_onboarding  # import tardif : évite un import circulaire

    return list(_load_onboarding())


def _owned_titles(user_id: str) -> Tuple[set, Dict[str, int]]:
    """Titres déjà dans la bibliothèque, et poids par catégorie."""
    from app.database.connection import books_collection

    titles: set = set()
    categories: Dict[str, int] = {}
    try:
        for book in books_collection.find({"user_id": user_id}, {"title": 1, "category": 1, "_id": 0}):
            titles.add(_norm(book.get("title", "")))
            category = book.get("category")
            if category:
                categories[category] = categories.get(category, 0) + 1
    except Exception as exc:  # pragma: no cover - base indisponible
        logger.warning("Lecture bibliothèque pour le repli impossible: %s", exc)
    return titles, categories


def _library_size(user_id: str) -> int:
    from app.database.connection import books_collection

    try:
        return books_collection.count_documents({"user_id": user_id})
    except Exception:  # pragma: no cover - base indisponible
        return -1


def _to_recommendation(work: Dict, reason: str, source: str) -> Dict:
    ol_key = work.get("ol_key") or ""
    title = work.get("title", "")
    return {
        "book_id": ol_key or work.get("id") or title,
        "title": title,
        "original_title": title,
        "title_fr": title,
        "display_title": title,
        "author": work.get("author", ""),
        "category": work.get("category", "roman"),
        "cover_url": work.get("cover_url"),
        "ol_key": ol_key,
        "saga": "",
        "subjects": [work["genre"]] if work.get("genre") else [],
        "publication_year": None,
        "isFromOpenLibrary": bool(ol_key),
        "confidence_score": 0.5,
        "reasons": [reason],
        "source": source,
        "metadata": {"ol_key": ol_key, "fallback": "local_catalog", "genre": work.get("genre")},
    }


def local_fallback(user_id: Optional[str], limit: int, *, personalized: bool) -> Dict:
    """Propositions tirées du catalogue local, hors titres déjà possédés."""
    pool = _local_pool()
    owned: set = set()
    categories: Dict[str, int] = {}
    if user_id:
        owned, categories = _owned_titles(user_id)
    candidates = [w for w in pool if w.get("title") and _norm(w["title"]) not in owned]

    rng = random.Random()
    rng.shuffle(candidates)
    if personalized and categories:
        # ~70 % dans les catégories déjà lues, le reste pour varier (liste déjà mélangée :
        # « Rafraîchir » change donc les propositions).
        liked = [w for w in candidates if categories.get(w.get("category", ""), 0)]
        other = [w for w in candidates if not categories.get(w.get("category", ""), 0)]
        quota = max(1, int(limit * 0.7))
        picked = liked[:quota] + other[: max(0, limit - quota)]
        picked += [w for w in liked[quota:] if w not in picked]
        candidates = picked

    reason = "Sélection Booktime" if not personalized else "Dans l'esprit de ta bibliothèque"
    source = "popular"
    recs = [_to_recommendation(w, reason, source) for w in candidates[:limit]]
    return {
        "recommendations": recs,
        "user_profile": {"has_books": bool(owned)},
        "algorithm_info": {"type": "local_fallback", "count": len(recs)},
        "fallback": True,
        "generated_at": utcnow().isoformat(),
    }


async def _run(coro, timeout: float, label: str) -> Optional[Dict]:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("%s : délai de %.0f s dépassé", label, timeout)
    except Exception as exc:
        logger.warning("%s : échec (%s)", label, exc)
    return None


async def personalized(service, user_id: str, limit: int, refresh: bool = False) -> Dict:
    """Recommandations perso : cache frais → génération bornée → dernière liste connue → repli local."""
    # Le nombre de livres fait partie de la clé : ajouter/supprimer un livre invalide le cache.
    key = f"perso:{user_id}:{_library_size(user_id)}:{limit}"
    if not refresh:
        fresh = _lookup(key, PERSONALIZED_TTL)
        if _has_items(fresh):
            return fresh

    result = await _run(
        service.get_personalized_recommendations(user_id=user_id, limit=limit),
        personalized_timeout(),
        "Recommandations personnalisées",
    )
    if _has_items(result):
        _store(key, result)
        return result

    stale = _lookup(key, STALE_MAX_AGE)
    if _has_items(stale):
        return {**stale, "stale": True}

    return local_fallback(user_id, limit, personalized=True)


async def popular(service, limit: int) -> Dict:
    """Recommandations populaires : cache → génération bornée → repli local."""
    key = f"popular:{limit}"
    fresh = _lookup(key, POPULAR_TTL)
    if _has_items(fresh):
        return fresh

    result = await _run(service._get_popular_recommendations(limit), popular_timeout(), "Livres populaires")
    if _has_items(result):
        _store(key, result)
        return result

    stale = _lookup(key, STALE_MAX_AGE)
    if _has_items(stale):
        return {**stale, "stale": True}

    return local_fallback(None, limit, personalized=False)
