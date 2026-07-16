"""
Importe l'export statique Wikidata (wikidata_series_db.json) dans MongoDB Atlas.

Motivation : le fichier fait ~255 Mo et 537k entrees ; le charger en RAM sur Render
free (512 Mo) provoque un OOM. En base, on interroge a la demande via des index.

Ne sont importees que les series REELLES (is_real_series) : ~179k documents.
Chaque document = ligne Wikidata "lite" + works (tomes) + cles de recherche.

Collection : wikidata_series
  _id         = qid (Q...)
  name/name_fr/name_en, type, work_count, category (pre-calculee)
  works       = tomes (tronques si le doc depasse ~15 Mo, limite Mongo 16 Mo)
  title_keys  = titres normalises (exact + prefixe)   -> index multikey
  search_blob = tokens uniques                         -> index texte (mots)

Usage :
    cd backend
    python scripts/import_wikidata_to_mongo.py            # import complet
    python scripts/import_wikidata_to_mongo.py --limit 5000  # test rapide
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from app.static_wikidata.service import (  # noqa: E402
    infer_series_category,
    is_real_series,
    norm_title,
)
from app.config import WIKIDATA_SERIES_DB_PATH  # noqa: E402
from app.db_config import Database  # noqa: E402

COLLECTION = "wikidata_series"
MAX_DOC_BYTES = 15_000_000  # marge sous la limite Mongo de 16 Mo/document
BATCH = 1500


def _invert_title_index(title_index: dict) -> dict[str, list[str]]:
    """title_index (norm_title -> qid) => qid -> [norm_titles]."""
    out: dict[str, list[str]] = {}
    for key, qid in title_index.items():
        if isinstance(qid, str) and isinstance(key, str):
            out.setdefault(qid, []).append(key)
    return out


def _build_doc(qid: str, row: dict, titles: list[str]) -> dict:
    name = row.get("name") or ""
    name_fr = row.get("name_fr") or ""
    name_en = row.get("name_en") or ""

    keys = {t for t in titles if t}
    for nm in (name, name_fr, name_en):
        nk = norm_title(nm)
        if nk:
            keys.add(nk)
    title_keys = sorted(keys)

    tokens: set[str] = set()
    for k in title_keys:
        tokens.update(k.split())
    search_blob = " ".join(sorted(tokens))

    doc = {
        "_id": qid,
        "qid": qid,
        "name": name,
        "name_fr": name_fr,
        "name_en": name_en,
        "type": row.get("type") or "",
        "work_count": int(row.get("work_count") or 0),
        "category": infer_series_category(row),
        "title_keys": title_keys,
        "search_blob": search_blob,
    }
    if row.get("main_subjects_en"):
        doc["main_subjects_en"] = row["main_subjects_en"]

    works = row.get("works") or []
    if works:
        doc["works"] = works
        # Tronquer les works si le document depasse la limite Mongo (rare : ~1 cas).
        while doc["works"] and len(
            json.dumps(doc, ensure_ascii=False).encode("utf-8")
        ) > MAX_DOC_BYTES:
            doc["works"] = doc["works"][: max(1, len(doc["works"]) // 2)]
            doc["works_truncated"] = True
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="n'importer que N series (test)")
    args = ap.parse_args()

    dbo = Database()
    if dbo.is_mock_mode():
        print("[ERREUR] Mode MOCK actif : definis MONGO_URL (Atlas) et RAILWAY_MONGODB_MOCK=false")
        return 1

    path = WIKIDATA_SERIES_DB_PATH
    if not path.is_file():
        print(f"[ERREUR] Fichier introuvable : {path}")
        return 1

    print(f"[1/5] Lecture de {path} ({path.stat().st_size/1024/1024:.0f} Mo)...")
    with open(path, encoding="utf-8") as f:
        db = json.load(f)
    by_qid = db.get("by_qid") or {}
    title_index = db.get("title_index") or {}
    print(f"      {len(by_qid):,} entrees, {len(title_index):,} titres indexes")

    print("[2/5] Inversion de l'index des titres...")
    qid_titles = _invert_title_index(title_index)

    coll = dbo.db[COLLECTION]
    print(f"[3/5] Suppression de la collection existante '{COLLECTION}'...")
    coll.drop()

    print("[4/5] Insertion des series reelles...")
    batch: list[dict] = []
    total = 0
    skipped = 0
    truncated = 0
    t0 = time.time()
    for qid, row in by_qid.items():
        if not isinstance(row, dict) or not is_real_series(row):
            skipped += 1
            continue
        doc = _build_doc(qid, row, qid_titles.get(qid, []))
        if doc.get("works_truncated"):
            truncated += 1
        batch.append(doc)
        if len(batch) >= BATCH:
            coll.insert_many(batch, ordered=False)
            total += len(batch)
            batch = []
            if total % 15000 == 0:
                print(f"      {total:,} inseres ({time.time()-t0:.0f}s)")
        if args.limit and total >= args.limit:
            break
    if batch:
        coll.insert_many(batch, ordered=False)
        total += len(batch)

    print(f"      OK : {total:,} inseres, {skipped:,} ignores (non-series), {truncated} works tronques")

    print("[5/5] Creation des index...")
    coll.create_index("title_keys", name="title_keys_multikey")
    coll.create_index([("search_blob", "text")], default_language="none", name="search_blob_text")
    coll.create_index([("work_count", -1)], name="work_count_desc")
    print("      Index crees : title_keys, search_blob (text), work_count")

    stats = dbo.db.command("collstats", COLLECTION)
    size_mb = stats.get("storageSize", 0) / 1024 / 1024
    idx_mb = stats.get("totalIndexSize", 0) / 1024 / 1024
    print(
        f"\nTermine en {time.time()-t0:.0f}s. "
        f"Documents={stats.get('count', total):,}, "
        f"stockage={size_mb:.0f} Mo, index={idx_mb:.0f} Mo"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
