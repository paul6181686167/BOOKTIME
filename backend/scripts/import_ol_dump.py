"""Import dump Open Library (auteurs / works / editions).

  python scripts/import_ol_dump.py --download all
  python scripts/import_ol_dump.py --authors-limit 300000
  python scripts/import_ol_dump.py --works-limit 50000 --worker-id 0 --workers 4
  python scripts/import_ol_dump.py --editions-limit 50000
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
    parser.add_argument("--download", choices=["authors", "works", "editions", "all"], default="")
    parser.add_argument("--authors-limit", type=int, default=-1, help="-1=skip, 0=all, N=cap")
    parser.add_argument("--works-limit", type=int, default=-1)
    parser.add_argument("--editions-limit", type=int, default=-1)
    parser.add_argument("--authors-file", default="")
    parser.add_argument("--works-file", default="")
    parser.add_argument("--editions-file", default="")
    parser.add_argument("--worker-id", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
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

    if args.download:
        kinds = ["authors", "works", "editions"] if args.download == "all" else [args.download]
        for kind in kinds:
            path = ol_dump_import.download_dump(kind)
            print(f"downloaded {kind} -> {path} ({path.stat().st_size} bytes)", flush=True)

    if args.authors_limit >= 0 or args.authors_file:
        print("=== authors ===", flush=True)
        print(
            ol_dump_import.import_authors_dump(
                args.authors_file or None,
                limit=max(0, args.authors_limit),
            ),
            flush=True,
        )

    if args.works_limit >= 0 or args.works_file:
        print("=== works ===", flush=True)
        print(
            ol_dump_import.import_works_dump(
                args.works_file or None,
                limit=args.works_limit if args.works_limit >= 0 else 50000,
                worker_id=args.worker_id,
                workers=max(1, args.workers),
            ),
            flush=True,
        )

    if args.editions_limit >= 0 or args.editions_file:
        print("=== editions ===", flush=True)
        print(
            ol_dump_import.import_editions_dump(
                args.editions_file or None,
                limit=args.editions_limit if args.editions_limit >= 0 else 50000,
                worker_id=args.worker_id,
                workers=max(1, args.workers),
            ),
            flush=True,
        )

    series = db["catalog_daily_series"].count_documents({})
    authors = db["authors"].count_documents({})
    print(f"catalog series={series} authors={authors} total={series + authors}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
