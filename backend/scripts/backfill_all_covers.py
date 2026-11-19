"""Trouve une jaquette pour toutes les fiches SQLite sans cover.

  python scripts/backfill_all_covers.py --workers 16
  python scripts/backfill_all_covers.py --limit 500
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _db() -> Path:
    raw = (os.environ.get("CATALOG_LOCAL_SQLITE") or "").strip()
    return Path(raw) if raw else ROOT / "data" / "local_catalog.sqlite"


def _flush(updates: list[tuple]) -> None:
    if not updates:
        return
    con = sqlite3.connect(str(_db()), timeout=180)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=180000")
    try:
        for attempt in range(12):
            try:
                con.executemany(
                    """
                    UPDATE catalog_daily_series
                    SET doc_json=?, synced=0
                    WHERE qid=?
                    """,
                    updates,
                )
                con.commit()
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= 11:
                    raise
                time.sleep(1.5 * (attempt + 1))
    finally:
        con.close()


def _apply_cover(doc: dict, url: str, source: str) -> None:
    from app.catalog.daily_ingest import usable_cover

    url = usable_cover(url) or url
    doc["cover_url"] = url
    doc["needs_cover"] = False
    doc["cover_source"] = source
    details = doc.get("volume_details")
    if isinstance(details, dict):
        for block in details.values():
            if isinstance(block, dict) and not usable_cover(block.get("cover_url")):
                block["cover_url"] = url


def _one(item: tuple[str, dict]) -> tuple[str, dict, str] | None:
    from app.catalog.catalog_covers import resolve_cover

    qid, doc = item
    try:
        url, src = resolve_cover(doc)
    except Exception:
        return None
    if not url:
        return None
    _apply_cover(doc, url, src)
    return qid, doc, src


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument(
        "--isbn-only",
        action="store_true",
        help="Uniquement covers via ISBN déjà présent (instantané)",
    )
    args = p.parse_args()
    _load_env()

    from app.catalog.daily_ingest import usable_cover

    path = _db()
    print(f"db={path}", flush=True)
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=120)
    rows = con.execute("SELECT qid, doc_json FROM catalog_daily_series").fetchall()
    con.close()

    real_jobs: list[tuple[str, dict]] = []
    flag_fixes: list[tuple] = []
    for qid, raw in rows:
        try:
            doc = json.loads(raw)
        except Exception:
            continue
        if usable_cover(doc.get("cover_url")):
            if doc.get("needs_cover"):
                doc["needs_cover"] = False
                flag_fixes.append((json.dumps(doc, ensure_ascii=False, default=str), qid))
            continue
        real_jobs.append((qid, doc))
        if args.limit and len(real_jobs) >= args.limit:
            break

    if flag_fixes:
        _flush(flag_fixes)
        print(f"flag_fixes={len(flag_fixes)}", flush=True)

    # Passe ISBN locale (sans réseau)
    from app.catalog.daily_ingest import pick_isbn

    isbn_updates: list[tuple] = []
    remaining: list[tuple[str, dict]] = []
    for qid, doc in real_jobs:
        details = doc.get("volume_details") if isinstance(doc.get("volume_details"), dict) else {}
        isbn = ""
        for d in details.values():
            if isinstance(d, dict):
                isbn = pick_isbn(d.get("isbn"))
                if isbn:
                    break
        if isbn:
            _apply_cover(doc, f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg", "isbn")
            isbn_updates.append((json.dumps(doc, ensure_ascii=False, default=str), qid))
        else:
            remaining.append((qid, doc))
    if isbn_updates:
        _flush(isbn_updates)
        print(f"isbn_covers={len(isbn_updates)}", flush=True)
    if args.isbn_only:
        print("DONE isbn-only", flush=True)
        return 0

    real_jobs = remaining
    print(f"need_cover={len(real_jobs)} workers={args.workers}", flush=True)
    filled = len(isbn_updates)
    tried = 0
    by_src: dict[str, int] = {"isbn": len(isbn_updates)}
    updates: list[tuple] = []

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futs = {pool.submit(_one, j): j[0] for j in real_jobs}
        for fut in as_completed(futs):
            tried += 1
            try:
                got = fut.result()
            except Exception:
                got = None
            if got:
                qid, doc, src = got
                updates.append((json.dumps(doc, ensure_ascii=False, default=str), qid))
                filled += 1
                by_src[src] = by_src.get(src, 0) + 1
            if len(updates) >= 40:
                _flush(updates)
                updates.clear()
            if tried % 200 == 0:
                print(
                    f"  tried={tried}/{len(real_jobs)} filled={filled} src={by_src}",
                    flush=True,
                )
    _flush(updates)
    print(f"DONE tried={tried} filled={filled} by_source={by_src}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
