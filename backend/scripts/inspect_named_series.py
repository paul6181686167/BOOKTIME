import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db_config import series_library_collection

needles = ["seigneur", "time rider", "dimanche", "fianc"]
for s in series_library_collection.find({}):
    name = (s.get("series_name") or s.get("name") or "").lower()
    if any(n in name for n in needles):
        vols = s.get("volumes") or []
        print("=" * 60)
        print("name:", s.get("series_name") or s.get("name"))
        print("total_volumes:", s.get("total_volumes"), "len(volumes):", len(vols) if isinstance(vols, list) else vols)
        print("authors:", s.get("authors"))
        print("category:", s.get("category"))
        if isinstance(vols, list):
            for v in vols[:15]:
                print("  -", v.get("volume_number"), v.get("volume_title"))
            if len(vols) > 15:
                print(f"  ... +{len(vols)-15}")
