"""Résolution rapide de jaquettes catalogue (OL id / search / ISBN / wiki)."""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

logger = logging.getLogger("booktime.catalog_covers")

UA = {"User-Agent": "BooktimeCovers/1.0 (catalog backfill)"}
_SESSION = requests.Session()
_SESSION.headers.update(UA)
OL_SEARCH = "https://openlibrary.org/search.json"


def cover_url_from_id(cover_i: Any) -> str:
    try:
        n = int(cover_i)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    return f"https://covers.openlibrary.org/b/id/{n}-M.jpg"


def ol_cover_from_qid(qid: str) -> str:
    """Jaquette directe depuis une clé Open Library (work ou édition)."""
    key = (qid or "").strip()
    if not key.startswith("OL"):
        return ""
    try:
        if key.endswith("W"):
            url = f"https://openlibrary.org/works/{key}.json"
        elif key.endswith("M"):
            url = f"https://openlibrary.org/books/{key}.json"
        else:
            return ""
        for attempt in range(3):
            r = _SESSION.get(url, timeout=12)
            if r.status_code == 429:
                time.sleep(2.5 * (attempt + 1))
                continue
            if r.status_code != 200:
                return ""
            data = r.json() or {}
            covers = data.get("covers") or []
            if covers:
                return cover_url_from_id(covers[0])
            for field in ("isbn_13", "isbn_10"):
                for isbn in data.get(field) or []:
                    isbn = re.sub(r"\D", "", str(isbn))
                    if len(isbn) in (10, 13):
                        return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            # Search index (cover_i) — 1 req max
            if key.endswith("W"):
                time.sleep(0.05)
                sr = _SESSION.get(
                    OL_SEARCH,
                    params={
                        "q": f"key:/works/{key}",
                        "limit": 1,
                        "fields": "cover_i,isbn",
                    },
                    timeout=12,
                )
                if sr.status_code == 429:
                    time.sleep(3)
                    return ""
                if sr.status_code == 200:
                    docs = (sr.json() or {}).get("docs") or []
                    if docs:
                        u = cover_url_from_id(docs[0].get("cover_i"))
                        if u:
                            return u
                        for isbn in docs[0].get("isbn") or []:
                            isbn = re.sub(r"\D", "", str(isbn))
                            if len(isbn) in (10, 13):
                                return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            return ""
    except Exception as exc:
        logger.debug("ol cover %s: %s", key, exc)
    return ""


def search_cover(title: str, author: str = "", title_en: str = "") -> str:
    for t in (title, title_en):
        t = (t or "").strip()
        if len(t) < 3:
            continue
        params: dict[str, Any] = {
            "title": t,
            "limit": 5,
            "fields": "title,author_name,isbn,cover_i,key",
        }
        if author:
            params["author"] = author
        try:
            r = _SESSION.get(OL_SEARCH, params=params, timeout=12)
            if r.status_code == 429:
                time.sleep(2)
                continue
            if r.status_code != 200:
                continue
            t_l = t.lower()
            for doc in (r.json() or {}).get("docs") or []:
                dt = str(doc.get("title") or "").lower()
                if not dt:
                    continue
                # match souple : égalité ou inclusion
                if dt != t_l and t_l not in dt and dt not in t_l:
                    continue
                u = cover_url_from_id(doc.get("cover_i"))
                if u:
                    return u
                for isbn in doc.get("isbn") or []:
                    isbn = re.sub(r"\D", "", str(isbn))
                    if len(isbn) in (10, 13):
                        return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        except Exception as exc:
            logger.debug("search cover: %s", exc)
    return ""


def gb_cover(title: str, author: str = "") -> str:
    import os

    t = (title or "").strip()
    if len(t) < 3:
        return ""
    q = f'intitle:"{t}"'
    if author:
        q += f' inauthor:"{author}"'
    params: dict[str, Any] = {"q": q, "maxResults": 3, "printType": "books"}
    key = (os.getenv("GOOGLE_BOOKS_API_KEY") or "").strip()
    if key:
        params["key"] = key
    try:
        r = _SESSION.get(
            "https://www.googleapis.com/books/v1/volumes", params=params, timeout=10
        )
        if r.status_code != 200:
            return ""
        for item in (r.json() or {}).get("items") or []:
            info = item.get("volumeInfo") or {}
            links = info.get("imageLinks") or {}
            thumb = (links.get("thumbnail") or links.get("smallThumbnail") or "").strip()
            if thumb:
                return thumb.replace("http://", "https://")
    except Exception:
        return ""
    return ""


def resolve_cover(doc: dict[str, Any]) -> tuple[str, str]:
    """Retourne (url, source)."""
    from .daily_ingest import pick_isbn, usable_cover, wiki_cover

    existing = usable_cover(doc.get("cover_url"))
    if existing:
        return existing, "existing"

    qid = str(doc.get("qid") or "").strip()
    if qid.startswith("OL"):
        u = usable_cover(ol_cover_from_qid(qid))
        if u:
            return u, "openlibrary"

    details = doc.get("volume_details") if isinstance(doc.get("volume_details"), dict) else {}
    for vn in sorted(details, key=lambda k: int(k) if str(k).isdigit() else 0):
        d = details.get(vn) or {}
        if not isinstance(d, dict):
            continue
        isbn = pick_isbn(d.get("isbn"))
        if isbn:
            return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg", "isbn"

    title = (doc.get("name") or "").strip()
    authors = doc.get("authors") if isinstance(doc.get("authors"), list) else []
    author = str(authors[0] if authors else "")
    title_en = (doc.get("name_en") or "").strip()

    u = usable_cover(search_cover(title, author, title_en))
    if u:
        return u, "ol_search"

    u = usable_cover(gb_cover(title, author))
    if u:
        return u, "google_books"

    u = usable_cover(wiki_cover(title, title_en or None))
    if u:
        return u, "wikipedia"

    return "", ""
