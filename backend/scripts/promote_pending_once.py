"""Backfill one-shot : promote la file pending (hors fiches quotidiennes)."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
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
    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    os.environ.setdefault("ENVIRONMENT", "development")
    _log("boot")

    from pymongo import MongoClient

    mongo_url = os.environ.get("MONGO_URL") or ""
    db_name = os.environ.get("DATABASE_NAME") or "booktime"
    if not mongo_url:
        _log("no_mongo_url")
        return 2
    _log("mongo_connect")
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=20000, connectTimeoutMS=20000)
    client.admin.command("ping")
    db = client[db_name]
    pending_n = db["catalog_daily_pending"].count_documents({})
    _log(f"pending_before={pending_n}")
    if pending_n <= 0:
        _log("nothing_to_do")
        return 0

    # Branche l'app sur le même client déjà ouvert.
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    from app.db_config import database
    from app.catalog import daily_ingest, daily_pending

    # Remplace la connexion lazy par celle déjà pingée si possible.
    database._client = client
    database._db = db
    _log("promote_start")
    t0 = time.time()
    got = daily_pending.enrich_and_promote(cap=max(pending_n, 250), force=True)
    _log(f"promote_done_sec={int(time.time() - t0)}")
    after = daily_pending.count()
    _log("covers_start")
    covers = daily_ingest.complete_missing_covers(cap=400)
    _log(
        "promoted_fiches={fiches} series={series} books={books} authors={authors} "
        "pending_after={after} covers_filled={covers}".format(
            fiches=got.get("fiches"),
            series=got.get("added_series"),
            books=got.get("added_books"),
            authors=got.get("added_authors"),
            after=after,
            covers=covers,
        )
    )
    names = list(got.get("names") or [])[:12]
    if names:
        _log("sample=" + " | ".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
