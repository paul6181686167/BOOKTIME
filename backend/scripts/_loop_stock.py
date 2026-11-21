"""Boucle 1/3 — stock RAPIDE : dumps OL en continu + jaquettes/daily en parallèle.

Le dump ne redémarre plus (évite de re-fast-skip 18M lignes à chaque lot).

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
    print("======== STOCK (dumps continus) ========", flush=True)
    # 1 worker, lots illimités, boucle interne : un seul fast-skip puis flux continu
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
            "2",
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
                        "2",
                    ],
                    cwd=str(ROOT),
                )
            _run(
                "covers",
                [
                    PY,
                    str(ROOT / "scripts" / "backfill_all_covers.py"),
                    "--workers",
                    "3",
                    "--limit",
                    "2000",
                ],
                timeout=20 * 60,
            )
            # Daily seulement 1 side sur 3 (Atlas souvent plein)
            if n % 3 == 1:
                _run(
                    "daily",
                    [
                        PY,
                        str(ROOT / "scripts" / "run_daily_ingest.py"),
                        "--sync",
                        "--limit",
                        "120",
                    ],
                    timeout=25 * 60,
                )
            time.sleep(2)
    finally:
        if dump.poll() is None:
            dump.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
