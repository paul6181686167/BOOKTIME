"""Recalcule catégories des séries bibliothèque (bd/manga) via OL + tampon."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db_config import series_library_collection, database
from app.utils.category_verify import verify_category_via_search
from app.utils.category_buffer import buffer_stats


def main() -> None:
    print("mock_mode=", database.is_mock_mode())
    series = list(series_library_collection.find({}))
    suspicious = [s for s in series if s.get("category") in ("bd", "manga")]
    print(f"series total={len(series)} suspicious={len(suspicious)}")
    updated = 0
    for s in suspicious:
        name = s.get("name") or s.get("series_name") or s.get("title") or ""
        author = s.get("author") or s.get("authors") or ""
        if isinstance(author, list):
            author = ", ".join(str(a) for a in author)
        old = s.get("category")
        result = verify_category_via_search(name, author, force=True, current_category=old)
        new = result["category"]
        print(f"  {name!r} | {author!r} | {old} -> {new} ({result.get('source')})")
        if new != old:
            series_library_collection.update_one(
                {"id": s.get("id")} if s.get("id") else {"_id": s.get("_id")},
                {"$set": {"category": new, "category_verified": True}},
            )
            updated += 1
        else:
            series_library_collection.update_one(
                {"id": s.get("id")} if s.get("id") else {"_id": s.get("_id")},
                {"$set": {"category_verified": True}},
            )
    print(f"updated={updated} buffer={buffer_stats()}")


if __name__ == "__main__":
    main()
