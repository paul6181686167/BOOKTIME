"""Rejets uniques enrichissables : file hors compteur, promotion une fois complets.

On ne stocke pas les doublons déjà au catalogue, les titres QID, ni l'overlay.
Une fiche pending n'entre dans catalog_fiche_total() qu'après jaquette / photo.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from . import isbn_resolve
from .daily_ingest import (
    _already_catalogued,
    _env_int,
    _lit,
    _persist,
    _qid,
    _sparql,
    build_complete_entry,
    commons_url,
    existing_names,
    existing_qids,
    fetch_works,
    is_human_label,
    is_qid_label,
    pick_isbn,
    usable_cover,
    wiki_cover,
)

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 8
_wd_budget = 0


def pending_promote_limit() -> int:
    return _env_int("CATALOG_PENDING_PROMOTE", 2500, 0, 8000)


def reset_wd_budget(n: int = 250) -> None:
    global _wd_budget
    _wd_budget = max(0, int(n))


def _coll():
    import os

    from ..db_config import MockCollection, database

    if os.getenv("ENVIRONMENT", "").lower() == "test":
        return MockCollection("catalog_daily_pending")
    return database.db["catalog_daily_pending"]


def count() -> int:
    try:
        coll = _coll()
        counted = getattr(coll, "count_documents", None)
        if callable(counted):
            return int(counted({}))
        n = 0
        for _ in coll.find({}, {"_id": 1}) or []:
            n += 1
        return n
    except Exception:
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _work_author(cand: dict[str, Any], works: list[dict[str, Any]] | None) -> str:
    author = (cand.get("author") or "").strip()
    if is_human_label(author):
        return author
    for w in works or []:
        a = (w.get("author") or "").strip()
        if is_human_label(a):
            return a
    return ""


def _identity_ok(kind: str, cand: dict[str, Any], works: list[dict[str, Any]] | None) -> bool:
    qid = (cand.get("qid") or cand.get("wikidata_qid") or "").strip()
    name = (cand.get("name") or "").strip()
    if not qid or not is_human_label(name) or is_qid_label(name):
        return False
    if kind == "author":
        return True
    return bool(_work_author(cand, works))


def remember(
    kind: str,
    cand: dict[str, Any],
    *,
    reason: str,
    works: list[dict[str, Any]] | None = None,
    known: set[str] | None = None,
    names: set[str] | None = None,
) -> bool:
    """Une entrée par QID. False si déjà en file, déjà au catalogue, ou non enrichissable."""
    if kind not in {"book", "series", "author"}:
        return False
    if not _identity_ok(kind, cand, works):
        return False
    qid = (cand.get("qid") or cand.get("wikidata_qid") or "").strip()
    if kind != "author":
        if _already_catalogued(cand, known or set(), names or set()):
            return False
    else:
        if qid and known and qid in known:
            return False
        from ..authors.service import normalize_author_name

        key = normalize_author_name(cand.get("name") or "")
        if key and names and key in names:
            return False
    try:
        coll = _coll()
        if coll.find_one({"qid": qid}, {"_id": 1}):
            return False
        compact_works: list[dict[str, Any]] = []
        for w in (works or [])[:80]:
            if not isinstance(w, dict):
                continue
            compact_works.append(
                {
                    "title": w.get("title") or "",
                    "title_en": w.get("title_en") or "",
                    "author": w.get("author") or "",
                    "published_year": w.get("published_year") or w.get("year"),
                    "isbn": w.get("isbn") or "",
                    "ol_key": w.get("ol_key") or "",
                    "work_qid": w.get("work_qid") or "",
                    "author_qid": w.get("author_qid") or "",
                }
            )
        doc = {
            "qid": qid,
            "kind": kind,
            "reason": reason,
            "attempts": 0,
            "name": cand.get("name"),
            "name_en": cand.get("name_en"),
            "author": _work_author(cand, works),
            "author_qid": qid if kind == "author" else (cand.get("author_qid") or ""),
            "category": cand.get("category") or "roman",
            "genre": cand.get("genre") or "Roman",
            "year": cand.get("year") or cand.get("published_year"),
            "cover_url": cand.get("cover_url") or "",
            "isbn": pick_isbn(cand.get("isbn")) if cand.get("isbn") else "",
            "ol_key": cand.get("ol_key") or "",
            "photo_url": cand.get("photo_url") or cand.get("image_url") or "",
            "birth_date": cand.get("birth_date"),
            "death_date": cand.get("death_date"),
            "wikipedia_url": cand.get("wikipedia_url"),
            "bio": cand.get("bio") or "",
            "nationality": cand.get("nationality"),
            "works": compact_works,
            "source": "pending",
            "updated_at": _now(),
            "created_at": _now(),
        }
        if kind == "author":
            doc["author_qid"] = qid
        coll.update_one({"qid": qid}, {"$set": doc}, upsert=True)
        return True
    except Exception as exc:
        logger.warning("Pending remember %s %s : %s", kind, qid, exc)
        return False


def drop(qid: str) -> None:
    qid = (qid or "").strip()
    if not qid:
        return
    try:
        _coll().delete_one({"qid": qid})
    except Exception:
        pass


def _bump(qid: str, extra: dict[str, Any] | None = None) -> None:
    patch = {"attempts": int((extra or {}).get("attempts") or 0), "updated_at": _now()}
    if extra:
        patch.update({k: v for k, v in extra.items() if k != "attempts" and v is not None})
    try:
        _coll().update_one({"qid": qid}, {"$set": patch})
    except Exception:
        pass


def enrich_work_candidate(cand: dict[str, Any], works: list[dict[str, Any]]) -> None:
    """Complète jaquette / ISBN sur le candidat (Open Library, Google Books)."""
    if usable_cover(cand.get("cover_url")):
        return
    isbn = pick_isbn(cand.get("isbn"))
    if not isbn:
        for w in works or []:
            isbn = pick_isbn(w.get("isbn"))
            if isbn:
                break
    title = cand.get("name") or ((works[0].get("title") if works else "") or "")
    author = _work_author(cand, works)
    title_en = cand.get("name_en") or ((works[0].get("title_en") if works else "") or "")
    ol_key = cand.get("ol_key") or ((works[0].get("ol_key") if works else "") or "")
    cover, got_isbn = isbn_resolve.find_cover(
        title=title,
        author=author,
        title_en=title_en,
        isbn=isbn or "",
        ol_key=ol_key or "",
    )
    if got_isbn:
        cand["isbn"] = got_isbn
        if works and not pick_isbn(works[0].get("isbn")):
            works[0]["isbn"] = got_isbn
    if cover:
        cand["cover_url"] = cover


def _author_wikidata(qid: str) -> dict[str, str]:
    global _wd_budget
    out: dict[str, str] = {}
    if not qid or not qid.startswith("Q") or _wd_budget <= 0:
        return out
    _wd_budget -= 1
    query = f"""
