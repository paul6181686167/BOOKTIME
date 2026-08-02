"""
Recalcule les catégories bd/manga via recherche Open Library + mémoire tampon.
Usage: python scripts/reclassify_library_categories.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db_config import books_collection, database
from app.utils.category_verify import reclassify_books
from app.utils.category_buffer import buffer_stats


def main() -> None:
    print("mock_mode=", database.is_mock_mode())
    books = list(books_collection.find({"category": {"$in": ["bd", "manga"]}}))
    print(f"livres bd/manga a verifier: {len(books)}")
    for b in books[:20]:
        print(f"  - {b.get('title')!r} | {b.get('author')!r} | {b.get('category')}")

    report = reclassify_books(books, only_suspicious=True, force=True)
    updated = report.get("updated") or []
    print(f"checked={report.get('checked')} unchanged={report.get('unchanged')} to_update={len(updated)}")
    applied = 0
    for u in updated:
        res = books_collection.update_one(
            {"id": u["id"]},
            {"$set": {"category": u["new_category"], "category_verified": True}},
        )
        applied += int(getattr(res, "modified_count", 0) or 0)
        print(
            f"  FIX {u.get('title')!r}: {u.get('old_category')} -> {u.get('new_category')} ({u.get('source')})"
        )
    # Marquer le reste comme verifie
    for b in books:
        if not any(u.get("id") == b.get("id") for u in updated):
            books_collection.update_one(
                {"id": b.get("id")},
                {"$set": {"category_verified": True}},
            )
    print(f"applied={applied} buffer={buffer_stats()}")


if __name__ == "__main__":
    main()
