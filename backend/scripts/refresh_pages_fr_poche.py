"""Recalcule total_pages en priorisant l'édition poche française."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db_config import books_collection, database
from app.utils.book_synopsis import fetch_french_paperback_pages, fetch_book_synopsis


def main() -> None:
    print("mock=", database.is_mock_mode(), flush=True)
    books = list(books_collection.find({}))
    print(f"livres: {len(books)}", flush=True)
    updated = 0
    for b in books:
        title = b.get("title") or ""
        old = b.get("total_pages")
        hit = fetch_french_paperback_pages(
            title=title,
            author=b.get("author") or "",
            isbn=b.get("isbn") or b.get("isbn13") or "",
            ol_key=b.get("ol_key") or "",
        )
        pages = hit.get("pages") if hit else None
        src = hit.get("source") if hit else None
        if not pages:
            syn = fetch_book_synopsis(
                title=title,
                author=b.get("author") or "",
                isbn=b.get("isbn") or b.get("isbn13") or "",
                ol_key=b.get("ol_key") or "",
            )
            pages = syn.get("pages")
            src = syn.get("pages_source") or syn.get("source")
        print(f"  {title[:45]!r}: {old} -> {pages} [{src}]", flush=True)
        if not pages or int(pages) == old:
            continue
        books_collection.update_one(
            {"id": b.get("id")},
            {"$set": {"total_pages": int(pages), "pages_edition": "fr_poche"}},
        )
        updated += 1
    print(f"updated={updated}", flush=True)


if __name__ == "__main__":
    main()