SELECT ?img ?birth ?death ?wikipedia WHERE {{
  OPTIONAL {{ wd:{qid} wdt:P18 ?img. }}
  OPTIONAL {{ wd:{qid} wdt:P569 ?birth. }}
  OPTIONAL {{ wd:{qid} wdt:P570 ?death. }}
  OPTIONAL {{
    ?wikipedia schema:about wd:{qid} .
    ?wikipedia schema:isPartOf <https://fr.wikipedia.org/> .
  }}
}}
LIMIT 1
"""
    try:
        rows = _sparql(query, timeout=20)
    except Exception as exc:
        logger.debug("Pending SPARQL auteur %s : %s", qid, exc)
        return out
    if not rows:
        return out
    row = rows[0]
    img = _lit(row, "img")
    if img.startswith("http"):
        img = img.rsplit("/", 1)[-1]
    if img:
        out["photo_url"] = commons_url(img)
    birth = _lit(row, "birth")
    if birth:
        out["birth_date"] = birth[:10]
    death = _lit(row, "death")
    if death:
        out["death_date"] = death[:10]
    wiki = _lit(row, "wikipedia")
    if wiki:
        out["wikipedia_url"] = wiki
    return out


def enrich_author_candidate(cand: dict[str, Any]) -> None:
    from .daily_authors import wiki_bio

    qid = (cand.get("qid") or cand.get("wikidata_qid") or "").strip()
    photo = usable_cover(cand.get("photo_url") or cand.get("image_url") or cand.get("cover_url"))
    if not photo:
        photo = wiki_cover(cand.get("name") or "", cand.get("name_en"))
    extra = {}
    if qid and (not photo or not cand.get("birth_date")):
        extra = _author_wikidata(qid)
        if not photo:
            photo = usable_cover(extra.get("photo_url"))
        if extra.get("birth_date") and not cand.get("birth_date"):
            cand["birth_date"] = extra["birth_date"]
        if extra.get("death_date") and not cand.get("death_date"):
            cand["death_date"] = extra["death_date"]
        if extra.get("wikipedia_url") and not cand.get("wikipedia_url"):
            cand["wikipedia_url"] = extra["wikipedia_url"]
    if photo:
        cand["photo_url"] = photo
        cand["image_url"] = photo
        cand["cover_url"] = photo
    if not (cand.get("bio") or "").strip():
        bio, wiki_url = wiki_bio(cand.get("name") or "", cand.get("name_en"), cand.get("wikipedia_url") or "")
        if bio:
            cand["bio"] = bio
        if wiki_url:
            cand["wikipedia_url"] = wiki_url


def _cand_from_pending(doc: dict[str, Any]) -> dict[str, Any]:
    qid = doc.get("qid") or ""
    return {
        "qid": qid,
        "wikidata_qid": qid,
        "name": doc.get("name"),
        "name_en": doc.get("name_en"),
        "author": doc.get("author"),
        "author_qid": doc.get("author_qid") or (qid if doc.get("kind") == "author" else ""),
        "category": doc.get("category") or "roman",
        "genre": doc.get("genre") or "Roman",
        "year": doc.get("year"),
        "cover_url": doc.get("cover_url") or "",
        "isbn": doc.get("isbn") or "",
        "ol_key": doc.get("ol_key") or "",
        "photo_url": doc.get("photo_url") or "",
        "image_url": doc.get("photo_url") or "",
        "birth_date": doc.get("birth_date"),
        "death_date": doc.get("death_date"),
        "wikipedia_url": doc.get("wikipedia_url"),
        "bio": doc.get("bio") or "",
        "nationality": doc.get("nationality"),
    }


def _promote_work(
    doc: dict[str, Any],
    known: set[str],
    names: set[str],
    added: list[str],
    hints: list[dict[str, Any]],
) -> tuple[bool, int]:
    cand = _cand_from_pending(doc)
    works = list(doc.get("works") or [])
    kind = doc.get("kind") or "book"
    if kind == "series" and not works:
        try:
            works = fetch_works(cand["qid"])
        except Exception:
            works = []
    enrich_work_candidate(cand, works)
    standalone = kind == "book" or len([w for w in works if is_human_label(w.get("title"))]) < 2
    entry = build_complete_entry(cand, works, min_volumes=1 if standalone else 2, standalone=standalone)
    if not entry and not standalone:
        entry = build_complete_entry(cand, works, min_volumes=1, standalone=True)
    if not entry:
        return False, 0
    tomes = _persist(entry, known, added, hints, names)
    drop(cand["qid"])
    return True, tomes


def _promote_author(doc: dict[str, Any], known: set[str], names: set[str], added: list[str]) -> bool:
    from .daily_authors import build_complete_author, upsert_author

    cand = _cand_from_pending(doc)
    enrich_author_candidate(cand)
    entry = build_complete_author(cand)
    if not entry:
        return False
    upsert_author(entry)
    qid = entry.get("wikidata_qid") or ""
    if qid:
        known.add(qid)
    key = entry.get("name_normalized")
    if key:
        names.add(key)
    added.append(entry["name"])
    drop(cand["qid"])
    return True


def enrich_and_promote(*, cap: int) -> dict[str, Any]:
    """Tente de compléter la file pending et n'ajoute que les fiches désormais valides."""
    added_series: list[str] = []
    added_books: list[str] = []
    added_authors: list[str] = []
    tomes = 0
    if cap <= 0:
        return {
            "added_series": 0,
            "added_books": 0,
            "added_authors": 0,
            "fiches": 0,
            "tomes": 0,
            "names": [],
            "author_names": [],
        }
    from . import daily_authors

    known = existing_qids()
    names = existing_names()
    author_ids = daily_authors.known_qids()
    author_names = daily_authors.known_names()
    hints: list[dict[str, Any]] = []
    try:
        cur = _coll().find({}).sort("attempts", 1).limit(max(cap * 3, 80))
        docs = [d for d in (cur or []) if isinstance(d, dict)]
    except Exception as exc:
        logger.warning("Lecture pending échouée : %s", exc)
        docs = []

    fiches = 0
    for doc in docs:
        if fiches >= cap:
            break
        qid = (doc.get("qid") or "").strip()
        kind = doc.get("kind") or ""
        if not qid:
            continue
        attempts = int(doc.get("attempts") or 0) + 1
        if attempts > _MAX_ATTEMPTS:
            continue
        if kind == "author":
            if qid in author_ids:
                drop(qid)
                continue
            ok = _promote_author(doc, author_ids, author_names, added_authors)
            if ok:
                fiches += 1
            else:
                _bump(qid, {"attempts": attempts})
            continue
        if _already_catalogued(_cand_from_pending(doc), known, names):
            drop(qid)
            continue
        ok, n_tomes = _promote_work(doc, known, names, added_series if kind == "series" else added_books, hints)
        if ok:
            fiches += 1
            tomes += n_tomes
        else:
            _bump(qid, {"attempts": attempts, "cover_url": doc.get("cover_url"), "isbn": doc.get("isbn")})
    logger.info(
        "Pending : +%d séries, +%d livres, +%d auteurs (file restante %d)",
        len(added_series),
        len(added_books),
        len(added_authors),
        count(),
    )
    return {
        "added_series": len(added_series),
        "added_books": len(added_books),
        "added_authors": len(added_authors),
        "fiches": fiches,
        "tomes": tomes,
        "names": (added_series + added_books)[:24],
        "author_names": added_authors[:24],
    }
