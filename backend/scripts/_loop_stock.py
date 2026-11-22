"""Boucle 1/3 — stock jusqu'à 1M, puis enrichissement dump-local uniquement.

Plus d'ajout de fiches après CATALOG_CAP. Priorité : ISBN/jaquettes/résumés
depuis les dumps OL locaux (sans API).

  python scripts/_loop_stock.py
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
CAP = int(os.environ.get("CATALOG_CAP") or 1_000_000)

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


def _catalog_total() -> int:
    db = Path(os.environ["CATALOG_LOCAL_SQLITE"])
    if not db.exists():
        return 0
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=60)
    try:
        series = int(con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0])
        authors = int(con.execute("SELECT COUNT(*) FROM catalog_authors").fetchone()[0])
        return series + authors
    finally:
        con.close()


def _spawn_dumps() -> subprocess.Popen:
    return subprocess.Popen(
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
            "--goal",
            str(CAP),
            "--sleep",
            "2",
        ],
        cwd=str(ROOT),
    )


def main() -> int:
    total = _catalog_total()
    print(f"======== STOCK total={total} cap={CAP} ========", flush=True)
    dump: subprocess.Popen | None = None
    if total < CAP:
        dump = _spawn_dumps()
        print(f"dumps pid={dump.pid} (stop à {CAP})", flush=True)
    else:
        print("CAP atteint — plus d'ajout, mode enrichissement dump", flush=True)

    n = 0
    try:
        while True:
            n += 1
            total = _catalog_total()
            print(f"\n======== STOCK #{n} total={total}/{CAP} ========", flush=True)

            if total >= CAP:
                if dump is not None and dump.poll() is None:
                    print("CAP — arrêt dumps", flush=True)
                    dump.terminate()
                    try:
                        dump.wait(timeout=30)
                    except Exception:
                        dump.kill()
                    dump = None
            elif dump is None:
                dump = _spawn_dumps()
                print(f"dumps relancés pid={dump.pid}", flush=True)
            elif dump.poll() is not None:
                if total < CAP:
                    print("dumps mort — relance", flush=True)
                    dump = _spawn_dumps()
                    print(f"dumps pid={dump.pid}", flush=True)

            # Enrichissement local (UPDATE only) — cœur de la complétion
            _run(
                "enrich_dumps",
                [
                    PY,
                    str(ROOT / "scripts" / "enrich_existing_from_ol_dumps.py"),
                    "--phase",
                    "both",
                    "--max-lines",
                    "800000",
                ],
                timeout=75 * 60,
            )

            _run(
                "covers",
                [
                    PY,
                    str(ROOT / "scripts" / "backfill_all_covers.py"),
                    "--workers",
                    "12",
                    "--limit",
                    "3000",
                ],
                timeout=20 * 60,
            )
            time.sleep(2)
    finally:
        if dump is not None and dump.poll() is None:
            dump.terminate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
