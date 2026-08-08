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
    roman | bd | manga — catégories Google + titre/sous-titre (pas la description).
    Light novel → roman. Heuristiques prudentes (voir category_detect).
    """
    from ..utils.category_detect import detect_category_from_google

    return detect_category_from_google(
        categories=it.get("categories"),
        title=str(it.get("title") or ""),
        subtitle=str(it.get("subtitle") or ""),
        description=str(it.get("description") or ""),
    )


def is_enabled() -> bool:
    """True si une clé Google Books est configurée (sinon les appels échouent)."""
    return bool(GOOGLE_BOOKS_API_KEY)


def _require_key() -> str:
    if not GOOGLE_BOOKS_API_KEY:
        raise RuntimeError("GOOGLE_BOOKS_API_KEY manquante dans l'environnement (.env)")
    return GOOGLE_BOOKS_API_KEY


def normalize_isbn(s: str) -> str:
    return re.sub(r"[^0-9Xx]", "", (s or "").strip())


def search_volumes(
    q: str,
    *,
    max_results: int = 10,
    order_by: str | None = None,
    lang_restrict: str | None = None,
    print_type: str | None = None,
) -> dict[str, Any]:
    """
    Requête brute `volumes.list` : `q` peut être un titre, `isbn:978...`, `intitle:... inauthor:...`, etc.
    `order_by` accepte "newest" (tri par date) ou "relevance" (défaut Google).
    `lang_restrict` : ex. "fr" pour ne garder que les volumes dans cette langue.
    `print_type` : "books" | "magazines".
    Retourne le JSON Google (items, totalItems, ...).
    """
    key = _require_key()
    n = max(1, min(int(max_results), 40))
    params = {"q": q.strip(), "maxResults": n, "key": key}
    if order_by in ("newest", "relevance"):
        params["orderBy"] = order_by
    if lang_restrict:
        params["langRestrict"] = lang_restrict
    if print_type in ("books", "magazines"):
        params["printType"] = print_type
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


def search_similar_books(
    title: str,
    author: str = "",
    *,
    limit: int = 10,
    subjects: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Livres proches via Google Books (sujets / catégories du seed).
    Retourne le format « integration book » (title, author, cover_url, …).
    """
    if not is_enabled():
        return []
    seed_title = (title or "").strip()
    if not seed_title:
        return []
    seed_author = (author or "").split(",")[0].strip()
    seed_norm = seed_title.lower()[:50]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    seed_author_norm = seed_author.lower()
    seed_tokens = [
        w.lower()
        for w in re.split(r"[\s:–—\-]+", seed_title)
        if len(w) >= 4
    ]

    def _append(it: dict[str, Any]) -> None:
        book = simplified_volume_to_integration_book(it)
        t = (book.get("title") or "").strip()
        if not t:
            return
        t_norm = t.lower()
        author_b = (book.get("author") or "").lower()
        blob = f"{t_norm} {' '.join(it.get('categories') or [])}".lower()
        if seed_norm and (seed_norm in t_norm or seed_norm in blob):
            return
        if seed_tokens and all(tok in blob for tok in seed_tokens[:3]):
            return
        # Pas le même auteur (évite la même série)
        if seed_author_norm and seed_author_norm in author_b:
            return
        key = f"{t_norm}|{author_b}"
        if key in seen:
            return
        seen.add(key)
        book["ol_key"] = f"gbooks_{book.get('google_books_id') or ''}"
        book["google_books_id"] = book.get("google_books_id") or it.get("google_books_id")
        book["subjects"] = it.get("categories") or []
        book["isFromGoogleBooks"] = True
        book["isFromOpenLibrary"] = False
        book["display_title"] = t
        book["saga"] = ""
        out.append(book)

    try:
        # 1) Catégories du seed (sans tirer toute la bibliographie de l'auteur)
        q_seed = f'intitle:"{seed_title[:70]}"'
        if seed_author:
            q_seed += f' inauthor:"{seed_author[:40]}"'
        seed_raw = search_volumes(q_seed, max_results=5, print_type="books")
        if not (seed_raw.get("items") or []):
            seed_raw = search_volumes(
                q_seed, max_results=5, lang_restrict="fr", print_type="books"
            )
        cats: list[str] = []
        if not seed_author:
            for item in seed_raw.get("items") or []:
                if not isinstance(item, dict):
                    continue
                simplified = simplify_item(item)
                authors = simplified.get("authors") or []
                if authors:
                    seed_author = str(authors[0]).split(",")[0].strip()
                    seed_author_norm = seed_author.lower()
                    break
        for item in seed_raw.get("items") or []:
            if not isinstance(item, dict):
                continue
            simplified = simplify_item(item)
            for c in simplified.get("categories") or []:
                c = str(c).strip()
                if c and c not in cats and 2 < len(c) < 60:
                    cats.append(c)
            if cats:
                break
        for s in subjects or []:
            s = str(s).strip()
            if s and s not in cats and 2 < len(s) < 60:
                cats.append(s)

        # Uniquement des sujets / genres — jamais inauthor:seed
        queries: list[str] = []
        if cats:
            queries.append(f'subject:"{cats[0]}"')
            if len(cats) > 1:
                queries.append(f'subject:"{cats[1]}"')
        queries.extend(
            [
                'subject:"Juvenile Fiction" subject:Fantasy',
                'subject:"Young Adult Fiction" mythology',
                "mythology fantasy",
            ]
        )
        queries.append("fantasy young adult")

        for q in queries:
            if len(out) >= limit:
                break
            try:
                raw = search_volumes(
                    q,
                    max_results=min(limit + 6, 20),
                    print_type="books",
                )
            except Exception:
                raw = search_volumes(
                    q, max_results=min(limit + 6, 20), lang_restrict="fr", print_type="books"
                )
            for item in raw.get("items") or []:
                if not isinstance(item, dict):
                    continue
                _append(simplify_item(item))
                if len(out) >= limit:
                    break
    except Exception:
        return out[:limit]

    return out[:limit]
