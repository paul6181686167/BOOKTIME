"""Recherche de couvertures (Open Library + IA/Amazon/AbeBooks + Google Books)."""
from __future__ import annotations

import logging
import re
from typing import Any, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = (2, 8)
_OL_COVER = "https://covers.openlibrary.org/b"


def normalize_cover_url(url: Optional[str]) -> str:
    """Normalise une URL de couverture vers un CDN fiable."""
    if not url:
        return ""
    u = str(url).strip()
    if not u or u.startswith("data:"):
        return ""
    u = u.replace("http://", "https://")
    if "books.google." in u or "googleusercontent.com" in u:
        u = re.sub(r"([?&])zoom=\d", r"\1zoom=0", u, flags=re.I)
        if "edge=" not in u:
            u += ("&" if "?" in u else "?") + "edge=curl"
        return u
    if "ssl-images-amazon.com" in u or "pictures.abebooks.com" in u:
        return u
    if "archive.org" in u:
        if "/services/img/" in u or "/page/cover" in u or "/download/" in u:
            return u.split("?")[0]
        m = re.search(r"(?:/|=)(\d+)-[LM]\.jpe?g", u, re.I)
        if m:
            return f"{_OL_COVER}/id/{m.group(1)}-M.jpg"
        return u
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
        if "/services/img/" in u:
            return True
        if re.search(r"\.(jpe?g|png|webp)(\?|$)", u, re.I) or "/download/" in u:
            return True
        return False
    return True


