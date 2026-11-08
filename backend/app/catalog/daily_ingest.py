"""Ajoute chaque jour de nouvelles fiches COMPLÈTES au noyau curé.

Sources : Wikidata (séries + livres individuels), Wikipedia / Commons pour la jaquette.
ISBN uniquement s'il est réel. Rien n'est inventé.
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
_BOOK_PAGE = 400
_ingest_lock = threading.Lock()
_job_running = False
_job_last: dict[str, Any] | None = None


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(os.getenv(name, str(default))), hi))
    except (TypeError, ValueError):
        return default


def daily_series_limit() -> int:
    return _env_int("CATALOG_DAILY_SERIES", 80, 1, 200)


def daily_books_limit() -> int:
    return _env_int("CATALOG_DAILY_BOOKS", 10000, 0, 12000)


def daily_fiches_target() -> int:
    """Objectif : tomes de séries + livres individuels ajoutés ce jour."""
    return _env_int("CATALOG_DAILY_FICHES", 10000, 100, 15000)


def daily_limit() -> int:
    """Compat : plafond de séries (le job ajoute aussi des livres individuels)."""
    return daily_series_limit()


def usable_cover(url: str | None) -> str:
    u = (url or "").strip()
    if not u or u.startswith("data:") or "undefined" in u:
        return ""
    if OL_W_COVER.search(u):
        return ""
    return u.replace("http://", "https:")


def pick_isbn(raw: Any) -> str:
    if not raw:
        return ""
    digits = re.sub(r"[^0-9Xx]", "", str(raw)).upper()
    if len(digits) == 13 and digits.isdigit():
        return digits
    if len(digits) == 10 and digits[:9].isdigit():
        return digits
    return ""


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
    """Séries Wikidata récentes, puis rotation annuelle pour alimenter chaque jour."""
    year = datetime.now(timezone.utc).year - 3
    types = " ".join([NOVEL, BOOK_SERIES, MANGA, COMICS, COMIC_BOOK])
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
LIMIT {max(limit * 4, 40)}
"""
    rows = _sparql(query_recent)
    if len(rows) < limit:
        offset = (datetime.now(timezone.utc).timetuple().tm_yday * 17) % 8000
        query_rot = f"""
SELECT DISTINCT ?series ?seriesLabel ?enLabel ?type ?img WHERE {{
  VALUES ?type {{ {NOVEL} {MANGA} {COMICS} }}
  ?series wdt:P31 ?type .
  OPTIONAL {{ ?series wdt:P18 ?img. }}
  OPTIONAL {{
    ?series rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
OFFSET {offset}
LIMIT {limit * 3}
"""
        try:
            rows.extend(_sparql(query_rot))
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
        img = _lit(row, "img")
        if img.startswith("http"):
            img = img.rsplit("/", 1)[-1]
        cat, genre = TYPE_GENRE.get(type_qid, ("roman", "Roman"))
        out.append(
            {
                "qid": qid,
                "name": _lit(row, "seriesLabel") or qid,
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
                "name": _lit(row, "workLabel") or qid,
                "name_en": _lit(row, "enLabel") or None,
                "author": _lit(row, "authorLabel"),
                "author_qid": _qid(_lit(row, "author")),
                "category": cat,
                "genre": genre,
                "cover_url": commons_url(img) if img else "",
                "isbn": pick_isbn(_lit(row, "isbn")),
                "ol_key": f"/works/{ol}" if ol else "",
                "year": year,
            }
        )
    return out


def _book_years(n: int) -> list[int]:
    now = datetime.now(timezone.utc).year
    yday = datetime.now(timezone.utc).timetuple().tm_yday
    span = max(1, now - 1850)
    start = 1850 + (yday * 17) % span
    years: list[int] = []
    y = start
    while len(years) < n:
        if 1800 <= y <= now:
            years.append(y)
        y += 1
        if y > now:
            y = 1800
    return years


def _books_sparql(year: int | None, limit: int, offset: int = 0) -> str:
    types = " ".join([NOVEL_WORK, GRAPHIC_NOVEL, COMIC_ALBUM, MANGA_ONESHOT])
    year_filter = f"FILTER(YEAR(?date) = {year})" if year else ""
    offset_clause = f"OFFSET {offset}" if offset else ""
    return f"""
SELECT DISTINCT ?work ?workLabel ?enLabel ?author ?authorLabel ?date ?isbn ?ol ?img ?type WHERE {{
  VALUES ?type {{ {types} }}
  ?work wdt:P31 ?type .
  ?work wdt:P50 ?author .
  ?work wdt:P18 ?img .
  ?work wdt:P577 ?date .
  {year_filter}
  FILTER NOT EXISTS {{ ?work wdt:P179 ?serie . }}
  OPTIONAL {{
    ?work rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  OPTIONAL {{ ?work wdt:P212 ?isbn. }}
  OPTIONAL {{ ?work wdt:P648 ?ol. }}
  ?author rdfs:label ?authorLabel .
  FILTER((LANG(?authorLabel) = "fr") || (LANG(?authorLabel) = "en"))
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
{offset_clause}
LIMIT {min(max(limit, 20), 500)}
"""


def _fetch_books_page(year: int | None, limit: int, offset: int = 0) -> list[dict[str, Any]]:
    try:
        rows = _sparql(_books_sparql(year, limit, offset), timeout=50)
    except Exception as exc:
        logger.warning("SPARQL livres %s échoué : %s", year if year else f"offset={offset}", exc)
        return []
    return _parse_book_rows(rows)


