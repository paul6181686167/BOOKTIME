"""Import massif Open Library (dumps authors + works) vers catalog_daily_series.

Streams gzip TSV sans décompresser entièrement sur disque.
Auteurs → cache Mongo `ol_author_cache` ; œuvres → fiches standalone (needs_cover OK).
"""
from __future__ import annotations

import gzip
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

from pymongo import UpdateOne

from ..static_wikidata.service import norm_title
from .daily_ingest import is_human_label, usable_cover

logger = logging.getLogger(__name__)

AUTHORS_URL = "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
WORKS_URL = "https://openlibrary.org/data/ol_dump_works_latest.txt.gz"
_QID_OK = re.compile(r"^OL\d+W$", re.I)
_AUTHOR_OK = re.compile(r"^OL\d+A$", re.I)
UA = "BooktimeCatalog/1.0 (ol dump import)"


def _progress_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "_ol_dump_progress.json"


def load_progress() -> dict[str, Any]:
    p = _progress_path()
    if not p.exists():
        return {"authors_done": False, "works_lines": 0, "promoted": 0}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"authors_done": False, "works_lines": 0, "promoted": 0}


def save_progress(data: dict[str, Any]) -> None:
    p = _progress_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _open_dump(source: str):
    """source = URL http(s) ou chemin local .txt.gz / .txt"""
    if source.startswith("http://") or source.startswith("https://"):
        req = Request(source, headers={"User-Agent": UA})
        raw = urlopen(req, timeout=120)  # noqa: S310 — URL OL contrôlée
        return gzip.GzipFile(fileobj=raw)
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(source)
    if str(path).endswith(".gz"):
        return gzip.open(path, "rb")
    return open(path, "rb")


def _iter_json_records(source: str) -> Iterable[tuple[str, dict[str, Any]]]:
    with _open_dump(source) as fh:
        for raw in fh:
            try:
                line = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
            except Exception:
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            key = (parts[1] or "").strip()
            try:
                data = json.loads(parts[4])
            except Exception:
                continue
            if isinstance(data, dict):
                yield key, data


def _author_coll():
    from ..db_config import database

    return database.db["ol_author_cache"]


def _series_coll():
    from ..db_config import database

    return database.db["catalog_daily_series"]


def import_authors_dump(source: str | None = None, *, limit: int = 0) -> dict[str, Any]:
    """Charge le dump auteurs dans ol_author_cache. limit=0 → tout."""
    src = source or AUTHORS_URL
    coll = _author_coll()
    batch: list[UpdateOne] = []
    n = 0
    t0 = time.time()
    for key, data in _iter_json_records(src):
        olid = key.rstrip("/").rsplit("/", 1)[-1]
        if not _AUTHOR_OK.match(olid):
            continue
        name = (data.get("name") or data.get("personal_name") or "").strip()
        if not is_human_label(name):
            continue
        batch.append(
            UpdateOne(
                {"_id": olid},
                {"$set": {"name": name, "name_norm": norm_title(name)}},
                upsert=True,
            )
        )
        if len(batch) >= 1000:
            coll.bulk_write(batch, ordered=False)
            n += len(batch)
            batch = []
            if n % 50000 == 0:
                logger.info("OL authors cache : %d (%.0fs)", n, time.time() - t0)
            if limit and n >= limit:
                break
    if batch and (not limit or n < limit):
        coll.bulk_write(batch, ordered=False)
        n += len(batch)
    prog = load_progress()
    prog["authors_done"] = True if not limit else prog.get("authors_done", False)
    prog["authors_cached"] = n
    save_progress(prog)
    return {"authors_upserted": n, "elapsed": int(time.time() - t0)}


def _resolve_authors(keys: list[str], cache: dict[str, str]) -> list[str]:
    missing = [k for k in keys if k not in cache]
    if missing:
        coll = _author_coll()
        for doc in coll.find({"_id": {"$in": missing}}, {"name": 1}):
            cache[doc["_id"]] = doc.get("name") or ""
    names = []
    for k in keys:
        name = cache.get(k) or ""
        if is_human_label(name):
            names.append(name)
    return names


