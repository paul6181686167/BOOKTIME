#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src"

PROP = re.compile(
    r"""((?:label|title|text|description|message|placeholder)\s*:\s*)(['"])[ \t]+""",
    re.I,
)
TOAST = re.compile(r"""(toast\.(?:success|error)\()(['"])[ \t]+""")
GEAR = "\u2699"


def main() -> None:
    n = 0
    for path in ROOT.rglob("*.js"):
        if "__tests__" in path.parts:
            continue
        original = path.read_text(encoding="utf-8")
        updated = PROP.sub(r"\1\2", original)
        updated = TOAST.sub(r"\1\2", updated)
        updated = updated.replace(f"{GEAR} ", "").replace(GEAR, "")
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            n += 1
            print(path.relative_to(ROOT))
    print(f"done {n}")


if __name__ == "__main__":
    main()
