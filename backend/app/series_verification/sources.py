"""
Récupérateurs de tomes par source, pour la vérification croisée.

Chaque fonction est défensive : en cas d'erreur réseau ou de source indisponible,
elle renvoie une liste vide (jamais d'exception), pour que la vérification continue
avec les autres sources.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import requests

from ..static_wikidata import service as static_wd
from ..google_books import service as gb

logger = logging.getLogger("booktime.series_verification")

_OL_SEARCH = "https://openlibrary.org/search.json"
_OL_TIMEOUT = 6


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


# Titres à écarter : coffrets / intégrales / compilations (ne sont pas un tome).
_BOX_SET = re.compile(
    r"\b(box ?set|omnibus|coffret|int[ée]grale|complete (collection|series|set)|"
    r"collector|anthologie|compilation|vol(?:s|umes)?\.? ?\d+\s*[-–]\s*\d+|\d+\s*[-–]\s*\d+\s*$)\b",
    re.I,
)


def _is_box_set(title: str) -> bool:
    t = title or ""
    return bool(_BOX_SET.search(t)) or len(t) >= 90


def fetch_wikidata_static(qid: str | None, name: str) -> list[dict[str, Any]]:
    """Tomes depuis l'index Wikidata statique (works), via QID si connu, sinon par titre."""
    try:
        row = None
        if qid:
            row = static_wd.get_series(qid)
        if row is None and name:
            hits = static_wd.search_series_by_title(q=name, limit=1)
            if hits:
                row = static_wd.get_series(hits[0].get("qid"))
        if not row:
            return []
        out: list[dict[str, Any]] = []
        for w in row.get("works") or []:
            if not isinstance(w, dict):
                continue
            out.append(
                {
                    "title": w.get("title_fr") or w.get("title_en") or "",
                    "volume": w.get("volume"),
                    "isbns": w.get("isbns") or [],
                    "publication_date": w.get("publication_date"),
                }
            )
        return out
    except Exception as e:  # noqa: BLE001
        logger.warning("WD statique indisponible pour %r: %s", name, e)
        return []


def fetch_openlibrary(name: str, author: str | None, limit: int = 40) -> list[dict[str, Any]]:
    """Tomes depuis Open Library (recherche par nom de série, filtrée par pertinence)."""
    if not name:
        return []
    name_norm = _norm(name)
    name_words = [w for w in name_norm.split() if len(w) >= 3]

    def is_relevant(doc: dict) -> bool:
        title_norm = _norm(doc.get("title", ""))
        series_field = doc.get("series") or []
        series_str = _norm(series_field[0] if series_field else "")
        if series_str and any(w in series_str for w in name_words):
            return True
        if name_words and all(w in title_norm for w in name_words[:2]):
            return True
        return False

    try:
        query = f'"{name}"'
        if author:
            query += f' author:"{author}"'
        params = {
            "q": query,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,series",
        }
        resp = requests.get(_OL_SEARCH, params=params, timeout=_OL_TIMEOUT)
        resp.raise_for_status()
        docs = resp.json().get("docs", [])
        relevant = [d for d in docs if is_relevant(d)] or docs

        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for doc in relevant:
            key = doc.get("key", "")
            if key in seen:
                continue
            seen.add(key)
            if _is_box_set(doc.get("title", "")):
                continue
            raw_series = doc.get("series") or []
            series_str = raw_series[0] if raw_series else ""
            out.append(
                {
                    "title": doc.get("title", ""),
                    "volume": series_str,  # contient souvent "... #3"
                    "isbn": (doc.get("isbn") or [None])[0],
                    "first_publish_year": doc.get("first_publish_year"),
                }
            )
        return out
    except requests.RequestException as e:
        logger.warning("Open Library indisponible pour %r: %s", name, e)
        return []


def fetch_google_books(name: str, author: str | None, limit: int = 40) -> list[dict[str, Any]]:
    """Tomes depuis Google Books (intitle + inauthor). Vide si pas de clé API."""
    if not name:
        return []
    try:
        q = f'intitle:"{name}"'
        if author:
            q += f' inauthor:"{author}"'
        data = gb.search_volumes_simplified(q, max_results=min(limit, 40))
        out: list[dict[str, Any]] = []
        for it in data.get("items") or []:
            title = (it.get("title") or "").strip()
            sub = (it.get("subtitle") or "").strip()
            full = f"{title} {sub}".strip()
            if _is_box_set(full):
                continue
            out.append(
                {
                    "title": full or title,
                    "isbn_13": it.get("isbn_13"),
                    "isbn_10": it.get("isbn_10"),
                    "published_date": it.get("published_date"),
                }
            )
        return out
    except RuntimeError as e:
        # Clé API absente : on dégrade silencieusement (Google Books optionnel).
        logger.info("Google Books non interrogé (%s)", e)
        return []
    except Exception as e:  # noqa: BLE001
        logger.warning("Google Books indisponible pour %r: %s", name, e)
        return []
