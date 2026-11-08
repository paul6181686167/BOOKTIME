"""Persistance Mongo des séries ajoutées chaque jour au noyau curé."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..db_config import catalog_daily_collection


def _coll():
    return catalog_daily_collection


def all_series() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        for doc in _coll().find({}) or []:
            if not isinstance(doc, dict):
                continue
            row = {k: v for k, v in doc.items() if k != "_id"}
            if row.get("name") and row.get("volume_titles"):
                out.append(row)
    except Exception:
        return []
    return out


def known_qids() -> set[str]:
    qids: set[str] = set()
    try:
        for doc in _coll().find({}) or []:
            qid = (doc or {}).get("qid") or (doc or {}).get("wikidata_qid")
            if qid:
                qids.add(str(qid))
    except Exception:
        return set()
    return qids


def upsert_series(entry: dict[str, Any]) -> None:
    qid = (entry.get("qid") or entry.get("wikidata_qid") or "").strip()
    if not qid:
        return
    doc = dict(entry)
    doc["qid"] = qid
    doc["wikidata_qid"] = qid
    doc["source"] = doc.get("source") or "daily"
    doc["added_at"] = datetime.now(timezone.utc).isoformat()
    _coll().update_one({"qid": qid}, {"$set": doc}, upsert=True)
