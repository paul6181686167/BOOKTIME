"""Pousse le catalogue SQLite local vers Mongo Atlas (quand il y a de la place).

  python scripts/sync_local_catalog_to_mongo.py --batch 2000 --rounds 50
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=2000)
    p.add_argument("--rounds", type=int, default=100)
    args = p.parse_args()

    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"

    from pymongo import MongoClient, UpdateOne
    from pymongo.errors import OperationFailure
    from app.db_config import database
    from app.catalog import local_catalog_sqlite as local_cat

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    db = client[os.environ.get("DATABASE_NAME") or "booktime"]
    database._client = client
    database._db = db
    coll = db["catalog_daily_series"]

    print(
        f"local_db={local_cat.db_path()} series={local_cat.count_series()} "
        f"unsynced={local_cat.count_unsynced()}",
        flush=True,
    )

    total = 0
    for rnd in range(1, args.rounds + 1):
        docs = local_cat.iter_unsynced(args.batch)
        if not docs:
            print("nothing to sync", flush=True)
            break
        ops = [
            UpdateOne({"qid": d["qid"]}, {"$set": d}, upsert=True)
            for d in docs
            if d.get("qid")
        ]
        try:
            if ops:
                coll.bulk_write(ops, ordered=False)
            local_cat.mark_synced([d["qid"] for d in docs if d.get("qid")])
            total += len(ops)
            print(
                f"round {rnd}: synced +{len(ops)} total_sync={total} "
                f"remaining={local_cat.count_unsynced()}",
                flush=True,
            )
        except OperationFailure as exc:
            print(f"mongo blocked: {exc}", flush=True)
            return 2
        except Exception as exc:
            print(f"sync error: {exc}", flush=True)
            return 1
    print(f"done synced={total}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
