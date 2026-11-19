"""Backfill fiches auteurs vers complétude max (Mongo + SQLite).

Remplit : bio, photo, birth/death, nationality, wikipedia_url, series, individual_books.
Reprend via data/_authors_complete_progress.json.

  python scripts/backfill_authors_complete.py
  python scripts/backfill_authors_complete.py --batch 80 --sleep 0.4
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WD_SPARQL = "https://query.wikidata.org/sparql"
PROGRESS = ROOT / "data" / "_authors_complete_progress.json"


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


def _load_prog() -> dict[str, Any]:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"offset": 0, "updated": 0, "bios": 0, "nats": 0, "works": 0, "photos": 0}


def _save_prog(p: dict[str, Any]) -> None:
    p["updated_at"] = _utcnow()
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def _needs(doc: dict[str, Any]) -> bool:
    if not (doc.get("bio") or "").strip():
        return True
    if not (doc.get("nationality") or "").strip():
        return True
    if not (doc.get("photo_url") or doc.get("image_url") or "").strip():
        return True
    series = doc.get("series") or []
    books = doc.get("individual_books") or []
    if not series and not books:
        return True
    if not (doc.get("wikipedia_url") or "").strip():
        return True
    return False


def _sparql(query: str, *, timeout: int = 60) -> list[dict]:
    r = requests.get(
        WD_SPARQL,
        params={"query": query, "format": "json"},
        headers={"User-Agent": "BooktimeAuthorBackfill/1.0 (catalog enrichment)"},
        timeout=timeout,
    )
    r.raise_for_status()
    bindings = ((r.json() or {}).get("results") or {}).get("bindings") or []
    out = []
    for b in bindings:
        row = {}
        for k, v in b.items():
            row[k] = (v or {}).get("value")
        out.append(row)
    return out


def _qid_uri(qid: str) -> str:
    q = qid.strip()
    if q.startswith("http"):
        return q
    return f"http://www.wikidata.org/entity/{q}"


def _resolve_qid_by_name(name: str) -> str | None:
    """Recherche Wikidata wbsearchentities → QID personne."""
    try:
        r = requests.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": name,
                "language": "en",
                "uselang": "fr",
                "type": "item",
                "limit": 5,
                "format": "json",
            },
            headers={"User-Agent": "BooktimeAuthorBackfill/1.0"},
            timeout=15,
        )
        r.raise_for_status()
        for hit in (r.json() or {}).get("search") or []:
            qid = (hit.get("id") or "").strip()
            desc = f"{hit.get('description') or ''} {hit.get('label') or ''}".lower()
            if not qid.startswith("Q"):
                continue
            # éviter villages / albums homonymes si possible
            if any(
                x in desc
                for x in (
                    "writer",
                    "author",
                    "novelist",
                    "écrivain",
                    "auteur",
                    "poet",
                    "poète",
                    "comics",
                    "manga",
                    "illustrator",
                    "screenwriter",
                )
            ):
                return qid
        # fallback 1er résultat
        hits = (r.json() or {}).get("search") or []
        if hits:
            q = (hits[0].get("id") or "").strip()
            return q if q.startswith("Q") else None
    except Exception:
        return None
    return None


def _batch_profile(qids: list[str]) -> dict[str, dict[str, Any]]:
    if not qids:
        return {}
    values = " ".join(f"wd:{q}" for q in qids if q.startswith("Q"))
    if not values:
        return {}
    query = f"""
