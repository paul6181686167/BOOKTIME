"""Ajoute chaque jour de nouvelles fiches COMPLÈTES au noyau curé.

Sources : Wikidata (séries + livres individuels), Wikipedia / Commons pour la jaquette.
ISBN uniquement s'il est réel. Rien n'est inventé.
"""
from __future__ import annotations

import logging
import os
import re
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


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(os.getenv(name, str(default))), hi))
    except (TypeError, ValueError):
        return default


def daily_series_limit() -> int:
    return _env_int("CATALOG_DAILY_SERIES", 80, 1, 200)


def daily_books_limit() -> int:
    return _env_int("CATALOG_DAILY_BOOKS", 400, 0, 800)


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


def fetch_candidate_books(limit: int) -> list[dict[str, Any]]:
    """Livres individuels (hors saga) : roman, one-shot manga, album BD, roman graphique."""
    if limit <= 0:
        return []
    offset = (datetime.now(timezone.utc).timetuple().tm_yday * 23) % 4000
    types = " ".join([NOVEL_WORK, GRAPHIC_NOVEL, COMIC_ALBUM, MANGA_ONESHOT])
    query = f"""
SELECT DISTINCT ?work ?workLabel ?enLabel ?authorLabel ?date ?isbn ?ol ?img ?type WHERE {{
  VALUES ?type {{ {types} }}
  ?work wdt:P31 ?type .
  ?work wdt:P50 ?author .
  ?work wdt:P18 ?img .
  FILTER NOT EXISTS {{ ?work wdt:P179 ?serie . }}
  OPTIONAL {{
    ?work rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  OPTIONAL {{ ?work wdt:P577 ?date. }}
  OPTIONAL {{ ?work wdt:P212 ?isbn. }}
  OPTIONAL {{ ?work wdt:P648 ?ol. }}
  ?author rdfs:label ?authorLabel .
  FILTER((LANG(?authorLabel) = "fr") || (LANG(?authorLabel) = "en"))
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
OFFSET {offset}
LIMIT {min(max(limit + 80, 40), 1000)}
"""
    try:
        rows = _sparql(query, timeout=55)
    except Exception as exc:
        logger.warning("SPARQL livres individuels échoué : %s", exc)
        return []
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
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
                "category": cat,
                "genre": genre,
                "cover_url": commons_url(img) if img else "",
                "isbn": pick_isbn(_lit(row, "isbn")),
                "ol_key": f"/works/{ol}" if ol else "",
                "year": year,
            }
        )
    return out


def fetch_works(qid: str) -> list[dict[str, Any]]:
    query = f"""
SELECT ?work ?frLabel ?enLabel ?date ?isbn ?ol ?authorLabel WHERE {{
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
    qids = set(daily_store.known_qids())
    for s in expanded.all_series():
        qid = s.get("qid") or s.get("wikidata_qid")
        if qid:
            qids.add(str(qid))
    return qids


def _persist(entry: dict[str, Any], known: set[str], added: list[str]) -> None:
    daily_store.upsert_series(entry)
    known.add(entry["qid"])
    added.append(entry["name"])


def _ingest_series(cap: int, known: set[str]) -> tuple[list[str], int]:
    added: list[str] = []
    skipped = 0
    if cap <= 0:
        return added, skipped
    try:
        candidates = fetch_candidate_series(cap)
    except Exception as exc:
        logger.warning("Ingest quotidien : SPARQL séries échoué : %s", exc)
        return added, skipped
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
            _persist(entry, known, added)
    return added, skipped


def _ingest_books(cap: int, known: set[str]) -> tuple[list[str], int]:
    added: list[str] = []
    skipped = 0
    if cap <= 0:
        return added, skipped
    try:
        candidates = fetch_candidate_books(cap)
    except Exception as exc:
        logger.warning("Ingest quotidien : SPARQL livres échoué : %s", exc)
        return added, skipped
    for cand in candidates:
        if len(added) >= cap:
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
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            skipped += 1
            continue
        _persist(entry, known, added)
    return added, skipped


def run_daily_ingest(*, limit: int | None = None, books_limit: int | None = None) -> dict[str, Any]:
    """Ajoute séries + livres individuels complets. Idempotent (qid déjà connu ignoré)."""
    global _wiki_cover_budget
    _wiki_cover_budget = 25
    series_cap = limit if limit is not None else daily_series_limit()
    book_cap = books_limit if books_limit is not None else (0 if limit is not None else daily_books_limit())
    known = existing_qids()
    series_names, skip_s = _ingest_series(series_cap, known)
    book_names, skip_b = _ingest_books(book_cap, known)
    added = series_names + book_names
    skipped = skip_s + skip_b
    if added:
        expanded.clear_cache()
        curated_mod.clear_cache()
    logger.info(
        "Ingest quotidien : +%d séries, +%d livres (%s), ignorés=%d",
        len(series_names),
        len(book_names),
        added[:8],
        skipped,
    )
    return {
        "added": len(added),
        "added_series": len(series_names),
        "added_books": len(book_names),
        "skipped": skipped,
        "names": added,
    }
