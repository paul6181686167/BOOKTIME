"""Boucle 3/3 — auteurs : priorité enrichissement (rapide).

  python scripts/_loop_authors.py
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
        print(f"\n======== AUTHORS #{n} ========", flush=True)
        # Enrich = priorité absolue (3 passes pour 1 promo)
        for _ in range(3):
            _run(
                "enrich",
                [
                    PY,
                    str(ROOT / "scripts" / "backfill_authors_complete.py"),
                    "--sqlite-only",
                    "--fast",
                    "--batch",
                    "150",
                    "--sleep",
                    "0.05",
                    "--max-batches",
                    "60",
                ],
                timeout=45 * 60,
            )
        # Promo cache : moins souvent
        if n % 2 == 1:
            _run(
                "promote",
                [
                    PY,
                    str(ROOT / "scripts" / "promote_ol_cache_to_authors.py"),
                    "--sqlite-only",
                    "--batch",
                    "100",
                    "--sleep",
                    "0.1",
                    "--max-batches",
                    "20",
                ],
                timeout=25 * 60,
            )
        # Œuvres OL : rare (coûteux / souvent 0 hit)
        if n % 4 == 0:
            _run(
                "works",
                [
                    PY,
                    str(ROOT / "scripts" / "link_author_works_from_catalog.py"),
                    "--ol-api",
                    "--batch",
                    "100",
                    "--loop",
                    "--max-rounds",
                    "8",
                    "--skip-catalog",
                    "--sqlite-only",
                    "--sleep",
                    "0.2",
                ],
                timeout=15 * 60,
            )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
