"""Fiches auteur quotidiennes : Wikidata → Mongo (`authors`), pas de fusion RAM.

Une fiche est complète si nom + photo + (bio ou date de naissance) + QID.
L'écran auteur lit déjà cette collection : les fiches du jour s'affichent sans Wikidata live.
"""
from __future__ import annotations

import logging
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests

from ..authors.service import author_fiche_ready, normalize_author_name
from ..utils.timeutils import utcnow
from .daily_ingest import (
    UA,
    WIKI_SUMMARY,
    _env_int,
    _lit,
    _purge_enabled,
    _qid,
    _sparql,
    commons_url,
    is_human_label,
    is_qid_label,
    usable_cover,
)

logger = logging.getLogger(__name__)

WRITER = "wd:Q36180"
NOVELIST = "wd:Q6625963"
AUTHOR = "wd:Q482980"
MANGAKA = "wd:Q191633"
COMICS_ARTIST = "wd:Q715301"
POET = "wd:Q49757"
PLAYWRIGHT = "wd:Q214917"
CHILDRENS_WRITER = "wd:Q4853732"
_AUTHOR_PAGE = 400
_wiki_bio_budget = 80


def daily_authors_limit() -> int:
    return _env_int("CATALOG_DAILY_AUTHORS", 10000, 0, 12000)


def _coll():
    from ..db_config import database

    return database.authors_collection


def known_qids() -> set[str]:
    qids: set[str] = set()
    try:
        for doc in _coll().find({}, {"wikidata_qid": 1, "_id": 0}) or []:
            qid = (doc or {}).get("wikidata_qid")
            if qid:
                qids.add(str(qid))
    except Exception:
        return set()
    return qids


def known_names() -> set[str]:
    names: set[str] = set()
    try:
        for doc in _coll().find({}, {"name_normalized": 1, "_id": 0}) or []:
            key = (doc or {}).get("name_normalized")
            if key:
                names.add(str(key))
    except Exception:
        return set()
    return names


def purge_qid_named_authors() -> int:
    """Retire les fiches auteur quotidiennes dont le nom n'est qu'un identifiant Wikidata."""
    if not _purge_enabled():
        return 0
    n = 0
    try:
        for doc in _coll().find({"source": "daily"}, {"wikidata_qid": 1, "name": 1, "name_normalized": 1}) or []:
            if not is_qid_label((doc or {}).get("name")):
                continue
            qid = (doc or {}).get("wikidata_qid")
            key = (doc or {}).get("name_normalized")
            filt: dict[str, Any] = {"source": "daily"}
            if qid:
                filt["wikidata_qid"] = qid
            elif key:
                filt["name_normalized"] = key
            else:
                continue
            _coll().delete_one(filt)
            n += 1
    except Exception as exc:
        logger.warning("Purge auteurs QID : %s", exc)
    return n


def count() -> int:
    try:
        coll = _coll()
        counted = getattr(coll, "count_documents", None)
        if callable(counted):
            return int(counted({"source": "daily"}))
        n = 0
        for _ in coll.find({"source": "daily"}, {"_id": 1}) or []:
            n += 1
        return n
    except Exception:
        return 0


def search(q: str, limit: int = 8) -> list[dict[str, Any]]:
    raw = (q or "").strip()
    if len(raw) < 2:
        return []
    escaped = re.escape(raw)
    needle = {"$regex": escaped, "$options": "i"}
    try:
        cur = _coll().find(
            {"$or": [{"name": needle}, {"name_en": needle}]},
            {"_id": 0},
        ).limit(max(1, min(int(limit), 20)))
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for doc in cur or []:
            if not isinstance(doc, dict) or not doc.get("name"):
                continue
            if not author_fiche_ready(doc):
                continue
            key = str(doc.get("wikidata_qid") or doc.get("name_normalized") or doc["name"])
            if key in seen:
                continue
            seen.add(key)
            out.append(doc)
        return out
    except Exception:
        return []


def author_lite(doc: dict[str, Any]) -> dict[str, Any]:
    photo = usable_cover(doc.get("photo_url") or doc.get("image_url") or doc.get("cover_url"))
    return {
        "type": "author",
        "key": doc.get("name_normalized") or doc.get("name"),
        "qid": doc.get("wikidata_qid"),
        "name": doc.get("name"),
        "name_en": doc.get("name_en"),
        "authors": [doc.get("name")] if doc.get("name") else [],
        "cover_url": photo,
        "photo_url": photo,
        "birth_date": doc.get("birth_date"),
        "death_date": doc.get("death_date"),
        "nationality": doc.get("nationality"),
        "bio": (doc.get("bio") or "")[:280],
        "wikipedia_url": doc.get("wikipedia_url"),
        "wikidata_qid": doc.get("wikidata_qid"),
        "source": doc.get("source") or "daily",
        "volumes": 0,
    }


