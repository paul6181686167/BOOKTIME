"""Remplit les descriptions manquantes (4ᵉ de couverture) pour tous les livres."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db_config import books_collection, database
from app.utils.book_synopsis import fetch_book_synopsis


def main() -> None:
    print("mock=", database.is_mock_mode())
    books = [
        b
        for b in books_collection.find({})
        if not (b.get("description") or "").strip()
    ]
    print(f"sans resume: {len(books)}")
    filled = 0
    for b in books:
        title = b.get("title") or ""
        result = fetch_book_synopsis(
            title=title,
            author=b.get("author") or "",
            isbn=b.get("isbn") or b.get("isbn13") or "",
            ol_key=b.get("ol_key") or "",
        )
        desc = (result.get("description") or "").strip()
        src = result.get("source")
        print(f"  [{src}] {title[:60]!r} -> {len(desc)} chars")
        if not desc:
            continue
        patch = {"description": desc}
        if result.get("ol_key") and not b.get("ol_key"):
            patch["ol_key"] = result["ol_key"]
        books_collection.update_one({"id": b.get("id")}, {"$set": patch})
        filled += 1
    print(f"remplis: {filled}/{len(books)}")


if __name__ == "__main__":
    main()
