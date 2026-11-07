"""
Notes d'autres sites pour une fiche livre ou série.

Sources interrogées (API publiques, sans scraping) :
  - Open Library  : note moyenne des lecteurs d'un livre (ratings_average / ratings_count)
  - Google Books  : note moyenne quand l'éditeur en publie une
  - AniList       : score des lecteurs de mangas (0-100)
  - MyAnimeList   : score des lecteurs de mangas, via l'API Jikan (0-10)

Goodreads et Babelio n'ont pas d'API publique : on ne propose qu'un lien de recherche.

Toutes les notes sont ramenées sur 5. Un échec d'une source n'empêche jamais les autres.
Les réponses sont gardées 24 h en mémoire pour ménager ces API gratuites.
"""

from __future__ import annotations

import logging
import os
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 6
CACHE_TTL_SECONDS = 24 * 3600
CACHE_MAX_ENTRIES = 500
MANGA_CATEGORIES = {"manga"}

_cache: dict[tuple, tuple[float, dict]] = {}

HttpGet = Callable[..., Any]


# ─────────────────────────── utilitaires ───────────────────────────

def normalize(text: Optional[str]) -> str:
    """Minuscules, sans accents ni ponctuation, espaces simples."""
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_VOLUME_RE = re.compile(r"\b(?:tome|vol(?:ume)?|t|n|no|numero|book|livre|#)\s*\d+\b|\b\d+\s*$")


def strip_volume(text: str) -> str:
    """Retire « tome 3 », « vol. 2 », « #4 » ou un numéro final : on compare l'œuvre, pas le tome."""
    base = normalize(text)
    stripped = re.sub(r"\s+", " ", _VOLUME_RE.sub(" ", base)).strip()
    return stripped if len(stripped) >= 3 else base  # « 1984 » reste « 1984 »


def titles_match(wanted: str, found: str, *, loose: bool = False) -> bool:
    """
    Même œuvre ?
    - strict (livres) : titres égaux, ou l'un couvre au moins 75 % des mots de l'autre
      (« Dune » ne correspond donc pas à « Dune Messiah »).
    - loose (séries de mangas) : l'un contient l'autre, car on compare un titre de tome
      (« One Piece - Tome 1 ») au nom de la série.
    """
    a, b = strip_volume(wanted), strip_volume(found)
    if len(a) < 3 or len(b) < 3:
        return False
    if a == b:
        return True
    contained = f" {b} " in f" {a} " or f" {a} " in f" {b} "
    if loose:
        return contained
    short, long_ = sorted((a.split(), b.split()), key=len)
    return contained and len(short) / len(long_) >= 0.75


def authors_match(wanted: str, found: list[str]) -> bool:
    """Sans auteur demandé ou trouvé on ne rejette pas ; sinon un nom de famille doit coïncider."""
    wanted_tokens = {t for t in normalize(wanted).split() if len(t) > 2}
    if not wanted_tokens or not found:
        return True
    found_tokens = {t for name in found for t in normalize(name).split() if len(t) > 2}
    return bool(wanted_tokens & found_tokens)


def _entry(
    source: str, label: str, score: float, scale: float, count: Optional[int], url: Optional[str],
    scope: str = "book",
) -> dict[str, Any]:
    return {
        "source": source,
        "label": label,
        "score": round(score / scale * 5, 2),  # toujours sur 5
        "count": int(count) if count else None,
        "url": url,
        "scope": scope,  # "book" = ce livre ; "series" = la série entière
    }


# ─────────────────────────── sources ───────────────────────────

