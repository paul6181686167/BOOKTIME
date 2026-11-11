"""ISBN réel à partir d'un titre : Wikidata n'a pas tout.

Cascade : Open Library (clé œuvre / search) → Google Books → BnF.
Aucun ISBN inventé : longueur + clé de contrôle. Budget pour ne pas saturer les APIs.
"""
from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
from typing import Any

import requests

from ..openlibrary.isbn_lookup import (
    _DC,
    _bnf_text,
    clean_isbn,
    is_valid_isbn,
    isbn10_to_13,
)
from ..static_wikidata.service import norm_title

logger = logging.getLogger(__name__)

UA = {
    "User-Agent": (
        "BooktimeCatalog/1.0 (https://github.com/paul6181686167/BOOKTIME; ISBN resolve)"
    ),
    "Accept": "application/json",
}
OL_SEARCH = "https://openlibrary.org/search.json"
GB_URL = "https://www.googleapis.com/books/v1/volumes"
BNF_SRU = "https://catalogue.bnf.fr/api/SRU"

_budget = 400
_cover_budget = 0


def reset_budget(n: int = 400) -> None:
    global _budget
    _budget = max(0, int(n))


def reset_cover_budget(n: int = 0) -> None:
    global _cover_budget
    _cover_budget = max(0, int(n))


def _spend_cover() -> bool:
    global _cover_budget
    if _cover_budget <= 0:
        return False
    _cover_budget -= 1
    return True


def _spend() -> bool:
    global _budget
    if _budget <= 0:
        return False
    _budget -= 1
    return True


def prefer_isbn(candidates: list[Any]) -> str:
    cleaned: list[str] = []
    for raw in candidates:
        if not raw:
            continue
        if isinstance(raw, (list, tuple)):
            got = prefer_isbn(list(raw))
            if got:
                cleaned.append(got)
            continue
        d = clean_isbn(str(raw))
        if len(d) == 10 and is_valid_isbn(d):
            d = isbn10_to_13(d)
        if len(d) == 13 and d.isdigit() and is_valid_isbn(d):
            cleaned.append(d)
    if not cleaned:
        return ""
    for prefix in ("9782", "978", "979"):
        for isbn in cleaned:
            if isbn.startswith(prefix):
                return isbn
    return cleaned[0]


