#!/usr/bin/env python3
"""Nettoyage après strip d'emojis : espaces en tête de labels, placeholders vides."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src"

# label/title/text/description: ' Foo' ou " Foo"
PROP_LEAD = re.compile(
    r"""((?:label|title|text|description|message|placeholder|aria-label)\s*:\s*)(['"])\s+""",
    re.I,
)

# Placeholders décoratifs devenus vides
EMPTY_DECOR = [
    re.compile(r"""[ \t]*<div className="text-(?:[345]|6)xl[^"]*"></div>\r?\n"""),
    re.compile(r"""[ \t]*<span className="text-(?:[345]|6)xl[^"]*"></span>\r?\n"""),
    re.compile(r"""[ \t]*<span className="text-(?:[345]|6)xl[^"]*block"></span>\r?\n"""),
    re.compile(r"""[ \t]*<span className="text-2xl opacity-90"></span>\r?\n?"""),
    re.compile(r"""[ \t]*<span className="text-xl opacity-90"></span>\r?\n?"""),
    re.compile(r"""[ \t]*<div className="text-5xl mb-4 opacity-40"></div>\r?\n"""),
    re.compile(r"""[ \t]*<div className="text-5xl mb-3"></div>\r?\n"""),
]

# toast / props icon|emoji vides
TOAST_EMPTY_ICON = re.compile(r""",\s*\{\s*icon:\s*['\"]['\"]\s*\}""")
ICON_PROP_EMPTY = re.compile(r""",\s*icon:\s*['\"]['\"]""")
EMOJI_PROP_EMPTY = re.compile(r""",\s*emoji:\s*['\"]['\"]""")

# Libellés UI après emoji : ' Stats' / " Objectif"
UI_LEAD = re.compile(
    r"""((?:label|title|text|description|message)\s*:\s*)(['"])[ \t]+""",
    re.I,
)


def clean(text: str) -> str:
    text = PROP_LEAD.sub(r"\1\2", text)
    text = UI_LEAD.sub(r"\1\2", text)
    for rx in EMPTY_DECOR:
        text = rx.sub("", text)
    text = TOAST_EMPTY_ICON.sub("", text)
    text = ICON_PROP_EMPTY.sub("", text)
    text = EMOJI_PROP_EMPTY.sub("", text)
    return text


def main() -> None:
    skip = {"__tests__", "node_modules"}
    n = 0
    for path in ROOT.rglob("*"):
        if path.suffix not in {".js", ".jsx"}:
            continue
        if any(p in skip for p in path.parts):
            continue
        original = path.read_text(encoding="utf-8")
        updated = clean(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            n += 1
            print(f"cleaned {path.relative_to(ROOT)}")
    print(f"done: {n} files")


if __name__ == "__main__":
    main()
