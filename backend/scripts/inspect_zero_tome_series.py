"""Liste les series_library avec 0/0 tomes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db_config import series_library_collection, database

print("mock", database.is_mock_mode())
for s in series_library_collection.find({}):
    vols = s.get("volumes") or []
    n = len(vols) if isinstance(vols, list) else int(vols or 0)
    tv = s.get("total_volumes")
    name = s.get("series_name") or s.get("name")
    if n == 0 or tv == 0 or tv is None:
        print(f"n={n} total_volumes={tv!r} name={name!r} authors={s.get('authors')}")
