"""Boucle 1/3 — stock : dumps OL prioritaires (croissance fiches).

Jaquettes / daily en fond rare — ne plus bloquer SQLite 20 min pour 0 cover.

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
    print("======== STOCK (dumps prioritaires) ========", flush=True)
    dump = subprocess.Popen(
        [
            PY,
            str(ROOT / "scripts" / "import_ol_dump_workers.py"),
            "--loop",
            "--workers",
            "1",
            "--works-limit",
            "0",
            "--editions-limit",
            "0",
            "--sleep",
            "1",
        ],
        cwd=str(ROOT),
    )
    print(f"dumps pid={dump.pid}", flush=True)

    n = 0
    try:
        while True:
            n += 1
            print(f"\n======== STOCK side #{n} ========", flush=True)
            if dump.poll() is not None:
                print("dumps mort — relance", flush=True)
                dump = subprocess.Popen(
                    [
                        PY,
                        str(ROOT / "scripts" / "import_ol_dump_workers.py"),
                        "--loop",
                        "--workers",
                        "1",
                        "--works-limit",
                        "0",
                        "--editions-limit",
                        "0",
                        "--sleep",
                        "1",
                    ],
                    cwd=str(ROOT),
                )
                print(f"dumps pid={dump.pid}", flush=True)

            # Laisser le dump respirer (SQLite) — side jobs rares
            time.sleep(90)

            # Jaquettes : petit lot, rare (rendement souvent 0)
            if n % 4 == 0:
                _run(
                    "covers",
                    [
                        PY,
                        str(ROOT / "scripts" / "backfill_all_covers.py"),
                        "--workers",
                        "2",
                        "--limit",
                        "400",
                    ],
                    timeout=8 * 60,
                )

            # Daily Atlas : très rare
            if n % 8 == 1:
                _run(
                    "daily",
                    [
                        PY,
                        str(ROOT / "scripts" / "run_daily_ingest.py"),
                        "--sync",
                        "--limit",
                        "80",
                    ],
                    timeout=12 * 60,
                )
    finally:
        if dump.poll() is None:
            dump.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
