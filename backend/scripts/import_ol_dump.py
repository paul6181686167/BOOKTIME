"""Import dump Open Library (auteurs puis œuvres) vers Mongo live.

Exemples :
  python scripts/import_ol_dump.py --authors-limit 500000
  python scripts/import_ol_dump.py --works-limit 80000
  python scripts/import_ol_dump.py --works-limit 100000 --works-file D:/data/ol_dump_works.txt.gz
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--authors-limit", type=int, default=0, help="0 = tout le dump auteurs")
    parser.add_argument("--works-limit", type=int, default=50000)
    parser.add_argument("--authors-file", default="", help="chemin local dump auteurs .gz")
    parser.add_argument("--works-file", default="", help="chemin local dump works .gz")
    parser.add_argument("--skip-authors", action="store_true")
    parser.add_argument("--authors-only", action="store_true")
    args = parser.parse_args()

    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    os.environ.setdefault("CATALOG_ADD_AUTHORS", "0")

    from pymongo import MongoClient
    from app.db_config import database
    from app.catalog.isbn_resolve import reset_budget, reset_cover_budget
    from app.catalog import ol_dump_import

    reset_budget(0)
    reset_cover_budget(0)

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    db = client[os.environ.get("DATABASE_NAME") or "booktime"]
    database._client = client
    database._db = db

    if not args.skip_authors:
        print("=== authors dump ===", flush=True)
        stats = ol_dump_import.import_authors_dump(
            args.authors_file or None,
            limit=args.authors_limit,
        )
        print(stats, flush=True)
        if args.authors_only:
            return 0

    print("=== works dump ===", flush=True)
    stats = ol_dump_import.import_works_dump(
        args.works_file or None,
        limit=args.works_limit,
    )
    print(stats, flush=True)
    series = db["catalog_daily_series"].count_documents({})
    authors = db["authors"].count_documents({})
    print(f"catalog series={series} authors={authors} total={series + authors}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
