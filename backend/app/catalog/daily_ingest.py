"""Ajoute chaque jour de nouvelles fiches COMPLÈTES au noyau curé.

Sources : Wikidata (séries + livres + auteurs, fenêtre QID/OFFSET tournante),
Open Library (livres avec jaquette), Wikipedia / Commons / Google Books / BnF
pour compléter jaquette, photo, ISBN. Rien n'est inventé.
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
_BOOK_PAGE = 100
_ingest_lock = threading.Lock()
_job_running = False
_job_last: dict[str, Any] | None = None
_active_window = 0
_WINDOW_KEY = "wd_window"


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(os.getenv(name, str(default))), hi))
    except (TypeError, ValueError):
        return default


def daily_series_limit() -> int:
    return _env_int("CATALOG_DAILY_SERIES", 400, 1, 1000)


def daily_books_limit() -> int:
    return _env_int("CATALOG_DAILY_BOOKS", 10000, 0, 12000)


def daily_fiches_target() -> int:
    """Objectif : 10 000 fiches (séries + livres + auteurs) par lot."""
    return _env_int("CATALOG_DAILY_FICHES", 10000, 100, 15000)


def catalog_goal() -> int:
    """Plafond catalogue (séries + livres + auteurs) : on enchaîne les lots jusqu'ici."""
    return _env_int("CATALOG_FICHES_GOAL", 100000, 1000, 500000)


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
    return u.replace("http://", "https:")


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
    """Livres individuels : curseur année + page, pour ne plus rescanner les 8 mêmes pages."""
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
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _absorb(batch: list[dict[str, Any]]) -> None:
        for cand in batch:
            qid = cand.get("qid")
            if not qid or qid in seen:
                continue
            seen.add(qid)
            out.append(cand)

    for i in range(0, len(years), 4):
        if len(out) >= limit:
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
            _absorb(batch)
            if len(out) >= limit:
                break

    if len(out) >= min(limit, 80):
        meta_save_pair("wd_book_scan", n, off + _BOOK_PAGE)
    else:
        meta_save_pair("wd_book_scan", n + pages, 0)

    if len(out) < limit:
        yday = datetime.now(timezone.utc).timetuple().tm_yday
        offset = (yday * 23 + salt * 97) % 80000
        _absorb(_fetch_books_page(None, min(_BOOK_PAGE, limit - len(out) + 80), offset))
    if os.getenv("ENVIRONMENT", "").lower() != "test" and len(out) < limit:
        _absorb(fetch_candidate_books_openlibrary(limit - len(out)))
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
)


