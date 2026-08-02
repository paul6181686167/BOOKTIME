"""Remplit total_volumes = len(volumes) pour les series_library."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db_config import series_library_collection, database

print("mock", database.is_mock_mode())
fixed = 0
for s in series_library_collection.find({}):
    vols = s.get("volumes") or []
    n = len(vols) if isinstance(vols, list) else int(vols or 0)
    if s.get("total_volumes") == n:
        continue
    filt = {"id": s["id"]} if s.get("id") else {"_id": s["_id"]}
    series_library_collection.update_one(filt, {"$set": {"total_volumes": n}})
    fixed += 1
    print(f"  {s.get('series_name') or s.get('name')!r}: total_volumes={n}")
print(f"updated={fixed}")