def _clean_title(title: str) -> str:
    t = (title or "").strip()
    t = re.sub(
        r"\s*[,:\-–—]?\s*(tome|t\.?|vol\.?|volume|book|n°|no\.?)\s*\d+.*$",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", t)
    t = re.sub(r"[?？!！.…]+$", "", t).strip()
    return t.strip() or (title or "").strip()


def _norm(s: str) -> str:
    import unicodedata

    t = unicodedata.normalize("NFD", str(s or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def _title_score(query: str, candidate: str) -> int:
    q, c = _norm(query), _norm(candidate)
    if not q or not c:
        return 0
    if q == c:
        return 100
    if c.startswith(q) or q.startswith(c):
        return 90
    if q in c or c in q:
        return 75
    qw = [w for w in q.split() if len(w) > 2]
    if not qw:
        return 0
    hits = sum(1 for w in qw if w in c)
    return int(round((hits / len(qw)) * 70))


def isbn13_to_10(isbn: str) -> Optional[str]:
    d = re.sub(r"[^0-9Xx]", "", isbn or "")
    if len(d) == 10:
        return d.upper()
    if len(d) != 13 or not d.startswith("978"):
        return None
    core = d[3:12]
    total = sum((10 - i) * int(core[i]) for i in range(9))
    check = (11 - (total % 11)) % 11
    return core + ("X" if check == 10 else str(check))


def _cover_amazon(isbn: str) -> Optional[str]:
    isbn10 = isbn13_to_10(isbn)
    if not isbn10:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/P/{isbn10}.01.LZZZZZZZ.jpg"


def _cover_abebooks(isbn: str) -> Optional[str]:
    d = re.sub(r"[^0-9Xx]", "", isbn or "")
    if len(d) < 10:
        return None
    return f"https://pictures.abebooks.com/isbn/{d}-us.jpg"


def _cover_ocaid(ocaid: str) -> Optional[str]:
    oid = (ocaid or "").strip()
    if len(oid) < 3:
        return None
    return f"https://archive.org/services/img/{quote(oid)}"


def _title_variants(title: str) -> list[str]:
    base = _clean_title(title)
    if not base:
        return []
    out = [base]
    low = base.lower()
    if "au pied du paradis" in low:
        out.append(re.sub(r"au pied du paradis", "Un pied au paradis", base, flags=re.I))
    if "un pied au paradis" in low:
        out.append(re.sub(r"un pied au paradis", "Au pied du paradis", base, flags=re.I))
    if re.search(r"\bjulitte\b", base, re.I):
        out.append(re.sub(r"\bjulitte\b", "Juliette", base, flags=re.I))
    # Corruption OL : Cui ↔ Q.I.
    if re.search(r"\bq\.?\s*i\.?\b|\bqi\b", base, re.I):
        out.append(re.sub(r"\bq\.?\s*i\.?\b|\bqi\b", "Cui", base, flags=re.I))
    if re.search(r"\bcui\b", base, re.I):
        out.append(re.sub(r"\bcui\b", "Q.I.", base, flags=re.I))
        out.append(re.sub(r"\bcui\b", "QI", base, flags=re.I))
    return list(dict.fromkeys(out))


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

    isbn_clean = re.sub(r"[^0-9Xx]", "", isbn or "")
    if len(isbn_clean) >= 10:
        amz = _cover_amazon(isbn_clean)
        if amz:
            return amz
        abe = _cover_abebooks(isbn_clean)
        if abe:
            return abe

    title_raw = (title or "").strip()
    title_c = _clean_title(title_raw)
    author = (author or "").strip()
    author_ok = bool(author) and author.lower() not in ("auteur inconnu", "unknown", "")

    queries: list[str] = []
    for variant in _title_variants(title_c or title_raw):
        if author_ok:
            queries.append(f"{variant} {author}")
        queries.append(variant)

    seen_q: set[str] = set()
    for q in queries:
        qn = q.strip().lower()
        if not qn or qn in seen_q:
            continue
        seen_q.add(qn)
        cover = _ol_search_cover(q, prefer_title=title_c or title_raw)
        if cover:
            return cover

    for q in queries[:4]:
        cover = _gb_search_cover(q, prefer_title=title_c or title_raw)
        if cover:
            return cover

    if len(isbn_clean) >= 10:
        return f"{_OL_COVER}/isbn/{isbn_clean}-M.jpg"

    return None


def _ol_search_cover(q: str, prefer_title: str = "") -> Optional[str]:
    try:
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "q": q,
                "limit": 10,
                "fields": "cover_i,key,title,isbn,edition_key,ia",
            },
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return None
        docs = r.json().get("docs") or []
        ranked = sorted(
            docs,
            key=lambda d: _title_score(prefer_title, d.get("title") or ""),
            reverse=True,
        )
        for doc in ranked:
            score = _title_score(prefer_title, doc.get("title") or "")
            if prefer_title and score < 45:
                continue
            cover_i = doc.get("cover_i")
            if cover_i:
                return f"{_OL_COVER}/id/{int(cover_i)}-M.jpg"
            ia = doc.get("ia") or []
            if ia:
                cover = _cover_ocaid(ia[0])
                if cover:
                    return cover
            isbns = doc.get("isbn") or []
            for isbn in isbns[:4]:
                amz = _cover_amazon(str(isbn))
                if amz:
                    return amz
            for isbn in isbns[:2]:
                abe = _cover_abebooks(str(isbn))
                if abe:
                    return abe
            eds = doc.get("edition_key") or []
            if eds:
                cover = _cover_from_edition(eds[0])
                if cover:
                    return cover
    except Exception as e:
        logger.debug("OL cover search failed: %s", e)
    return None


def _cover_from_edition(edition_key: str) -> Optional[str]:
    m = re.search(r"(OL\d+M)\b", edition_key or "", re.I)
    if not m:
        return None
    try:
        r = requests.get(
            f"https://openlibrary.org/books/{m.group(1)}.json",
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return None
        data: dict[str, Any] = r.json()
        for c in data.get("covers") or []:
            try:
                cid = int(c)
            except (TypeError, ValueError):
                continue
            if cid > 0:
                return f"{_OL_COVER}/id/{cid}-M.jpg"
        if data.get("ocaid"):
            cover = _cover_ocaid(str(data["ocaid"]))
            if cover:
                return cover
        for src in data.get("source_records") or []:
            am = re.match(r"^amazon:(\d{9}[\dXx])$", str(src), re.I)
            if am:
                return _cover_amazon(am.group(1))
        for isbn in (data.get("isbn_10") or []) + (data.get("isbn_13") or []):
            amz = _cover_amazon(str(isbn))
            if amz:
                return amz
    except Exception as e:
        logger.debug("OL edition cover failed: %s", e)
    return None


def _gb_search_cover(q: str, prefer_title: str = "") -> Optional[str]:
    try:
        r = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": q, "maxResults": 8, "printType": "books"},
            timeout=_TIMEOUT,
        )
        if not r.ok:
            return None
        items = r.json().get("items") or []
        ranked = sorted(
            items,
            key=lambda it: _title_score(
                prefer_title, ((it.get("volumeInfo") or {}).get("title") or "")
            ),
            reverse=True,
        )
        for item in ranked:
            vi = item.get("volumeInfo") or {}
            if prefer_title and _title_score(prefer_title, vi.get("title") or "") < 40:
                continue
            links = vi.get("imageLinks") or {}
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
