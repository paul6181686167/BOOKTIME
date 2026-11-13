"""Rejoue catalog_daily_skip (no_author / incomplete) avec OL + Wikidata."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def retry_skipped_no_author(*, cap: int = 400) -> dict[str, Any]:
    """Pour chaque QID ignoré sans auteur : tente P50 / OL, promeut si complet."""
    from . import daily_pending, daily_store
    from .daily_ingest import (
        UA,
        build_complete_entry,
        fill_missing_author,
        is_human_label,
    )
    import requests

    try:
        coll = daily_pending._skip_coll()  # noqa: SLF001
    except Exception:
        return {"retried": 0, "promoted": 0, "left": 0}

    docs = list(
        coll.find({"reason": {"$in": ["no_author", "incomplete", "works_timeout"]}}).limit(
            max(1, int(cap))
        )
    )
    promoted = 0
    failed = 0
    for doc in docs:
        qid = (doc.get("qid") or "").strip()
        if not qid:
            continue
        reason = doc.get("reason") or ""
        cand: dict[str, Any] = {"qid": qid, "name": "", "author": "", "cover_url": "", "category": "roman", "genre": "Roman"}

        # Open Library work/edition
        if qid.startswith("OL") and qid.endswith("W"):
            try:
                r = requests.get(f"https://openlibrary.org/works/{qid}.json", timeout=12, headers=UA)
                if r.status_code == 200:
                    data = r.json() or {}
                    cand["name"] = (data.get("title") or "").strip()
                    cand["ol_key"] = f"/works/{qid}"
            except Exception as exc:
                logger.debug("retry OL work %s: %s", qid, exc)
        elif qid.startswith("OL") and qid.endswith("M"):
            try:
                r = requests.get(f"https://openlibrary.org/books/{qid}.json", timeout=12, headers=UA)
                if r.status_code == 200:
                    data = r.json() or {}
                    cand["name"] = (data.get("title") or "").strip()
            except Exception as exc:
                logger.debug("retry OL book %s: %s", qid, exc)
        elif qid.startswith("Q"):
            try:
                r = requests.get(
                    f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
                    timeout=20,
                    headers=UA,
                )
                if r.status_code == 200:
                    ent = (r.json().get("entities") or {}).get(qid) or {}
                    labels = ent.get("labels") or {}
                    cand["name"] = (
                        (labels.get("fr") or {}).get("value")
                        or (labels.get("en") or {}).get("value")
                        or ""
                    ).strip()
            except Exception as exc:
                logger.debug("retry WD %s: %s", qid, exc)

        if not is_human_label(cand.get("name")):
            # garder en skip
            failed += 1
            continue

        fill_missing_author(cand, [])
        author = (cand.get("author") or "").strip()
        if not is_human_label(author):
            failed += 1
            continue

        work = {
            "title": cand["name"],
            "author": author,
            "author_qid": cand.get("author_qid") or "",
            "work_qid": qid,
            "ol_key": cand.get("ol_key") or "",
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            failed += 1
            continue
        daily_store.upsert_series(entry)
        try:
            coll.delete_one({"qid": qid})
        except Exception:
            pass
        promoted += 1
        logger.info("retry skip ok %s %s — %s (%s)", qid, cand["name"], author, reason)

    left = 0
    try:
        left = int(coll.count_documents({}))
    except Exception:
        pass
    return {
        "retried": len(docs),
        "promoted": promoted,
        "failed": failed,
        "left": left,
        "covers": sum(1 for _ in []),  # placeholder compat
    }
