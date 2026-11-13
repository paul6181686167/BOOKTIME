"""Boucle backfill œuvres 24/7 : dump OL + auteurs×WD + API multi-sources.

  python scripts/backfill_works_loop.py --rounds 20 --works-limit 20000
  python scripts/backfill_works_loop.py --no-dump --api-cap 5000 --rounds 100
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
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


def _log(msg: str) -> None:
    print(msg, flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=50)
    p.add_argument("--works-limit", type=int, default=20000, help="œuvres dump OL par round")
    p.add_argument("--api-cap", type=int, default=3000, help="fiches via API OL/GB/BnF/WD par round")
    p.add_argument("--recover-cap", type=int, default=2000, help="auteurs DB × Wikidata par round")
    p.add_argument("--authors-seed", type=int, default=300000, help="cache auteurs OL au 1er passage")
    p.add_argument("--no-dump", action="store_true")
    p.add_argument("--sleep", type=int, default=5)
    args = p.parse_args()

    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    os.environ.setdefault("CATALOG_ADD_AUTHORS", "0")
    os.environ["ENVIRONMENT"] = "production"

    from pymongo import MongoClient
    from app.db_config import database
    from app.catalog.isbn_resolve import reset_budget, reset_cover_budget
    from app.catalog.daily_ingest import (
        catalog_fiche_total,
        catalog_goal,
        run_works_backfill,
        meta_save_pair,
    )

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    db = client[os.environ.get("DATABASE_NAME") or "booktime"]
    database._client = client
    database._db = db
    meta_save_pair("ingest_focus", 1, 0)

    goal = catalog_goal()
    for rnd in range(1, args.rounds + 1):
        total = catalog_fiche_total()
        if total >= goal:
            _log(f"goal reached total={total}/{goal}")
            break
        _log(f"=== round {rnd}/{args.rounds} total={total} remaining={goal - total} ===")
        reset_budget(0)
        reset_cover_budget(100)

        if not args.no_dump:
            try:
                from app.catalog import ol_dump_import

                cached = 0
                try:
                    cached = int(db["ol_author_cache"].estimated_document_count())
                except Exception:
                    cached = 0
                prog = ol_dump_import.load_progress()
                if not prog.get("authors_done") and cached < 100000:
                    _log(f"seeding authors cache (cap {args.authors_seed})…")
                    _log(str(ol_dump_import.import_authors_dump(limit=args.authors_seed)))
                _log(str(ol_dump_import.import_works_dump(limit=args.works_limit)))
            except Exception as exc:
                _log(f"dump_err {exc}")

        try:
            env = os.environ.copy()
            env["RECOVER_WORKS_CAP"] = str(args.recover_cap)
            env["RECOVER_AUTHORS_SCAN"] = "4000"
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "recover_author_works.py")],
                cwd=str(ROOT),
                env=env,
                check=False,
            )
        except Exception as exc:
            _log(f"recover_err {exc}")

        try:
            res = run_works_backfill(args.api_cap)
            _log(f"api_backfill fiches={res.get('fiches')} catalog={res.get('catalog_fiches')}")
        except Exception as exc:
            _log(f"api_err {exc}")

        time.sleep(max(0, args.sleep))

    _log(f"done total={catalog_fiche_total()}/{goal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
