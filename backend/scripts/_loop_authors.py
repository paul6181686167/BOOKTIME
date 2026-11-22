"""Boucle 3/3 — auteurs : enrichissement bio/œuvres (cache déjà promu).

  python scripts/_loop_authors.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
PROMOTE_PROG = ROOT / "data" / "_promote_cache_authors_progress.json"

os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
os.environ.setdefault("CATALOG_LOCAL_SQLITE", str(ROOT / "data" / "local_catalog.sqlite"))


def _run(label: str, args: list[str], *, timeout: int) -> None:
    print(f"\n>> {label}", flush=True)
    try:
        rc = subprocess.call(args, cwd=str(ROOT), timeout=timeout)
        print(f"<< {label} rc={rc}", flush=True)
    except subprocess.TimeoutExpired:
        print(f"<< {label} timeout>{timeout}s — continue", flush=True)


def _cache_done() -> bool:
    if not PROMOTE_PROG.exists():
        return False
    try:
        p = json.loads(PROMOTE_PROG.read_text(encoding="utf-8"))
        return int(p.get("offset") or 0) >= 300000
    except Exception:
        return False


def main() -> int:
    n = 0
    while True:
        n += 1
        print(f"\n======== AUTHORS #{n} ========", flush=True)

        if not _cache_done():
            _run(
                "promote",
                [
                    PY,
                    str(ROOT / "scripts" / "promote_ol_cache_to_authors.py"),
                    "--sqlite-only",
                    "--fast",
                    "--batch",
                    "200",
                    "--sleep",
                    "0.02",
                    "--max-batches",
                    "100",
                ],
                timeout=60 * 60,
            )

        _run(
            "enrich",
            [
                PY,
                str(ROOT / "scripts" / "backfill_authors_complete.py"),
                "--sqlite-only",
                "--fast",
                "--batch",
                "220",
                "--sleep",
                "0.02",
                "--max-batches",
                "80",
            ],
            timeout=50 * 60,
        )

        if n % 2 == 0:
            _run(
                "works_catalog",
                [
                    PY,
                    str(ROOT / "scripts" / "link_author_works_from_catalog.py"),
                    "--sqlite-only",
                ],
                timeout=25 * 60,
            )
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
