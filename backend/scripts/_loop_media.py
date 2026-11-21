"""Boucle 2/3 — médias : résumés + ISBN (GB en 429 → OL/BnF/Wiki).

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
        # Résumés EN PREMIER (étaient starving derrière ISBN)
        _run(
            "synopses",
            [
                PY,
                str(ROOT / "scripts" / "backfill_synopses_loop.py"),
                "--batch",
                "40",
                "--rounds",
                "20",
                "--sleep",
                "0.08",
                "--loop",
            ],
            timeout=30 * 60,
        )
        # ISBN : lots plus courts, OL/BnF d'abord (moins de GB)
        _run(
            "isbn",
            [
                PY,
                str(ROOT / "scripts" / "backfill_real_isbns.py"),
                "--batch",
                "60",
                "--per-doc",
                "3",
                "--rounds",
                "10",
                "--sleep",
                "0.2",
                "--skip-purge",
                "--loop",
            ],
            timeout=25 * 60,
        )
        # Titres FR : 1 cycle sur 2
        if n % 2 == 0:
            _run(
                "titles_fr",
                [
                    PY,
                    str(ROOT / "scripts" / "backfill_french_titles.py"),
                    "--phase",
                    "google",
                    "--workers",
                    "4",
                    "--limit",
                    "400",
                ],
                timeout=20 * 60,
            )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
