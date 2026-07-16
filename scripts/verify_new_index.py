"""Vérifie que l'index v1.4 contient les franchises canoniques avec leurs tomes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.static_wikidata import service as s  # noqa: E402

s.ensure_loaded()
db = s._series_db
by = db.get("by_qid") or {}
ti = db.get("title_index") or {}

print(f"TOTAL series : {len(by):,}  |  title_index : {len(ti):,}")
print("-" * 70)

labels = [
    "harry potter",
    "one piece",
    "naruto",
    "le seigneur des anneaux",
    "asterix",
    "dragon ball",
    "game of thrones",
    "twilight",
]
for label in labels:
    qn = s.norm_title(label)
    qid = ti.get(qn)
    if qid:
        r = by.get(qid, {})
        name = r.get("name")
        typ = r.get("type")
        wc = r.get("work_count")
        cat = s.infer_series_category(r)
        print(f"{label:26} -> {qid:12} | {name} | type={typ} | tomes={wc} | cat={cat}")
    else:
        print(f"{label:26} -> AUCUN match exact")

print("-" * 70)
for query in ("harry potter", "one piece", "asterix"):
    print(f"Recherche live pour '{query}' :")
    for r in s.search_series_by_title(q=query, limit=6):
        print(f"   {r.get('name')} | cat={r.get('category')} | tomes={r.get('work_count')}")
    print()
