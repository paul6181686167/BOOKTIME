"""Lance un passage fiches quotidiennes (sync).

  python scripts/run_daily_ingest.py --sync --limit 80
"""
from __future__ import annotations

import argparse
import json
import os
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sync", action="store_true", default=True)
    p.add_argument("--limit", type=int, default=80, help="cap séries/livres ce passage")
    p.add_argument("--authors-limit", type=int, default=40)
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    os.environ.setdefault(
        "CATALOG_LOCAL_SQLITE", str(ROOT / "data" / "local_catalog.sqlite")
    )
    # Budgets raisonnables pour un lot
    os.environ.setdefault("CATALOG_DAILY_SERIES", str(max(10, args.limit)))
    os.environ.setdefault("CATALOG_DAILY_BOOKS", str(max(10, args.limit)))
    os.environ.setdefault("CATALOG_ISBN_LOOKUPS", "120")
    os.environ.setdefault("CATALOG_COVER_LOOKUPS", "200")
    os.environ.setdefault("CATALOG_SYNOPSIS_LOOKUPS", "40")

    from app.catalog.daily_ingest import run_daily_ingest

    result = run_daily_ingest(
        limit=args.limit,
        books_limit=args.limit,
        authors_limit=args.authors_limit,
    )
    print(json.dumps(result, ensure_ascii=False, default=str), flush=True)
    return 0 if (result or {}).get("status") in ("ok", "busy", None) or result else 0


if __name__ == "__main__":
    raise SystemExit(main())