def fetch_candidate_books_openlibrary(limit: int) -> list[dict[str, Any]]:
    """Livres Open Library déjà illustrés — 2e source, hors Wikidata."""
    if limit <= 0:
        return []
    salt = window_salt()
    subject = _OL_BOOK_SUBJECTS[salt % len(_OL_BOOK_SUBJECTS)]
    offset = ((salt // len(_OL_BOOK_SUBJECTS)) % 250) * 40
    params: dict[str, Any] = {
        "q": f"subject:{subject}",
        "limit": min(max(int(limit), 20), 80),
        "offset": offset,
        "fields": "key,title,author_name,isbn,cover_i,first_publish_year,language,subject",
    }
    if salt % 2 == 0:
        params["language"] = "fre"
    try:
        r = requests.get(
            "https://openlibrary.org/search.json",
            params=params,
            timeout=12,
            headers=UA,
        )
        if r.status_code != 200:
            return []
        docs = (r.json() or {}).get("docs") or []
    except Exception as exc:
        logger.warning("Open Library livres échoué : %s", exc)
        return []
    from .isbn_resolve import _ol_cover_url

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        title = (doc.get("title") or "").strip()
        authors = [a for a in (doc.get("author_name") or []) if is_human_label(a)]
        cover = _ol_cover_url(doc.get("cover_i"))
        key = (doc.get("key") or "").rstrip("/").rsplit("/", 1)[-1]
        if not key.startswith("OL") or key in seen:
            continue
        if not is_human_label(title) or not authors or not cover:
            continue
        seen.add(key)
        subjects = [str(s).lower() for s in (doc.get("subject") or [])[:8]]
        cat, genre = "roman", "Roman"
        joined = " ".join(subjects)
        if "manga" in joined:
            cat, genre = "manga", "Manga"
        elif "bande dessinée" in joined or "comic" in joined or "graphic novel" in joined:
            cat, genre = "bd", "BD"
        year = doc.get("first_publish_year")
        try:
            year = int(year) if year else None
        except (TypeError, ValueError):
            year = None
        isbn = pick_isbn(doc.get("isbn") or [])
        out.append(
            {
                "qid": key,
                "name": title,
                "name_en": title,
                "author": authors[0],
                "author_qid": "",
                "category": cat,
                "genre": genre,
                "cover_url": cover,
                "isbn": isbn or "",
                "ol_key": f"/works/{key}" if key.endswith("W") else doc.get("key") or "",
                "year": year if year and 1400 <= year <= 2035 else None,
            }
        )
        if len(out) >= limit:
            break
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
    """None si la fiche n'est pas complète (titre, auteur, jaquette, assez de tomes)."""
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
    if not cover:
        return None
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
    candidates.sort(key=lambda c: 0 if usable_cover(c.get("cover_url")) else 1)
    pending = [c for c in candidates if c.get("qid") and not _already_catalogued(c, known, names)]
    skipped += max(0, len(candidates) - len(pending))
    pending = pending[: cap + 30]

    def _load(cand: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
        try:
            return cand, fetch_works(cand["qid"])
        except Exception:
            return cand, None

    workers = min(6, max(1, len(pending)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_load, cand) for cand in pending]
        for fut in as_completed(futs):
            if len(added) >= cap:
                break
            cand, works = fut.result()
            if _already_catalogued(cand, known, names):
                skipped += 1
                continue
            if works is None:
                from . import daily_pending

                daily_pending.remember(
                    "series", cand, reason="works_timeout", works=[], known=known, names=names
                )
                skipped += 1
                continue
            entry = build_complete_entry(cand, works)
            if not entry:
                entry = build_complete_entry(cand, works, min_volumes=1, standalone=True)
            if not entry:
                from . import daily_pending

                daily_pending.enrich_work_candidate(cand, works)
                entry = build_complete_entry(cand, works)
                if not entry:
                    entry = build_complete_entry(cand, works, min_volumes=1, standalone=True)
            if not entry:
                from . import daily_pending

                daily_pending.remember(
                    "series", cand, reason="incomplete", works=works, known=known, names=names
                )
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
    for cand in candidates:
        if fiches >= cap:
            break
        qid = cand.get("qid") or ""
        if not qid or _already_catalogued(cand, known, names):
            skipped += 1
            continue
        author = (cand.get("author") or "").strip()
        if not is_human_label(author) or not is_human_label(cand.get("name")):
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
            from . import daily_pending

            daily_pending.enrich_work_candidate(cand, [work])
            entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            from . import daily_pending

            daily_pending.remember(
                "book", cand, reason="incomplete", works=[work], known=known, names=names
            )
            skipped += 1
            continue
        fiches += _persist(entry, known, added, hints, names)
    return added, skipped, fiches


def run_daily_ingest(
    *,
    limit: int | None = None,
    books_limit: int | None = None,
    authors_limit: int | None = None,
) -> dict[str, Any]:
    """Ajoute séries + livres + auteurs complets. Idempotent (qid déjà connu ignoré)."""
    global _wiki_cover_budget, _job_last, _job_running
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
        from .isbn_resolve import reset_budget, reset_cover_budget
        from . import daily_pending

        isbn_default = 0 if test_env else 800
        cover_default = 0 if test_env else 1500
        reset_budget(_env_int("CATALOG_ISBN_LOOKUPS", isbn_default, 0, 2000))
        reset_cover_budget(_env_int("CATALOG_COVER_LOOKUPS", cover_default, 0, 4000))
        daily_pending.reset_wd_budget(0 if test_env else _env_int("CATALOG_PENDING_WD", 400, 0, 800))
        if not test_env:
            _wiki_cover_budget = _env_int("CATALOG_WIKI_COVERS", 400, 0, 800)
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
        if remaining > 0:
            _merge_recovered(
                daily_pending.enrich_and_promote(
                    cap=min(remaining, daily_pending.pending_promote_limit())
                )
            )
            n_series = int(recovered.get("added_series") or 0) + len(more_s)
            n_books = int(recovered.get("added_books") or 0) + len(book_names)
            series_names = list(recovered.get("names") or []) + more_s
            remaining = max(0, target - n_series - n_books - int(recovered.get("added_authors") or 0))
        if authors_limit is not None:
            author_cap = authors_limit
        elif limit is not None or books_limit is not None:
            author_cap = 0
        else:
            author_cap = min(daily_authors_limit(), remaining)
        author_names, skip_a = ingest_authors(author_cap, hints=author_hints)
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
