"""Boucle 2/3 — médias turbo : résumé + ISBN en parallèle (API) + dump local.

  python scripts/_loop_media.py
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
os.environ.setdefault("CATALOG_LOCAL_SQLITE", str(ROOT / "data" / "local_catalog.sqlite"))


def _run(label: str, args: list[str], *, timeout: int) -> None:
    print(f"\n>> {label}", flush=True)
    try:
        rc = subprocess.call(args, cwd=str(ROOT), timeout=timeout)
        print(f"<< {label} rc={rc}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"<< {label} timeout>{timeout}s — continue", flush=True)


def _parallel(jobs: list[tuple[str, list[str]]], *, timeout: int) -> None:
    """Lance plusieurs enrichissements API en parallèle."""
    procs: list[tuple[str, subprocess.Popen]] = []
    for label, args in jobs:
        print(f"\n>> {label} (parallel)", flush=True)
        procs.append((label, subprocess.Popen(args, cwd=str(ROOT))))
    t0 = time.time()
    while procs:
        still: list[tuple[str, subprocess.Popen]] = []
        for label, p in procs:
            rc = p.poll()
            if rc is None:
                if time.time() - t0 > timeout:
                    print(f"<< {label} timeout>{timeout}s — kill", flush=True)
                    p.terminate()
                    try:
                        p.wait(timeout=15)
                    except Exception:
                        p.kill()
                else:
                    still.append((label, p))
            else:
                print(f"<< {label} rc={rc}", flush=True)
        procs = still
        if procs:
            time.sleep(2)


def main() -> int:
    n = 0
    while True:
        n += 1
        print(f"\n======== MEDIA #{n} ========", flush=True)

        # API parallèle (le dump local est géré par _loop_stock)
        _parallel(
            [
                (
                    "synopses",
                    [
                        PY,
                        str(ROOT / "scripts" / "backfill_synopses_loop.py"),
                        "--batch",
                        "160",
                        "--rounds",
                        "40",
                        "--sleep",
                        "0.02",
                        "--loop",
                        "--workers",
                        "14",
                    ],
                ),
                (
                    "isbn",
                    [
                        PY,
                        str(ROOT / "scripts" / "backfill_real_isbns.py"),
                        "--batch",
                        "180",
                        "--per-doc",
                        "2",
                        "--rounds",
                        "30",
                        "--sleep",
                        "0.03",
                        "--workers",
                        "12",
                        "--skip-purge",
                        "--loop",
                    ],
                ),
            ],
            timeout=45 * 60,
        )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
