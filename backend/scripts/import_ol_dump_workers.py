"""Lance N workers parallèles sur works et/ou editions (offsets modulo).

  python scripts/import_ol_dump_workers.py --workers 4 --works-limit 40000 --editions-limit 40000
  python scripts/import_ol_dump_workers.py --loop --workers 4 --works-limit 50000 --editions-limit 50000
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _spawn_round(
    *,
    py: str,
    script: str,
    workers: int,
    works_limit: int,
    editions_limit: int,
) -> int:
    procs: list[subprocess.Popen] = []
    for wid in range(workers):
        cmd = [
            py,
            script,
            "--authors-limit",
            "-1",
            "--worker-id",
            str(wid),
            "--workers",
            str(workers),
        ]
        # 0 = illimité (jusqu'à EOF) ; -1 = skip cette phase
        cmd += ["--works-limit", str(works_limit), "--editions-limit", str(editions_limit)]
        print("spawn", " ".join(cmd), flush=True)
        procs.append(subprocess.Popen(cmd, cwd=str(ROOT)))

    codes = [p.wait() for p in procs]
    print("worker_exit_codes", codes, flush=True)
    return 0 if all(c == 0 for c in codes) else 1


def _catalog_total() -> int:
    """Compte le stock de référence : SQLite PC si dump local, sinon Mongo."""
    try:
        sys.path.insert(0, str(ROOT))
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

        local_only = (os.environ.get("CATALOG_DUMP_LOCAL_ONLY") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        if local_only or (os.environ.get("CATALOG_DUMP_LOCAL") or "1").strip() not in {
            "0",
            "false",
            "no",
            "off",
        }:
            import sqlite3

            db_path = Path(
                os.environ.get("CATALOG_LOCAL_SQLITE")
                or (ROOT / "data" / "local_catalog.sqlite")
            )
            if db_path.exists():
                con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
                try:
                    series = con.execute(
                        "SELECT COUNT(*) FROM catalog_daily_series"
                    ).fetchone()[0]
                    authors = con.execute(
                        "SELECT COUNT(*) FROM catalog_authors"
                    ).fetchone()[0]
                    return int(series + authors)
                finally:
                    con.close()

        os.environ["RAILWAY_MONGODB_MOCK"] = "false"
        from pymongo import MongoClient

        client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=15000)
        db = client[os.environ.get("DATABASE_NAME") or "booktime"]
        series = db["catalog_daily_series"].count_documents({})
        authors = db["authors"].count_documents({})
        return int(series + authors)
    except Exception as exc:
        print(f"catalog_total_error {exc}", flush=True)
        return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--works-limit", type=int, default=20000)
    p.add_argument("--editions-limit", type=int, default=20000)
    p.add_argument("--download", action="store_true")
    p.add_argument("--loop", action="store_true", help="relance tant que goal non atteint")
    p.add_argument("--goal", type=int, default=1000000)
    p.add_argument("--sleep", type=int, default=8, help="pause entre rounds (loop)")
    p.add_argument("--max-rounds", type=int, default=0, help="0 = illimité (loop)")
    args = p.parse_args()
    workers = max(1, min(16, args.workers))
    py = sys.executable
    script = str(ROOT / "scripts" / "import_ol_dump.py")

    if args.download:
        subprocess.run([py, script, "--download", "all"], cwd=str(ROOT), check=False)

    rounds = 0
    while True:
        rounds += 1
        total = _catalog_total()
        print(f"=== dump round {rounds} total={total} goal={args.goal} ===", flush=True)
        if total >= args.goal:
            print("goal reached", flush=True)
            return 0
        code = _spawn_round(
            py=py,
            script=script,
            workers=workers,
            works_limit=args.works_limit,
            editions_limit=args.editions_limit,
        )
        if not args.loop:
            return code
        if args.max_rounds and rounds >= args.max_rounds:
            print(f"max_rounds={args.max_rounds} reached", flush=True)
            return code
        time.sleep(max(0, args.sleep))


if __name__ == "__main__":
    raise SystemExit(main())
