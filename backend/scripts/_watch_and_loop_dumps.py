"""Attend la fin des workers en cours, puis lance la boucle dump works+editions."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
py = sys.executable

# Tampon local (SQLite) tant qu'Atlas est saturé
os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
os.environ.setdefault("CATALOG_DUMP_LOCAL_ONLY", "1")
os.environ.setdefault(
    "CATALOG_LOCAL_SQLITE",
    str(ROOT / "data" / "local_catalog.sqlite"),
)


def _editions_ready() -> bool:
    p = ROOT / "data" / "ol_dumps" / "ol_dump_editions_latest.txt.gz"
    return p.exists() and p.stat().st_size > 1_000_000


def main() -> int:
    # Attendre qu'aucun import_ol_dump.py worker ne tourne (hors download)
    print("waiting previous dump workers…", flush=True)
    while True:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -match 'import_ol_dump.py --authors-limit' } | "
             "Measure-Object | Select-Object -ExpandProperty Count"],
            text=True,
        ).strip()
        try:
            n = int(out or "0")
        except ValueError:
            n = 0
        print(f"active_workers={n}", flush=True)
        if n == 0:
            break
        time.sleep(20)

    if not _editions_ready():
        print("downloading editions dump…", flush=True)
        subprocess.run(
            [py, str(ROOT / "scripts" / "import_ol_dump.py"), "--download", "editions"],
            cwd=str(ROOT),
            check=False,
        )

    # 1 lecteur gzip + lots illimités (0) : un seul fast-skip puis jusqu'à EOF
    print("starting loop works+editions (1 worker, fast-skip, unlimited)…", flush=True)
    return subprocess.call(
        [
            py,
            str(ROOT / "scripts" / "import_ol_dump_workers.py"),
            "--loop",
            "--workers",
            "1",
            "--works-limit",
            "0",
            "--editions-limit",
            "0",
            "--sleep",
            "5",
        ],
        cwd=str(ROOT),
    )


if __name__ == "__main__":
    raise SystemExit(main())
