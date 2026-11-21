"""Boucle 2/3 — médias RAPIDE : ISBN prioritaire, résumés, titres FR.

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
        # ISBN : plus gros lots, moins de sleep (2 rounds media = 24 rounds ISBN)
        _run(
            "isbn",
            [
                PY,
                str(ROOT / "scripts" / "backfill_real_isbns.py"),
                "--batch",
                "80",
                "--per-doc",
                "3",
                "--rounds",
                "24",
                "--sleep",
                "0.15",
                "--skip-purge",
                "--loop",
            ],
            timeout=40 * 60,
        )
        # Résumés : moins souvent (rendement faible) — 1 media sur 2
        if n % 2 == 0:
            _run(
                "synopses",
                [
                    PY,
                    str(ROOT / "scripts" / "backfill_synopses_loop.py"),
                    "--batch",
                    "80",
                    "--rounds",
                    "8",
                    "--sleep",
                    "0.2",
                    "--loop",
                ],
                timeout=15 * 60,
            )
        _run(
            "titles_fr",
            [
                PY,
                str(ROOT / "scripts" / "backfill_french_titles.py"),
                "--phase",
                "google",
                "--workers",
                "6",
                "--limit",
                "800",
            ],
            timeout=25 * 60,
        )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