def _work_author_keys(data: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for a in data.get("authors") or []:
        if not isinstance(a, dict):
            continue
        ref = a.get("author") if isinstance(a.get("author"), dict) else a
        key = ""
        if isinstance(ref, dict):
            key = (ref.get("key") or "").strip()
        if key:
            olid = key.rstrip("/").rsplit("/", 1)[-1]
            if _AUTHOR_OK.match(olid):
                out.append(olid)
    return out


def _cover_from_work(data: dict[str, Any]) -> str:
    covers = data.get("covers") or []
    if not covers:
        return ""
    try:
        cid = int(covers[0])
    except (TypeError, ValueError):
        return ""
    if cid <= 0:
        return ""
    return f"https://covers.openlibrary.org/b/id/{cid}-M.jpg"


def _cat_from_subjects(subjects: list[Any]) -> tuple[str, str]:
    joined = " ".join(str(s).lower() for s in subjects[:12])
    if "manga" in joined:
        return "manga", "Manga"
    if any(x in joined for x in ("comic", "bande dessinée", "graphic novel", "comics")):
        return "bd", "BD"
    return "roman", "Roman"


def _year_from_work(data: dict[str, Any]) -> int | None:
    for key in ("first_publish_date", "first_publish_year"):
        raw = str(data.get(key) or "")
        m = re.search(r"(1[5-9]\d{2}|20[0-3]\d)", raw)
        if m:
            return int(m.group(1))
    return None


def import_works_dump(
    source: str | None = None,
    *,
    limit: int = 50000,
    skip_lines: int | None = None,
) -> dict[str, Any]:
    """Importe jusqu'à `limit` œuvres nouvelles (titre+auteur). Reprend où progress s'est arrêté."""
    from . import daily_store
    from .daily_ingest import build_complete_entry

    src = source or WORKS_URL
    prog = load_progress()
    start_skip = int(skip_lines if skip_lines is not None else prog.get("works_lines") or 0)
    known = set()
    try:
        for doc in _series_coll().find({}, {"qid": 1}):
            q = (doc.get("qid") or "").strip()
            if q:
                known.add(q)
    except Exception:
        pass

    cache: dict[str, str] = {}
    batch_entries: list[dict[str, Any]] = []
    promoted = 0
    scanned = 0
    skipped = 0
    line_no = 0
    t0 = time.time()

    for key, data in _iter_json_records(src):
        line_no += 1
        if line_no <= start_skip:
            continue
        scanned += 1
        olid = key.rstrip("/").rsplit("/", 1)[-1]
        if not _QID_OK.match(olid):
            skipped += 1
            continue
        if olid in known:
            skipped += 1
            continue
        title = (data.get("title") or "").strip()
        if not is_human_label(title):
            skipped += 1
            continue
        akeys = _work_author_keys(data)
        if not akeys:
            skipped += 1
            continue
        authors = _resolve_authors(akeys[:3], cache)
        if not authors:
            skipped += 1
            continue
        author = authors[0]
        cover = usable_cover(_cover_from_work(data)) or ""
        subjects = list(data.get("subjects") or [])[:12]
        cat, genre = _cat_from_subjects(subjects)
        year = _year_from_work(data)
        cand = {
            "qid": olid,
            "name": title,
            "name_en": title,
            "author": author,
            "author_qid": "",
            "cover_url": cover,
            "category": cat,
            "genre": genre,
        }
        work = {
            "title": title,
            "author": author,
            "published_year": year,
            "work_qid": olid,
            "ol_key": f"/works/{olid}",
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            skipped += 1
            continue
        entry["source"] = "openlibrary_dump"
        batch_entries.append(entry)
        known.add(olid)
        if len(batch_entries) >= 200:
            for e in batch_entries:
                daily_store.upsert_series(e)
            promoted += len(batch_entries)
            batch_entries = []
            if promoted % 2000 == 0:
                prog["works_lines"] = line_no
                prog["promoted"] = int(prog.get("promoted") or 0) + 2000
                save_progress(prog)
                logger.info(
                    "OL works import : +%d (scanned=%d skip=%d line=%d %.0fs)",
                    promoted,
                    scanned,
                    skipped,
                    line_no,
                    time.time() - t0,
                )
        if promoted >= limit:
            break

    if batch_entries:
        for e in batch_entries:
            daily_store.upsert_series(e)
        promoted += len(batch_entries)

    prog["works_lines"] = line_no
    prog["promoted"] = int(prog.get("promoted") or 0) + promoted
    save_progress(prog)
    return {
        "promoted": promoted,
        "scanned": scanned,
        "skipped": skipped,
        "works_lines": line_no,
        "elapsed": int(time.time() - t0),
    }
