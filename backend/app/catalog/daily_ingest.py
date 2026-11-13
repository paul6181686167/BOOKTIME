"""Ajoute chaque jour de nouvelles fiches COMPLÈTES au noyau curé.

Sources œuvres : Wikidata, Open Library, Google Books, BnF (mélange).
Enrichissement : Wikipedia / Commons / Google Books / BnF (jaquette, photo, ISBN).
Rien n'est inventé.
"""
from __future__ import annotations

import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests

from ..static_wikidata.service import norm_title
from . import daily_store
from . import expanded
from ..series_verification import curated as curated_mod

logger = logging.getLogger(__name__)

UA = {
    "User-Agent": (
        "BooktimeCatalog/1.0 (https://github.com/paul6181686167/BOOKTIME; "
        "daily complete fiches)"
    ),
    "Accept": "application/json",
}
SPARQL_UA = {**UA, "Accept": "application/sparql-results+json"}
WD_SPARQL = "https://query.wikidata.org/sparql"
WIKI_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
PAGES_BY_CAT = {"manga": 192, "bd": 48, "roman": 280}
OL_W_COVER = re.compile(r"/b/(?:id|olid)/OL\d+W", re.I)
_QID_LABEL = re.compile(r"^Q\d+$", re.I)

NOVEL = "wd:Q1667921"
BOOK_SERIES = "wd:Q277759"
MANGA = "wd:Q21198342"
COMICS = "wd:Q14406742"
COMIC_BOOK = "wd:Q742169"
NOVEL_WORK = "wd:Q8261"
GRAPHIC_NOVEL = "wd:Q12833777"
COMIC_ALBUM = "wd:Q838796"
MANGA_ONESHOT = "wd:Q725377"

TYPE_GENRE = {
    "Q1667921": ("roman", "Roman"),
    "Q277759": ("roman", "Roman"),
    "Q21198342": ("manga", "Manga"),
    "Q14406742": ("bd", "BD"),
    "Q742169": ("bd", "BD"),
}
BOOK_TYPE_GENRE = {
    "Q8261": ("roman", "Roman"),
    "Q12833777": ("bd", "Roman graphique"),
    "Q838796": ("bd", "BD"),
    "Q725377": ("manga", "Manga"),
}

_wiki_cover_budget = 25
_author_lookup_budget = 0
_BOOK_PAGE = 100
_ingest_lock = threading.Lock()
_job_running = False
_job_last: dict[str, Any] | None = None
_active_window = 0
_WINDOW_KEY = "wd_window"
_FOCUS_KEY = "ingest_focus"
_DRY_KEY = "author_dry_streak"


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(os.getenv(name, str(default))), hi))
    except (TypeError, ValueError):
        return default


def ingest_focus() -> str:
    """authors = gisement photo+naissance ; works = séries et livres."""
    if not authors_ingest_enabled():
        return "works"
    n, _ = meta_pair(_FOCUS_KEY)
    return "works" if int(n) else "authors"


def authors_ingest_enabled() -> bool:
    """False = plus d'auteurs dans les lots (focus œuvres uniquement)."""
    raw = (os.getenv("CATALOG_ADD_AUTHORS") or "0").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return True


def remember_author_yield(n_authors: int) -> None:
    """3 lots pauvres en auteurs complets → on bascule sur séries/livres."""
    if not authors_ingest_enabled():
        meta_save_pair(_FOCUS_KEY, 1, 0)
        meta_save_pair(_DRY_KEY, 0, 0)
        return
    n_authors = int(n_authors or 0)
    if n_authors >= 1500:
        meta_save_pair(_FOCUS_KEY, 0, 0)
        meta_save_pair(_DRY_KEY, 0, 0)
        return
    dry, _ = meta_pair(_DRY_KEY)
    dry = dry + 1 if n_authors < 400 else 0
    meta_save_pair(_DRY_KEY, dry, 0)
    if dry >= 3:
        meta_save_pair(_FOCUS_KEY, 1, 0)


def daily_series_limit() -> int:
    default = 8000 if ingest_focus() == "works" else 400
    return _env_int("CATALOG_DAILY_SERIES", default, 1, 12000)


def daily_books_limit() -> int:
    return _env_int("CATALOG_DAILY_BOOKS", 10000, 0, 12000)


def author_fill_cap(remaining: int) -> int:
    """Auteurs seulement si CATALOG_ADD_AUTHORS est activé."""
    if not authors_ingest_enabled():
        return 0
    from .daily_authors import daily_authors_limit

    return min(daily_authors_limit(), max(0, int(remaining or 0)))


def daily_fiches_target() -> int:
    """Objectif : 10 000 fiches (séries + livres + auteurs) par lot."""
    return _env_int("CATALOG_DAILY_FICHES", 10000, 100, 15000)


def catalog_goal() -> int:
    """Plafond catalogue (séries + livres + auteurs) : on enchaîne les lots jusqu'ici."""
    return _env_int("CATALOG_FICHES_GOAL", 1000000, 1000, 2000000)


def catalog_fiche_total() -> int:
    """Une fiche = 1 série ou 1 livre ou 1 auteur quotidien."""
    from . import daily_authors, daily_store

    try:
        return int(daily_store.count() or 0) + int(daily_authors.count() or 0)
    except Exception:
        return 0


def window_salt() -> int:
    """Sel SPARQL du lot en cours (0 = première fenêtre, comme avant)."""
    return int(_active_window or 0)


def _window_coll():
    from ..db_config import database

    return database.db["catalog_ingest_meta"]


def meta_pair(key: str) -> tuple[int, int]:
    """Curseur persisté (n, offset) pour scanner Wikidata sans recouvrir les mêmes pages."""
    try:
        doc = _window_coll().find_one({"key": key}) or {}
        return int(doc.get("n") or 0), int(doc.get("offset") or 0)
    except Exception:
        return 0, 0


def meta_save_pair(key: str, n: int, offset: int) -> None:
    try:
        _window_coll().update_one(
            {"key": key},
            {"$set": {"key": key, "n": int(n), "offset": int(offset)}},
            upsert=True,
        )
    except Exception:
        pass


def take_window_index() -> int:
    """Compteur persisté : +1 à chaque lot, même si le jour n'a pas changé."""
    try:
        coll = _window_coll()
        doc = coll.find_one({"key": _WINDOW_KEY}) or {}
        n = int(doc.get("n") or 0) + 1
        coll.update_one(
            {"key": _WINDOW_KEY},
            {"$set": {"key": _WINDOW_KEY, "n": n}},
            upsert=True,
        )
        return n
    except Exception:
        return 0


def begin_ingest_window() -> int:
    """Nouvelle fenêtre Wikidata à chaque lot — pas seulement chaque jour."""
    global _active_window
    env = os.getenv("CATALOG_WD_WINDOW")
    if env is not None and str(env).strip() != "":
        try:
            _active_window = max(0, int(env))
            return _active_window
        except ValueError:
            pass
    yday = datetime.now(timezone.utc).timetuple().tm_yday
    total = catalog_fiche_total()
    n = take_window_index()
    _active_window = abs(yday * 100003 + total * 7919 + n * 104729)
    return _active_window