SELECT ?author ?birth ?death ?natLabel ?img ?article WHERE {{
  VALUES ?author {{ {values} }}
  OPTIONAL {{ ?author wdt:P569 ?birth. }}
  OPTIONAL {{ ?author wdt:P570 ?death. }}
  OPTIONAL {{ ?author wdt:P27 ?nat. }}
  OPTIONAL {{ ?author wdt:P18 ?img. }}
  OPTIONAL {{
    ?article schema:about ?author ;
             schema:isPartOf <https://fr.wikipedia.org/> .
  }}
  OPTIONAL {{
    ?articleEn schema:about ?author ;
               schema:isPartOf <https://en.wikipedia.org/> .
  }}
  BIND(COALESCE(?article, ?articleEn) AS ?article)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
"""
    rows = _sparql(query)
    by: dict[str, dict[str, Any]] = {}
    for row in rows:
        uri = row.get("author") or ""
        qid = uri.rsplit("/", 1)[-1]
        cur = by.setdefault(qid, {})
        if row.get("birth") and not cur.get("birth_date"):
            cur["birth_date"] = str(row["birth"])[:10]
        if row.get("death") and not cur.get("death_date"):
            cur["death_date"] = str(row["death"])[:10]
        if row.get("natLabel") and not cur.get("nationality"):
            cur["nationality"] = row["natLabel"]
        if row.get("img") and not cur.get("photo_url"):
            from app.catalog.daily_ingest import commons_url

            cur["photo_url"] = commons_url(row["img"]) or row["img"]
        if row.get("article") and not cur.get("wikipedia_url"):
            cur["wikipedia_url"] = row["article"]
    return by


def _batch_works(qids: list[str], *, per_author: int = 40) -> dict[str, list[dict[str, Any]]]:
    if not qids:
        return {}
    values = " ".join(f"wd:{q}" for q in qids if q.startswith("Q"))
    if not values:
        return {}
    # Œuvres littéraires (P50) — borné
    query = f"""
SELECT ?author ?work ?workLabel ?date WHERE {{
  VALUES ?author {{ {values} }}
  ?work wdt:P50 ?author .
  OPTIONAL {{ ?work wdt:P577 ?date. }}
  OPTIONAL {{ ?work wdt:P31 ?type. }}
  FILTER(!BOUND(?type) || ?type != wd:Q4167410)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
LIMIT {max(200, len(qids) * per_author)}
"""
    try:
        rows = _sparql(query, timeout=90)
    except Exception:
        return {}
    by: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        uri = row.get("author") or ""
        qid = uri.rsplit("/", 1)[-1]
        wuri = row.get("work") or ""
        wqid = wuri.rsplit("/", 1)[-1]
        title = (row.get("workLabel") or "").strip()
        if not title or title == wqid or title.startswith("Q"):
            continue
        lst = by.setdefault(qid, [])
        if len(lst) >= per_author:
            continue
        if any(x.get("id") == wqid for x in lst):
            continue
        date = row.get("date") or ""
        lst.append(
            {
                "id": wqid,
                "title": title[:200],
                "series_id": None,
                "series_name": None,
                "volume_number": None,
                "publication_date": str(date)[:10] if date else None,
                "genre": "",
                "language": None,
                "pages": None,
                "isbn": "",
                "publisher": "",
                "description": None,
                "book_type": "œuvre littéraire",
            }
        )
    return by


def _wiki_bio(name: str, wikipedia_url: str | None) -> tuple[str, str]:
    from app.catalog.daily_authors import wiki_bio

    return wiki_bio(name, None, wikipedia_url)


def _local_catalog_works(name: str, *, cap: int = 40) -> list[dict[str, Any]]:
    """Œuvres déjà présentes dans catalog_daily_series pour cet auteur (PC)."""
    import re
    import sqlite3

    key = re.sub(r"\s+", " ", (name or "").strip().lower())
    if len(key) < 2:
        return []
    path = ROOT / "data" / "local_catalog.sqlite"
    if not path.exists():
        return []
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        out: list[dict[str, Any]] = []
        # Scan borné : filtre JSON trop cher ; on matche name dans authors via LIKE sur doc
        rows = con.execute(
            "SELECT qid, name, doc_json FROM catalog_daily_series "
            "WHERE doc_json LIKE ? LIMIT 400",
            (f"%{name[:80]}%",),
        ).fetchall()
        for qid, title, raw in rows:
            try:
                d = json.loads(raw or "{}")
            except Exception:
                continue
            authors = d.get("authors") or []
            if not any(
                re.sub(r"\s+", " ", str(a).strip().lower()) == key for a in authors
            ):
                continue
            out.append(
                {
                    "id": qid,
                    "title": str(title or d.get("name") or "")[:200],
                    "series_id": None,
                    "series_name": None,
                    "volume_number": None,
                    "publication_date": str(d.get("first_published") or "")[:10] or None,
                    "genre": str(d.get("genre") or ""),
                    "language": d.get("language"),
                    "pages": None,
                    "isbn": str(d.get("isbn") or ""),
                    "publisher": "",
                    "description": None,
                    "book_type": "œuvre littéraire",
                    "source": "local_catalog",
                }
            )
            if len(out) >= cap:
                break
        return out
    finally:
        con.close()


def _incomplete_filter() -> dict:
    return {
        "$and": [
            {"enrich_stuck": {"$ne": True}},
            {
                "$or": [
                    {"bio": {"$in": [None, ""]}},
                    {"bio": {"$exists": False}},
                    {"nationality": {"$in": [None, ""]}},
                    {"nationality": {"$exists": False}},
                    {"photo_url": {"$in": [None, ""]}},
                    {"image_url": {"$in": [None, ""]}},
                    {"series": {"$in": [None, []]}},
                    {"series": {"$exists": False}},
                    {"individual_books": {"$in": [None, []]}},
                    {"individual_books": {"$exists": False}},
                    {"wikipedia_url": {"$in": [None, ""]}},
                    {"wikipedia_url": {"$exists": False}},
                ]
            },
        ]
    }


def _sqlite_incomplete(batch_n: int, *, offset: int = 0) -> list[dict[str, Any]]:
    """Lit les auteurs incomplets depuis le PC (quand Atlas est plein)."""
    import sqlite3

    path = ROOT / "data" / "local_catalog.sqlite"
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=60)
    out: list[dict[str, Any]] = []
    skipped = 0
    try:
        for (raw,) in con.execute(
            "SELECT doc_json FROM catalog_authors ORDER BY rowid"
        ):
            try:
                d = json.loads(raw or "{}")
            except Exception:
                continue
            if d.get("enrich_stuck") is True:
                continue
            if not _needs(d):
                continue
            if skipped < offset:
                skipped += 1
                continue
            out.append(d)
            if len(out) >= batch_n:
                break
    finally:
        con.close()
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=60)
    p.add_argument("--sleep", type=float, default=0.5)
    p.add_argument("--max-batches", type=int, default=0, help="0 = illimité")
    p.add_argument("--no-works", action="store_true")
    p.add_argument(
        "--sqlite-only",
        action="store_true",
        help="Lire/écrire uniquement SQLite (si quota Atlas)",
    )
    args = p.parse_args()
    _load_env()

    from app.catalog import local_catalog_sqlite as local_cat

    coll = None
    mongo_ok = not args.sqlite_only
    if mongo_ok:
        try:
            from pymongo import MongoClient

            client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=15000)
            coll = client[
                os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"
            ]["authors"]
            # test write capacity lightly
            _ = coll.estimated_document_count()
        except Exception as exc:
            print(f"mongo_unavailable → sqlite-only ({exc})", flush=True)
            mongo_ok = False
            coll = None

    prog = _load_prog()
    batch_n = max(10, min(120, args.batch))
    rounds = 0
    sqlite_offset = int(prog.get("sqlite_offset") or 0)

    if mongo_ok and coll is not None:
        try:
            print(
                f"authors_incomplete≈{coll.count_documents(_incomplete_filter())} batch={batch_n}",
                flush=True,
            )
        except Exception as exc:
            print(f"mongo_count_fail → sqlite-only ({exc})", flush=True)
            mongo_ok = False
    if not mongo_ok:
        print(f"sqlite-only batch={batch_n} offset={sqlite_offset}", flush=True)

    while True:
        rounds += 1
        if args.max_batches and rounds > args.max_batches:
            break
        docs: list[dict[str, Any]] = []
        if mongo_ok and coll is not None:
            try:
                docs = list(
                    coll.find(
                        {
                            **_incomplete_filter(),
                            "wikidata_qid": {"$type": "string", "$regex": "^Q"},
                        },
                        {"_id": 0},
                    ).limit(batch_n)
                )
                if len(docs) < batch_n:
                    extra = list(
                        coll.find(
                            {
                                **_incomplete_filter(),
                                "$or": [
                                    {"wikidata_qid": None},
                                    {"wikidata_qid": ""},
                                    {"wikidata_qid": {"$exists": False}},
                                ],
                            },
                            {"_id": 0},
                        ).limit(batch_n - len(docs))
                    )
                    docs.extend(extra)
            except Exception as exc:
                print(f"mongo_read_fail → sqlite-only ({exc})", flush=True)
                mongo_ok = False
                docs = []

        if not docs:
            docs = _sqlite_incomplete(batch_n, offset=sqlite_offset)
            if not docs and sqlite_offset:
                sqlite_offset = 0
                docs = _sqlite_incomplete(batch_n, offset=0)
            sqlite_offset += len(docs)

        if not docs:
            print("COMPLETE — plus de fiches incomplètes détectées", flush=True)
            break

        # Résoudre QID manquants par nom
        for d in docs:
            q = (d.get("wikidata_qid") or "").strip()
            if q.startswith("Q"):
                continue
            name = (d.get("name") or "").strip()
            if not name:
                continue
            q2 = _resolve_qid_by_name(name)
            if q2:
                d["wikidata_qid"] = q2
                if mongo_ok and coll is not None:
                    try:
                        coll.update_one(
                            {"id": d.get("id")},
                            {"$set": {"wikidata_qid": q2, "updated_at": _utcnow()}},
                        )
                    except Exception as exc:
                        if "space quota" in str(exc).lower() or "8000" in str(exc):
                            print("mongo_quota → sqlite-only", flush=True)
                            mongo_ok = False
                        else:
                            print(f"mongo_qid_warn {exc}", flush=True)
            time.sleep(0.08)

        qids = []
        for d in docs:
            q = (d.get("wikidata_qid") or "").strip()
            if q.startswith("Q"):
                qids.append(q)

        profiles: dict[str, dict[str, Any]] = {}
        works: dict[str, list] = {}
        try:
            profiles = _batch_profile(qids)
        except Exception as exc:
            print(f"sparql_profile_fail {exc}", flush=True)
            time.sleep(5)
        if not args.no_works:
            try:
                works = _batch_works(qids)
            except Exception as exc:
                print(f"sparql_works_fail {exc}", flush=True)

        updated = bios = nats = wks = photos = qids_linked = 0
        sqlite_docs: list[dict] = []

        for d in docs:
            q = (d.get("wikidata_qid") or "").strip()
            patch: dict[str, Any] = {}
            if q.startswith("Q") and not (d.get("wikidata_qid") or "").startswith("Q"):
                patch["wikidata_qid"] = q
                qids_linked += 1
            elif q.startswith("Q"):
                # already set above for newly resolved
                pass

            prof = profiles.get(q) or {}
            if not (d.get("nationality") or "").strip() and prof.get("nationality"):
                patch["nationality"] = prof["nationality"]
                nats += 1
            birth = d.get("birth_date")
            birth_s = str(birth or "").strip()
            if not birth_s and prof.get("birth_date"):
                patch["birth_date"] = prof["birth_date"]
            death = d.get("death_date")
            if not str(death or "").strip() and prof.get("death_date"):
                patch["death_date"] = prof["death_date"]
            if not (d.get("wikipedia_url") or "").strip() and prof.get("wikipedia_url"):
                patch["wikipedia_url"] = prof["wikipedia_url"]
            if not (d.get("photo_url") or d.get("image_url") or "").strip() and prof.get(
                "photo_url"
            ):
                patch["photo_url"] = prof["photo_url"]
                patch["image_url"] = prof["photo_url"]
                photos += 1

            books = works.get(q) or []
            if not books and not (d.get("individual_books") or []):
                # Secours local : œuvres déjà dans le catalogue PC pour cet auteur
                try:
                    books = _local_catalog_works(d.get("name") or "")
                except Exception:
                    books = []
            if books and not (d.get("individual_books") or []):
                patch["individual_books"] = books
                patch["total_individual_books"] = len(books)
                wks += 1

            if not (d.get("bio") or "").strip():
                name = (d.get("name") or "").strip()
                wiki = patch.get("wikipedia_url") or d.get("wikipedia_url")
                try:
                    bio, wiki2 = _wiki_bio(name, wiki)
                except Exception:
                    bio, wiki2 = "", wiki or ""
                if bio:
                    patch["bio"] = bio
                    bios += 1
                if wiki2 and not (d.get("wikipedia_url") or patch.get("wikipedia_url")):
                    patch["wikipedia_url"] = wiki2
                time.sleep(0.05)

            if q.startswith("Q") and d.get("wikidata_qid") != q:
                patch["wikidata_qid"] = q
                qids_linked += 1

            patch["enrich_attempted_at"] = _utcnow()
            merged_preview = {**d, **patch}
            # Ne marquer stuck que si QID connu et sources épuisées
            if q.startswith("Q") and _needs(merged_preview):
                patch["enrich_stuck"] = True
            elif not q.startswith("Q"):
                patch["enrich_stuck"] = True  # pas de QID trouvable
            else:
                patch["enrich_stuck"] = False

            patch["updated_at"] = _utcnow()
            patch["enriched_at"] = _utcnow()
            key = d.get("name_normalized") or d.get("id") or q
            filt = {"$or": [{"id": d.get("id")}, {"wikidata_qid": q}, {"name_normalized": key}]}
            if mongo_ok and coll is not None:
                try:
                    coll.update_one(filt, {"$set": patch})
                except Exception as exc:
                    if "space quota" in str(exc).lower() or "8000" in str(exc):
                        print("mongo_quota → sqlite-only", flush=True)
                        mongo_ok = False
                    else:
                        print(f"mongo_update_warn {exc}", flush=True)
            merged = {**d, **patch}
            sqlite_docs.append(merged)
            updated += 1

        if sqlite_docs and local_cat.enabled():
            try:
                # synced=0 si Mongo indisponible (à remonter plus tard)
                local_cat.upsert_author_docs(sqlite_docs, synced=1 if mongo_ok else 0)
            except Exception as exc:
                print(f"sqlite_fail {exc}", flush=True)

        prog["updated"] = int(prog.get("updated") or 0) + updated
        prog["bios"] = int(prog.get("bios") or 0) + bios
        prog["nats"] = int(prog.get("nats") or 0) + nats
        prog["works"] = int(prog.get("works") or 0) + wks
        prog["photos"] = int(prog.get("photos") or 0) + photos
        prog["rounds"] = int(prog.get("rounds") or 0) + 1
        prog["sqlite_offset"] = sqlite_offset
        prog["mongo_ok"] = bool(mongo_ok)
        _save_prog(prog)
        print(
            f"round={rounds} updated={updated} bios+={bios} nat+={nats} works+={wks} photo+={photos} "
            f"qid+={qids_linked} tot_upd={prog['updated']}",
            flush=True,
        )

        time.sleep(max(0.2, args.sleep))

    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
