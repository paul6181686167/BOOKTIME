from pathlib import Path

p = Path(__file__).resolve().parents[1] / "frontend/src/services/seriesLibraryService.js"
t = p.read_text(encoding="utf-8")
old = "%3E%3C/text%3E%3C/svg%3E"
new = "%3EB%3C/text%3E%3C/svg%3E"
if old in t and "%3EB%3C/text" not in t:
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    print("ok")
else:
    print("skip", old in t, "%3EB%3C/text" in t)
