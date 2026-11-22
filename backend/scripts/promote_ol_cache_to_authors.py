"""Promeut ol_author_cache → fiches auteurs complètes (Mongo + SQLite).

  python scripts/promote_ol_cache_to_authors.py --batch 50
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROGRESS = ROOT / "data" / "_promote_cache_authors_progress.json"


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


def _utcnow() -> datetime:
    return datetime.utcnow()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_prog() -> dict[str, Any]:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"offset": 0, "created": 0, "skipped": 0, "bios": 0, "nats": 0, "works": 0}


def _save_prog(p: dict[str, Any]) -> None:
    p["updated_at"] = _utcnow_iso()
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=40)
    p.add_argument("--sleep", type=float, default=0.5)
    p.add_argument("--max-batches", type=int, default=0)
    p.add_argument("--no-works", action="store_true")
    p.add_argument(
        "--fast",
        action="store_true",
        help="Wiki seulement si URL WD ; plus de débit",
    )
    p.add_argument(
        "--sqlite-only",
        action="store_true",
        help="Lire cache SQLite + écrire auteurs SQLite (si quota Atlas)",
    )
    args = p.parse_args()
    _load_env()

    import importlib.util
    import sqlite3

    spec = importlib.util.spec_from_file_location(
        "backfill_authors_complete",
        ROOT / "scripts" / "backfill_authors_complete.py",
    )
    bac = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(bac)
    _batch_profile = bac._batch_profile
    _batch_works = bac._batch_works
    _resolve_qid_by_name = bac._resolve_qid_by_name
    _wiki_bio = bac._wiki_bio

    from app.authors.service import normalize_author_name
    from app.catalog import local_catalog_sqlite as local_cat

    mongo_ok = not args.sqlite_only
    cache = authors = None
    if mongo_ok:
        try:
            from pymongo import MongoClient

            client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=15000)
            db = client[
                os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"
            ]
            cache = db["ol_author_cache"]
            authors = db["authors"]
        except Exception as exc:
            print(f"mongo_unavailable → sqlite-only ({exc})", flush=True)
            mongo_ok = False

    sqlite_path = ROOT / "data" / "local_catalog.sqlite"
    known: set[str] = set()
    if mongo_ok and authors is not None:
        try:
            for doc in authors.find({}, {"name_normalized": 1, "_id": 0}):
                k = (doc.get("name_normalized") or "").strip()
                if k:
                    known.add(k)
        except Exception as exc:
            print(f"mongo_known_fail → sqlite ({exc})", flush=True)
            mongo_ok = False
    # Toujours compléter known depuis SQLite
    con = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True, timeout=60)
    try:
        for (nn,) in con.execute(
            "SELECT name_norm FROM catalog_authors WHERE name_norm IS NOT NULL AND name_norm!=''"
        ):
            known.add(str(nn).strip())
        cache_total = int(con.execute("SELECT COUNT(*) FROM ol_author_cache").fetchone()[0])
    finally:
        con.close()
    print(
        f"known_authors={len(known)} cache≈{cache_total} mode={'sqlite' if not mongo_ok else 'mongo+sqlite'}",
        flush=True,
    )

    prog = _load_prog()
    offset = int(prog.get("offset") or 0)
    batch_n = max(20, min(200, args.batch))
    rounds = 0
    fast = bool(getattr(args, "fast", False))

    # Budget wiki + index œuvres locales
    try:
        from app.catalog.daily_authors import reset_wiki_bio_budget

        reset_wiki_bio_budget(8000 if fast else 3000)
    except Exception:
        pass
    local_works = {}
    try:
        local_works = bac._ensure_local_works_index()
    except Exception as exc:
        print(f"local_works_warn {exc}", flush=True)

    while True:
        rounds += 1
        if args.max_batches and rounds > args.max_batches:
            break

        rows: list[dict] = []
        if mongo_ok and cache is not None:
            try:
                rows = list(cache.find({}, {"_id": 0}).skip(offset).limit(batch_n))
            except Exception as exc:
                print(f"mongo_cache_fail → sqlite ({exc})", flush=True)
                mongo_ok = False
                rows = []
        if not rows:
            con = sqlite3.connect(
                f"file:{sqlite_path.as_posix()}?mode=ro", uri=True, timeout=60
            )
            try:
                for olid, name, nn in con.execute(
                    "SELECT olid, name, name_norm FROM ol_author_cache "
                    "ORDER BY rowid LIMIT ? OFFSET ?",
                    (batch_n, offset),
                ):
                    rows.append({"olid": olid, "name": name, "name_norm": nn})
            finally:
                con.close()
        if not rows:
            print("CACHE_DONE", flush=True)
            break

        offset += len(rows)
        prog["offset"] = offset

        # Filtrer déjà présents
        todo = []
        for r in rows:
            name = (r.get("name") or "").strip()
            key = normalize_author_name(name) or (r.get("name_norm") or "").strip()
            if not name or not key or key in known:
                prog["skipped"] = int(prog.get("skipped") or 0) + 1
                continue
            todo.append({**r, "name_normalized": key})

        if not todo:
            _save_prog(prog)
            if rounds % 20 == 0:
                print(f"round={rounds} offset={offset} skip_all", flush=True)
            continue

        # Fast = OL + œuvres locales seulement (pas de Wikidata / SPARQL)
        profiles: dict[str, dict] = {}
        works: dict[str, list] = {}
        if not fast:
            for d in todo:
                q = _resolve_qid_by_name(d["name"])
                if q:
                    d["wikidata_qid"] = q
                time.sleep(0.06)
            qids = [
                d["wikidata_qid"]
                for d in todo
                if (d.get("wikidata_qid") or "").startswith("Q")
            ]
            try:
                profiles = _batch_profile(qids)
            except Exception as exc:
                print(f"sparql_profile_fail {exc}", flush=True)
                time.sleep(3)
            if not args.no_works:
                try:
                    works = _batch_works(qids)
                except Exception as exc:
                    print(f"sparql_works_fail {exc}", flush=True)

        created = bios = nats = wks = photos = 0
        sqlite_docs: list[dict] = []

        for d in todo:
            name = d["name"]
            key = d["name_normalized"]
            q = (d.get("wikidata_qid") or "").strip()
            prof = profiles.get(q) or {}
            now = _utcnow()
            olid = (d.get("olid") or "").strip()

            bio = ""
            wiki = prof.get("wikipedia_url") or ""
            # Wiki seulement si URL WD connue (hors fast : toujours tenter)
            if wiki or not fast:
                try:
                    bio, wiki2 = _wiki_bio(name, wiki)
                    if wiki2:
                        wiki = wiki2
                except Exception:
                    pass
                time.sleep(0.02 if fast else 0.04)

            # Profil OL HTTP : hors --fast (sinon débit trop bas pour 100k+ fiches)
            olp: dict = {}
            if olid and not fast and (not bio or not prof.get("photo_url")):
                try:
                    olp = bac._ol_author_profile(olid)
                except Exception:
                    olp = {}
                if not bio and olp.get("bio"):
                    bio = olp["bio"]
                time.sleep(0.05)

            if bio:
                bios += 1

            books = works.get(q) or []
            if not books:
                books = (local_works.get(key) or local_works.get(name.lower()) or [])[:40]
            if books:
                wks += 1
            if prof.get("nationality"):
                nats += 1
            photo = prof.get("photo_url") or olp.get("photo_url") or ""
            if not photo and olid:
                photo = f"https://covers.openlibrary.org/a/olid/{olid}-M.jpg"
            if photo:
                photos += 1

            birth = prof.get("birth_date") or olp.get("birth_date")
            death = prof.get("death_date") or olp.get("death_date")

            doc = {
                "id": str(uuid.uuid4()),
                "name": name,
                "name_normalized": key,
                "bio": bio or None,
                "photo_url": photo or None,
                "image_url": photo or None,
                "birth_date": birth,
                "death_date": death,
                "nationality": prof.get("nationality"),
                "occupation": ["écrivain"],
                "genres": [],
                "awards": [],
                "wikidata_qid": q or None,
                "wikipedia_url": wiki or None,
                "series": [],
                "individual_books": books,
                "total_series": 0,
                "total_individual_books": len(books),
                "sources": {
                    "ol_author_cache": True,
                    "wikidata_profile": bool(q),
                    **({"wikipedia": True} if bio else {}),
                    **({"openlibrary": True} if olp else {}),
                },
                "source": "ol_author_cache",
                "olid": olid or None,
                "enriched_at": now,
                "updated_at": now,
                "created_at": now,
            }
            missing = []
            if not bio:
                missing.append("bio")
            if not q:
                missing.append("qid")
            if not photo:
                missing.append("photo")
            if not prof.get("nationality"):
                missing.append("nationality")
            if not books:
                missing.append("works")
            doc["enrich_missing"] = missing
            doc["enrich_stuck"] = len(missing) > 0
            doc["enrich_attempted_at"] = _utcnow_iso()

            insert_fields = {"id": doc.pop("id"), "created_at": doc.pop("created_at")}
            if mongo_ok and authors is not None:
                try:
                    authors.update_one(
                        {"name_normalized": key},
                        {"$setOnInsert": insert_fields, "$set": doc},
                        upsert=True,
                    )
                except Exception as exc:
                    if "space quota" in str(exc).lower() or "8000" in str(exc):
                        print("mongo_quota → sqlite-only", flush=True)
                        mongo_ok = False
                    else:
                        print(f"mongo_upsert_warn {exc}", flush=True)
            doc["id"] = insert_fields["id"]
            doc["created_at"] = insert_fields["created_at"]
            known.add(key)
            sqlite_docs.append(doc)
            created += 1

        if sqlite_docs and local_cat.enabled():
            try:
                local_cat.upsert_author_docs(sqlite_docs, synced=1 if mongo_ok else 0)
            except Exception as exc:
                print(f"sqlite_fail {exc}", flush=True)

        prog["created"] = int(prog.get("created") or 0) + created
        prog["bios"] = int(prog.get("bios") or 0) + bios
        prog["nats"] = int(prog.get("nats") or 0) + nats
        prog["works"] = int(prog.get("works") or 0) + wks
        prog["photos"] = int(prog.get("photos") or 0) + photos
        prog["rounds"] = int(prog.get("rounds") or 0) + 1
        prog["mongo_ok"] = bool(mongo_ok)
        _save_prog(prog)
        print(
            f"round={rounds} offset={offset}/{cache_total} "
            f"created+={created} bios+={bios} nat+={nats} works+={wks} photo+={photos} "
            f"tot_created={prog['created']}",
            flush=True,
        )
        time.sleep(max(0.05, args.sleep))

    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    # Permettre import relatif depuis scripts/
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
