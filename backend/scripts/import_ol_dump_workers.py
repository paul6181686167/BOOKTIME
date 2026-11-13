"""Lance N workers parallèles sur works et/ou editions (offsets modulo).

  python scripts/import_ol_dump_workers.py --workers 4 --works-limit 40000 --editions-limit 40000
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--works-limit", type=int, default=20000)
    p.add_argument("--editions-limit", type=int, default=20000)
    p.add_argument("--download", action="store_true")
    args = p.parse_args()
    workers = max(1, min(16, args.workers))
    py = sys.executable
    script = str(ROOT / "scripts" / "import_ol_dump.py")

    if args.download:
        subprocess.run([py, script, "--download", "all"], cwd=str(ROOT), check=False)

    procs: list[subprocess.Popen] = []
    for wid in range(workers):
        cmd = [
            py,
            script,
            "--authors-limit",
            "-1",
            "--worker-id",
            str(wid),
            "--workers",
            str(workers),
        ]
        if args.works_limit > 0:
            cmd += ["--works-limit", str(args.works_limit)]
        if args.editions_limit > 0:
            cmd += ["--editions-limit", str(args.editions_limit)]
        print("spawn", " ".join(cmd), flush=True)
        procs.append(subprocess.Popen(cmd, cwd=str(ROOT)))

    codes = [p.wait() for p in procs]
    print("worker_exit_codes", codes, flush=True)
    return 0 if all(c == 0 for c in codes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
