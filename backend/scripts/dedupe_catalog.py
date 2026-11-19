"""Déduplique le catalogue SQLite (et optionnellement Mongo).

1) Même titre+auteur → garde la meilleure fiche (W > M, série > solo, cover, etc.)
2) Solo = tome d'une série (même auteur) → supprime le solo

  python scripts/dedupe_catalog.py --dry-run
  python scripts/dedupe_catalog.py
  python scripts/dedupe_catalog.py --mongo
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _norm(s: str) -> str:
    try:
        from app.static_wikidata.service import norm_title

        return norm_title(s or "")
    except Exception:
        return " ".join((s or "").lower().split())


def _db_path() -> Path:
    raw = (os.environ.get("CATALOG_LOCAL_SQLITE") or "").strip()
    return Path(raw) if raw else ROOT / "data" / "local_catalog.sqlite"


def _score(doc: dict, qid: str) -> tuple:
    """Score décroissant : plus haut = à garder."""
    typ = str(doc.get("type") or "")
    vols = doc.get("volume_titles") if isinstance(doc.get("volume_titles"), dict) else {}
    nvol = len(vols) if vols else int(doc.get("volumes") or 0)
    is_series = nvol >= 2 or typ in {
        "daily",
        "novel series",
        "book series",
        "literary series hub",
        "comics series",
        "manga series",
        "written work series",
        "literary franchise",
        "heptalogy",
        "children's book series",
    }
    cover = 1 if (doc.get("cover_url") or "").strip() else 0
    desc = (doc.get("description") or "")
    has_desc = 1 if len(desc) > 80 else 0
    src = str(doc.get("source") or "")
    src_rank = {
        "core": 5,
        "daily": 4,
        "openlibrary_dump": 2,
        "openlibrary_editions_dump": 1,
    }.get(src, 0)
    if qid.startswith("Q"):
        id_rank = 5
    elif qid.startswith("OL") and qid.endswith("W"):
        id_rank = 4
    elif qid.startswith("OL") and qid.endswith("M"):
        id_rank = 2
    elif qid.startswith("BNF") or qid.startswith("cb"):
        id_rank = 3
    else:
        id_rank = 1
    title_fr = 1 if doc.get("title_fr") else 0
    return (
        1 if is_series else 0,
        nvol,
        cover,
        has_desc,
        title_fr,
        src_rank,
        id_rank,
        len(json.dumps(doc, ensure_ascii=False, default=str)),
    )


def _author_norm(doc: dict) -> str:
    authors = doc.get("authors") if isinstance(doc.get("authors"), list) else []
    if authors:
        return _norm(str(authors[0] or ""))
    return _norm(str(doc.get("author") or ""))


def _merge_into(winner: dict, loser: dict) -> dict:
    """Récupère cover / name_en / description utiles du perdant."""
    if not (winner.get("cover_url") or "").strip() and (loser.get("cover_url") or "").strip():
        winner["cover_url"] = loser["cover_url"]
        winner["needs_cover"] = False
    if not (winner.get("name_en") or "").strip() and (loser.get("name_en") or "").strip():
        winner["name_en"] = loser["name_en"]
    if not (winner.get("description") or "").strip() and (loser.get("description") or "").strip():
        if len(str(loser.get("description") or "")) > 80:
            winner["description"] = loser["description"]
            winner["needs_summary"] = False
    if not winner.get("title_fr") and loser.get("title_fr"):
        winner["title_fr"] = loser["title_fr"]
        winner["title_fr_source"] = loser.get("title_fr_source")
    return winner


def dedupe_sqlite(*, dry_run: bool = False) -> dict:
    path = _db_path()
    con = sqlite3.connect(str(path), timeout=180)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=180000")

    print(f"db={path}", flush=True)
    before = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]
    print(f"before={before}", flush=True)

    # Charger léger : qid + champs utiles ; doc_json seulement si besoin merge
    rows = con.execute(
        "SELECT qid, name, name_norm, source, doc_json FROM catalog_daily_series"
    ).fetchall()

    docs: dict[str, dict] = {}
    groups: dict[str, list[str]] = defaultdict(list)
    series_index: dict[tuple[str, str], str] = {}  # (vol_norm, author_norm) -> series qid

    for i, row in enumerate(rows, 1):
        if i % 100000 == 0:
            print(f"  load {i}/{len(rows)}", flush=True)
        qid = row["qid"]
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        doc["qid"] = qid
        if not doc.get("name"):
            doc["name"] = row["name"]
        if not doc.get("name_norm"):
            doc["name_norm"] = row["name_norm"] or _norm(doc.get("name") or "")
        if not doc.get("source"):
            doc["source"] = row["source"]
        docs[qid] = doc
        nn = (doc.get("name_norm") or _norm(doc.get("name") or "")).strip()
        an = _author_norm(doc)
        if nn and an:
            groups[f"{nn}|{an}"].append(qid)

        vols = doc.get("volume_titles") if isinstance(doc.get("volume_titles"), dict) else {}
        nvol = len(vols) if vols else int(doc.get("volumes") or 0)
        if nvol >= 2 and an:
            for vt in vols.values():
                vn = _norm(str(vt or ""))
                # titres trop courts / génériques → ignore pour éviter faux positifs
                if len(vn) < 8:
                    continue
                key = (vn, an)
                # préfère garder la première série ; si collision, celle au meilleur score
                prev = series_index.get(key)
                if not prev or _score(doc, qid) > _score(docs.get(prev, {}), prev):
                    series_index[key] = qid

    print(f"groups_with_author={len(groups)} series_vol_keys={len(series_index)}", flush=True)

    to_delete: set[str] = set()
    to_update: dict[str, dict] = {}
    dup_removed = 0
    tome_removed = 0

    # 1) Dédup titre+auteur
    for key, qids in groups.items():
        uniq = list(dict.fromkeys(qids))
        if len(uniq) < 2:
            continue
        ranked = sorted(uniq, key=lambda q: _score(docs[q], q), reverse=True)
        winner_q = ranked[0]
        winner = docs[winner_q]
        for loser_q in ranked[1:]:
            if loser_q in to_delete:
                continue
            loser = docs[loser_q]
            winner = _merge_into(winner, loser)
            to_delete.add(loser_q)
            dup_removed += 1
        docs[winner_q] = winner
        to_update[winner_q] = winner

    # 2) Solo = tome de série (même auteur, titre tome assez long)
    for qid, doc in docs.items():
        if qid in to_delete:
            continue
        vols = doc.get("volume_titles") if isinstance(doc.get("volume_titles"), dict) else {}
        nvol = len(vols) if vols else int(doc.get("volumes") or 0)
        typ = str(doc.get("type") or "")
        is_series = nvol >= 2 or typ in {
            "daily",
            "novel series",
            "book series",
            "literary series hub",
            "comics series",
            "manga series",
            "written work series",
            "literary franchise",
            "heptalogy",
            "children's book series",
        }
        if is_series:
            continue
        nn = (doc.get("name_norm") or _norm(doc.get("name") or "")).strip()
        an = _author_norm(doc)
        if len(nn) < 8 or not an:
            continue
        series_q = series_index.get((nn, an))
        if not series_q or series_q == qid or series_q in to_delete:
            continue
        # merge cover into series if useful
        series = docs.get(series_q)
        if series:
            docs[series_q] = _merge_into(series, doc)
            to_update[series_q] = docs[series_q]
        to_delete.add(qid)
        tome_removed += 1

    print(
        f"to_delete={len(to_delete)} dup_removed={dup_removed} tome_removed={tome_removed} "
        f"to_update={len(to_update)}",
        flush=True,
    )

    if dry_run:
        con.close()
        return {
            "before": before,
            "dup_removed": dup_removed,
            "tome_removed": tome_removed,
            "after_est": before - len(to_delete),
            "dry_run": True,
        }

    # Persister merges puis deletes (par lots)
    updates = []
    for qid, doc in to_update.items():
        if qid in to_delete:
            continue
        updates.append(
            (
                str(doc.get("name") or ""),
                str(doc.get("name_norm") or ""),
                json.dumps(doc, ensure_ascii=False, default=str),
                qid,
            )
        )
    for i in range(0, len(updates), 500):
        chunk = updates[i : i + 500]
        for attempt in range(10):
            try:
                con.executemany(
                    "UPDATE catalog_daily_series SET name=?, name_norm=?, doc_json=?, synced=0 WHERE qid=?",
                    chunk,
                )
                con.commit()
                break
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= 9:
                    raise
                time.sleep(1.5 * (attempt + 1))
        if (i // 500) % 10 == 0:
            print(f"  updated {min(i+500,len(updates))}/{len(updates)}", flush=True)

    doomed = list(to_delete)
    for i in range(0, len(doomed), 1000):
        chunk = doomed[i : i + 1000]
        for attempt in range(10):
            try:
                con.executemany(
                    "DELETE FROM catalog_daily_series WHERE qid=?",
                    [(q,) for q in chunk],
                )
                con.commit()
                break
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= 9:
                    raise
                time.sleep(1.5 * (attempt + 1))
        if (i // 1000) % 5 == 0:
            print(f"  deleted {min(i+1000,len(doomed))}/{len(doomed)}", flush=True)

    after = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]
    con.execute("VACUUM")
    con.close()
    print(f"after={after}", flush=True)
    return {
        "before": before,
        "dup_removed": dup_removed,
        "tome_removed": tome_removed,
        "deleted": len(to_delete),
        "after": after,
        "dry_run": False,
    }


def dedupe_mongo(*, dry_run: bool = False) -> dict:
    """Même logique sur Mongo (plus lent, best-effort)."""
    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    coll = client[os.environ.get("DB_NAME") or "booktime"]["catalog_daily_series"]
    before = coll.estimated_document_count()
    print(f"mongo before≈{before}", flush=True)

    groups: dict[str, list[dict]] = defaultdict(list)
    series_index: dict[tuple[str, str], dict] = {}
    n = 0
    for doc in coll.find({}, {"_id": 0}):
        n += 1
        if n % 50000 == 0:
            print(f"  mongo load {n}", flush=True)
        qid = str(doc.get("qid") or "").strip()
        if not qid:
            continue
        nn = (doc.get("name_norm") or _norm(doc.get("name") or "")).strip()
        an = _author_norm(doc)
        if nn and an:
            groups[f"{nn}|{an}"].append(doc)
        vols = doc.get("volume_titles") if isinstance(doc.get("volume_titles"), dict) else {}
        nvol = len(vols) if vols else int(doc.get("volumes") or 0)
        if nvol >= 2 and an:
            for vt in vols.values():
                vn = _norm(str(vt or ""))
                if len(vn) < 8:
                    continue
                key = (vn, an)
                prev = series_index.get(key)
                if not prev or _score(doc, qid) > _score(prev, str(prev.get("qid") or "")):
                    series_index[key] = doc

    to_delete: list[str] = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        ranked = sorted(
            items, key=lambda d: _score(d, str(d.get("qid") or "")), reverse=True
        )
        for loser in ranked[1:]:
            q = str(loser.get("qid") or "")
            if q:
                to_delete.append(q)

    docs_by_q = {}
    for items in groups.values():
        for d in items:
            docs_by_q[str(d.get("qid") or "")] = d

    tome_n = 0
    for qid, doc in list(docs_by_q.items()):
        if qid in to_delete:
            continue
        vols = doc.get("volume_titles") if isinstance(doc.get("volume_titles"), dict) else {}
        nvol = len(vols) if vols else int(doc.get("volumes") or 0)
        if nvol >= 2:
            continue
        nn = (doc.get("name_norm") or _norm(doc.get("name") or "")).strip()
        an = _author_norm(doc)
        if len(nn) < 8 or not an:
            continue
        series = series_index.get((nn, an))
        if not series or str(series.get("qid")) == qid:
            continue
        to_delete.append(qid)
        tome_n += 1

    to_delete = list(dict.fromkeys(to_delete))
    print(f"mongo to_delete={len(to_delete)} tome≈{tome_n}", flush=True)
    if dry_run:
        return {"before": before, "deleted": len(to_delete), "dry_run": True}

    deleted = 0
    for i in range(0, len(to_delete), 500):
        chunk = to_delete[i : i + 500]
        res = coll.delete_many({"qid": {"$in": chunk}})
        deleted += int(res.deleted_count or 0)
        if i % 5000 == 0:
            print(f"  mongo deleted {deleted}", flush=True)
    after = coll.estimated_document_count()
    return {"before": before, "deleted": deleted, "after": after, "dry_run": False}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mongo", action="store_true")
    p.add_argument("--sqlite-only", action="store_true")
    args = p.parse_args()
    _load_env()

    print("=== sqlite ===", flush=True)
    print(dedupe_sqlite(dry_run=args.dry_run), flush=True)
    if args.mongo and not args.sqlite_only:
        print("=== mongo ===", flush=True)
        print(dedupe_mongo(dry_run=args.dry_run), flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
