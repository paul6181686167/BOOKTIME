"""Boucle 2/3 — médias turbo : résumés + ISBN en parallèle de lots.

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


def main() -> int:
    n = 0
    while True:
        n += 1
        print(f"\n======== MEDIA #{n} ========", flush=True)

        _run(
            "synopses",
            [
                PY,
                str(ROOT / "scripts" / "backfill_synopses_loop.py"),
                "--batch",
                "120",
                "--rounds",
                "30",
                "--sleep",
                "0.03",
                "--loop",
                "--workers",
                "10",
            ],
            timeout=40 * 60,
        )

        _run(
            "isbn",
            [
                PY,
                str(ROOT / "scripts" / "backfill_real_isbns.py"),
                "--batch",
                "150",
                "--per-doc",
                "2",
                "--rounds",
                "24",
                "--sleep",
                "0.05",
                "--workers",
                "8",
                "--skip-purge",
                "--loop",
            ],
            timeout=35 * 60,
        )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