def daily_limit() -> int:
    """Compat : plafond de séries (le job ajoute aussi des livres individuels)."""
    return daily_series_limit()


def is_human_label(value: str | None) -> bool:
    """Titre ou nom lisible — pas un identifiant Wikidata (Q123) ni une chaîne vide."""
    t = (value or "").strip()
    if len(t) < 2 or is_qid_label(t):
        return False
    if re.search(r"[^\W\d_]", t, flags=re.UNICODE):
        return True
    return bool(re.fullmatch(r"\d{2,4}", t))


def is_qid_label(value: str | None) -> bool:
    return bool(_QID_LABEL.match((value or "").strip()))


def _purge_enabled() -> bool:
    if os.getenv("ENVIRONMENT", "").lower() == "test":
        return os.getenv("CATALOG_DAILY_PURGE", "").lower() in {"1", "true", "yes"}
    return True


def usable_cover(url: str | None) -> str:
    u = (url or "").strip()
    if not u or u.startswith("data:") or "undefined" in u:
        return ""
    if OL_W_COVER.search(u):
        return ""
    if u.startswith("http://"):
        u = "https://" + u[len("http://") :]
    return u


def pick_isbn(raw: Any) -> str:
    from .isbn_resolve import prefer_isbn

    return prefer_isbn([raw]) if raw else ""


def commons_url(filename: str) -> str:
    fn = (filename or "").strip().replace(" ", "_")
    if not fn:
        return ""
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(fn)}?width=400"


def blurb(
    title: str,
    n: int,
    series: str,
    author: str,
    year: Any,
    genre: str,
    lang: str,
    cat: str,
    *,
    standalone: bool = False,
) -> str:
    cat_fr = {"manga": "manga", "bd": "bande dessinée", "roman": "roman"}.get(cat, "livre")
    if standalone:
        head = f"« {title} » est un {cat_fr}"
        if author:
            head += f" de {author}"
    else:
        head = f"« {title} » est le tome {n} de la série {series}"
        if author:
            head += f", par {author}"
    bits = [x for x in (genre, lang, str(year) if year else "", cat_fr) if x]
    extra = f" ({', '.join(dict.fromkeys(bits))})" if bits else ""
    return head + extra + "."


def _sparql(query: str, timeout: int = 55) -> list[dict]:
    r = requests.get(
        WD_SPARQL,
        params={"query": query, "format": "json"},
        headers=SPARQL_UA,
        timeout=timeout,
    )
    r.raise_for_status()
    return (r.json().get("results") or {}).get("bindings") or []


def _lit(row: dict, key: str) -> str:
    return ((row.get(key) or {}).get("value") or "").strip()


def _qid(uri: str) -> str:
    return (uri or "").rsplit("/", 1)[-1]


def fetch_candidate_series(limit: int) -> list[dict[str, Any]]:
    """Séries Wikidata : récentes, puis page suivante du scan (curseur), jaquette d'abord."""
    year = datetime.now(timezone.utc).year - 15
    salt = window_salt()
    types = " ".join([NOVEL, BOOK_SERIES, MANGA, COMICS, COMIC_BOOK])
    recent_off = (salt * 80) % 50000
    recent_offset_clause = f"OFFSET {recent_off}" if recent_off else ""
    query_recent = f"""
SELECT DISTINCT ?series ?seriesLabel ?enLabel ?type ?img WHERE {{
  VALUES ?type {{ {types} }}
  ?series wdt:P31 ?type .
  ?series wdt:P577 ?date .
  FILTER(?date >= "{year}-01-01T00:00:00Z"^^xsd:dateTime)
  OPTIONAL {{ ?series wdt:P18 ?img. }}
  OPTIONAL {{
    ?series rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
{recent_offset_clause}
LIMIT {max(limit * 10, 120)}
"""
    rows = _sparql(query_recent)
    _, series_off = meta_pair("wd_series_scan")
    page = max(limit * 8, 200)
    query_rot = f"""
SELECT DISTINCT ?series ?seriesLabel ?enLabel ?type ?img WHERE {{
  VALUES ?type {{ {types} }}
  ?series wdt:P31 ?type .
  ?series wdt:P18 ?img .
  OPTIONAL {{
    ?series rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
OFFSET {series_off}
LIMIT {page}
"""
    try:
        extra = _sparql(query_rot)
        rows.extend(extra)
        nxt = series_off + page
        if not extra or len(extra) < 20:
            nxt = 0
        meta_save_pair("wd_series_scan", 0, nxt)
    except Exception as exc:
        logger.warning("Rotation Wikidata ignorée : %s", exc)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        qid = _qid(_lit(row, "series"))
        if not qid or qid in seen:
            continue
        seen.add(qid)
        type_qid = _qid(_lit(row, "type"))
        name = _lit(row, "seriesLabel") or ""
        if not is_human_label(name):
            continue
        img = _lit(row, "img")
        if img.startswith("http"):
            img = img.rsplit("/", 1)[-1]
        cat, genre = TYPE_GENRE.get(type_qid, ("roman", "Roman"))
        out.append(
            {
                "qid": qid,
                "name": name,
                "name_en": _lit(row, "enLabel") or None,
                "category": cat,
                "genre": genre,
                "cover_url": commons_url(img) if img else "",
            }
        )
    return out


