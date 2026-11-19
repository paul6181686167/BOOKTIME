"""Boucle 1/3 — stock : dumps OL + jaquettes.

  python scripts/_loop_stock.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
os.environ.setdefault("CATALOG_DUMP_LOCAL_ONLY", "1")
os.environ.setdefault("CATALOG_LOCAL_SQLITE", str(ROOT / "data" / "local_catalog.sqlite"))


def _run(label: str, args: list[str], *, timeout: int) -> None:
    print(f"\n>> {label}", flush=True)
    try:
        rc = subprocess.call(args, cwd=str(ROOT), timeout=timeout)
        print(f"<< {label} rc={rc}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"<< {label} timeout>{timeout}s — continue", flush=True)


def main() -> int:
    n = 0
    while True:
        n += 1
        print(f"\n======== STOCK #{n} ========", flush=True)
        _run(
            "dumps",
            [
                PY,
                str(ROOT / "scripts" / "import_ol_dump_workers.py"),
                "--workers",
                "1",
                "--works-limit",
                "12000",
                "--editions-limit",
                "12000",
                "--sleep",
                "3",
            ],
            timeout=45 * 60,
        )
        _run(
            "covers",
            [
                PY,
                str(ROOT / "scripts" / "backfill_all_covers.py"),
                "--workers",
                "2",
                "--limit",
                "800",
            ],
            timeout=25 * 60,
        )
        # Fiches quotidiennes (Wikidata/OL curated) — lot borné
        _run(
            "daily",
            [
                PY,
                str(ROOT / "scripts" / "run_daily_ingest.py"),
                "--sync",
                "--limit",
                "80",
            ],
            timeout=35 * 60,
        )
        time.sleep(4)


if __name__ == "__main__":
    raise SystemExit(main())