def fetch_candidate_books(limit: int) -> list[dict[str, Any]]:
    """Livres individuels paginés par année (évite un OFFSET Wikidata trop lent)."""
    if limit <= 0:
        return []
    pages = max(8, (limit + _BOOK_PAGE - 1) // _BOOK_PAGE + 4)
    years = _book_years(pages)
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
            batches = list(pool.map(lambda y: _fetch_books_page(y, _BOOK_PAGE), chunk))
        for batch in batches:
            _absorb(batch)
            if len(out) >= limit:
                break

    if len(out) < limit:
        offset = (datetime.now(timezone.utc).timetuple().tm_yday * 23) % 8000
        _absorb(_fetch_books_page(None, min(_BOOK_PAGE, limit - len(out) + 80), offset))
    return out


def fetch_works(qid: str) -> list[dict[str, Any]]:
    query = f"""
SELECT ?work ?frLabel ?enLabel ?date ?isbn ?ol ?author ?authorLabel WHERE {{
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
        if not title or title in seen:
            continue
        seen.add(title)
        date = _lit(row, "date")
        year = None
        m = re.search(r"(\d{4})", date)
        if m:
            year = int(m.group(1))
        ol = _lit(row, "ol")
        works.append(
            {
                "title": title,
                "title_en": _lit(row, "enLabel"),
                "published_year": year if year and 1400 <= year <= 2035 else None,
                "isbn": pick_isbn(_lit(row, "isbn")),
                "ol_key": f"/works/{ol}" if ol and ol.endswith("W") else (f"/works/{ol}" if ol else ""),
                "author": _lit(row, "authorLabel"),
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
    titled = [w for w in works if (w.get("title") or "").strip()]
    if len(titled) < min_volumes:
        return None
    author = next((w.get("author") for w in titled if (w.get("author") or "").strip()), "") or ""
    if not author.strip():
        return None
    author_qid = (cand.get("author_qid") or "") or next(
        (w.get("author_qid") for w in titled if w.get("author_qid")),
        "",
    )
    cover = usable_cover(cand.get("cover_url")) or wiki_cover(cand.get("name") or "", cand.get("name_en"))
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
        if w.get("isbn"):
            detail["isbn"] = w["isbn"]
            if not usable_cover(detail.get("cover_url")):
                detail["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{w['isbn']}-M.jpg"
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


def existing_qids() -> set[str]:
    try:
        from .seed import ensure_seeded

        ensure_seeded()
    except Exception:
        pass
    return set(daily_store.known_qids())


def _persist(
    entry: dict[str, Any],
    known: set[str],
    added: list[str],
    hints: list[dict[str, Any]] | None = None,
) -> int:
    daily_store.upsert_series(entry)
    known.add(entry["qid"])
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
    cap: int, known: set[str], hints: list[dict[str, Any]] | None = None
) -> tuple[list[str], int, int]:
    added: list[str] = []
    skipped = 0
    fiches = 0
    if cap <= 0:
        return added, skipped, fiches
    try:
        candidates = fetch_candidate_series(cap)
    except Exception as exc:
        logger.warning("Ingest quotidien : SPARQL séries échoué : %s", exc)
        return added, skipped, fiches
    candidates.sort(key=lambda c: 0 if usable_cover(c.get("cover_url")) else 1)
    pending = [c for c in candidates if c.get("qid") and c["qid"] not in known]
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
            if cand["qid"] in known:
                skipped += 1
                continue
            if works is None:
                skipped += 1
                continue
            entry = build_complete_entry(cand, works)
            if not entry:
                skipped += 1
                continue
            fiches += _persist(entry, known, added, hints)
    return added, skipped, fiches


def _ingest_books(
    cap: int, known: set[str], hints: list[dict[str, Any]] | None = None
) -> tuple[list[str], int, int]:
    added: list[str] = []
    skipped = 0
    fiches = 0
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
        if not qid or qid in known:
            skipped += 1
            continue
        author = (cand.get("author") or "").strip()
        cover = usable_cover(cand.get("cover_url"))
        if not author or not cover:
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
            skipped += 1
            continue
        fiches += _persist(entry, known, added, hints)
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
        _wiki_cover_budget = 25
        series_cap = limit if limit is not None else daily_series_limit()
        target = daily_fiches_target()
        if books_limit is not None:
            book_cap = books_limit
        elif limit is not None:
            book_cap = 0
        else:
            book_cap = daily_books_limit()
        known = existing_qids()
        author_hints: list[dict[str, Any]] = []
        series_names, skip_s, series_fiches = _ingest_series(series_cap, known, author_hints)
        if books_limit is None and limit is None:
            book_cap = min(book_cap, max(0, target - series_fiches))
        book_names, skip_b, book_fiches = _ingest_books(book_cap, known, author_hints)
        from .daily_authors import daily_authors_limit, ingest_authors

        if authors_limit is not None:
            author_cap = authors_limit
        elif limit is not None or books_limit is not None:
            author_cap = 0
        else:
            author_cap = daily_authors_limit()
        author_names, skip_a = ingest_authors(author_cap, hints=author_hints)
        added = series_names + book_names
        skipped = skip_s + skip_b + skip_a
        fiches = series_fiches + book_fiches
        if added or author_names:
            expanded.stats.cache_clear()
            curated_mod.clear_cache()
        logger.info(
            "Ingest quotidien : +%d séries (%d tomes), +%d livres, +%d auteurs, fiches=%d/%d, ignorés=%d",
            len(series_names),
            series_fiches,
            len(book_names),
            len(author_names),
            fiches,
            target,
            skipped,
        )
        result = {
            "status": "ok",
            "added": len(added),
            "added_series": len(series_names),
            "added_books": len(book_names),
            "added_authors": len(author_names),
            "fiches": fiches,
            "target_fiches": target,
            "skipped": skipped,
            "names": added[:24],
            "author_names": author_names[:24],
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
    return {
        "running": _job_running,
        "target_fiches": daily_fiches_target(),
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
            "target_fiches": daily_fiches_target(),
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
    }
