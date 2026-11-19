"""Backfill jaquettes + résumés sur le catalogue SQLite (PC) et optionnellement Mongo.

  python scripts/backfill_catalog_media.py --limit 500
  python scripts/backfill_catalog_media.py --limit 200 --mongo
  python scripts/backfill_catalog_media.py --authors 100
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
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


def _sqlite_path() -> Path:
    raw = (os.environ.get("CATALOG_LOCAL_SQLITE") or "").strip()
    if raw:
        return Path(raw)
    return ROOT / "data" / "local_catalog.sqlite"


def _connect(path: Path, *, readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        uri = f"file:{path.as_posix()}?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=60)
    else:
        con = sqlite3.connect(str(path), timeout=120)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=120000")
    con.row_factory = sqlite3.Row
    return con


def _collect_candidates(path: Path, limit: int) -> list[tuple[str, dict]]:
    """Lecture seule : liste (qid, doc) à enrichir."""
    from app.catalog import catalog_media
    from app.catalog.daily_ingest import usable_cover

    con = _connect(path, readonly=True)
    out: list[tuple[str, dict]] = []
    offset = 0
    batch = 120
    looked = 0
    try:
        while len(out) < limit:
            rows = con.execute(
                "SELECT qid, doc_json FROM catalog_daily_series "
                "ORDER BY rowid DESC LIMIT ? OFFSET ?",
                (batch, offset),
            ).fetchall()
            if not rows:
                break
            offset += len(rows)
            for row in rows:
                looked += 1
                try:
                    doc = json.loads(row["doc_json"])
                except Exception:
                    continue
                if not isinstance(doc, dict):
                    continue
                need_c = not usable_cover(doc.get("cover_url")) or bool(doc.get("needs_cover"))
                need_s = not catalog_media.has_real_synopsis(doc)
                if not need_c and not need_s:
                    continue
                out.append((row["qid"], doc))
                if len(out) >= limit:
                    break
            if looked % 500 == 0:
                print(f"  collect looked={looked} candidates={len(out)}", flush=True)
    finally:
        con.close()
    print(f"candidates={len(out)} (looked={looked})", flush=True)
    return out


def backfill_sqlite(limit: int) -> dict[str, int]:
    from app.catalog import catalog_media

    path = _sqlite_path()
    if not path.exists():
        print(f"missing sqlite {path}", flush=True)
        return {"cover": 0, "summary": 0, "scanned": 0}

    catalog_media.reset_budgets(synopsis=max(limit, 50), covers=max(limit, 50))
    candidates = _collect_candidates(path, limit)

    cover_n = summary_n = 0
    updates: list[tuple] = []
    for i, (qid, doc) in enumerate(candidates, 1):
        need_c = bool(doc.get("needs_cover")) or not doc.get("cover_url")
        need_s = not catalog_media.has_real_synopsis(doc)
        got = catalog_media.enrich_doc_media(doc, want_cover=need_c, want_summary=need_s)
        if not (got["cover"] or got["summary"]):
            if i % 10 == 0:
                print(
                    f"  enrich {i}/{len(candidates)} cover+={cover_n} summary+={summary_n}",
                    flush=True,
                )
            continue
        updates.append(
            (
                str(doc.get("name") or ""),
                str(doc.get("name_norm") or ""),
                json.dumps(doc, ensure_ascii=False, default=str),
                str(doc.get("source") or ""),
                str(doc.get("added_at") or ""),
                qid,
            )
        )
        if got["cover"]:
            cover_n += 1
        if got["summary"]:
            summary_n += 1
        if i % 10 == 0:
            print(
                f"  enrich {i}/{len(candidates)} cover+={cover_n} summary+={summary_n}",
                flush=True,
            )

    if updates:
        con = _connect(path, readonly=False)
        try:
            for attempt in range(10):
                try:
                    con.executemany(
                        """
                        UPDATE catalog_daily_series
                        SET name=?, name_norm=?, doc_json=?, source=?, added_at=?, synced=0
                        WHERE qid=?
                        """,
                        updates,
                    )
                    con.commit()
                    break
                except sqlite3.OperationalError as exc:
                    if "locked" not in str(exc).lower() or attempt >= 9:
                        raise
                    wait = 2 * (attempt + 1)
                    print(f"  db locked, retry in {wait}s…", flush=True)
                    time.sleep(wait)
        finally:
            con.close()

    return {
        "cover": cover_n,
        "summary": summary_n,
        "scanned": len(candidates),
        "written": len(updates),
    }


def backfill_mongo(limit: int) -> dict[str, int]:
    from app.catalog import catalog_media, daily_ingest

    catalog_media.reset_budgets(synopsis=max(limit, 50), covers=max(limit, 50))
    c = daily_ingest.complete_missing_covers(limit)
    s = daily_ingest.complete_missing_summaries(limit)
    return {"cover": c, "summary": s}


def backfill_authors(limit: int) -> int:
    from pymongo import MongoClient
    from app.catalog.daily_authors import wiki_bio

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    db = client[os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"]
    coll = db["authors"]
    n = 0
    for doc in coll.find(
        {"$or": [{"bio": {"$exists": False}}, {"bio": ""}, {"bio": None}]},
        {"_id": 0},
    ).limit(max(1, limit)):
        name = (doc.get("name") or "").strip()
        if not name:
            continue
        bio, wiki = wiki_bio(name, None, doc.get("wikipedia_url"))
        if not bio:
            continue
        patch = {"bio": bio}
        if wiki and not doc.get("wikipedia_url"):
            patch["wikipedia_url"] = wiki
        key = doc.get("id") or doc.get("wikidata_qid") or doc.get("name_normalized")
        if not key:
            continue
        coll.update_one(
            {"$or": [{"id": key}, {"wikidata_qid": key}, {"name_normalized": key}]},
            {"$set": patch},
        )
        n += 1
        if n % 20 == 0:
            print(f"  authors bio+={n}", flush=True)
    return n


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=400)
    p.add_argument("--mongo", action="store_true", help="Aussi backfill Mongo Atlas")
    p.add_argument("--authors", type=int, default=0, help="Backfill bios auteurs Mongo")
    p.add_argument("--sqlite-only", action="store_true")
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")

    print(f"sqlite={_sqlite_path()}", flush=True)
    sq = backfill_sqlite(args.limit)
    print(f"SQLITE done {sq}", flush=True)

    if args.mongo and not args.sqlite_only:
        mo = backfill_mongo(args.limit)
        print(f"MONGO done {mo}", flush=True)

    if args.authors > 0:
        an = backfill_authors(args.authors)
        print(f"AUTHORS bio filled={an}", flush=True)

    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
