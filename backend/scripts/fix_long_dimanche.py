import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db_config import series_library_collection

for s in list(series_library_collection.find({})):
    name = (s.get("series_name") or s.get("name") or "")
    if "dimanche" not in name.lower() and "fianc" not in name.lower():
        continue
    vols = s.get("volumes") or []
    keep = (
        vols[0]
        if vols
        else {
            "volume_number": 1,
            "volume_title": "Un long dimanche de fiançailles",
            "is_read": False,
            "date_read": None,
        }
    )
    keep["volume_title"] = "Un long dimanche de fiançailles"
    keep["volume_number"] = 1
    filt = {"id": s["id"]} if s.get("id") else {"_id": s["_id"]}
    series_library_collection.update_one(
        filt,
        {
            "$set": {
                "volumes": [keep],
                "total_volumes": 1,
                "series_name": "Un long dimanche de fiançailles",
            }
        },
    )
    print("fixed:", name, "-> 1 volume")
