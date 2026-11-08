"""Noyau catalogue : Mongo (graine JSON 50k + fiches du jour)."""
from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..static_wikidata.service import norm_title

_DEFAULT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "expanded_fiches_catalog.json"
_PATH = _DEFAULT_PATH
_lock = threading.Lock()
_json_meta: dict[str, Any] | None = None


def clear_cache() -> None:
    global _json_meta
    with _lock:
        _json_meta = None
    try:
        from .seed import reset_seed_flag

        reset_seed_flag()
    except Exception:
        pass
    stats.cache_clear()


def _json_meta_only() -> dict[str, Any]:
    """Meta du fichier git, sans conserver les séries en RAM."""
    global _json_meta
    with _lock:
        if _json_meta is not None:
            return _json_meta
        from .seed import read_json_catalog

        data = read_json_catalog()
        _json_meta = dict(data.get("meta") or {})
        return _json_meta


def _mongo_counts() -> tuple[int, int, int]:
    try:
        from . import daily_store

        return daily_store.count(), daily_store.fiche_count(), daily_store.count_by_source("daily")
    except Exception:
        return 0, 0, 0


def _daily_author_count() -> int:
    try:
        from . import daily_authors

        return daily_authors.count()
    except Exception:
        return 0


@lru_cache(maxsize=1)
def stats() -> dict[str, Any]:
    n, fiches, daily_n = _mongo_counts()
    meta = _json_meta_only()
    if n <= 0:
        n = int(meta.get("series_count") or 0)
        fiches = int(meta.get("book_count") or 0)
    return {
        "series": n,
        "books": fiches,
        "ready": n > 0 or bool(meta.get("ready")) or int(meta.get("book_count") or 0) > 0,
        "categories": meta.get("categories") or {},
        "series_with_cover": int(meta.get("series_with_cover") or 0),
        "daily_series": daily_n,
        "daily_fiches": daily_n,
        "daily_authors": _daily_author_count(),
        "source": "mongodb" if n else (meta.get("source") or "expanded_fiches_catalog.json"),
    }


def all_series() -> list[dict[str, Any]]:
    """Audit / tests : lit le JSON git, ne sert pas la recherche live."""
    from .seed import read_json_catalog

    return list(read_json_catalog().get("series") or [])


def catalog_payload() -> dict[str, Any]:
    return {"meta": stats(), "series": []}


def _series_lite(s: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": s.get("key"),
        "qid": s.get("qid") or s.get("wikidata_qid"),
        "name": s.get("name"),
        "name_en": s.get("name_en"),
        "authors": s.get("authors") or [],
        "category": s.get("category"),
        "volumes": s.get("volumes"),
        "cover_url": s.get("cover_url"),
        "first_published": s.get("first_published"),
        "genre": s.get("genre"),
        "language": s.get("language"),
        "wikidata_qid": s.get("wikidata_qid") or s.get("qid"),
        "source": s.get("source") or "wikidata",
        "type": s.get("type"),
    }


def _score_series(s: dict[str, Any], qn: str) -> int:
    name = s.get("name_norm") or norm_title(str(s.get("name") or ""))
    name_en = s.get("name_en_norm") or norm_title(str(s.get("name_en") or ""))
    if name == qn or name_en == qn:
        return 3
    if name.startswith(qn) or name_en.startswith(qn):
        return 2
    if len(qn) >= 4 and (qn in name or qn in name_en):
        return 1
    titles = s.get("title_norms") or []
    if isinstance(titles, list) and qn in titles:
        return 1
    raw_titles = s.get("volume_titles") or {}
    if isinstance(raw_titles, dict):
        for title in raw_titles.values():
            tn = norm_title(str(title or ""))
            if tn == qn or (len(qn) >= 4 and qn in tn):
                return 1
    return 0


def search_authors(q: str, limit: int = 8) -> list[dict[str, Any]]:
    try:
        from .daily_authors import author_lite, search as search_daily_authors

        return [author_lite(d) for d in search_daily_authors(q, limit=limit)]
    except Exception:
        return []


def search_series(q: str, limit: int = 20) -> list[dict[str, Any]]:
    qn = norm_title(q or "")
    if len(qn) < 2:
        return []
    try:
        from .seed import ensure_seeded

        ensure_seeded()
    except Exception:
        pass
    try:
        from . import daily_store

        extras = daily_store.search(q, limit=max(limit * 3, 40))
    except Exception:
        extras = []
    hits: list[tuple[int, dict[str, Any]]] = []
    for s in extras:
        if not isinstance(s, dict):
            continue
        score = _score_series(s, qn)
        if score:
            hits.append((score, s))
    hits.sort(key=lambda h: (h[0], int(h[1].get("volumes") or 0)), reverse=True)
    return [
        _series_lite(s) | {"volume_titles": s.get("volume_titles"), "volume_details": s.get("volume_details")}
        for _, s in hits[:limit]
    ]
