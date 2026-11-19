"""Retire manuels, thèses, rapports, proceedings, etc. du catalogue SQLite (± Mongo).

  python scripts/purge_non_fiction_noise.py --dry-run
  python scripts/purge_non_fiction_noise.py
  python scripts/purge_non_fiction_noise.py --mongo
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog.catalog_quality_filters import is_catalog_noise_doc


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def purge_sqlite(*, dry_run: bool) -> dict:
    path = Path(os.environ.get("CATALOG_LOCAL_SQLITE") or ROOT / "data" / "local_catalog.sqlite")
    con = sqlite3.connect(str(path), timeout=180)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=180000")
    before = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]
    doomed: list[str] = []
    samples: list[str] = []
    for qid, name, raw in con.execute("SELECT qid, name, doc_json FROM catalog_daily_series"):
        try:
            doc = json.loads(raw)
        except Exception:
            continue
        if not is_catalog_noise_doc(doc):
            continue
        doomed.append(qid)
        if len(samples) < 12:
            samples.append((name or "")[:80])
    print(f"sqlite before={before} noise={len(doomed)}", flush=True)
    for s in samples:
        print(f"  ex: {s}", flush=True)
    if dry_run:
        con.close()
        return {"before": before, "noise": len(doomed), "dry_run": True}
    for i in range(0, len(doomed), 1000):
        chunk = doomed[i : i + 1000]
        for attempt in range(10):
            try:
                con.executemany(
                    "DELETE FROM catalog_daily_series WHERE qid=?",
                    [(q,) for q in chunk],
                )
                con.commit()
                break
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= 9:
                    raise
                time.sleep(1.5 * (attempt + 1))
        if i % 5000 == 0:
            print(f"  deleted {min(i+1000,len(doomed))}/{len(doomed)}", flush=True)
    after = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]
    con.close()
    return {"before": before, "deleted": len(doomed), "after": after}


def purge_mongo(*, dry_run: bool) -> dict:
    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    coll = client[os.environ.get("DB_NAME") or "booktime"]["catalog_daily_series"]
    before = coll.estimated_document_count()
    doomed: list[str] = []
    for doc in coll.find({}, {"qid": 1, "name": 1, "genre": 1, "category": 1, "_id": 0}):
        if is_catalog_noise_doc(doc):
            q = str(doc.get("qid") or "")
            if q:
                doomed.append(q)
    print(f"mongo before≈{before} noise={len(doomed)}", flush=True)
    if dry_run:
        return {"before": before, "noise": len(doomed), "dry_run": True}
    deleted = 0
    for i in range(0, len(doomed), 500):
        res = coll.delete_many({"qid": {"$in": doomed[i : i + 500]}})
        deleted += int(res.deleted_count or 0)
    return {"before": before, "deleted": deleted, "after": coll.estimated_document_count()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mongo", action="store_true")
    args = p.parse_args()
    _load_env()
    print(purge_sqlite(dry_run=args.dry_run), flush=True)
    if args.mongo:
        print(purge_mongo(dry_run=args.dry_run), flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
