"""Catalogue Mongo (noyau 50k + fiches du jour). Jamais de scan complet en requête."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from ..db_config import catalog_daily_collection
from ..static_wikidata.service import norm_title


def _coll():
    return catalog_daily_collection


def _strip_id(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(doc, dict):
        return None
    return {k: v for k, v in doc.items() if k != "_id"}


def _title_norms(entry: dict[str, Any]) -> list[str]:
    titles = entry.get("volume_titles") or {}
    out: list[str] = []
    seen: set[str] = set()
    values = titles.values() if isinstance(titles, dict) else []
    for title in values:
        n = norm_title(str(title or ""))
        if len(n) < 4 or n in seen:
            continue
        seen.add(n)
        out.append(n)
        if len(out) >= 80:
            break
    return out


def prepare_entry(entry: dict[str, Any]) -> dict[str, Any]:
    doc = dict(entry)
    qid = (doc.get("qid") or doc.get("wikidata_qid") or "").strip()
    if qid:
        doc["qid"] = qid
        doc["wikidata_qid"] = qid
    doc["name_norm"] = norm_title(str(doc.get("name") or ""))
    doc["name_en_norm"] = norm_title(str(doc.get("name_en") or ""))
    doc["title_norms"] = _title_norms(doc)
    return doc


def all_series() -> list[dict[str, Any]]:
    """Scan complet — tests / outils seulement, pas le chemin de recherche."""
    out: list[dict[str, Any]] = []
    try:
        for doc in _coll().find({}) or []:
            row = _strip_id(doc if isinstance(doc, dict) else None)
            if row and row.get("name") and row.get("volume_titles"):
                out.append(row)
    except Exception:
        return []
    return out


def known_qids() -> set[str]:
    qids: set[str] = set()
    try:
        for doc in _coll().find({}, {"qid": 1, "wikidata_qid": 1, "_id": 0}) or []:
            qid = (doc or {}).get("qid") or (doc or {}).get("wikidata_qid")
            if qid:
                qids.add(str(qid))
    except Exception:
        return set()
    return qids


def known_names() -> set[str]:
    names: set[str] = set()
    try:
        for doc in _coll().find({}, {"name_norm": 1, "name_en_norm": 1, "_id": 0}) or []:
            for key in ((doc or {}).get("name_norm"), (doc or {}).get("name_en_norm")):
                if key:
                    names.add(str(key))
    except Exception:
        return set()
    return names


def count() -> int:
    try:
        coll = _coll()
        counted = getattr(coll, "estimated_document_count", None)
        if callable(counted):
            return int(counted())
        n = 0
        for _ in coll.find({}, {"_id": 1}) or []:
            n += 1
        return n
    except Exception:
        return 0


def count_by_source(source: str) -> int:
    n = 0
    try:
        for _ in _coll().find({"source": source}, {"_id": 1}) or []:
            n += 1
    except Exception:
        return 0
    return n


def fiche_count() -> int:
    n = 0
    try:
        for doc in _coll().find({}, {"volumes": 1, "_id": 0}) or []:
            n += int((doc or {}).get("volumes") or 0)
    except Exception:
        return 0
    return n


def find_by_name(name: str) -> dict[str, Any] | None:
    qn = norm_title(name or "")
    if len(qn) < 2:
        return None
    try:
        doc = _coll().find_one({"name_norm": qn}, {"_id": 0})
        row = _strip_id(doc)
        if row and row.get("name"):
            return row
        doc = _coll().find_one({"name_en_norm": qn}, {"_id": 0})
        row = _strip_id(doc)
        if row and row.get("name"):
            return row
    except Exception:
        return None
    return None


def search(q: str, limit: int = 20) -> list[dict[str, Any]]:
    qn = norm_title(q or "")
    if len(qn) < 2:
        return []
    prefix = {"$regex": f"^{re.escape(qn)}"}
    clauses: list[dict[str, Any]] = [
        {"name_norm": qn},
        {"name_en_norm": qn},
        {"name_norm": prefix},
        {"name_en_norm": prefix},
    ]
    if len(qn) >= 4:
        clauses.append({"title_norms": {"$regex": re.escape(qn)}})
    try:
        cur = _coll().find({"$or": clauses}, {"_id": 0}).limit(max(1, min(int(limit), 80)))
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        for doc in cur or []:
            row = _strip_id(doc if isinstance(doc, dict) else None)
            if not row or not row.get("name"):
                continue
            qid = str(row.get("qid") or row.get("wikidata_qid") or row.get("name"))
            if qid in seen:
                continue
            seen.add(qid)
            out.append(row)
        return out
    except Exception:
        return []


def needing_cover(limit: int = 400) -> list[dict[str, Any]]:
    """Fiches quotidiennes titre+auteur déjà en base, jaquette encore à trouver."""
    out: list[dict[str, Any]] = []
    try:
        cur = _coll().find({"needs_cover": True}).limit(max(1, int(limit)))
        for doc in cur or []:
            row = _strip_id(doc if isinstance(doc, dict) else None)
            if row and row.get("qid") and row.get("name"):
                out.append(row)
            if len(out) >= limit:
                break
    except Exception:
        return out
    return out


def upsert_series(entry: dict[str, Any]) -> None:
    doc = prepare_entry(entry)
    qid = (doc.get("qid") or "").strip()
    if not qid:
        return
    doc["source"] = doc.get("source") or "daily"
    doc["added_at"] = datetime.now(timezone.utc).isoformat()
    _coll().update_one({"qid": qid}, {"$set": doc}, upsert=True)
