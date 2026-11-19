"""Audit incohérences catalogue ↔ app suivi de lecture.

  python scripts/_audit_catalog_app_coherence.py
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if (ROOT / ".env").exists() else []:
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, v = s.split("=", 1)
    k, v = k.strip(), v.strip().strip('"').strip("'")
    if k and k not in os.environ:
        os.environ[k] = v

from app.catalog.catalog_quality_filters import is_catalog_noise_doc  # noqa: E402

VALID_CAT = {"roman", "bd", "manga"}
OL_WORK_COVER = re.compile(r"/b/(?:id|olid)/OL\d+W", re.I)
QID_WD = re.compile(r"^Q\d+$")


def usable_cover(url: str | None) -> bool:
    u = (url or "").strip()
    if not u.startswith(("http://", "https://")):
        return False
    if u.startswith("data:"):
        return False
    if OL_WORK_COVER.search(u):
        return False
    return True


def main() -> int:
    db = Path(os.environ.get("CATALOG_LOCAL_SQLITE") or ROOT / "data" / "local_catalog.sqlite")
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    total = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]

    c = Counter()
    samples: dict[str, list[str]] = {k: [] for k in (
        "no_author", "bad_cover", "no_cover", "vol_mismatch", "solo_multi",
        "series_one", "bad_category", "no_title_fr", "noise", "bad_qid",
        "vol_titles_missing", "name_norm_drift",
    )}

    def note(key: str, name: str) -> None:
        c[key] += 1
        if len(samples[key]) < 5 and name:
            samples[key].append(name[:80])

    for qid, name, name_norm, raw in con.execute(
        "SELECT qid, name, name_norm, doc_json FROM catalog_daily_series"
    ):
        try:
            doc = json.loads(raw) if raw else {}
        except Exception:
            c["bad_json"] += 1
            continue

        c["scanned"] += 1
        authors = doc.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        if not any(str(a).strip() for a in authors):
            # volume_details fallback
            vd = doc.get("volume_details") or {}
            has_va = False
            if isinstance(vd, dict):
                for v in vd.values():
                    if isinstance(v, dict) and (v.get("author") or "").strip():
                        has_va = True
                        break
            if not has_va:
                note("no_author", name or qid)

        cover = (doc.get("cover_url") or "").strip()
        if not cover or doc.get("needs_cover"):
            note("no_cover", name or qid)
        elif not usable_cover(cover):
            note("bad_cover", name or qid)

        desc = (doc.get("description") or "").strip()
        if not desc or doc.get("needs_summary"):
            c["no_summary"] += 1

        if not doc.get("title_fr"):
            note("no_title_fr", name or qid)

        cat = (doc.get("category") or "").strip().lower()
        if cat not in VALID_CAT:
            note("bad_category", name or qid)
            c[f"cat_{cat or 'empty'}"] += 1
        else:
            c[f"cat_{cat}"] += 1

        typ = (doc.get("type") or "").strip()
        vols = doc.get("volumes")
        try:
            vols_n = int(vols) if vols is not None else 0
        except Exception:
            vols_n = 0
            c["volumes_non_int"] += 1

        vt = doc.get("volume_titles")
        if not vt:
            note("vol_titles_missing", name or qid)
            vt_n = 0
        elif isinstance(vt, dict):
            vt_n = len(vt)
        elif isinstance(vt, list):
            vt_n = len(vt)
            c["vol_titles_list"] += 1
        else:
            vt_n = 0
            c["vol_titles_weird"] += 1

        if vols_n and vt_n and vols_n != vt_n:
            note("vol_mismatch", name or qid)

        if typ == "standalone" and vols_n > 1:
            note("solo_multi", name or qid)
        if typ in ("daily", "series") and vols_n == 1:
            note("series_one", name or qid)
        if typ == "standalone":
            c["type_standalone"] += 1
        elif typ == "daily":
            c["type_daily"] += 1
        else:
            c[f"type_{typ or 'empty'}"] += 1

        if not QID_WD.match(str(qid or "")):
            note("bad_qid", f"{qid}|{name}")

        dn = (doc.get("name_norm") or "").strip()
        if name_norm and dn and name_norm != dn:
            note("name_norm_drift", name or qid)

        if is_catalog_noise_doc(doc):
            note("noise", name or qid)

        src = doc.get("source") or "unknown"
        c[f"src_{src}"] += 1

    synced0 = con.execute(
        "SELECT COUNT(*) FROM catalog_daily_series WHERE synced=0 OR synced IS NULL"
    ).fetchone()[0]
    con.close()

    # Mongo: app-facing catalog + user library drift
    mongo = {}
    try:
        from pymongo import MongoClient

        client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=20000)
        mdb = client[os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"]
        coll = mdb["catalog_daily_series"]
        mongo["catalog_n"] = coll.estimated_document_count()
        mongo["no_cover"] = coll.count_documents(
            {"$or": [{"cover_url": {"$in": [None, ""]}}, {"needs_cover": True}]}
        )
        mongo["no_author"] = coll.count_documents(
            {"$or": [{"authors": {"$size": 0}}, {"authors": None}, {"authors": {"$exists": False}}]}
        )
        mongo["bad_category"] = coll.count_documents(
            {"category": {"$nin": list(VALID_CAT)}}
        )
        mongo["no_title_fr"] = coll.count_documents(
            {"$or": [{"title_fr": {"$exists": False}}, {"title_fr": None}, {"title_fr": ""}]}
        )
        mongo["standalone"] = coll.count_documents({"type": "standalone"})
        mongo["daily"] = coll.count_documents({"type": "daily"})
        mongo["pending"] = mdb["catalog_daily_pending"].estimated_document_count()
        mongo["skip"] = mdb["catalog_daily_skip"].estimated_document_count()

        books = mdb["books"]
        series = mdb["series_library"]
        mongo["user_books"] = books.estimated_document_count()
        mongo["user_series"] = series.estimated_document_count()
        mongo["user_books_no_cover"] = books.count_documents(
            {"$or": [{"cover_url": {"$in": [None, ""]}}, {"cover_url": {"$exists": False}}]}
        )
        mongo["user_books_no_pages"] = books.count_documents(
            {"$or": [{"total_pages": {"$in": [None, 0]}}, {"total_pages": {"$exists": False}}]}
        )
        # category hors enum
        mongo["user_books_bad_cat"] = books.count_documents(
            {"category": {"$nin": list(VALID_CAT)}}
        )
        mongo["user_series_bad_cat"] = series.count_documents(
            {"category": {"$nin": list(VALID_CAT)}}
        )
        # status vocab
        mongo["user_books_status"] = {
            s: books.count_documents({"status": s})
            for s in ("to_read", "reading", "to_reread", "completed", None)
        }
        # series without volumes list
        mongo["user_series_empty_vols"] = series.count_documents(
            {"$or": [{"volumes": {"$size": 0}}, {"volumes": None}, {"volumes": {"$exists": False}}]}
        )
    except Exception as exc:
        mongo["error"] = str(exc)

    out = {
        "sqlite_total": total,
        "sqlite_synced0": synced0,
        "counts": dict(c),
        "samples": samples,
        "mongo": mongo,
        "pct": {
            "no_cover": round(100 * c["no_cover"] / max(total, 1), 1),
            "no_summary": round(100 * c["no_summary"] / max(total, 1), 1),
            "no_title_fr": round(100 * c["no_title_fr"] / max(total, 1), 1),
            "no_author": round(100 * c["no_author"] / max(total, 1), 1),
            "vol_mismatch": round(100 * c["vol_mismatch"] / max(total, 1), 1),
            "solo_multi": round(100 * c["solo_multi"] / max(total, 1), 1),
            "bad_category": round(100 * c["bad_category"] / max(total, 1), 1),
            "noise_remaining": round(100 * c["noise"] / max(total, 1), 1),
            "bad_qid": round(100 * c["bad_qid"] / max(total, 1), 1),
        },
    }
    dest = ROOT / "data" / "_coherence_audit.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("sqlite_total", "sqlite_synced0", "pct", "mongo")}, ensure_ascii=False, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
