"""Lie les œuvres du catalogue local (+ OL works API) aux fiches auteurs.

Priorité lecture-app : chaque auteur doit avoir individual_books / series.
Sources :
  1) catalog_daily_series.authors → individual_books (rapide, local)
  2) ol_author_cache + API /authors/{OLID}/works.json
  3) (optionnel) ne touche pas Wikidata — laisse backfill_authors_complete

  python scripts/link_author_works_from_catalog.py
  python scripts/link_author_works_from_catalog.py --ol-api --batch 80 --loop
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROGRESS = ROOT / "data" / "_link_author_works_progress.json"
UA = {"User-Agent": "BooktimeLinkWorks/1.0 (catalog enrichment)"}


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


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _db() -> Path:
    raw = (os.environ.get("CATALOG_LOCAL_SQLITE") or "").strip()
    return Path(raw) if raw else ROOT / "data" / "local_catalog.sqlite"


def _load_prog() -> dict[str, Any]:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "catalog_linked": 0,
        "ol_linked": 0,
        "ol_offset": 0,
        "updated": 0,
        "rounds": 0,
    }


def _save_prog(p: dict[str, Any]) -> None:
    p["updated_at"] = _utcnow()
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def _book_from_series(d: dict) -> dict[str, Any]:
    qid = (d.get("qid") or d.get("wikidata_qid") or "").strip()
    year = d.get("first_published") or ""
    return {
        "id": qid,
        "title": str(d.get("name") or "")[:200],
        "series_id": None,
        "series_name": None,
        "volume_number": None,
        "publication_date": str(year)[:10] if year else None,
        "genre": str(d.get("genre") or ""),
        "language": d.get("language"),
        "pages": None,
        "isbn": str(d.get("isbn") or ""),
        "publisher": "",
        "description": None,
        "book_type": "œuvre littéraire",
        "cover_url": d.get("cover_url") or "",
        "source": "local_catalog",
    }


_SERIES_INDEX_CACHE = ROOT / "data" / "_works_series_index.json"


def build_series_index(con: sqlite3.Connection) -> dict[str, list[dict]]:
    # Cache disque 6h (évite rescanner 500k+ séries à chaque cycle)
    try:
        if _SERIES_INDEX_CACHE.exists():
            age = time.time() - _SERIES_INDEX_CACHE.stat().st_mtime
            if age < 6 * 3600:
                raw = json.loads(_SERIES_INDEX_CACHE.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and len(raw) > 1000:
                    print(f"series_index cache hit keys={len(raw)}", flush=True)
                    return raw
    except Exception as exc:
        print(f"series_index_cache_miss {exc}", flush=True)

    by: dict[str, list[dict]] = defaultdict(list)
    for (raw,) in con.execute("SELECT doc_json FROM catalog_daily_series"):
        try:
            d = json.loads(raw or "{}")
        except Exception:
            continue
        authors = d.get("authors") or []
        if not isinstance(authors, list):
            continue
        book = _book_from_series(d)
        if not book["title"]:
            continue
        for a in authors:
            key = _norm(str(a))
            if len(key) < 2:
                continue
            lst = by[key]
            if len(lst) >= 60:
                continue
            if any(x.get("id") == book["id"] and book["id"] for x in lst):
                continue
            if any(x.get("title", "").lower() == book["title"].lower() for x in lst):
                continue
            lst.append(book)
    out = dict(by)
    try:
        _SERIES_INDEX_CACHE.write_text(
            json.dumps(out, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass
    return out


def build_cache_index(con: sqlite3.Connection) -> dict[str, list[str]]:
    by: dict[str, list[str]] = defaultdict(list)
    for olid, name, nn in con.execute(
        "SELECT olid, name, name_norm FROM ol_author_cache"
    ):
        key = _norm(nn or name or "")
        if key and olid:
            by[key].append(str(olid))
    return by


def _ol_author_works(olid: str, *, limit: int = 40) -> list[dict[str, Any]]:
    key = (olid or "").strip()
    if key.startswith("/authors/"):
        key = key.rsplit("/", 1)[-1]
    if not key.startswith("OL"):
        return []
    try:
        r = requests.get(
            f"https://openlibrary.org/authors/{key}/works.json",
            params={"limit": limit},
            headers=UA,
            timeout=8,
        )
        if r.status_code != 200:
            return []
        entries = (r.json() or {}).get("entries") or []
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for ent in entries:
        title = (ent.get("title") or "").strip()
        wkey = (ent.get("key") or "").strip()
        wid = wkey.rsplit("/", 1)[-1] if wkey else ""
        if not title or title.startswith("Q"):
            continue
        out.append(
            {
                "id": wid,
                "title": title[:200],
                "series_id": None,
                "series_name": None,
                "volume_number": None,
                "publication_date": None,
                "genre": "",
                "language": None,
                "pages": None,
                "isbn": "",
                "publisher": "",
                "description": None,
                "book_type": "œuvre littéraire",
                "source": "openlibrary_author_works",
            }
        )
        if len(out) >= limit:
            break
    return out


def _merge_books(existing: list, extra: list, *, cap: int = 60) -> list:
    out = list(existing or [])
    seen_id = {str(x.get("id") or "") for x in out if x.get("id")}
    seen_title = {_norm(str(x.get("title") or "")) for x in out}
    for b in extra:
        if len(out) >= cap:
            break
        bid = str(b.get("id") or "")
        title = _norm(str(b.get("title") or ""))
        if bid and bid in seen_id:
            continue
        if title and title in seen_title:
            continue
        out.append(b)
        if bid:
            seen_id.add(bid)
        if title:
            seen_title.add(title)
    return out


def _has_works(d: dict) -> bool:
    return bool(d.get("series") or d.get("individual_books"))


def link_from_catalog(con: sqlite3.Connection, by_series: dict[str, list]) -> dict[str, int]:
    from app.catalog import local_catalog_sqlite as local_cat

    updated = linked = already = 0
    sqlite_docs: list[dict] = []
    rows = list(con.execute("SELECT id, name, name_norm, doc_json FROM catalog_authors"))
    for aid, name, nn, raw in rows:
        try:
            d = json.loads(raw or "{}")
        except Exception:
            continue
        key = _norm(nn or name or d.get("name") or "")
        books = by_series.get(key) or []
        if not books:
            continue
        if _has_works(d):
            # enrichir tant qu'on a < 25 œuvres locales
            cur = list(d.get("individual_books") or [])
            if len(cur) >= 25:
                already += 1
                continue
            merged = _merge_books(cur, books, cap=60)
            if len(merged) == len(cur):
                already += 1
                continue
            if not (d.get("individual_books") or d.get("series")):
                linked += 1
        else:
            merged = books[:60]
            linked += 1
        d["individual_books"] = merged
        d["total_individual_books"] = len(merged)
        d["updated_at"] = _utcnow()
        src = d.get("sources") if isinstance(d.get("sources"), dict) else {}
        src["local_catalog_works"] = True
        d["sources"] = src
        # œuvres trouvées → débloquer pour bio/nat plus tard
        if d.get("enrich_stuck") and merged:
            d["enrich_stuck"] = False
        sqlite_docs.append(d)
        updated += 1
        if len(sqlite_docs) >= 200:
            local_cat.upsert_author_docs(sqlite_docs, synced=0)
            _mongo_upsert(sqlite_docs)
            sqlite_docs.clear()
            print(f"  catalog flush updated={updated} linked_new={linked}", flush=True)
    if sqlite_docs:
        local_cat.upsert_author_docs(sqlite_docs, synced=0)
        _mongo_upsert(sqlite_docs)
    return {"updated": updated, "linked_new": linked, "already": already}


_mongo_coll = None
_mongo_disabled = False


def _mongo_upsert(docs: list[dict]) -> None:
    global _mongo_coll, _mongo_disabled
    if not docs or _mongo_disabled:
        return
    try:
        if _mongo_coll is None:
            from pymongo import MongoClient

            client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=8000)
            _mongo_coll = client[
                os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"
            ]["authors"]
        for d in docs:
            filt = {
                "$or": [
                    {"id": d.get("id")},
                    {"name_normalized": d.get("name_normalized") or d.get("name_norm")},
                    {"wikidata_qid": d.get("wikidata_qid")},
                ]
            }
            _mongo_coll.update_one(
                filt,
                {
                    "$set": {
                        "individual_books": d.get("individual_books"),
                        "total_individual_books": d.get("total_individual_books"),
                        "sources": d.get("sources"),
                        "enrich_stuck": d.get("enrich_stuck"),
                        "updated_at": d.get("updated_at"),
                        "openlibrary_key": d.get("openlibrary_key"),
                    }
                },
                upsert=False,
            )
    except Exception as exc:
        msg = str(exc).lower()
        if "space quota" in msg or "8000" in msg:
            _mongo_disabled = True
            print("mongo_quota → sqlite-only (œuvres)", flush=True)
        else:
            print(f"mongo_warn {exc}", flush=True)


def build_ol_todo(
    con: sqlite3.Connection, cache_by: dict[str, list[str]]
) -> list[tuple[str, str, list[str]]]:
    """Index léger (id, name_key, olids) — sans garder tous les doc_json en RAM."""
    todo: list[tuple[str, str, list[str]]] = []
    cur = con.execute("SELECT id, name, name_norm, doc_json FROM catalog_authors")
    n = 0
    while True:
        rows = cur.fetchmany(500)
        if not rows:
            break
        for aid, name, nn, raw in rows:
            n += 1
            raw_s = raw or ""
            # filtre rapide avant json.loads
            if '"individual_books": [' in raw_s and '"individual_books": []' not in raw_s:
                if '"individual_books": []' not in raw_s and '"individual_books":[]' not in raw_s:
                    # non-vide probable
                    if '"individual_books": null' not in raw_s:
                        try:
                            d = json.loads(raw_s)
                            if _has_works(d):
                                continue
                        except Exception:
                            continue
            key = _norm(nn or name or "")
            olids = cache_by.get(key) or []
            if not olids:
                continue
            # confirmer absence d'œuvres
            try:
                d = json.loads(raw_s)
            except Exception:
                continue
            if _has_works(d):
                continue
            todo.append((str(aid), key, olids[:2]))
        if n % 20000 == 0:
            print(f"  todo_scan n={n} todo={len(todo)}", flush=True)
    return todo


def link_from_ol_api(
    con: sqlite3.Connection,
    todo: list[tuple[str, str, list[str]]],
    *,
    batch: int,
    offset: int,
    mongo: bool = True,
) -> tuple[dict[str, int], int]:
    from app.catalog import local_catalog_sqlite as local_cat

    if offset >= len(todo):
        offset = 0
    slice_ = todo[offset : offset + batch]
    updated = linked = 0
    sqlite_docs: list[dict] = []
    for aid, key, olids in slice_:
        row = con.execute(
            "SELECT doc_json FROM catalog_authors WHERE id=?", (aid,)
        ).fetchone()
        if not row:
            continue
        try:
            d = json.loads(row[0] or "{}")
        except Exception:
            continue
        if _has_works(d):
            continue
        books: list[dict] = []
        used_olid = ""
        for olid in olids:
            books = _ol_author_works(olid)
            if books:
                used_olid = olid
                break
            time.sleep(0.12)
        if not books:
            time.sleep(0.08)
            continue
        d["individual_books"] = books
        d["total_individual_books"] = len(books)
        if used_olid:
            d["openlibrary_key"] = (
                used_olid
                if used_olid.startswith("/authors/")
                else f"/authors/{used_olid}"
            )
        d["updated_at"] = _utcnow()
        src = d.get("sources") if isinstance(d.get("sources"), dict) else {}
        src["openlibrary_author_works"] = True
        d["sources"] = src
        d["enrich_stuck"] = False
        if not d.get("id"):
            d["id"] = aid
        sqlite_docs.append(d)
        updated += 1
        linked += 1
        time.sleep(0.15)
        if len(sqlite_docs) >= 40:
            local_cat.upsert_author_docs(sqlite_docs, synced=0)
            if mongo:
                _mongo_upsert(sqlite_docs)
            sqlite_docs.clear()
            print(f"  olapi flush linked={linked}", flush=True)
    if sqlite_docs:
        local_cat.upsert_author_docs(sqlite_docs, synced=0)
        if mongo:
            _mongo_upsert(sqlite_docs)
    new_offset = offset + len(slice_)
    if new_offset >= len(todo):
        new_offset = 0
    return {"updated": updated, "linked": linked, "todo": len(todo)}, new_offset


def main() -> int:
    global _mongo_disabled
    p = argparse.ArgumentParser()
    p.add_argument("--ol-api", action="store_true", help="Compléter via API OL authors/works")
    p.add_argument("--batch", type=int, default=60)
    p.add_argument("--loop", action="store_true", help="Boucler l'API OL")
    p.add_argument("--sleep", type=float, default=2.0)
    p.add_argument("--max-rounds", type=int, default=0, help="0=illimité si --loop")
    p.add_argument("--skip-catalog", action="store_true")
    p.add_argument(
        "--sqlite-only",
        action="store_true",
        help="Ne pas écrire Mongo (quota Atlas)",
    )
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    if args.sqlite_only:
        _mongo_disabled = True

    path = _db()
    print(f"db={path} mongo={'off' if _mongo_disabled else 'on'}", flush=True)
    con = sqlite3.connect(str(path), timeout=180)
    con.row_factory = sqlite3.Row
    prog = _load_prog()

    if not args.skip_catalog:
        print("=== index catalogue → auteurs ===", flush=True)
        by = build_series_index(con)
        print(f"author_keys_in_series={len(by)}", flush=True)
        res = link_from_catalog(con, by)
        prog["catalog_linked"] = int(prog.get("catalog_linked") or 0) + int(res["linked_new"])
        prog["updated"] = int(prog.get("updated") or 0) + int(res["updated"])
        prog["rounds"] = int(prog.get("rounds") or 0) + 1
        _save_prog(prog)
        print(f"CATALOG done {res}", flush=True)

    if args.ol_api:
        cache_by = build_cache_index(con)
        print(f"ol_cache_keys={len(cache_by)}", flush=True)
        print("=== build OL todo (léger) ===", flush=True)
        todo = build_ol_todo(con, cache_by)
        print(f"ol_todo={len(todo)}", flush=True)
        ol_rounds = 0
        while True:
            ol_rounds += 1
            prog = _load_prog()
            offset = int(prog.get("ol_offset") or 0)
            res, new_off = link_from_ol_api(
                con,
                todo,
                batch=max(10, args.batch),
                offset=offset,
                mongo=not _mongo_disabled,
            )
            prog["ol_linked"] = int(prog.get("ol_linked") or 0) + int(res["linked"])
            prog["updated"] = int(prog.get("updated") or 0) + int(res["updated"])
            prog["ol_offset"] = new_off
            prog["rounds"] = int(prog.get("rounds") or 0) + 1
            _save_prog(prog)
            print(f"OLAPI done {res} offset={new_off}", flush=True)
            if not args.loop:
                break
            if args.max_rounds and ol_rounds >= args.max_rounds:
                break
            if res["todo"] == 0 or (res["linked"] == 0 and new_off == 0):
                print("OLAPI idle — rebuild todo", flush=True)
                todo = build_ol_todo(con, cache_by)
                time.sleep(max(2.0, args.sleep))
            else:
                time.sleep(max(0.2, args.sleep))

    con.close()
    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
