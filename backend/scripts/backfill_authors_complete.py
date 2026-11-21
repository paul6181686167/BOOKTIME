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


UA_EXTRA = {"User-Agent": "BooktimeAuthorBackfill/1.1 (multi-source enrichment)"}


def _olid_from_cache(name: str) -> str:
    """OLID depuis ol_author_cache uniquement (pas d'API — trop lent en masse)."""
    import re
    import sqlite3

    key = re.sub(r"\s+", " ", (name or "").strip().lower())
    if len(key) < 2:
        return ""
    path = ROOT / "data" / "local_catalog.sqlite"
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=20)
    try:
        row = con.execute(
            "SELECT olid FROM ol_author_cache WHERE name_norm=? LIMIT 1", (key,)
        ).fetchone()
        if row and row[0]:
            return str(row[0])
        row = con.execute(
            "SELECT olid FROM ol_author_cache WHERE name_norm LIKE ? LIMIT 1",
            (key[:40] + "%",),
        ).fetchone()
        return str(row[0]) if row and row[0] else ""
    finally:
        con.close()


def _ol_author_profile(olid: str) -> dict[str, Any]:
    """Bio + photo Open Library /authors/{OLID}.json."""
    key = (olid or "").strip()
    if key.startswith("/authors/"):
        key = key.rsplit("/", 1)[-1]
    if not key.startswith("OL"):
        return {}
    try:
        r = requests.get(
            f"https://openlibrary.org/authors/{key}.json",
            headers=UA_EXTRA,
            timeout=6,
        )
        if r.status_code != 200:
            return {}
        data = r.json() or {}
    except Exception:
        return {}
    out: dict[str, Any] = {"olid": key}
    bio = data.get("bio")
    if isinstance(bio, dict):
        bio = bio.get("value") or ""
    bio = (bio or "").strip()
    if len(bio) >= 40:
        out["bio"] = bio[:2000]
    # photo
    photos = data.get("photos") or []
    if isinstance(photos, list) and photos:
        try:
            pid = int(photos[0])
            if pid > 0:
                out["photo_url"] = f"https://covers.openlibrary.org/a/id/{pid}-M.jpg"
        except (TypeError, ValueError):
            pass
    if not out.get("photo_url"):
        out["photo_url"] = f"https://covers.openlibrary.org/a/olid/{key}-M.jpg"
    # dates
    for src, dst in (("birth_date", "birth_date"), ("death_date", "death_date")):
        raw = (data.get(src) or "").strip()
        if raw:
            out[dst] = raw[:10] if len(raw) >= 10 and raw[:4].isdigit() else raw
    return out


def _bnf_author_hint(name: str) -> dict[str, Any]:
    """Piste BnF SRU (autorités + notices) : note biographique FR."""
    import re

    q = (name or "").strip().replace('"', " ")
    if len(q) < 3:
        return {}
    # Une seule requête autorités (2ᵉ trop lente / peu de bios)
    queries = (f'aut.anywhere all "{q}"',)
    for query in queries:
        try:
            r = requests.get(
                "https://catalogue.bnf.fr/api/SRU",
                params={
                    "version": "1.2",
                    "operation": "searchRetrieve",
                    "query": query,
                    "recordSchema": "dublincore",
                    "maximumRecords": "3",
                },
                headers={**UA_EXTRA, "Accept": "application/xml"},
                timeout=6,
            )
            if r.status_code != 200 or not r.text:
                continue
            for m in re.finditer(
                r"<dc:description[^>]*>([^<]{40,2000})</dc:description>",
                r.text,
                flags=re.I,
            ):
                bio = m.group(1).strip()
                low = bio.lower()
                # Écarter notes techniques catalogue (EAN, cote, etc.)
                if any(
                    x in low
                    for x in (
                        "code à barres",
                        "ean ",
                        "isbn ",
                        "cote ",
                        "in-8",
                        "in-12",
                        "broché",
                        "relié",
                    )
                ):
                    continue
                if len(bio) >= 60:
                    return {"bio": bio[:2000]}
        except Exception:
            continue
    return {}


def _local_catalog_works(name: str, *, cap: int = 40) -> list[dict[str, Any]]:
    """Œuvres déjà présentes dans catalog_daily_series pour cet auteur (PC)."""
    import re

    key = re.sub(r"\s+", " ", (name or "").strip().lower())
    if len(key) < 2:
        return []
    return (_ensure_local_works_index().get(key) or [])[:cap]


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


_LOCAL_WORKS_INDEX: dict[str, list[dict[str, Any]]] | None = None
_WORKS_INDEX_CACHE = ROOT / "data" / "_local_works_index.json"


