"""Mirroir Mongo Atlas → SQLite PC (séries + auteurs).

  python scripts/sync_mongo_to_local.py
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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


def _chunks(items: list[str], n: int):
    for i in range(0, len(items), n):
        yield items[i : i + n]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=500)
    p.add_argument("--series-only", action="store_true")
    p.add_argument("--authors-only", action="store_true")
    args = p.parse_args()
    _load_env()

    from pymongo import MongoClient
    from app.catalog import local_catalog_sqlite as local_cat

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    db = client[os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"]
    batch = max(50, int(args.batch))

    print(f"local_db={local_cat.db_path()}", flush=True)

    if not args.authors_only:
        known = local_cat.known_qids()
        print(f"local series={len(known)} — scan qids Mongo…", flush=True)
        mongo_qids: list[str] = []
        for doc in db["catalog_daily_series"].find(
            {"qid": {"$exists": True, "$nin": [None, ""]}},
            {"qid": 1, "_id": 0},
        ):
            q = str(doc.get("qid") or "").strip()
            if q and q not in known:
                mongo_qids.append(q)
        print(f"series missing on PC: {len(mongo_qids)}", flush=True)
        n = 0
        for i, chunk in enumerate(_chunks(mongo_qids, batch), 1):
            docs = list(
                db["catalog_daily_series"].find({"qid": {"$in": chunk}}, {"_id": 0})
            )
            n += local_cat.upsert_series(docs, synced=1)
            if i % 10 == 0 or n == len(mongo_qids):
                print(f"  series +{n}/{len(mongo_qids)}", flush=True)
        print(f"series local_now={local_cat.count_series()}", flush=True)

    if not args.series_only:
        local_cat.upsert_author_docs([], synced=1)
        con = sqlite3.connect(str(local_cat.db_path()))
        known_a = {str(r[0]) for r in con.execute("SELECT id FROM catalog_authors") if r and r[0]}
        con.close()
        print(f"local authors={len(known_a)} — scan ids Mongo…", flush=True)
        missing: list[dict] = []
        # stream authors; keep only missing (ids are small enough)
        n = 0
        buf: list[dict] = []
        seen = 0
        for doc in db["authors"].find({}, {"_id": 0}):
            seen += 1
            aid = (
                str(doc.get("id") or "").strip()
                or str(doc.get("wikidata_qid") or "").strip()
                or str(doc.get("name_normalized") or "").strip()
            )
            if not aid or aid in known_a:
                continue
            buf.append(doc)
            known_a.add(aid)
            if len(buf) >= batch:
                n += local_cat.upsert_author_docs(buf, synced=1)
                buf.clear()
                print(f"  authors +{n} scanned={seen}", flush=True)
        if buf:
            n += local_cat.upsert_author_docs(buf, synced=1)
        con = sqlite3.connect(str(local_cat.db_path()))
        a_n = con.execute("SELECT COUNT(*) FROM catalog_authors").fetchone()[0]
        con.close()
        print(f"authors upserts={n} local_now={a_n}", flush=True)

    con = sqlite3.connect(str(local_cat.db_path()))
    series_n = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]
    try:
        authors_n = con.execute("SELECT COUNT(*) FROM catalog_authors").fetchone()[0]
    except Exception:
        authors_n = 0
    con.close()
    print(
        f"DONE PC series={series_n} authors={authors_n} fiches_total={series_n + authors_n}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
