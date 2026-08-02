"""
Appels https://www.googleapis.com/books/v1/volumes (documentation officielle Google Books).
Utilisé comme 3e source de métadonnées (après Wikidata + Open Library) — voir BOOKTIME_TODO.md.
"""

from __future__ import annotations

import re
from typing import Any

import requests

from ..config import GOOGLE_BOOKS_API_KEY

GB_VOLUMES_URL = "https://www.googleapis.com/books/v1/volumes"
_TIMEOUT = 15


def infer_book_category_from_google_item(it: dict[str, Any]) -> str:
    """
    roman | bd | manga — à partir des catégories Google Books + titre/sous-titre/description.
    """
    parts: list[str] = []
    cats = it.get("categories")
    if isinstance(cats, list):
        parts.extend(str(c) for c in cats if c)
    elif cats:
        parts.append(str(cats))
    parts.append(str(it.get("title") or ""))
    parts.append(str(it.get("subtitle") or ""))
    desc = str(it.get("description") or "")
    parts.append(desc[:500])
    blob = " ".join(parts).lower()
    if re.search(
        r"\b(manga|manhwa|manhua|light novel|webtoon|shōnen|shonen|shounen|seinen|josei|kodomo|shojo|shōjo)\b",
        blob,
        re.I,
    ):
        return "manga"
    if re.search(
        r"\b(comic|comics|comic book|graphic novel|roman graphique|bande dessinée|fumetti|marvel\b|dc comics)\b",
        blob,
        re.I,
    ):
        return "bd"
    return "roman"


def is_enabled() -> bool:
    """True si une clé Google Books est configurée (sinon les appels échouent)."""
    return bool(GOOGLE_BOOKS_API_KEY)


def _require_key() -> str:
    if not GOOGLE_BOOKS_API_KEY:
        raise RuntimeError("GOOGLE_BOOKS_API_KEY manquante dans l'environnement (.env)")
    return GOOGLE_BOOKS_API_KEY


def normalize_isbn(s: str) -> str:
    return re.sub(r"[^0-9Xx]", "", (s or "").strip())


def search_volumes(q: str, *, max_results: int = 10, order_by: str | None = None) -> dict[str, Any]:
    """
    Requête brute `volumes.list` : `q` peut être un titre, `isbn:978...`, `intitle:... inauthor:...`, etc.
    `order_by` accepte "newest" (tri par date) ou "relevance" (défaut Google).
    Retourne le JSON Google (items, totalItems, ...).
    """
    key = _require_key()
    n = max(1, min(int(max_results), 40))
    params = {"q": q.strip(), "maxResults": n, "key": key}
    if order_by in ("newest", "relevance"):
        params["orderBy"] = order_by
    r = requests.get(GB_VOLUMES_URL, params=params, timeout=_TIMEOUT)
    r.raise_for_status()
    return r.json()


def simplify_item(item: dict[str, Any]) -> dict[str, Any]:
    """Réponse allégée pour le front / autres services."""
    vid = item.get("id") or ""
    vi = item.get("volumeInfo") or {}
    ids = vi.get("industryIdentifiers") or []
    isbn13 = next((x.get("identifier") for x in ids if x.get("type") == "ISBN_13"), None)
    isbn10 = next((x.get("identifier") for x in ids if x.get("type") == "ISBN_10"), None)
    thumbs = vi.get("imageLinks") or {}
    cats = vi.get("categories") or []
    if not isinstance(cats, list):
        cats = []
    return {
        "google_books_id": vid,
        "title": vi.get("title") or "",
        "subtitle": vi.get("subtitle") or "",
        "authors": vi.get("authors") or [],
        "publisher": vi.get("publisher") or "",
        "published_date": vi.get("publishedDate") or "",
        "page_count": int(vi.get("pageCount") or 0),
        "description": (vi.get("description") or "")[:2000],
        "language": vi.get("language") or "",
        "isbn_13": isbn13,
        "isbn_10": isbn10,
        "thumbnail": thumbs.get("thumbnail") or thumbs.get("smallThumbnail") or "",
        "preview_link": vi.get("previewLink") or "",
        "info_link": vi.get("infoLink") or "",
        "categories": cats,
    }


def simplified_volume_to_integration_book(it: dict[str, Any]) -> dict[str, Any]:
    """Format livre attendu par le modal Intégrations (legacy) et la recherche combinée."""
    authors = it.get("authors") or []
    author = ", ".join(authors) if authors else ""
    pd = it.get("published_date") or ""
    publication_year = 0
    if pd and str(pd)[:4].isdigit():
        publication_year = int(str(pd)[:4])
    vid = it.get("google_books_id") or ""
    thumb = (it.get("thumbnail") or "").replace("http://", "https://")
    return {
        "title": it.get("title") or "",
        "author": author,
        "category": infer_book_category_from_google_item(it),
        "description": (it.get("description") or "")[:1000],
        "cover_url": thumb,
        "isbn": it.get("isbn_10") or "",
        "isbn13": it.get("isbn_13") or "",
        "publication_year": publication_year,
        "publisher": it.get("publisher") or "",
        "total_pages": int(it.get("page_count") or 0),
        "language": it.get("language") or "fr",
        "source": "google_books",
        "google_books_id": vid,
        "metadata": {
            "google_books_id": vid,
            "published_date": pd,
            "subtitle": it.get("subtitle") or "",
            "preview_link": it.get("preview_link") or "",
            "info_link": it.get("info_link") or "",
        },
    }


def search_volumes_simplified(q: str, *, max_results: int = 10, order_by: str | None = None) -> dict[str, Any]:
    raw = search_volumes(q, max_results=max_results, order_by=order_by)
    items = raw.get("items") or []
    return {
        "source": "google_books",
        "total_items": raw.get("totalItems"),
        "query": q.strip(),
        "items": [simplify_item(it) for it in items if isinstance(it, dict)],
    }


def get_volume_by_id(volume_id: str) -> dict[str, Any]:
    """Détail d'un volume par identifiant Google Books (GET /volumes/{id})."""
    key = _require_key()
    vid = (volume_id or "").strip()
    if not vid:
        raise ValueError("Identifiant de volume vide")
    url = f"{GB_VOLUMES_URL}/{vid}"
    r = requests.get(url, params={"key": key}, timeout=_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("Réponse Google Books invalide")
    return simplify_item(data)


def lookup_isbn(isbn: str, *, max_results: int = 5) -> dict[str, Any]:
    """Recherche par ISBN (10 ou 13)."""
    clean = normalize_isbn(isbn)
    if len(clean) not in (10, 13):
        raise ValueError("ISBN invalide (attendu 10 ou 13 caractères utiles)")
    return search_volumes_simplified(f"isbn:{clean}", max_results=max_results)
