"""Recherche de couvertures (Open Library + Google Books) — synchrone, via to_thread."""
from __future__ import annotations

import logging
import re
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = (2, 7)
_OL_COVER = "https://covers.openlibrary.org/b"


def normalize_cover_url(url: Optional[str]) -> str:
    """Normalise une URL de couverture vers le CDN OL (plus fiable qu'archive.org)."""
    if not url:
        return ""
    u = str(url).strip()
    if not u or u.startswith("data:"):
        return ""
    u = u.replace("http://", "https://")
    # Google Books : conserver les query params (id, printsec, img…)
    if "books.google." in u or "googleusercontent.com" in u:
        u = re.sub(r"([?&])zoom=\d", r"\1zoom=0", u, flags=re.I)
        if "edge=" not in u:
            u += ("&" if "?" in u else "?") + "edge=curl"
        return u
    if "archive.org" in u:
        m = re.search(r"(?:/|=)(\d+)-[LM]\.jpe?g", u, re.I)
        if m:
            return f"{_OL_COVER}/id/{m.group(1)}-M.jpg"
        return ""
    u = re.sub(
        r"(covers\.openlibrary\.org/b/(?:id|olid|isbn)/[^/?]+)-[LS]\.jpe?g",
        r"\1-M.jpg",
        u,
        flags=re.I,
    )
    return u.split("?")[0]


def is_usable_cover_url(url: Optional[str]) -> bool:
    u = (url or "").strip()
    if not u or u.startswith("data:"):
        return False
    if "undefined" in u:
        return False
    if re.search(r"/b/(?:id|olid)/OL\d+W", u, re.I):
        return False
    if "archive.org" in u:
        return False
    return True


def _clean_title(title: str) -> str:
    """Retire tome/volume pour élargir la recherche série/livre."""
    t = (title or "").strip()
    t = re.sub(
        r"\s*[,:\-–—]?\s*(tome|t\.?|vol\.?|volume|book|n°|no\.?)\s*\d+.*$",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", t)
    return t.strip() or (title or "").strip()


def resolve_cover_url(
    *,
    title: str = "",
    author: str = "",
    isbn: str = "",
    ol_key: str = "",
) -> Optional[str]:
    """Cherche une couverture. Retourne une URL CDN ou None."""
    edition = re.search(r"(OL\d+M)\b", ol_key or "", re.I)
    if edition:
        return f"{_OL_COVER}/olid/{edition.group(1)}-M.jpg"

    work = re.search(r"(OL\d+W)\b", ol_key or "", re.I)
    if work:
        cover = _cover_from_ol_work(work.group(1))
        if cover:
            return cover

    title_raw = (title or "").strip()
    title = _clean_title(title_raw)
    author = (author or "").strip()
    author_ok = bool(author) and author.lower() not in ("auteur inconnu", "unknown", "")

    # ISBN en dernier recours (souvent une image vide) — d'abord titre
    queries = []
    if title and author_ok:
        queries.append(f"{title} {author}")
        queries.append(f'title:"{title}" author:"{author}"')
    if title:
        queries.append(title)
        queries.append(f'title:"{title}"')
    if title_raw and title_raw != title:
        queries.append(title_raw)

    seen_q = set()
    for q in queries:
        qn = q.strip().lower()
        if not qn or qn in seen_q:
            continue
        seen_q.add(qn)
        cover = _ol_search_cover(q)
        if cover:
            return cover

    # Google Books
    for q in queries[:3]:
        cover = _gb_search_cover(q)
        if cover:
            return cover

    isbn_clean = re.sub(r"[^0-9Xx]", "", isbn or "")
    if len(isbn_clean) >= 10:
        return f"{_OL_COVER}/isbn/{isbn_clean}-M.jpg"

    return None


def _ol_search_cover(q: str) -> Optional[str]:
    try:
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "q": q,
                "limit": 8,
                "fields": "cover_i,key,title",
            },
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return None
        for doc in r.json().get("docs") or []:
            cover_i = doc.get("cover_i")
            if cover_i:
                return f"{_OL_COVER}/id/{int(cover_i)}-M.jpg"
    except Exception as e:
        logger.debug("OL cover search failed: %s", e)
    return None


def _gb_search_cover(q: str) -> Optional[str]:
    try:
        r = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": q, "maxResults": 5, "printType": "books"},
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return None
        for item in r.json().get("items") or []:
            links = (item.get("volumeInfo") or {}).get("imageLinks") or {}
            thumb = (
                links.get("thumbnail")
                or links.get("smallThumbnail")
                or links.get("medium")
            )
            if thumb:
                return str(thumb).replace("http://", "https://")
    except Exception as e:
        logger.debug("GB cover search failed: %s", e)
    return None


def _cover_from_ol_work(work_id: str) -> Optional[str]:
    try:
        r = requests.get(
            f"https://openlibrary.org/works/{work_id}.json",
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return None
        for c in r.json().get("covers") or []:
            try:
                cid = int(c)
            except (TypeError, ValueError):
                continue
            if cid > 0:
                return f"{_OL_COVER}/id/{cid}-M.jpg"
    except Exception as e:
        logger.debug("OL work cover failed: %s", e)
    return None
