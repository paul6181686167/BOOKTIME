"""Remplit total_pages manquant via Google Books / Open Library."""
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
        if not (isinstance(b.get("total_pages"), (int, float)) and int(b.get("total_pages") or 0) > 0)
    ]
    print(f"sans pages: {len(books)}")
    filled = 0
    for b in books:
        title = b.get("title") or ""
        result = fetch_book_synopsis(
            title=title,
            author=b.get("author") or "",
            isbn=b.get("isbn") or b.get("isbn13") or "",
            ol_key=b.get("ol_key") or "",
        )
        pages = result.get("pages")
        print(f"  [{result.get('source')}] {title[:50]!r} -> pages={pages}")
        if not pages:
            continue
        books_collection.update_one(
            {"id": b.get("id")},
            {"$set": {"total_pages": int(pages)}},
        )
        filled += 1
    print(f"remplis: {filled}/{len(books)}")


if __name__ == "__main__":
    main()