def _year_slice(n: int, salt: int | None = None) -> list[int]:
    """Répartit les années sur 1800→aujourd'hui ; le sel change à chaque lot."""
    from .daily_ingest import window_salt

    if salt is None:
        salt = window_salt()
    now = datetime.now(timezone.utc).year
    yday = datetime.now(timezone.utc).timetuple().tm_yday
    span = max(1, now - 1800)
    start = 1800 + ((yday * 19 + salt * 37) % span)
    stride = max(1, span // max(n, 1))
    years: list[int] = []
    seen: set[int] = set()
    y = start
    guard = 0
    while len(years) < n and guard < 500:
        guard += 1
        if 1800 <= y <= now and y not in seen:
            seen.add(y)
            years.append(y)
        y += stride
        if y > now:
            y = 1800 + ((y - 1800) % span)
            stride = 1 if stride > 1 else stride
    return years[:n]


def _authors_sparql(year: int, limit: int, offset: int = 0, salt: int = 0) -> str:
    types = " ".join(
        [WRITER, NOVELIST, AUTHOR, MANGAKA, COMICS_ARTIST, POET, PLAYWRIGHT, CHILDRENS_WRITER]
    )
    offset_clause = f"OFFSET {offset}" if offset else ""
    return f"""
SELECT DISTINCT ?author ?authorLabel ?enLabel ?birth ?death ?nationalityLabel ?img ?wikipedia WHERE {{
  VALUES ?occ {{ {types} }}
  ?author wdt:P106 ?occ .
  ?author wdt:P18 ?img .
  ?author wdt:P569 ?birth .
  FILTER(YEAR(?birth) = {year})
  OPTIONAL {{ ?author wdt:P570 ?death . }}
  OPTIONAL {{ ?author wdt:P27 ?nat . }}
  OPTIONAL {{
    ?author rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  OPTIONAL {{
    ?wikipedia schema:about ?author .
    ?wikipedia schema:isPartOf <https://fr.wikipedia.org/> .
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
{offset_clause}
LIMIT {min(max(limit, 20), 500)}
"""


def _parse_author_rows(rows: list[dict], seen: set[str] | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = seen if seen is not None else set()
    for row in rows:
        qid = _qid(_lit(row, "author"))
        name = _lit(row, "authorLabel") or ""
        if not qid or qid in seen or not is_human_label(name):
            continue
        seen.add(qid)
        img = _lit(row, "img")
        if img.startswith("http"):
            img = img.rsplit("/", 1)[-1]
        birth = _lit(row, "birth")
        death = _lit(row, "death")
        out.append(
            {
                "qid": qid,
                "name": name,
                "name_en": _lit(row, "enLabel") or None,
                "photo_url": commons_url(img) if img else "",
                "birth_date": birth[:10] if birth else None,
                "death_date": death[:10] if death else None,
                "nationality": _lit(row, "nationalityLabel") or None,
                "wikipedia_url": _lit(row, "wikipedia") or None,
            }
        )
    return out


def fetch_candidate_authors(limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    from .daily_ingest import meta_pair, meta_save_pair

    now = datetime.now(timezone.utc).year
    span = max(1, now - 1800 + 1)
    n, off = meta_pair("wd_author_scan")
    start = 1800 + (int(n) % span)
    pages = max(24, min(90, (limit + _AUTHOR_PAGE - 1) // _AUTHOR_PAGE + 25))
    if limit >= 4000:
        pages = max(pages, 70)
    years: list[int] = []
    y = start
    for _ in range(pages):
        years.append(y)
        y += 1
        if y > now:
            y = 1800
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    page_off = int(off)

    def _page(year: int) -> list[dict[str, Any]]:
        try:
            rows = _sparql(_authors_sparql(year, _AUTHOR_PAGE, page_off), timeout=50)
        except Exception as exc:
            logger.warning("SPARQL auteurs %s échoué : %s", year, exc)
            return []
        return _parse_author_rows(rows)

    for i in range(0, len(years), 4):
        if len(out) >= limit:
            break
        chunk = years[i : i + 4]
        with ThreadPoolExecutor(max_workers=min(4, len(chunk))) as pool:
            batches = list(pool.map(_page, chunk))
        for batch in batches:
            for cand in batch:
                qid = cand.get("qid")
                if not qid or qid in seen:
                    continue
                seen.add(qid)
                out.append(cand)
                if len(out) >= limit:
                    break
            if len(out) >= limit:
                break
    if len(out) >= min(limit, 200):
        meta_save_pair("wd_author_scan", n, page_off + _AUTHOR_PAGE)
    else:
        meta_save_pair("wd_author_scan", n + pages, 0)
    return out


def wiki_bio(name: str, name_en: str | None = None, wikipedia_url: str | None = None) -> tuple[str, str]:
    """Renvoie (extrait, url wikipedia). Budget limité : pas 10k appels Wikipedia."""
    global _wiki_bio_budget
    if _wiki_bio_budget <= 0:
        return "", wikipedia_url or ""
    titles: list[tuple[str, str]] = []
    if wikipedia_url and "wikipedia.org/wiki/" in wikipedia_url:
        slug = wikipedia_url.rsplit("/wiki/", 1)[-1]
        lang = "fr" if "fr.wikipedia" in wikipedia_url else "en"
        titles.append((lang, slug))
    if name:
        titles.append(("fr", quote(name.replace(" ", "_"), safe="_()")))
    if name_en and name_en != name:
        titles.append(("en", quote(name_en.replace(" ", "_"), safe="_()")))
    session = requests.Session()
    session.headers.update(UA)
    for lang, title in titles:
        if _wiki_bio_budget <= 0:
            break
        _wiki_bio_budget -= 1
        try:
            r = session.get(WIKI_SUMMARY.format(lang=lang, title=title), timeout=8)
            if r.status_code != 200:
                continue
            data = r.json() or {}
            extract = (data.get("extract") or "").strip()
            if len(extract) < 40:
                continue
            page = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") or ""
            return extract[:2000], page or wikipedia_url or ""
        except Exception:
            continue
    return "", wikipedia_url or ""


def build_complete_author(
    cand: dict[str, Any],
    *,
    works: dict[str, list] | None = None,
) -> dict[str, Any] | None:
    name = (cand.get("name") or "").strip()
    qid = (cand.get("qid") or cand.get("wikidata_qid") or "").strip()
    photo = usable_cover(cand.get("photo_url") or cand.get("image_url") or cand.get("cover_url"))
    if not is_human_label(name) or not qid or not photo:
        return None
    bio = (cand.get("bio") or "").strip()
    wiki_url = cand.get("wikipedia_url") or ""
    if not bio:
        bio, wiki_url = wiki_bio(name, cand.get("name_en"), wiki_url)
    birth = cand.get("birth_date")
    if isinstance(birth, str):
        birth = birth[:10] if birth else None
    if not bio and not birth:
        return None
    key = normalize_author_name(name)
    series = list((works or {}).get("series") or cand.get("series") or [])
    individual = list((works or {}).get("individual_books") or cand.get("individual_books") or [])
    now = utcnow()
    return {
        "id": cand.get("id") or str(uuid.uuid4()),
        "name": name,
        "name_en": cand.get("name_en") or None,
        "name_normalized": key,
        "bio": bio or None,
        "photo_url": photo,
        "image_url": photo,
        "cover_url": photo,
        "birth_date": birth,
        "death_date": (cand.get("death_date") or None),
        "nationality": cand.get("nationality") or None,
        "occupation": cand.get("occupation") or ["écrivain"],
        "genres": cand.get("genres") or [],
        "awards": cand.get("awards") or [],
        "wikidata_qid": qid,
        "wikipedia_url": wiki_url or None,
        "series": series,
        "individual_books": individual,
        "total_series": len(series),
        "total_individual_books": len(individual),
        "sources": {"wikidata_profile": True, "daily": True, **({"wikipedia": True} if bio else {})},
        "source": "daily",
        "enriched_at": now,
        "updated_at": now,
        "created_at": cand.get("created_at") or now,
    }


def upsert_author(entry: dict[str, Any]) -> None:
    key = entry.get("name_normalized") or normalize_author_name(entry.get("name") or "")
    qid = (entry.get("wikidata_qid") or "").strip()
    if not key:
        return
    filt: dict[str, Any]
    if qid:
        filt = {"$or": [{"wikidata_qid": qid}, {"name_normalized": key}]}
        existing = _coll().find_one(filt)
    else:
        existing = _coll().find_one({"name_normalized": key})
    if existing and author_fiche_ready(existing):
        # Ne pas écraser une fiche bibliothèque plus riche : on complète les trous.
        merged = dict(existing)
        for field in ("photo_url", "image_url", "bio", "birth_date", "death_date", "nationality", "wikipedia_url", "wikidata_qid"):
            if not merged.get(field) and entry.get(field):
                merged[field] = entry[field]
        if not merged.get("series") and entry.get("series"):
            merged["series"] = entry["series"]
            merged["total_series"] = entry.get("total_series") or 0
        if not merged.get("individual_books") and entry.get("individual_books"):
            merged["individual_books"] = entry["individual_books"]
            merged["total_individual_books"] = entry.get("total_individual_books") or 0
        merged["updated_at"] = utcnow()
        _coll().update_one({"name_normalized": existing.get("name_normalized") or key}, {"$set": merged})
        return
    doc = dict(entry)
    doc["name_normalized"] = key
    if existing:
        doc["id"] = existing.get("id") or doc.get("id")
        doc["created_at"] = existing.get("created_at") or doc.get("created_at")
        _coll().update_one({"name_normalized": existing.get("name_normalized") or key}, {"$set": doc})
    else:
        _coll().update_one({"name_normalized": key}, {"$set": doc}, upsert=True)


def _works_for(name: str, hints: list[dict[str, Any]]) -> dict[str, list]:
    key = normalize_author_name(name)
    series: list[dict] = []
    books: list[dict] = []
    for h in hints:
        if normalize_author_name(h.get("name") or "") != key:
            continue
        work = {
            "title": h.get("title") or h.get("work") or "",
            "qid": h.get("work_qid"),
            "cover_url": h.get("cover_url"),
        }
        if not work["title"]:
            continue
        if h.get("kind") == "series":
            series.append(work)
        else:
            books.append(work)
    return {"series": series[:40], "individual_books": books[:40]}


def ingest_authors(
    cap: int,
    *,
    hints: list[dict[str, Any]] | None = None,
) -> tuple[list[str], int]:
    """Ajoute jusqu'à `cap` fiches auteur complètes. `hints` = auteurs des livres du jour."""
    global _wiki_bio_budget
    added: list[str] = []
    skipped = 0
    if cap <= 0:
        return added, skipped
    _wiki_bio_budget = 80
    known_id = known_qids()
    known_n = known_names()
    pending: list[dict[str, Any]] = []
    seen: set[str] = set()
    for h in hints or []:
        qid = (h.get("qid") or h.get("author_qid") or "").strip()
        name = (h.get("author") or h.get("name") or "").strip()
        key = qid or normalize_author_name(name)
        if not key or key in seen:
            continue
        seen.add(key)
        pending.append(
            {
                "qid": qid,
                "name": name,
                "photo_url": h.get("photo_url") or "",
                "birth_date": h.get("birth_date"),
                "wikipedia_url": h.get("wikipedia_url"),
                "name_en": h.get("name_en"),
            }
        )
    try:
        extra = fetch_candidate_authors(max(cap + 400, int(cap * 1.6)))
    except Exception as exc:
        logger.warning("Ingest auteurs : SPARQL échoué : %s", exc)
        extra = []
    for cand in extra:
        qid = cand.get("qid") or ""
        if not qid or qid in seen:
            continue
        seen.add(qid)
        pending.append(cand)

    from . import daily_pending as pending_mod

    blocked = pending_mod.blocked_qids()
    for cand in pending:
        if len(added) >= cap:
            break
        qid = (cand.get("qid") or "").strip()
        key = normalize_author_name(cand.get("name") or "")
        if (qid and qid in known_id) or (key and key in known_n) or (qid and qid in blocked):
            skipped += 1
            continue
        works = _works_for(cand.get("name") or "", hints or [])
        entry = build_complete_author(cand, works=works)
        if not entry:
            from . import daily_pending

            daily_pending.enrich_author_candidate(cand)
            entry = build_complete_author(cand, works=works)
        if not entry:
            from . import daily_pending

            kept = daily_pending.remember(
                "author",
                cand,
                reason="incomplete",
                known=known_id,
                names=known_n,
            )
            if not kept and qid:
                daily_pending.remember_skip(qid, "incomplete")
            skipped += 1
            continue
        upsert_author(entry)
        known_id.add(entry["wikidata_qid"])
        known_n.add(entry["name_normalized"])
        added.append(entry["name"])
    return added, skipped