def _parse_book_rows(rows: list[dict], seen: set[str] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = seen if seen is not None else set()
    for row in rows:
        qid = _qid(_lit(row, "work"))
        if not qid or qid in seen:
            continue
        seen.add(qid)
        type_qid = _qid(_lit(row, "type"))
        cat, genre = BOOK_TYPE_GENRE.get(type_qid, ("roman", "Roman"))
        name = _lit(row, "workLabel") or ""
        author = _lit(row, "authorLabel")
        if not is_human_label(name) or not is_human_label(author):
            continue
        img = _lit(row, "img")
        if img.startswith("http"):
            img = img.rsplit("/", 1)[-1]
        date = _lit(row, "date")
        year = None
        m = re.search(r"(\d{4})", date)
        if m:
            y = int(m.group(1))
            if 1400 <= y <= 2035:
                year = y
        ol = _lit(row, "ol")
        out.append(
            {
                "qid": qid,
                "name": name,
                "name_en": _lit(row, "enLabel") or None,
                "author": author,
                "author_qid": _qid(_lit(row, "author")),
                "category": cat,
                "genre": genre,
                "cover_url": commons_url(img) if img else "",
                "isbn": pick_isbn(_lit(row, "isbn")) or pick_isbn(_lit(row, "isbn10")),
                "ol_key": f"/works/{ol}" if ol else "",
                "year": year,
            }
        )
    return out


def _book_years(n: int, salt: int | None = None) -> list[int]:
    """Années récentes d'abord, décalées à chaque lot, puis une fenêtre historique."""
    if salt is None:
        salt = window_salt()
    now = datetime.now(timezone.utc).year
    yday = datetime.now(timezone.utc).timetuple().tm_yday
    years: list[int] = []
    seen: set[int] = set()
    recent = [y for y in range(now, now - 12, -1) if 1800 <= y <= now]
    rot = salt % max(len(recent), 1)
    for y in recent[rot:] + recent[:rot]:
        if y not in seen:
            seen.add(y)
            years.append(y)
    span = max(1, now - 1850)
    start = 1850 + ((yday * 17 + salt * 41) % span)
    y = start
    guard = 0
    while len(years) < n and guard < 400:
        guard += 1
        if 1800 <= y <= now and y not in seen:
            seen.add(y)
            years.append(y)
        y += 1
        if y > now:
            y = 1800
    return years[:n]


def _book_page_offset(year: int, salt: int) -> int:
    """Page SPARQL dans l'année (repli si pas de curseur)."""
    return ((salt * 53 + year * 13) % 80) * 50


def _books_sparql(year: int | None, limit: int, offset: int = 0) -> str:
    types = " ".join([NOVEL_WORK, GRAPHIC_NOVEL, COMIC_ALBUM, MANGA_ONESHOT])
    year_filter = f"FILTER(YEAR(?date) = {year})" if year else ""
    offset_clause = f"OFFSET {offset}" if offset else ""
    # P18 et labels auteur en OPTIONAL : les exiger faisait timeout Wikidata (0 livre).
    return f"""
SELECT DISTINCT ?work ?workLabel ?enLabel ?author ?authorLabel ?date ?isbn ?isbn10 ?ol ?img ?type WHERE {{
  VALUES ?type {{ {types} }}
  ?work wdt:P31 ?type .
  ?work wdt:P50 ?author .
  ?work wdt:P577 ?date .
  {year_filter}
  FILTER NOT EXISTS {{ ?work wdt:P179 ?serie . }}
  OPTIONAL {{ ?work wdt:P18 ?img. }}
  OPTIONAL {{
    ?work rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  OPTIONAL {{ ?work wdt:P212 ?isbn. }}
  OPTIONAL {{ ?work wdt:P957 ?isbn10. }}
  OPTIONAL {{ ?work wdt:P648 ?ol. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
{offset_clause}
LIMIT {min(max(limit, 20), 120)}
"""


def _fetch_books_page(year: int | None, limit: int, offset: int = 0) -> list[dict[str, Any]]:
    try:
        rows = _sparql(_books_sparql(year, limit, offset), timeout=50)
    except Exception as exc:
        logger.warning("SPARQL livres %s échoué : %s", year if year else f"offset={offset}", exc)
        return []
    return _parse_book_rows(rows)


def fetch_candidate_books(limit: int) -> list[dict[str, Any]]:
    """Livres : Wikidata + Open Library + Google Books + BnF (mélange unique)."""
    if limit <= 0:
        return []
    salt = window_salt()
    now = datetime.now(timezone.utc).year
    span = max(1, now - 1800 + 1)
    n, off = meta_pair("wd_book_scan")
    start = 1800 + (int(n) % span)
    pages = max(20, min(80, (limit + _BOOK_PAGE - 1) // _BOOK_PAGE + 8))
    years: list[int] = []
    y = start
    for _ in range(pages):
        years.append(y)
        y += 1
        if y > now:
            y = 1800
    wd: list[dict[str, Any]] = []
    seen_wd: set[str] = set()

    def _absorb_wd(batch: list[dict[str, Any]]) -> None:
        for cand in batch:
            qid = cand.get("qid")
            if not qid or qid in seen_wd:
                continue
            seen_wd.add(qid)
            wd.append(cand)

    for i in range(0, len(years), 4):
        if len(wd) >= limit:
            break
        chunk = years[i : i + 4]
        with ThreadPoolExecutor(max_workers=min(4, len(chunk))) as pool:
            batches = list(
                pool.map(
                    lambda yr: _fetch_books_page(yr, _BOOK_PAGE, off),
                    chunk,
                )
            )
        for batch in batches:
            _absorb_wd(batch)
            if len(wd) >= limit:
                break

    if len(wd) >= min(limit, 80):
        meta_save_pair("wd_book_scan", n, off + _BOOK_PAGE)
    else:
        meta_save_pair("wd_book_scan", n + pages, 0)

    if len(wd) < limit:
        yday = datetime.now(timezone.utc).timetuple().tm_yday
        offset = (yday * 23 + salt * 97) % 80000
        _absorb_wd(_fetch_books_page(None, min(_BOOK_PAGE, limit - len(wd) + 80), offset))

    ext: list[dict[str, Any]] = []
    if os.getenv("ENVIRONMENT", "").lower() != "test":
        ext_cap = max(120, min(limit, max(limit // 2, limit - len(wd))))
        for fetch in (
            fetch_candidate_books_openlibrary,
            fetch_candidate_books_google,
            fetch_candidate_books_bnf,
        ):
            if len(ext) >= ext_cap:
                break
            try:
                ext.extend(fetch(ext_cap - len(ext)))
            except Exception as exc:
                logger.warning("Source livres externe échouée (%s) : %s", fetch.__name__, exc)

    # Mélange : ~55% Wikidata puis sources externes, puis reste WD.
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    wd_first = wd[: max(1, int(limit * 0.55))]

    def _push(batch: list[dict[str, Any]]) -> None:
        for cand in batch:
            if len(out) >= limit:
                return
            qid = cand.get("qid")
            if not qid or qid in seen:
                continue
            seen.add(qid)
            out.append(cand)

    _push(wd_first)
    _push(ext)
    _push(wd[len(wd_first) :])
    return out


_OL_BOOK_SUBJECTS = (
    "fiction",
    "roman",
    "fantasy",
    "science_fiction",
    "bande dessinée",
    "manga",
    "mystery",
    "historical fiction",
    "young adult",
    "poetry",
    "thriller",
    "romance",
    "horror",
    "biography",
    "children",
    "literature",
    "detective",
    "adventure",
    "classics",
    "short stories",
    "drama",
    "comics",
    "graphic novels",
    "science fiction",
    "littérature française",
    "roman policier",
)


def _book_cat_from_subjects(subjects: list[str]) -> tuple[str, str]:
    joined = " ".join(subjects).lower()
    if "manga" in joined:
        return "manga", "Manga"
    if any(x in joined for x in ("bande dessinée", "comic", "comics", "graphic novel", "bd")):
        return "bd", "BD"
    return "roman", "Roman"


def fetch_candidate_books_openlibrary(limit: int) -> list[dict[str, Any]]:
    """Livres Open Library — titre+auteur requis, jaquette optionnelle."""
    if limit <= 0:
        return []
    from .isbn_resolve import _ol_cover_url

    salt = window_salt()
    n, off = meta_pair("ol_book_scan")
    page_size = 80
    pages = min(10, max(2, (int(limit) + page_size - 1) // page_size))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(pages):
        if len(out) >= limit:
            break
        subject = _OL_BOOK_SUBJECTS[(salt + n + page) % len(_OL_BOOK_SUBJECTS)]
        offset = ((int(off) + page) * page_size) % 40000
        params: dict[str, Any] = {
            "q": f"subject:{subject}",
            "limit": min(max(int(limit) - len(out), 20), page_size),
            "offset": offset,
            "fields": "key,title,author_name,isbn,cover_i,first_publish_year,language,subject",
        }
        # Alterner FR / toutes langues / EN pour élargir le gisement.
        lang_mode = (salt + page) % 3
        if lang_mode == 0:
            params["language"] = "fre"
        elif lang_mode == 1:
            params["language"] = "eng"
        try:
            r = requests.get(
                "https://openlibrary.org/search.json",
                params=params,
                timeout=12,
                headers=UA,
            )
            if r.status_code != 200:
                continue
            docs = (r.json() or {}).get("docs") or []
        except Exception as exc:
            logger.warning("Open Library livres échoué : %s", exc)
            continue
        for doc in docs:
            if not isinstance(doc, dict):
                continue
            title = (doc.get("title") or "").strip()
            authors = [a for a in (doc.get("author_name") or []) if is_human_label(a)]
            cover = _ol_cover_url(doc.get("cover_i")) or ""
            key = (doc.get("key") or "").rstrip("/").rsplit("/", 1)[-1]
            if not key.startswith("OL") or key in seen:
                continue
            if not is_human_label(title) or not authors:
                continue
            seen.add(key)
            subjects = [str(s).lower() for s in (doc.get("subject") or [])[:8]]
            cat, genre = _book_cat_from_subjects(subjects)
            year = doc.get("first_publish_year")
            try:
                year = int(year) if year else None
            except (TypeError, ValueError):
                year = None
            isbn = pick_isbn(doc.get("isbn") or [])
            if not cover and isbn:
                cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            out.append(
                {
                    "qid": key,
                    "name": title,
                    "name_en": title,
                    "author": authors[0],
                    "author_qid": "",
                    "category": cat,
                    "genre": genre,
                    "cover_url": cover if usable_cover(cover) else "",
                    "isbn": isbn or "",
                    "ol_key": f"/works/{key}" if key.endswith("W") else doc.get("key") or "",
                    "year": year if year and 1400 <= year <= 2035 else None,
                    "source": "openlibrary",
                }
            )
            if len(out) >= limit:
                break
    meta_save_pair("ol_book_scan", n + 1, off + pages)
    return out


_GB_QUERIES = (
    "subject:fiction",
    "subject:fantasy",
    "subject:science fiction",
    "subject:mystery",
    "subject:romance",
    "subject:thriller",
    "subject:comics",
    "subject:manga",
    "subject:poetry",
    "subject:biography",
    "subject:juvenile fiction",
    "subject:historical fiction",
    'subject:"bande dessinée"',
    "inauthor:roman",
)


def fetch_candidate_books_google(limit: int) -> list[dict[str, Any]]:
    """Livres Google Books — 3e source (clé API optionnelle)."""
    if limit <= 0:
        return []
    from .isbn_resolve import GB_URL

    salt = window_salt()
    n, off = meta_pair("gb_book_scan")
    page_size = 40
    pages = min(8, max(1, (int(limit) + page_size - 1) // page_size))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    key = (os.getenv("GOOGLE_BOOKS_API_KEY") or "").strip()
    for page in range(pages):
        if len(out) >= limit:
            break
        q = _GB_QUERIES[(salt + n + page) % len(_GB_QUERIES)]
        start = (int(off) + page * page_size) % 800
        params: dict[str, Any] = {
            "q": q,
            "startIndex": start,
            "maxResults": min(page_size, max(10, limit - len(out))),
            "printType": "books",
            "orderBy": "newest" if (salt + page) % 2 == 0 else "relevance",
        }
        if (salt + page) % 3 == 0:
            params["langRestrict"] = "fr"
        if key:
            params["key"] = key
        try:
            r = requests.get(GB_URL, params=params, timeout=12, headers=UA)
            if r.status_code in (403, 429):
                logger.warning("Google Books limité (%s)", r.status_code)
                break
            if r.status_code != 200:
                continue
            items = (r.json() or {}).get("items") or []
        except Exception as exc:
            logger.warning("Google Books livres échoué : %s", exc)
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            info = item.get("volumeInfo") or {}
            title = (info.get("title") or "").strip()
            authors = [a for a in (info.get("authors") or []) if is_human_label(a)]
            if not is_human_label(title) or not authors:
                continue
            gid = str(item.get("id") or "").strip()
            if not gid or gid in seen:
                continue
            seen.add(gid)
            ids = info.get("industryIdentifiers") or []
            isbn = pick_isbn([x.get("identifier") for x in ids if isinstance(x, dict)])
            image = info.get("imageLinks") or {}
            cover = (
                usable_cover(image.get("thumbnail"))
                or usable_cover(image.get("smallThumbnail"))
                or ""
            )
            cover = usable_cover(cover)
            if not cover and isbn:
                cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            cats = [str(c).lower() for c in (info.get("categories") or [])[:6]]
            cat, genre = _book_cat_from_subjects(cats)
            year = None
            raw_date = str(info.get("publishedDate") or "")
            if len(raw_date) >= 4 and raw_date[:4].isdigit():
                try:
                    y = int(raw_date[:4])
                    year = y if 1400 <= y <= 2035 else None
                except ValueError:
                    year = None
            out.append(
                {
                    "qid": f"GB:{gid}",
                    "name": title,
                    "name_en": title,
                    "author": authors[0],
                    "author_qid": "",
                    "category": cat,
                    "genre": genre,
                    "cover_url": cover if usable_cover(cover) else "",
                    "isbn": isbn or "",
                    "ol_key": "",
                    "year": year,
                    "source": "google_books",
                }
            )
            if len(out) >= limit:
                break
    meta_save_pair("gb_book_scan", n + 1, off + pages * page_size)
    return out


_BNF_QUERIES = (
    'bib.title all "roman"',
    'bib.title all "nouvelle"',
    'bib.title all "poésie"',
    'bib.title all "bande dessinée"',
    'bib.title all "manga"',
    'bib.title all "thriller"',
    'bib.title all "policier"',
    'bib.title all "fantasy"',
    'bib.author all "a" and bib.doctype any "a"',
)


def fetch_candidate_books_bnf(limit: int) -> list[dict[str, Any]]:
    """Livres BnF (SRU) — 4e source, surtout français."""
    if limit <= 0:
        return []
    import xml.etree.ElementTree as ET

    from .isbn_resolve import BNF_SRU
    from ..openlibrary.isbn_lookup import _DC, _bnf_text

    salt = window_salt()
    n, off = meta_pair("bnf_book_scan")
    page_size = 20
    pages = min(6, max(1, (int(limit) + page_size - 1) // page_size))
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(pages):
        if len(out) >= limit:
            break
        query = _BNF_QUERIES[(salt + n + page) % len(_BNF_QUERIES)]
        start = 1 + ((int(off) + page * page_size) % 2000)
        try:
            r = requests.get(
                BNF_SRU,
                params={
                    "version": "1.2",
                    "operation": "searchRetrieve",
                    "query": query,
                    "recordSchema": "dublincore",
                    "maximumRecords": str(min(page_size, max(5, limit - len(out)))),
                    "startRecord": str(start),
                },
                timeout=12,
                headers={**UA, "Accept": "application/xml"},
            )
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
        except Exception as exc:
            logger.warning("BnF livres échoué : %s", exc)
            continue
        for dc in root.findall(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc"):
            title = _bnf_text(dc.find(f"{_DC}title")).split(" / ")[0].strip()
            creators = [
                _bnf_text(c).split("(")[0].strip()
                for c in dc.findall(f"{_DC}creator")
            ]
            authors = [a for a in creators if is_human_label(a)]
            if not is_human_label(title) or not authors:
                continue
            idents = [_bnf_text(i) for i in dc.findall(f"{_DC}identifier")]
            isbn = pick_isbn(idents)
            ark = next((x for x in idents if "ark:" in x or x.startswith("http")), "")
            qid = f"BNF:{(isbn or ark or title)[:80]}"
            if qid in seen:
                continue
            seen.add(qid)
            types = [_bnf_text(t).lower() for t in dc.findall(f"{_DC}type")]
            subjects = [_bnf_text(s).lower() for s in dc.findall(f"{_DC}subject")]
            cat, genre = _book_cat_from_subjects(types + subjects)
            year = None
            for d in dc.findall(f"{_DC}date"):
                raw = _bnf_text(d)
                m = re.search(r"(1[5-9]\d{2}|20[0-3]\d)", raw)
                if m:
                    year = int(m.group(1))
                    break
            cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn else ""
            out.append(
                {
                    "qid": qid,
                    "name": title,
                    "name_en": title,
                    "author": authors[0],
                    "author_qid": "",
                    "category": cat,
                    "genre": genre,
                    "cover_url": cover if usable_cover(cover) else "",
                    "isbn": isbn or "",
                    "ol_key": "",
                    "year": year,
                    "source": "bnf",
                }
            )
            if len(out) >= limit:
                break
    meta_save_pair("bnf_book_scan", n + 1, off + pages * page_size)
    return out


def fetch_works(qid: str) -> list[dict[str, Any]]:
    query = f"""
SELECT ?work ?frLabel ?enLabel ?date ?isbn ?isbn10 ?ol ?author ?authorLabel WHERE {{
  {{ ?work wdt:P179 wd:{qid} . }}
  UNION {{ wd:{qid} wdt:P527 ?work . }}
  OPTIONAL {{
    ?work rdfs:label ?frLabel .
    FILTER(LANG(?frLabel) = "fr")
  }}
  OPTIONAL {{
    ?work rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  OPTIONAL {{ ?work wdt:P577 ?date. }}
  OPTIONAL {{ ?work wdt:P212 ?isbn. }}
  OPTIONAL {{ ?work wdt:P957 ?isbn10. }}
  OPTIONAL {{ ?work wdt:P648 ?ol. }}
  OPTIONAL {{
    ?work wdt:P50 ?author .
    ?author rdfs:label ?authorLabel .
    FILTER(LANG(?authorLabel) = "en" || LANG(?authorLabel) = "fr")
  }}
}}
LIMIT 80
"""
    rows = _sparql(query)
    works: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        title = _lit(row, "frLabel") or _lit(row, "enLabel")
        if not is_human_label(title) or title in seen:
            continue
        seen.add(title)
        date = _lit(row, "date")
        year = None
        m = re.search(r"(\d{4})", date)
        if m:
            year = int(m.group(1))
        ol = _lit(row, "ol")
        author = _lit(row, "authorLabel")
        works.append(
            {
                "title": title,
                "title_en": _lit(row, "enLabel"),
                "published_year": year if year and 1400 <= year <= 2035 else None,
                "isbn": pick_isbn(_lit(row, "isbn")) or pick_isbn(_lit(row, "isbn10")),
                "ol_key": f"/works/{ol}" if ol and ol.endswith("W") else (f"/works/{ol}" if ol else ""),
                "author": author if is_human_label(author) else "",
                "author_qid": _qid(_lit(row, "author")),
                "work_qid": _qid(_lit(row, "work")),
            }
        )
    works.sort(key=lambda w: (w.get("published_year") or 9999, w["title"].lower()))
    return works


def fetch_entity_author(qid: str) -> tuple[str, str]:
    """Auteur P50 de l'entité Wikidata (série ou livre), ou ('', '')."""
    qid = (qid or "").strip()
    if not qid.startswith("Q"):
        return "", ""
    query = f"""
SELECT ?author ?authorLabel WHERE {{
  wd:{qid} wdt:P50 ?author .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
LIMIT 1
"""
    try:
        rows = _sparql(query, timeout=20)
    except Exception as exc:
        logger.debug("Auteur P50 %s : %s", qid, exc)
        return "", ""
    if not rows:
        return "", ""
    row = rows[0]
    name = _lit(row, "authorLabel")
    if not is_human_label(name):
        return "", ""
    return name, _qid(_lit(row, "author"))


def ol_title_author(title: str, title_en: str | None = None) -> str:
    """Premier auteur Open Library pour un titre proche, ou ''."""
    from .isbn_resolve import title_close

    for raw in (title, title_en):
        q = (raw or "").strip()
        if len(q) < 3:
            continue
        try:
            r = requests.get(
                "https://openlibrary.org/search.json",
                params={"title": q, "limit": 5, "fields": "title,author_name"},
                timeout=8,
                headers=UA,
            )
            if r.status_code != 200:
                continue
            for doc in (r.json() or {}).get("docs") or []:
                if not title_close(q, doc.get("title") or ""):
                    continue
                for a in doc.get("author_name") or []:
                    if is_human_label(a):
                        return a
        except Exception as exc:
            logger.debug("Auteur OL titre échoué %s: %s", q, exc)
    return ""


def fill_missing_author(cand: dict[str, Any], works: list[dict[str, Any]] | None) -> None:
    """Complète un auteur réel (P50 Wikidata, puis Open Library) avant d'ignorer."""
    global _author_lookup_budget
    works = works or []
    existing = (cand.get("author") or "").strip()
    if not is_human_label(existing):
        existing = next((w.get("author") for w in works if is_human_label(w.get("author"))), "") or ""
    if is_human_label(existing):
        cand["author"] = existing
        for w in works:
            if not is_human_label(w.get("author")):
                w["author"] = existing
                if cand.get("author_qid") and not w.get("author_qid"):
                    w["author_qid"] = cand.get("author_qid")
        return
    if _author_lookup_budget <= 0:
        return
    _author_lookup_budget -= 1
    name, aqid = fetch_entity_author(cand.get("qid") or "")
    if not is_human_label(name):
        name = ol_title_author(cand.get("name") or "", cand.get("name_en"))
        aqid = ""
    if not is_human_label(name):
        return
    cand["author"] = name
    if aqid:
        cand["author_qid"] = aqid
    if not works:
        return
    for w in works:
        if not is_human_label(w.get("author")):
            w["author"] = name
            if aqid:
                w["author_qid"] = aqid


def wiki_cover(name: str, name_en: str | None) -> str:
    global _wiki_cover_budget
    if _wiki_cover_budget <= 0:
        return ""
    _wiki_cover_budget -= 1
    session = requests.Session()
    session.headers.update(UA)
    for lang, title in (("fr", name), ("en", name_en or name)):
        if not title:
            continue
        try:
            r = session.get(
                WIKI_SUMMARY.format(lang=lang, title=quote(title.replace(" ", "_"))),
                timeout=8,
            )
            if r.status_code != 200:
                continue
            thumb = ((r.json() or {}).get("thumbnail") or {}).get("source") or ""
            if "/revision/" in thumb:
                thumb = thumb.split("/revision/")[0]
            cover = usable_cover(thumb)
            if cover:
                return cover
        except Exception:
            continue
    return ""


def build_complete_entry(
    cand: dict[str, Any],
    works: list[dict[str, Any]],
    *,
    min_volumes: int = 2,
    standalone: bool = False,
) -> dict[str, Any] | None:
    """None sans titre ou auteur réels. Jaquette optionnelle : needs_cover à compléter plus tard."""
    if not is_human_label(cand.get("name")):
        return None
    titled = [w for w in works if is_human_label(w.get("title"))]
    if len(titled) < min_volumes:
        return None
    author = next((w.get("author") for w in titled if is_human_label(w.get("author"))), "") or ""
    if not is_human_label(author):
        return None
    author_qid = (cand.get("author_qid") or "") or next(
        (w.get("author_qid") for w in titled if w.get("author_qid")),
        "",
    )
    cover = usable_cover(cand.get("cover_url")) or wiki_cover(cand.get("name") or "", cand.get("name_en"))
    if not cover:
        for w in titled:
            isbn = pick_isbn(w.get("isbn"))
            if isbn:
                cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
                break
    needs_cover = not bool(cover)
    cover = cover or ""
    cat = cand.get("category") or "roman"
    genre = cand.get("genre") or "Roman"
    lang = "français"
    if cand.get("name_en") and not re.search(r"[éèàùçîô]", cand.get("name") or ""):
        # nom uniquement ASCII : souvent EN ; on garde FR si le label SPARQL est FR
        if cand.get("name") == cand.get("name_en"):
            lang = "anglais"
    first_year = next((w.get("published_year") for w in titled if w.get("published_year")), None)
    volume_titles: dict[str, str] = {}
    volume_titles_en: dict[str, str] = {}
    volume_details: dict[str, dict] = {}
    running_year = first_year
    for i, w in enumerate(titled, start=1):
        vn = str(i)
        title = w["title"]
        volume_titles[vn] = title
        en = (w.get("title_en") or "").strip()
        if en and en != title:
            volume_titles_en[vn] = en
        year = w.get("published_year") or running_year or first_year or 2010
        running_year = year
        detail = {
            "author": (w.get("author") or author).strip(),
            "published_year": year,
            "genre": genre,
            "language": lang,
            "cover_url": cover,
            "pages": PAGES_BY_CAT.get(cat, 280),
            "description": blurb(
                title, i, cand["name"], author, year, genre, lang, cat, standalone=standalone
            ),
        }
        isbn = pick_isbn(w.get("isbn"))
        if not isbn:
            from .isbn_resolve import resolve_isbn

            isbn = resolve_isbn(
                title=title,
                author=(w.get("author") or author).strip(),
                title_en=en,
                ol_key=w.get("ol_key") or "",
            )
        if isbn:
            detail["isbn"] = isbn
            if not usable_cover(detail.get("cover_url")):
                detail["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        if w.get("ol_key"):
            detail["ol_key"] = w["ol_key"]
        if w.get("work_qid"):
            detail["work_qid"] = w["work_qid"]
        volume_details[vn] = detail
    name = cand["name"]
    key = (norm_title(name).replace(" ", "_")[:80] or cand["qid"])
    return {
        "key": key,
        "qid": cand["qid"],
        "name": name,
        "name_en": cand.get("name_en") or None,
        "authors": [author],
        "author_qid": author_qid or None,
        "category": cat,
        "type": "standalone" if standalone else "daily",
        "volumes": len(volume_titles),
        "volume_titles": volume_titles,
        "volume_details": volume_details,
        "first_published": str(first_year) if first_year else str(running_year or ""),
        "status": "completed" if standalone or len(titled) < 20 else "ongoing",
        "wikidata_qid": cand["qid"],
        "cover_url": cover,
        "language": lang,
        "genre": genre,
        "source": "daily",
        "needs_cover": needs_cover,
        **({"volume_titles_en": volume_titles_en} if volume_titles_en else {}),
    }


def purge_qid_named_daily() -> int:
    """Retire les fiches quotidiennes dont le titre n'est qu'un identifiant Wikidata."""
    if not _purge_enabled():
        return 0
    n = 0
    try:
        coll = daily_store._coll()
        for doc in coll.find({"source": "daily"}, {"qid": 1, "name": 1}) or []:
            if not is_qid_label((doc or {}).get("name")):
                continue
            qid = (doc or {}).get("qid")
            if not qid:
                continue
            coll.delete_one({"qid": qid, "source": "daily"})
            n += 1
    except Exception as exc:
        logger.warning("Purge titres QID : %s", exc)
    return n


def existing_qids() -> set[str]:
    try:
        from .seed import ensure_seeded

        ensure_seeded()
    except Exception:
        pass
    return set(daily_store.known_qids())


def existing_names() -> set[str]:
    try:
        from .seed import ensure_seeded

        ensure_seeded()
    except Exception:
        pass
    return set(daily_store.known_names())


def _name_keys(cand: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for raw in (cand.get("name"), cand.get("name_en")):
        n = norm_title(raw or "")
        if n and n not in seen:
            seen.add(n)
            keys.append(n)
    return keys


def _already_catalogued(
    cand: dict[str, Any], known: set[str], names: set[str]
) -> bool:
    """QID Mongo, nom déjà en base, ou série de l'overlay (One Piece, etc.)."""
    qid = cand.get("qid") or ""
    if qid and qid in known:
        return True
    for n in _name_keys(cand):
        if n in names:
            return True
    try:
        if curated_mod.has_canonical(cand.get("name") or ""):
            return True
        en = (cand.get("name_en") or "").strip()
        if en and en != (cand.get("name") or "") and curated_mod.has_canonical(en):
            return True
    except Exception:
        pass
    return False


def _persist(
    entry: dict[str, Any],
    known: set[str],
    added: list[str],
    hints: list[dict[str, Any]] | None = None,
    names: set[str] | None = None,
) -> int:
    daily_store.upsert_series(entry)
    known.add(entry["qid"])
    if names is not None:
        names.update(_name_keys(entry))
    added.append(entry["name"])
    if hints is not None:
        authors = [a for a in (entry.get("authors") or []) if a]
        hints.append(
            {
                "name": authors[0] if authors else "",
                "author": authors[0] if authors else "",
                "qid": entry.get("author_qid") or "",
                "author_qid": entry.get("author_qid") or "",
                "title": entry.get("name"),
                "work_qid": entry.get("qid"),
                "cover_url": entry.get("cover_url"),
                "kind": "book" if entry.get("type") == "standalone" else "series",
            }
        )
    return int(entry.get("volumes") or 0)


def _ingest_series(
    cap: int,
    known: set[str],
    hints: list[dict[str, Any]] | None = None,
    names: set[str] | None = None,
) -> tuple[list[str], int, int]:
    added: list[str] = []
    skipped = 0
    fiches = 0
    names = names if names is not None else set()
    if cap <= 0:
        return added, skipped, fiches
    try:
        candidates = fetch_candidate_series(cap)
    except Exception as exc:
        logger.warning("Ingest quotidien : SPARQL séries échoué : %s", exc)
        return added, skipped, fiches
    from . import daily_pending

    candidates.sort(key=lambda c: 0 if usable_cover(c.get("cover_url")) else 1)
    blocked = daily_pending.blocked_qids()
    fresh = []
    for c in candidates:
        qid = c.get("qid") or ""
        if not qid or _already_catalogued(c, known, names) or qid in blocked:
            skipped += 1
            continue
        fresh.append(c)
    max_fetch = _env_int("CATALOG_SERIES_WORK_FETCH", 120, 20, 800)
    to_load = fresh[: min(cap + 30, max_fetch)]
    skipped += max(0, len(fresh) - len(to_load))

    def _load(cand: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
        try:
            return cand, fetch_works(cand["qid"])
        except Exception:
            return cand, None

    chunk = 24
    for i in range(0, len(to_load), chunk):
        if len(added) >= cap:
            break
        batch = to_load[i : i + chunk]
        workers = min(6, max(1, len(batch)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = [pool.submit(_load, cand) for cand in batch]
            for fut in as_completed(futs):
                if len(added) >= cap:
                    break
                cand, works = fut.result()
                if _already_catalogued(cand, known, names):
                    skipped += 1
                    continue
                if works is None:
                    daily_pending.remember_skip(cand.get("qid") or "", "works_timeout")
                    skipped += 1
                    continue
                fill_missing_author(cand, works)
                entry = build_complete_entry(cand, works)
                if not entry:
                    entry = build_complete_entry(cand, works, min_volumes=1, standalone=True)
                if not entry:
                    kept = daily_pending.remember(
                        "series", cand, reason="incomplete", works=works, known=known, names=names
                    )
                    if not kept:
                        daily_pending.remember_skip(cand.get("qid") or "", "incomplete")
                    skipped += 1
                    continue
                fiches += _persist(entry, known, added, hints, names)
    return added, skipped, fiches


def _ingest_books(
    cap: int,
    known: set[str],
    hints: list[dict[str, Any]] | None = None,
    names: set[str] | None = None,
) -> tuple[list[str], int, int]:
    added: list[str] = []
    skipped = 0
    fiches = 0
    names = names if names is not None else set()
    if cap <= 0:
        return added, skipped, fiches
    try:
        candidates = fetch_candidate_books(cap)
    except Exception as exc:
        logger.warning("Ingest quotidien : SPARQL livres échoué : %s", exc)
        return added, skipped, fiches
    from . import daily_pending

    blocked = daily_pending.blocked_qids()
    for cand in candidates:
        if fiches >= cap:
            break
        qid = cand.get("qid") or ""
        if not qid or _already_catalogued(cand, known, names) or qid in blocked:
            skipped += 1
            continue
        author = (cand.get("author") or "").strip()
        if not is_human_label(author):
            fill_missing_author(cand, [])
            author = (cand.get("author") or "").strip()
        if not is_human_label(author) or not is_human_label(cand.get("name")):
            daily_pending.remember_skip(qid, "no_author")
            skipped += 1
            continue
        work = {
            "title": cand.get("name") or "",
            "title_en": cand.get("name_en") or "",
            "author": author,
            "published_year": cand.get("year"),
            "isbn": cand.get("isbn") or "",
            "ol_key": cand.get("ol_key") or "",
            "work_qid": qid,
            "author_qid": cand.get("author_qid") or "",
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            daily_pending.remember(
                "book", cand, reason="incomplete", works=[work], known=known, names=names
            )
            skipped += 1
            continue
        fiches += _persist(entry, known, added, hints, names)
    return added, skipped, fiches


def complete_missing_covers(cap: int = 400) -> int:
    """Complète les jaquettes des fiches déjà cataloguées (titre+auteur, sans image)."""
    from . import daily_pending, daily_store

    filled = 0
    if cap <= 0:
        return 0
    for doc in daily_store.needing_cover(cap):
        if usable_cover(doc.get("cover_url")):
            doc["needs_cover"] = False
            daily_store.upsert_series(doc)
            filled += 1
            continue
        details = doc.get("volume_details") if isinstance(doc.get("volume_details"), dict) else {}
        works: list[dict[str, Any]] = []
        for vn in sorted(details, key=lambda k: int(k) if str(k).isdigit() else 0):
            d = details.get(vn) or {}
            works.append(
                {
                    "title": (doc.get("volume_titles") or {}).get(vn) or doc.get("name") or "",
                    "author": d.get("author") or (doc.get("authors") or [""])[0],
                    "isbn": d.get("isbn") or "",
                    "ol_key": d.get("ol_key") or "",
                }
            )
        if not works:
            authors = [a for a in (doc.get("authors") or []) if a]
            works = [{"title": doc.get("name") or "", "author": authors[0] if authors else ""}]
        cand = {
            "qid": doc.get("qid"),
            "name": doc.get("name"),
            "name_en": doc.get("name_en"),
            "author": (doc.get("authors") or [""])[0] if doc.get("authors") else "",
            "cover_url": doc.get("cover_url") or "",
            "isbn": (works[0].get("isbn") if works else "") or "",
            "ol_key": (works[0].get("ol_key") if works else "") or "",
        }
        daily_pending.enrich_work_candidate(cand, works)
        cover = usable_cover(cand.get("cover_url"))
        if not cover:
            cover = wiki_cover(doc.get("name") or "", doc.get("name_en"))
        if not cover:
            continue
        doc["cover_url"] = cover
        doc["needs_cover"] = False
        for d in details.values():
            if isinstance(d, dict) and not usable_cover(d.get("cover_url")):
                d["cover_url"] = cover
        daily_store.upsert_series(doc)
        filled += 1
    return filled


def run_daily_ingest(
    *,
    limit: int | None = None,
    books_limit: int | None = None,
    authors_limit: int | None = None,
) -> dict[str, Any]:
    """Ajoute séries + livres + auteurs complets. Idempotent (qid déjà connu ignoré)."""
    global _wiki_cover_budget, _author_lookup_budget, _job_last, _job_running
    if not _ingest_lock.acquire(blocking=False):
        busy = {
            "status": "busy",
            "added": 0,
            "added_series": 0,
            "added_books": 0,
            "added_authors": 0,
            "fiches": 0,
            "skipped": 0,
            "names": [],
        }
        if _job_last:
            busy["last"] = {k: _job_last[k] for k in ("added", "fiches", "status") if k in _job_last}
        return busy
    _job_running = True
    try:
        test_env = os.getenv("ENVIRONMENT", "").lower() == "test"
        _wiki_cover_budget = 0 if test_env else 300
        _author_lookup_budget = 0 if test_env else 80
        from .isbn_resolve import reset_budget, reset_cover_budget
        from . import daily_pending

        isbn_default = 0 if test_env else 800
        cover_default = 0 if test_env else 1500
        reset_budget(_env_int("CATALOG_ISBN_LOOKUPS", isbn_default, 0, 2000))
        reset_cover_budget(_env_int("CATALOG_COVER_LOOKUPS", cover_default, 0, 4000))
        daily_pending.reset_wd_budget(0 if test_env else _env_int("CATALOG_PENDING_WD", 400, 0, 800))
        if not test_env:
            _wiki_cover_budget = _env_int("CATALOG_WIKI_COVERS", 400, 0, 800)
            _author_lookup_budget = _env_int("CATALOG_AUTHOR_LOOKUPS", 80, 0, 400)
        purged_series = purge_qid_named_daily()
        from .daily_authors import daily_authors_limit, ingest_authors, purge_qid_named_authors

        purged_authors = purge_qid_named_authors()
        total = catalog_fiche_total()
        goal = catalog_goal()
        remaining_goal = max(0, goal - total)
        if limit is None and books_limit is None and authors_limit is None:
            if remaining_goal <= 0:
                result = {
                    "status": "ok",
                    "added": 0,
                    "added_series": 0,
                    "added_books": 0,
                    "added_authors": 0,
                    "fiches": 0,
                    "tomes": 0,
                    "target_fiches": 0,
                    "skipped": 0,
                    "names": [],
                    "author_names": [],
                    "purged": purged_series + purged_authors,
                    "catalog_fiches": total,
                    "goal_fiches": goal,
                    "pending_fiches": daily_pending.count(),
                    "recovered": 0,
                }
                _job_last = result
                logger.info(
                    "Ingest quotidien : objectif atteint (%d/%d), rien à ajouter",
                    total,
                    goal,
                )
                return result
            target = min(daily_fiches_target(), remaining_goal)
        else:
            target = daily_fiches_target()
        wd_window = begin_ingest_window()
        logger.info("Ingest quotidien : fenêtre Wikidata %d, cible %d", wd_window, target)
        known = existing_qids()
        names = existing_names()
        author_hints: list[dict[str, Any]] = []
        recovered = {
            "added_series": 0,
            "added_books": 0,
            "added_authors": 0,
            "fiches": 0,
            "tomes": 0,
            "names": [],
            "author_names": [],
        }

        def _merge_recovered(part: dict[str, Any]) -> None:
            recovered["added_series"] += int(part.get("added_series") or 0)
            recovered["added_books"] += int(part.get("added_books") or 0)
            recovered["added_authors"] += int(part.get("added_authors") or 0)
            recovered["fiches"] += int(part.get("fiches") or 0)
            recovered["tomes"] += int(part.get("tomes") or 0)
            recovered["names"] = (list(recovered.get("names") or []) + list(part.get("names") or []))[:24]
            recovered["author_names"] = (
                list(recovered.get("author_names") or []) + list(part.get("author_names") or [])
            )[:24]

        remaining = target
        if remaining > 0:
            _merge_recovered(
                daily_pending.enrich_and_promote(
                    cap=min(remaining, daily_pending.pending_promote_limit())
                )
            )
            remaining = max(0, target - int(recovered.get("fiches") or 0))
            known = existing_qids()
            names = existing_names()
        n_series = int(recovered.get("added_series") or 0)
        n_books = int(recovered.get("added_books") or 0)
        series_names = list(recovered.get("names") or [])
        series_cap = limit if limit is not None else min(daily_series_limit(), remaining)
        more_s, skip_s, series_tomes = _ingest_series(
            series_cap, known, author_hints, names
        )
        series_names = series_names + more_s
        n_series += len(more_s)
        remaining = max(0, target - n_series - n_books - int(recovered.get("added_authors") or 0))
        if books_limit is not None:
            book_cap = books_limit
        elif limit is not None:
            book_cap = 0
        else:
            book_cap = min(daily_books_limit(), remaining)
        book_names, skip_b, book_tomes = _ingest_books(
            book_cap, known, author_hints, names
        )
        n_books += len(book_names)
        remaining = max(0, target - n_series - n_books - int(recovered.get("added_authors") or 0))
        complete_missing_covers(_env_int("CATALOG_COVER_BACKFILL", 400, 0, 2000))
        remaining = max(0, target - n_series - n_books - int(recovered.get("added_authors") or 0))
        if authors_limit is not None:
            author_cap = authors_limit
        elif limit is not None or books_limit is not None:
            author_cap = 0
        else:
            author_cap = author_fill_cap(remaining)
        author_names, skip_a = ingest_authors(author_cap, hints=author_hints)
        if limit is None and books_limit is None and authors_limit is None:
            remember_author_yield(len(author_names))
        n_authors = len(author_names) + int(recovered.get("added_authors") or 0)
        author_names = list(recovered.get("author_names") or []) + author_names
        added = series_names + book_names
        skipped = skip_s + skip_b + skip_a
        fiches = n_series + n_books + n_authors
        tomes = series_tomes + book_tomes + int(recovered.get("tomes") or 0)
        if added or author_names:
            expanded.stats.cache_clear()
            curated_mod.clear_cache()
        logger.info(
            "Ingest quotidien : +%d séries (%d tomes), +%d livres, +%d auteurs, fiches=%d/%d, ignorés=%d, pending=%d, recovered=%d",
            n_series,
            series_tomes,
            n_books,
            n_authors,
            fiches,
            target,
            skipped,
            daily_pending.count(),
            int(recovered.get("fiches") or 0),
        )
        result = {
            "status": "ok",
            "added": n_series + n_books,
            "added_series": n_series,
            "added_books": n_books,
            "added_authors": n_authors,
            "fiches": fiches,
            "tomes": tomes,
            "target_fiches": target,
            "skipped": skipped,
            "names": added[:24],
            "author_names": author_names[:24],
            "purged": purged_series + purged_authors,
            "catalog_fiches": catalog_fiche_total(),
            "goal_fiches": goal,
            "wd_window": wd_window,
            "pending_fiches": daily_pending.count(),
            "recovered": int(recovered.get("fiches") or 0),
            "focus": ingest_focus(),
        }
        _job_last = result
        return result
    except Exception as exc:
        _job_last = {"status": "error", "error": str(exc)[:240], "added": 0, "fiches": 0}
        raise
    finally:
        _job_running = False
        _ingest_lock.release()


def ingest_status() -> dict[str, Any]:
    from . import daily_pending

    total = catalog_fiche_total()
    goal = catalog_goal()
    return {
        "running": _job_running,
        "target_fiches": daily_fiches_target(),
        "catalog_fiches": total,
        "goal_fiches": goal,
        "remaining": max(0, goal - total),
        "wd_window": window_salt(),
        "pending_fiches": daily_pending.count(),
        "focus": ingest_focus(),
        "last": _job_last,
    }


def start_daily_ingest(*, sync: bool = False) -> dict[str, Any]:
    """En production : thread de fond (Render coupe les HTTP longs). Tests : sync."""
    if sync:
        return run_daily_ingest()
    if _job_running:
        return {
            "status": "busy",
            "running": True,
            "last": _job_last,
            **ingest_status(),
        }

    def _bg() -> None:
        try:
            run_daily_ingest()
        except Exception as exc:
            logger.warning("Ingest quotidien (fond) échoué : %s", exc)

    from .daily_authors import daily_authors_limit

    threading.Thread(target=_bg, daemon=True, name="catalog-daily-ingest").start()
    return {
        "status": "started",
        "running": True,
        "target_fiches": daily_fiches_target(),
        "target_books": daily_books_limit(),
        "target_series": daily_series_limit(),
        "target_authors": daily_authors_limit(),
        "catalog_fiches": catalog_fiche_total(),
        "goal_fiches": catalog_goal(),
    }
