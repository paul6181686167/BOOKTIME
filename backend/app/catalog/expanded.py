"""Noyau curé : 50 000 fiches tomes (Wikidata), overlay riche à part."""
from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..static_wikidata.service import norm_title

_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "expanded_fiches_catalog.json"
_lock = threading.Lock()
_doc: dict[str, Any] | None = None
_loaded = False


def clear_cache() -> None:
    global _doc, _loaded
    with _lock:
        _doc = None
        _loaded = False
    stats.cache_clear()


def _load() -> dict[str, Any]:
    global _doc, _loaded
    with _lock:
        if _loaded:
            return _doc or {"meta": {}, "series": []}
        _loaded = True
        if not _PATH.is_file():
            _doc = {"meta": {"book_count": 0, "series_count": 0, "ready": False}, "series": []}
            return _doc
        try:
            with open(_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {"meta": {}, "series": []}
            series = data.get("series") if isinstance(data.get("series"), list) else []
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            meta.setdefault("series_count", len(series))
            meta.setdefault("book_count", sum(int(s.get("volumes") or 0) for s in series if isinstance(s, dict)))
            meta["ready"] = True
            _doc = {"meta": meta, "series": series}
        except Exception:
            _doc = {"meta": {"book_count": 0, "series_count": 0, "ready": False}, "series": []}
        return _doc


@lru_cache(maxsize=1)
def stats() -> dict[str, Any]:
    doc = _load()
    meta = dict(doc.get("meta") or {})
    return {
        "series": int(meta.get("series_count") or 0),
        "books": int(meta.get("book_count") or 0),
        "ready": bool(meta.get("ready")),
        "categories": meta.get("categories") or {},
        "series_with_cover": int(meta.get("series_with_cover") or 0),
        "source": meta.get("source") or "expanded_fiches_catalog.json",
    }


def all_series() -> list[dict[str, Any]]:
    return list(_load().get("series") or [])


def catalog_payload() -> dict[str, Any]:
    doc = _load()
    return {"meta": stats(), "series": doc.get("series") or []}


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
    }


def search_series(q: str, limit: int = 20) -> list[dict[str, Any]]:
    qn = norm_title(q or "")
    if len(qn) < 2:
        return []
    hits: list[tuple[int, dict[str, Any]]] = []
    for s in all_series():
        if not isinstance(s, dict):
            continue
        name = norm_title(str(s.get("name") or ""))
        name_en = norm_title(str(s.get("name_en") or ""))
        score = 0
        if name == qn or name_en == qn:
            score = 3
        elif name.startswith(qn) or name_en.startswith(qn):
            score = 2
        elif (len(qn) >= 4 and (qn in name or qn in name_en)):
            score = 1
        else:
            titles = s.get("volume_titles") or {}
            if isinstance(titles, dict):
                for title in titles.values():
                    tn = norm_title(str(title or ""))
                    if tn == qn or (len(qn) >= 4 and qn in tn):
                        score = 1
                        break
        if score:
            hits.append((score, s))
    hits.sort(key=lambda h: (h[0], int(h[1].get("volumes") or 0)), reverse=True)
    return [_series_lite(s) | {"volume_titles": s.get("volume_titles"), "volume_details": s.get("volume_details")} for _, s in hits[:limit]]