def title_close(a: str, b: str) -> bool:
    na, nb = norm_title(a), norm_title(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if len(na) >= 8 and (na in nb or nb in na):
        return True
    return False


def from_ol_editions(ol_key: str, *, spend: bool = True) -> str:
    raw = (ol_key or "").strip().replace("https://openlibrary.org", "")
    kid = raw.rstrip("/").rsplit("/", 1)[-1]
    if not kid or (spend and not _spend()):
        return ""
    try:
        if kid.endswith("M"):
            r = requests.get(f"https://openlibrary.org/books/{kid}.json", timeout=12, headers=UA)
            if r.status_code != 200:
                return ""
            data = r.json() or {}
            return prefer_isbn(data.get("isbn_13") or data.get("isbn_10") or [])
        path = f"/works/{kid}/editions.json" if kid.endswith("W") else f"{raw}/editions.json"
        if not path.startswith("/"):
            path = "/" + path.lstrip("/")
        r = requests.get(
            f"https://openlibrary.org{path}",
            params={"limit": 8},
            timeout=15,
            headers=UA,
        )
        if r.status_code != 200:
            return ""
        cands: list[Any] = []
        for ed in (r.json() or {}).get("entries") or []:
            cands.extend(ed.get("isbn_13") or [])
            cands.extend(ed.get("isbn_10") or [])
        return prefer_isbn(cands)
    except Exception as exc:
        logger.debug("ISBN OL éditions échoué %s: %s", ol_key, exc)
        return ""


def from_ol_search(title: str, author: str = "", *, spend: bool = True) -> str:
    title = (title or "").strip()
    if len(title) < 3 or (spend and not _spend()):
        return ""
    params: dict[str, Any] = {"title": title, "limit": 5, "fields": "title,author_name,isbn,key"}
    if author:
        params["author"] = author
    try:
        r = requests.get(OL_SEARCH, params=params, timeout=8, headers=UA)
        if r.status_code != 200:
            return ""
        for doc in (r.json() or {}).get("docs") or []:
            if not title_close(title, doc.get("title") or ""):
                continue
            isbn = prefer_isbn(doc.get("isbn") or [])
            if isbn:
                return isbn
    except Exception as exc:
        logger.debug("ISBN OL search échoué %s: %s", title, exc)
    return ""


def from_google_books(title: str, author: str = "", *, spend: bool = True) -> str:
    title = (title or "").strip()
    if len(title) < 3 or (spend and not _spend()):
        return ""
    q = f'intitle:"{title}"'
    if author:
        q += f' inauthor:"{author}"'
    params: dict[str, Any] = {"q": q, "maxResults": 3, "printType": "books"}
    key = (os.getenv("GOOGLE_BOOKS_API_KEY") or "").strip()
    if key:
        params["key"] = key
    try:
        r = requests.get(GB_URL, params=params, timeout=8, headers=UA)
        if r.status_code in (403, 429):
            return ""
        if r.status_code != 200:
            return ""
        for item in (r.json() or {}).get("items") or []:
            info = item.get("volumeInfo") or {}
            if not title_close(title, info.get("title") or ""):
                continue
            ids = info.get("industryIdentifiers") or []
            cands = [x.get("identifier") for x in ids if isinstance(x, dict)]
            isbn = prefer_isbn(cands)
            if isbn:
                return isbn
    except Exception as exc:
        logger.debug("ISBN Google Books échoué %s: %s", title, exc)
    return ""


def from_bnf(title: str, author: str = "", *, spend: bool = True) -> str:
    title = (title or "").strip()
    if len(title) < 3 or (spend and not _spend()):
        return ""
    safe_title = title.replace('"', " ")
    query = f'bib.title all "{safe_title}"'
    if author:
        query += f' and bib.author all "{author.replace(chr(34), " ")}"'
    try:
        r = requests.get(
            BNF_SRU,
            params={
                "version": "1.2",
                "operation": "searchRetrieve",
                "query": query,
                "recordSchema": "dublincore",
                "maximumRecords": "3",
            },
            timeout=10,
            headers={**UA, "Accept": "application/xml"},
        )
        if r.status_code != 200:
            return ""
        root = ET.fromstring(r.content)
        for dc in root.findall(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc"):
            rec_title = _bnf_text(dc.find(f"{_DC}title")).split(" / ")[0]
            if rec_title and not title_close(title, rec_title):
                continue
            cands: list[str] = []
            for ident in dc.findall(f"{_DC}identifier"):
                text = _bnf_text(ident)
                if text:
                    cands.append(text)
            isbn = prefer_isbn(cands)
            if isbn:
                return isbn
    except Exception as exc:
        logger.debug("ISBN BnF échoué %s: %s", title, exc)
    return ""


def resolve_isbn(
    *,
    title: str,
    author: str = "",
    title_en: str = "",
    ol_key: str = "",
) -> str:
    """Renvoie un ISBN-13 réel ou ''."""
    if ol_key:
        got = from_ol_editions(ol_key)
        if got:
            return got
    for t in (title, title_en):
        if not (t or "").strip():
            continue
        for fn in (from_ol_search, from_google_books, from_bnf):
            got = fn(t, author)
            if got:
                return got
    return ""


def _ol_cover_url(cover_i: Any) -> str:
    try:
        n = int(cover_i)
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    return f"https://covers.openlibrary.org/b/id/{n}-M.jpg"


def find_cover(
    *,
    title: str,
    author: str = "",
    title_en: str = "",
    isbn: str = "",
    ol_key: str = "",
) -> tuple[str, str]:
    """Jaquette + ISBN réel (Open Library / Google). Jamais d'ISBN inventé."""
    isbn = prefer_isbn([isbn]) if isbn else ""
    if isbn:
        return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg", isbn
    if ol_key:
        got = from_ol_editions(ol_key)
        if got:
            return f"https://covers.openlibrary.org/b/isbn/{got}-M.jpg", got
    for t in (title, title_en):
        if len((t or "").strip()) < 3 or not _spend_cover():
            continue
        params: dict[str, Any] = {
            "title": t,
            "limit": 5,
            "fields": "title,author_name,isbn,key,cover_i",
        }
        if author:
            params["author"] = author
        try:
            r = requests.get(OL_SEARCH, params=params, timeout=8, headers=UA)
            if r.status_code == 200:
                for doc in (r.json() or {}).get("docs") or []:
                    if not title_close(t, doc.get("title") or ""):
                        continue
                    cover = _ol_cover_url(doc.get("cover_i"))
                    got = prefer_isbn(doc.get("isbn") or [])
                    if cover:
                        return cover, got
                    if got:
                        return f"https://covers.openlibrary.org/b/isbn/{got}-M.jpg", got
        except Exception as exc:
            logger.debug("Jaquette OL search échoué %s: %s", t, exc)
        if not _spend_cover():
            continue
        q = f'intitle:"{t}"'
        if author:
            q += f' inauthor:"{author}"'
        gb_params: dict[str, Any] = {"q": q, "maxResults": 3, "printType": "books"}
        key = (os.getenv("GOOGLE_BOOKS_API_KEY") or "").strip()
        if key:
            gb_params["key"] = key
        try:
            r = requests.get(GB_URL, params=gb_params, timeout=8, headers=UA)
            if r.status_code in (403, 429):
                continue
            if r.status_code != 200:
                continue
            for item in (r.json() or {}).get("items") or []:
                info = item.get("volumeInfo") or {}
                if not title_close(t, info.get("title") or ""):
                    continue
                ids = info.get("industryIdentifiers") or []
                got = prefer_isbn([x.get("identifier") for x in ids if isinstance(x, dict)])
                links = info.get("imageLinks") or {}
                thumb = (links.get("thumbnail") or links.get("smallThumbnail") or "").strip()
                if thumb:
                    if thumb.startswith("http://"):
                        thumb = "https://" + thumb[len("http://") :]
                    return thumb, got
                if got:
                    return f"https://covers.openlibrary.org/b/isbn/{got}-M.jpg", got
        except Exception as exc:
            logger.debug("Jaquette Google Books échoué %s: %s", t, exc)
    return "", isbn or ""
