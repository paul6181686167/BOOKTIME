"""Croise auteurs Mongo × œuvres Wikidata / individual_books → catalogue.

N'ajoute pas d'auteurs. Hors lots quotidiens.
"""
from __future__ import annotations

import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _log(msg: str) -> None:
    print(msg, flush=True)


def _year_from_date(raw: str | None) -> int | None:
    s = (raw or "").strip()
    if len(s) >= 4 and s[:4].isdigit():
        try:
            y = int(s[:4])
            return y if 1400 <= y <= 2035 else None
        except ValueError:
            return None
    if s.startswith("+") and len(s) >= 5:
        try:
            y = int(s[1:5])
            return y if 1400 <= y <= 2035 else None
        except ValueError:
            return None
    return None


def main() -> int:
    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    os.environ.setdefault("CATALOG_ADD_AUTHORS", "0")

    cap = int(os.getenv("RECOVER_WORKS_CAP", "3000"))
    batch_authors = int(os.getenv("RECOVER_AUTHOR_BATCH", "15"))
    max_authors = int(os.getenv("RECOVER_AUTHORS_SCAN", "8000"))

    from pymongo import MongoClient
    from app.db_config import database
    from app.catalog import daily_store
    from app.catalog.isbn_resolve import reset_budget, reset_cover_budget
    from app.catalog.daily_ingest import (
        _lit,
        _qid,
        _sparql,
        build_complete_entry,
        commons_url,
        is_human_label,
        meta_save_pair,
        usable_cover,
    )

    reset_budget(0)
    reset_cover_budget(300)

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=20000)
    db = client[os.environ.get("DATABASE_NAME") or "booktime"]
    database._client = client
    database._db = db

    meta_save_pair("ingest_focus", 1, 0)
    meta_save_pair("author_dry_streak", 0, 0)

    known: set[str] = set()
    for doc in db["catalog_daily_series"].find({}, {"qid": 1, "wikidata_qid": 1}):
        for k in ("qid", "wikidata_qid"):
            q = (doc.get(k) or "").strip()
            if q.startswith("Q"):
                known.add(q)
    _log(f"known_works={len(known)} target_cap={cap}")

    promoted = 0
    skipped_known = 0
    skipped_bad = 0
    seen_work: set[str] = set()
    t0 = time.time()

    def _promote(wqid: str, title: str, author: str, aqid: str, year: int | None, cover: str, isbn: str = "") -> bool:
        nonlocal promoted, skipped_bad
        if promoted >= cap:
            return False
        if not wqid.startswith("Q") or wqid in known or wqid in seen_work:
            return False
        seen_work.add(wqid)
        if not is_human_label(title) or not is_human_label(author):
            skipped_bad += 1
            return False
        cand = {
            "qid": wqid,
            "name": title,
            "name_en": title,
            "author": author,
            "author_qid": aqid,
            "cover_url": cover if usable_cover(cover) else "",
            "category": "roman",
            "genre": "Roman",
        }
        work = {
            "title": title,
            "author": author,
            "author_qid": aqid,
            "published_year": year,
            "isbn": isbn,
            "work_qid": wqid,
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            skipped_bad += 1
            return False
        daily_store.upsert_series(entry)
        known.add(wqid)
        promoted += 1
        if promoted % 100 == 0:
            _log(f"progress promoted={promoted} elapsed={int(time.time() - t0)}s")
        return True

    # --- Phase 1 : œuvres déjà liées dans authors.individual_books ---
    linked = 0
    for doc in db["authors"].find({"individual_books.0": {"$exists": True}}, {"name": 1, "wikidata_qid": 1, "individual_books": 1}):
        if promoted >= cap:
            break
        author = (doc.get("name") or "").strip()
        aqid = (doc.get("wikidata_qid") or "").strip()
        if not is_human_label(author):
            continue
        for book in doc.get("individual_books") or []:
            if promoted >= cap:
                break
            wqid = str((book or {}).get("id") or "").strip()
            title = str((book or {}).get("title") or "").strip()
            if title == wqid or not is_human_label(title):
                continue
            if wqid in known:
                skipped_known += 1
                continue
            year = _year_from_date(str((book or {}).get("publication_date") or ""))
            isbn = str((book or {}).get("isbn") or "").replace("-", "")
            if _promote(wqid, title, author, aqid, year, "", isbn):
                linked += 1
    _log(f"phase1_individual_books promoted={linked} total={promoted}")

    # --- Phase 2 : SPARQL P50 sans filtre de type trop étroit ---
    authors: list[tuple[str, str]] = []
    for doc in db["authors"].find(
        {"wikidata_qid": {"$regex": "^Q\\d+$"}, "source": "daily"},
        {"wikidata_qid": 1, "name": 1},
    ):
        qid = (doc.get("wikidata_qid") or "").strip()
        name = (doc.get("name") or "").strip()
        if qid.startswith("Q") and is_human_label(name):
            authors.append((qid, name))
    random.shuffle(authors)
    authors = authors[:max_authors]
    _log(f"phase2_authors={len(authors)}")

    types = " ".join(
        [
            "wd:Q8261",  # novel
            "wd:Q47461344",  # written work
            "wd:Q7725634",  # literary work
            "wd:Q571",  # book
            "wd:Q49084",  # short story
            "wd:Q253623",  # poetry collection
            "wd:Q12833777",
            "wd:Q838796",
            "wd:Q725377",
            "wd:Q1667921",
            "wd:Q277759",
            "wd:Q21198342",
            "wd:Q14406742",
            "wd:Q742169",
            "wd:Q131436",  # comic book / album variants
            "wd:Q1004",  # comics
        ]
    )
    sparql_errors = 0

    for i in range(0, len(authors), batch_authors):
        if promoted >= cap:
            break
        chunk = authors[i : i + batch_authors]
        values = " ".join(f"wd:{aq}" for aq, _ in chunk)
        author_names = {aq: nm for aq, nm in chunk}
        query = f"""
SELECT DISTINCT ?work ?workLabel ?enLabel ?author ?authorLabel ?date ?img ?isbn ?isbn10 WHERE {{
  VALUES ?author {{ {values} }}
  ?work wdt:P50 ?author .
  ?work wdt:P31 ?type .
  VALUES ?type {{ {types} }}
  OPTIONAL {{ ?work wdt:P577 ?date. }}
  OPTIONAL {{ ?work wdt:P18 ?img. }}
  OPTIONAL {{ ?work wdt:P212 ?isbn. }}
  OPTIONAL {{ ?work wdt:P957 ?isbn10. }}
  OPTIONAL {{
    ?work rdfs:label ?enLabel .
    FILTER(LANG(?enLabel) = "en")
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
LIMIT 500
"""
        try:
            rows = _sparql(query, timeout=60)
        except Exception as exc:
            sparql_errors += 1
            _log(f"sparql_err batch={i // batch_authors} {exc}")
            time.sleep(2)
            continue

        batch_ok = 0
        for row in rows:
            if promoted >= cap:
                break
            wqid = _qid(_lit(row, "work"))
            if not wqid.startswith("Q") or wqid in known or wqid in seen_work:
                skipped_known += 1
                continue
            title = _lit(row, "workLabel")
            if title == wqid or not is_human_label(title):
                title = _lit(row, "enLabel") or title
            aqid = _qid(_lit(row, "author"))
            author = author_names.get(aqid) or _lit(row, "authorLabel")
            year = _year_from_date(_lit(row, "date"))
            img = _lit(row, "img")
            cover = ""
            if img:
                cover = commons_url(img.rsplit("/", 1)[-1])
            isbn = (_lit(row, "isbn") or _lit(row, "isbn10") or "").replace("-", "")
            if _promote(wqid, title.strip(), author, aqid, year, cover, isbn):
                batch_ok += 1

        if (i // batch_authors) % 10 == 0 or batch_ok:
            _log(
                f"batch={i // batch_authors} authors={min(i + batch_authors, len(authors))}/{len(authors)} "
                f"+{batch_ok} promoted={promoted} rows={len(rows)}"
            )
        time.sleep(0.25)

    series_n = db["catalog_daily_series"].count_documents({})
    authors_n = db["authors"].count_documents({})
    _log(
        f"done promoted={promoted} skipped_known={skipped_known} skipped_bad={skipped_bad} "
        f"sparql_errors={sparql_errors} series={series_n} authors={authors_n} "
        f"elapsed={int(time.time() - t0)}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