def _ensure_local_works_index() -> dict[str, list[dict[str, Any]]]:
    """Index name_norm → œuvres catalogue (une fois par process + cache disque)."""
    global _LOCAL_WORKS_INDEX
    if _LOCAL_WORKS_INDEX is not None:
        return _LOCAL_WORKS_INDEX
    import re
    import sqlite3
    from collections import defaultdict

    path = ROOT / "data" / "local_catalog.sqlite"
    try:
        if _WORKS_INDEX_CACHE.exists() and path.exists():
            # Valide 6h (évite rebuild à chaque restart pendant dumps)
            age = time.time() - _WORKS_INDEX_CACHE.stat().st_mtime
            if age < 6 * 3600:
                raw = json.loads(_WORKS_INDEX_CACHE.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and len(raw) > 1000:
                    _LOCAL_WORKS_INDEX = raw
                    print(
                        f"local_works_index authors={len(_LOCAL_WORKS_INDEX)} (cache)",
                        flush=True,
                    )
                    return _LOCAL_WORKS_INDEX
    except Exception as exc:
        print(f"local_works_index_cache_miss {exc}", flush=True)

    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=60)
    try:
        for (raw,) in con.execute("SELECT doc_json FROM catalog_daily_series"):
            try:
                d = json.loads(raw or "{}")
            except Exception:
                continue
            authors = d.get("authors") or []
            if not isinstance(authors, list):
                continue
            title = str(d.get("name") or "")[:200]
            qid = str(d.get("qid") or d.get("wikidata_qid") or "")
            if not title:
                continue
            book = {
                "id": qid,
                "title": title,
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
            for a in authors:
                key = re.sub(r"\s+", " ", str(a).strip().lower())
                if len(key) < 2:
                    continue
                lst = by[key]
                if len(lst) >= 40:
                    continue
                if any(x.get("id") == qid and qid for x in lst):
                    continue
                lst.append(book)
    finally:
        con.close()
    _LOCAL_WORKS_INDEX = dict(by)
    try:
        _WORKS_INDEX_CACHE.write_text(
            json.dumps(_LOCAL_WORKS_INDEX, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass
    print(f"local_works_index authors={len(_LOCAL_WORKS_INDEX)}", flush=True)
    return _LOCAL_WORKS_INDEX


def _sqlite_incomplete(
    batch_n: int, *, after_rowid: int = 0
) -> tuple[list[dict[str, Any]], int]:
    """Lit les auteurs incomplets depuis le PC (curseur rowid, pas de re-scan offset)."""
    import sqlite3

    path = ROOT / "data" / "local_catalog.sqlite"
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=60)
    out: list[dict[str, Any]] = []
    last_rowid = after_rowid
    try:
        for rowid, raw in con.execute(
            "SELECT rowid, doc_json FROM catalog_authors "
            "WHERE rowid > ? ORDER BY rowid",
            (after_rowid,),
        ):
            last_rowid = int(rowid)
            try:
                d = json.loads(raw or "{}")
            except Exception:
                continue
            # Retenter aussi les stuck (sinon un seul passage puis plus rien)
            if not _needs(d):
                continue
            out.append(d)
            if len(out) >= batch_n:
                break
    finally:
        con.close()
    return out, last_rowid


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
    p.add_argument(
        "--fast",
        action="store_true",
        help="Lots agressifs : moins de sleep, retente les stuck, index œuvres local",
    )
    p.add_argument(
        "--skip-bio",
        action="store_true",
        help="Ne pas appeler Wikipédia bio (beaucoup plus rapide ; SPARQL only)",
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
    batch_n = max(10, min(250, args.batch))
    rounds = 0
    sqlite_rowid = int(prog.get("sqlite_rowid") or 0)

    # Budget Wikipedia généreux (sinon plafonné à ~80 bios / process)
    try:
        from app.catalog.daily_authors import reset_wiki_bio_budget

        reset_wiki_bio_budget(5000 if args.fast else 2000)
    except Exception:
        pass

    if args.fast or args.sqlite_only:
        # Précharge index œuvres (évite 1 LIKE SQL / auteur)
        try:
            _ensure_local_works_index()
        except Exception as exc:
            print(f"local_works_index_warn {exc}", flush=True)

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
        print(
            f"sqlite-only batch={batch_n} rowid>{sqlite_rowid} fast={bool(args.fast)}",
            flush=True,
        )

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
            docs, sqlite_rowid = _sqlite_incomplete(batch_n, after_rowid=sqlite_rowid)
            if not docs and sqlite_rowid:
                # fin de table → repartir du début
                sqlite_rowid = 0
                docs, sqlite_rowid = _sqlite_incomplete(batch_n, after_rowid=0)

        if not docs:
            print("COMPLETE — plus de fiches incomplètes détectées", flush=True)
            break

        # Résoudre QID manquants par nom
        qid_sleep = 0.03 if args.fast else 0.08
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
            time.sleep(qid_sleep)

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

            # Ordre rapide : Wikidata déjà fait → Wikipedia → OL (si OLID) → BnF
            need_bio = not (d.get("bio") or patch.get("bio") or "").strip()
            need_photo = not (
                d.get("photo_url") or d.get("image_url") or patch.get("photo_url") or ""
            ).strip()

            books = works.get(q) or []
            if not books and not (d.get("individual_books") or []):
                try:
                    books = _local_catalog_works(d.get("name") or "")
                except Exception:
                    books = []
            if books and not (d.get("individual_books") or []):
                patch["individual_books"] = books
                patch["total_individual_books"] = len(books)
                wks += 1

            filled_now = bool(patch)
            if not args.skip_bio and need_bio:
                name = (d.get("name") or "").strip()
                wiki = patch.get("wikipedia_url") or d.get("wikipedia_url")
                # En fast : Wikipedia seulement si URL déjà connue (évite 150× timeouts)
                if wiki or not args.fast:
                    try:
                        bio, wiki2 = _wiki_bio(name, wiki)
                    except Exception:
                        bio, wiki2 = "", wiki or ""
                    if bio:
                        patch["bio"] = bio
                        bios += 1
                        need_bio = False
                        filled_now = True
                    if wiki2 and not (d.get("wikipedia_url") or patch.get("wikipedia_url")):
                        patch["wikipedia_url"] = wiki2
                        filled_now = True
                    time.sleep(0.02 if args.fast else 0.05)

            # Open Library : seulement si OLID déjà connu (cache / fiche)
            if need_bio or need_photo:
                olid = (d.get("olid") or d.get("openlibrary_key") or "").strip()
                if not olid and (need_bio or need_photo):
                    try:
                        olid = _olid_from_cache(d.get("name") or "")
                    except Exception:
                        olid = ""
                if olid:
                    try:
                        olp = _ol_author_profile(olid)
                    except Exception:
                        olp = {}
                    if olp.get("olid") and not d.get("olid"):
                        patch["olid"] = olp["olid"]
                    if need_bio and olp.get("bio"):
                        patch["bio"] = olp["bio"]
                        bios += 1
                        need_bio = False
                        filled_now = True
                    if need_photo and olp.get("photo_url"):
                        patch["photo_url"] = olp["photo_url"]
                        patch["image_url"] = olp["photo_url"]
                        photos += 1
                        need_photo = False
                        filled_now = True
                    if not (d.get("birth_date") or patch.get("birth_date") or "").strip() and olp.get(
                        "birth_date"
                    ):
                        patch["birth_date"] = olp["birth_date"]
                        filled_now = True
                    time.sleep(0.03 if args.fast else 0.08)

            # BnF : dernier recours (désactivé en --fast : trop lent vs wiki/OL)
            if need_bio and not args.fast:
                try:
                    bnf = _bnf_author_hint(d.get("name") or "")
                except Exception:
                    bnf = {}
                if bnf.get("bio"):
                    patch["bio"] = bnf["bio"]
                    bios += 1
                    need_bio = False
                    filled_now = True
                time.sleep(0.08)

            if q.startswith("Q") and d.get("wikidata_qid") != q:
                patch["wikidata_qid"] = q
                qids_linked += 1

            patch["enrich_attempted_at"] = _utcnow()
            merged_preview = {**d, **patch}
            # Stuck seulement si aucune info nouvelle ET pas de QID (sinon on retente)
            if not q.startswith("Q") and not filled_now:
                patch["enrich_stuck"] = True
            elif args.fast:
                patch["enrich_stuck"] = False
            elif q.startswith("Q") and _needs(merged_preview) and not filled_now:
                patch["enrich_stuck"] = True
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
        prog["sqlite_rowid"] = sqlite_rowid
        prog["mongo_ok"] = bool(mongo_ok)
        _save_prog(prog)
        print(
            f"round={rounds} updated={updated} bios+={bios} nat+={nats} works+={wks} photo+={photos} "
            f"qid+={qids_linked} tot_upd={prog['updated']} rowid={sqlite_rowid}",
            flush=True,
        )

        time.sleep(max(0.05 if args.fast else 0.2, args.sleep))

    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
