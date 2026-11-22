"""Boucle 3/3 — auteurs : œuvres OL fréquentes + enrich (catalogue local rare).

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

        # Catalogue local : rare (déjà massivement fait, cache 6h)
        if n == 1 or n % 4 == 0:
            _run(
                "works_catalog",
                [
                    PY,
                    str(ROOT / "scripts" / "link_author_works_from_catalog.py"),
                    "--sqlite-only",
                ],
                timeout=30 * 60,
            )

        # OL API œuvres : chaque cycle (priorité restante)
        _run(
            "works_ol",
            [
                PY,
                str(ROOT / "scripts" / "link_author_works_from_catalog.py"),
                "--ol-api",
                "--skip-catalog",
                "--batch",
                "180",
                "--loop",
                "--max-rounds",
                "20",
                "--sqlite-only",
                "--sleep",
                "0.08",
            ],
            timeout=25 * 60,
        )

        # Enrich bio/nat
        _run(
            "enrich",
            [
                PY,
                str(ROOT / "scripts" / "backfill_authors_complete.py"),
                "--sqlite-only",
                "--fast",
                "--batch",
                "200",
                "--sleep",
                "0.03",
                "--max-batches",
                "50",
            ],
            timeout=40 * 60,
        )

        if n % 2 == 1:
            _run(
                "promote",
                [
                    PY,
                    str(ROOT / "scripts" / "promote_ol_cache_to_authors.py"),
                    "--sqlite-only",
                    "--batch",
                    "150",
                    "--sleep",
                    "0.06",
                    "--max-batches",
                    "30",
                ],
                timeout=25 * 60,
            )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
