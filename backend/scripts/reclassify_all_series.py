"""Recalcule la catégorie de TOUTES les séries bibliothèque via OL + tampon."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db_config import series_library_collection, database
from app.utils.category_verify import verify_category_via_search
from app.utils.category_buffer import clear_memory_buffer, buffer_stats


def main() -> None:
    clear_memory_buffer()
    # Purge tampon Mongo pour forcer un recalcul propre
    try:
        database.db["category_buffer"].delete_many({})
    except Exception:
        pass

    print("mock_mode=", database.is_mock_mode())
    series = list(series_library_collection.find({}))
    print(f"series total={len(series)}")
    updated = 0
    for s in series:
        name = s.get("name") or s.get("series_name") or s.get("title") or ""
        author = s.get("author") or s.get("authors") or ""
        if isinstance(author, list):
            author = ", ".join(str(a) for a in author)
        old = s.get("category") or "roman"
        result = verify_category_via_search(name, author, force=True, current_category=old)
        new = result["category"]
        print(f"  {old} -> {new} | {name} | {result.get('source')}")
        filt = {"id": s["id"]} if s.get("id") else {"_id": s.get("_id")}
        series_library_collection.update_one(
            filt,
            {"$set": {"category": new, "category_verified": True}},
        )
        if new != old:
            updated += 1
    print(f"changed={updated} buffer={buffer_stats()}")


if __name__ == "__main__":
    main()