def fetch_open_library(title: str, author: str, isbn: str, get: HttpGet) -> Optional[dict]:
    params: dict[str, Any] = {
        "limit": 5,
        "fields": "key,title,author_name,ratings_average,ratings_count",
    }
    if isbn:
        params["q"] = f"isbn:{isbn}"
    else:
        params["title"] = title
        if author:
            params["author"] = author
    r = get("https://openlibrary.org/search.json", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    for doc in r.json().get("docs", []):
        if not doc.get("ratings_average"):
            continue
        if not isbn and not (
            titles_match(title, doc.get("title", "")) and authors_match(author, doc.get("author_name") or [])
        ):
            continue
        return _entry(
            "openlibrary", "Open Library", doc["ratings_average"], 5, doc.get("ratings_count"),
            f"https://openlibrary.org{doc['key']}" if doc.get("key") else None,
        )
    return None


def fetch_google_books(title: str, author: str, isbn: str, get: HttpGet) -> Optional[dict]:
    if isbn:
        q = f"isbn:{isbn}"
    else:
        q = f'intitle:"{title}"' + (f' inauthor:"{author}"' if author else "")
    params: dict[str, Any] = {"q": q, "maxResults": 5, "printType": "books"}
    key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if key:
        params["key"] = key
    r = get("https://www.googleapis.com/books/v1/volumes", params=params, timeout=TIMEOUT)
    r.raise_for_status()
    for item in r.json().get("items", []):
        info = item.get("volumeInfo", {})
        if not info.get("averageRating"):
            continue
        if not isbn and not (
            titles_match(title, info.get("title", "")) and authors_match(author, info.get("authors") or [])
        ):
            continue
        return _entry(
            "googlebooks", "Google Books", info["averageRating"], 5, info.get("ratingsCount"),
            info.get("infoLink"),
        )
    return None


_ANILIST_QUERY = """
query ($search: String) {
  Media(search: $search, type: MANGA) {
    title { romaji english native }
    synonyms
    averageScore
    siteUrl
  }
}
"""


def fetch_anilist(title: str, get: HttpGet, post: Optional[HttpGet] = None) -> Optional[dict]:
    post = post or requests.post
    r = post(
        "https://graphql.anilist.co",
        json={"query": _ANILIST_QUERY, "variables": {"search": title}},
        timeout=TIMEOUT,
    )
    if r.status_code == 404:  # AniList répond 404 quand rien ne correspond
        return None
    r.raise_for_status()
    media = (r.json().get("data") or {}).get("Media")
    if not media or not media.get("averageScore"):
        return None
    names = [*(media.get("title") or {}).values(), *(media.get("synonyms") or [])]
    if not any(n and titles_match(title, n, loose=True) for n in names):
        return None
    return _entry("anilist", "AniList", media["averageScore"], 100, None, media.get("siteUrl"), "series")


def fetch_myanimelist(title: str, get: HttpGet) -> Optional[dict]:
    r = get("https://api.jikan.moe/v4/manga", params={"q": title, "limit": 5}, timeout=TIMEOUT)
    r.raise_for_status()
    for m in r.json().get("data", []):
        if not m.get("score"):
            continue
        names = [m.get("title"), m.get("title_english"), m.get("title_japanese")]
        names += [t.get("title") for t in m.get("titles", [])]
        if not any(n and titles_match(title, n, loose=True) for n in names):
            continue
        return _entry("myanimelist", "MyAnimeList", m["score"], 10, m.get("scored_by"), m.get("url"), "series")
    return None


# ─────────────────────────── agrégation ───────────────────────────

def search_links(title: str, author: str) -> list[dict[str, str]]:
    query = quote_plus(f"{title} {author}".strip())
    return [
        {"label": "Babelio", "url": f"https://www.babelio.com/resrecherche.php?Recherche={query}"},
        {"label": "Goodreads", "url": f"https://www.goodreads.com/search?q={query}"},
    ]


def get_external_ratings(
    title: str,
    author: str = "",
    isbn: str = "",
    kind: str = "book",
    category: str = "",
    *,
    get: HttpGet = requests.get,
    post: Optional[HttpGet] = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    title = (title or "").strip()
    author = (author or "").strip()
    isbn = re.sub(r"[^0-9Xx]", "", isbn or "")
    kind = "series" if kind == "series" else "book"
    category = (category or "").strip().lower()

    key = (normalize(title), normalize(author), isbn, kind, category)
    now = time.time()
    if use_cache and key in _cache and now - _cache[key][0] < CACHE_TTL_SECONDS:
        return _cache[key][1]

    jobs: list[tuple[str, Callable[[], Optional[dict]]]] = []
    is_manga = category in MANGA_CATEGORIES
    if kind == "book":
        jobs.append(("openlibrary", lambda: fetch_open_library(title, author, isbn, get)))
        jobs.append(("googlebooks", lambda: fetch_google_books(title, author, isbn, get)))
    # Pour une série, Open Library et Google Books ne notent que des tomes isolés : on les écarte
    # plutôt que d'afficher la note du premier tome comme si c'était celle de la série.
    if is_manga and title:
        jobs.append(("anilist", lambda: fetch_anilist(title, get, post)))
        jobs.append(("myanimelist", lambda: fetch_myanimelist(title, get)))

    ratings: list[dict] = []
    if title or isbn:
        with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
            futures = [(name, pool.submit(fn)) for name, fn in jobs]
            for name, fut in futures:
                try:
                    result = fut.result(timeout=TIMEOUT + 3)
                    if result:
                        ratings.append(result)
                except Exception as exc:  # une source en panne ne bloque pas les autres
                    logger.info("Notes externes : %s indisponible (%s)", name, exc)

    payload = {"ratings": ratings, "links": search_links(title, author) if title else []}
    # On ne garde pas en cache une réponse vide : une source en panne ne doit pas la figer 24 h
    if use_cache and ratings:
        if len(_cache) >= CACHE_MAX_ENTRIES:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (now, payload)
    return payload
