#!/usr/bin/env python3
"""Retire uniquement les emojis pictographiques du frontend (UI).

Conserve l'indentation et les symboles UI simples (✓ ✕ ★ ← →).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src"

# Pas de dingbats 2700–27BF (contient ✓ ✕) ni misc 2600 (contient ★)
EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U0000FE0F"  # variation selector
    "\U0000200D"  # ZWJ
    "]+"
)

# Symboles isolés fréquents hors plages ci-dessus
EXTRA = re.compile(
    "["
    "\u231A-\u231B"  # watch
    "\u23E9-\u23F3"
    "\u23F8-\u23FA"
    "\u25AA-\u25AB"
    "\u25B6\u25C0"
    "\u25FB-\u25FE"
    "\u26A0"  # ⚠
    "\u2614-\u2615"
    "\u2648-\u2653"
    "\u267F"
    "\u2693"
    "\u26A1"
    "\u26AA-\u26AB"
    "\u26BD-\u26BE"
    "\u26C4-\u26C5"
    "\u26CE"
    "\u26D4"
    "\u26EA"
    "\u26F2-\u26F3"
    "\u26F5"
    "\u26FA"
    "\u26FD"
    "\u2702"
    "\u2705"  # ✅ white heavy check - emoji style
    "\u2708-\u270D"
    "\u270F"
    "\u2712"
    "\u2714"  # ✔
    "\u2716"
    "\u271D"
    "\u2721"
    "\u2728"  # ✨
    "\u2733-\u2734"
    "\u2744"
    "\u2747"
    "\u274C"  # ❌
    "\u274E"
    "\u2753-\u2755"
    "\u2757"
    "\u2763-\u2764"
    "\u2795-\u2797"
    "\u27A1"
    "\u27B0"
    "\u27BF"
    "\u2934-\u2935"
    "\u2B05-\u2B07"
    "\u2B1B-\u2B1C"
    "\u2B50"
    "\u2B55"
    "\u3030"
    "\u303D"
    "\u3297"
    "\u3299"
    "]"
)


def clean(text: str) -> str:
    text = EMOJI_RE.sub("", text)
    text = EXTRA.sub("", text)
    return text


def main() -> None:
    skip = {"__tests__", "node_modules"}
    n_files = 0
    for path in ROOT.rglob("*"):
        if path.suffix not in {".js", ".jsx"}:
            continue
        if any(part in skip for part in path.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = clean(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            n_files += 1
            print(f"updated {path.relative_to(ROOT)}")
    print(f"done: {n_files} files")


if __name__ == "__main__":
    main()
