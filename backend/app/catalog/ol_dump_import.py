"""Import massif Open Library (dumps authors / works / editions).

- Streams gzip TSV (URL ou fichier local)
- Préfère Archive.org quand disponible
- Workers parallèles via (worker_id, workers) sur le n° de ligne
- bulk_write Mongo ~800 docs
"""
from __future__ import annotations

import gzip
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.request import Request, urlopen

from pymongo import UpdateOne

from ..static_wikidata.service import norm_title
from .daily_ingest import is_human_label, pick_isbn, usable_cover

logger = logging.getLogger(__name__)

AUTHORS_URL = "https://openlibrary.org/data/ol_dump_authors_latest.txt.gz"
WORKS_URL = "https://openlibrary.org/data/ol_dump_works_latest.txt.gz"
EDITIONS_URL = "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz"
_QID_WORK = re.compile(r"^OL\d+W$", re.I)
_QID_EDITION = re.compile(r"^OL\d+M$", re.I)
_AUTHOR_OK = re.compile(r"^OL\d+A$", re.I)
UA = "BooktimeCatalog/1.0 (ol dump import)"
BULK_SIZE = max(200, min(1000, int(os.getenv("OL_DUMP_BULK_SIZE", "800"))))


def _progress_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "_ol_dump_progress.json"


def _dumps_dir() -> Path:
    d = Path(__file__).resolve().parents[2] / "data" / "ol_dumps"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_progress() -> dict[str, Any]:
    p = _progress_path()
    if not p.exists():
        return {"authors_done": False, "works_lines": 0, "editions_lines": 0, "promoted": 0}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"authors_done": False, "works_lines": 0, "editions_lines": 0, "promoted": 0}


def save_progress(data: dict[str, Any]) -> None:
    p = _progress_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def latest_archive_item() -> str:
    """Identifiant Archive.org le plus récent dans ol_exports (ex. ol_dump_2025-11-30)."""
    forced = (os.getenv("OL_DUMP_IA_ITEM") or "").strip()
    if forced:
        return forced
    url = (
        "https://archive.org/advancedsearch.php?"
        "q=collection%3Aol_exports&fl[]=identifier&sort[]=-publicdate&rows=5&page=1&output=json"
    )
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=30) as r:  # noqa: S310
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        docs = ((data.get("response") or {}).get("docs") or [])
        for doc in docs:
            ident = str(doc.get("identifier") or "")
            if ident.startswith("ol_dump_") and len(ident) > 10:
                return ident
    except Exception as exc:
        logger.warning("IA search dumps échoué : %s", exc)
    return ""


def archive_dump_url(kind: str, item: str | None = None) -> str:
    """kind = authors|works|editions."""
    ident = (item or latest_archive_item() or "").strip()
    if not ident:
        return ""
    # Fichiers typiques : ol_dump_works_YYYY-MM-DD.txt.gz
    date = ident.replace("ol_dump_", "")
    name = f"ol_dump_{kind}_{date}.txt.gz"
    return f"https://archive.org/download/{ident}/{name}"


def resolve_dump_source(kind: str, explicit: str | None = None) -> str:
    """Ordre : chemin local → Archive.org → openlibrary.org latest."""
    if explicit:
        return explicit
    local = _dumps_dir() / f"ol_dump_{kind}_latest.txt.gz"
    if local.exists() and local.stat().st_size > 1000:
        return str(local)
    env_key = f"OL_DUMP_{kind.upper()}_URL"
    if (os.getenv(env_key) or "").strip():
        return os.environ[env_key].strip()
    ia = archive_dump_url(kind)
    if ia:
        return ia
    return {"authors": AUTHORS_URL, "works": WORKS_URL, "editions": EDITIONS_URL}[kind]


def download_dump(kind: str, *, force: bool = False) -> Path:
    """Télécharge le dump (Archive.org puis OL) vers data/ol_dumps/."""
    dest = _dumps_dir() / f"ol_dump_{kind}_latest.txt.gz"
    if dest.exists() and dest.stat().st_size > 1_000_000 and not force:
        return dest
    urls = []
    ia = archive_dump_url(kind)
    if ia:
        urls.append(ia)
    urls.append({"authors": AUTHORS_URL, "works": WORKS_URL, "editions": EDITIONS_URL}[kind])
    last_err: Exception | None = None
    for url in urls:
        try:
            logger.info("Téléchargement %s ← %s", kind, url)
            req = Request(url, headers={"User-Agent": UA})
            with urlopen(req, timeout=300) as r, open(dest, "wb") as out:  # noqa: S310
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            if dest.stat().st_size > 1000:
                return dest
        except Exception as exc:
            last_err = exc
            logger.warning("Download %s échoué (%s) : %s", kind, url, exc)
            if dest.exists():
                try:
                    dest.unlink()
                except Exception:
                    pass
    raise RuntimeError(f"Impossible de télécharger dump {kind}: {last_err}")


def _open_dump(source: str):
    if source.startswith("http://") or source.startswith("https://"):
        req = Request(source, headers={"User-Agent": UA})
        raw = urlopen(req, timeout=180)  # noqa: S310
        return gzip.GzipFile(fileobj=raw)
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(source)
    if str(path).endswith(".gz"):
        return gzip.open(path, "rb")
    return open(path, "rb")


def _iter_json_records(source: str) -> Iterable[tuple[int, str, dict[str, Any]]]:
    """Yield (line_no_1based, key, json)."""
    with _open_dump(source) as fh:
        line_no = 0
        for raw in fh:
            line_no += 1
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
                yield line_no, key, data


def _author_coll():
    from ..db_config import database

    return database.db["ol_author_cache"]


def _series_coll():
    from ..db_config import database

    return database.db["catalog_daily_series"]


def _flush_entries(entries: list[dict[str, Any]]) -> int:
    """Bulk upsert séries. Retourne le nombre écrit."""
    if not entries:
        return 0
    from .daily_store import prepare_entry

    ops: list[UpdateOne] = []
    now = datetime.now(timezone.utc).isoformat()
    for entry in entries:
        doc = prepare_entry(entry)
        qid = (doc.get("qid") or "").strip()
        if not qid:
            continue
        doc["source"] = doc.get("source") or "openlibrary_dump"
        doc["added_at"] = now
        ops.append(UpdateOne({"qid": qid}, {"$set": doc}, upsert=True))
    if not ops:
        return 0
    _series_coll().bulk_write(ops, ordered=False)
    return len(ops)


def import_authors_dump(source: str | None = None, *, limit: int = 0) -> dict[str, Any]:
    src = resolve_dump_source("authors", source)
    coll = _author_coll()
    batch: list[UpdateOne] = []
    n = 0
    t0 = time.time()
    for _line, key, data in _iter_json_records(src):
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
        if len(batch) >= BULK_SIZE:
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
    if not limit:
        prog["authors_done"] = True
    prog["authors_cached"] = n
    save_progress(prog)
    return {"authors_upserted": n, "source": src, "elapsed": int(time.time() - t0)}


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


def _author_keys_from_record(data: dict[str, Any]) -> list[str]:
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


def _cover_from_record(data: dict[str, Any]) -> str:
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


def _year_from_record(data: dict[str, Any]) -> int | None:
    for key in ("first_publish_date", "first_publish_year", "publish_date"):
        raw = str(data.get(key) or "")
        m = re.search(r"(1[5-9]\d{2}|20[0-3]\d)", raw)
        if m:
            return int(m.group(1))
    return None


def _known_qids() -> set[str]:
    known: set[str] = set()
    try:
        for doc in _series_coll().find({}, {"qid": 1}):
            q = (doc.get("qid") or "").strip()
            if q:
                known.add(q)
    except Exception:
        pass
    return known


def _worker_keeps(line_no: int, worker_id: int, workers: int) -> bool:
    if workers <= 1:
        return True
    return (line_no % workers) == (worker_id % workers)


def import_works_dump(
    source: str | None = None,
    *,
    limit: int = 50000,
    skip_lines: int | None = None,
    worker_id: int = 0,
    workers: int = 1,
) -> dict[str, Any]:
    from .daily_ingest import build_complete_entry

    src = resolve_dump_source("works", source)
    prog = load_progress()
    start_skip = int(skip_lines if skip_lines is not None else prog.get("works_lines") or 0)
    known = _known_qids()
    cache: dict[str, str] = {}
    batch_entries: list[dict[str, Any]] = []
    promoted = scanned = skipped = 0
    line_no = 0
    t0 = time.time()

    for line_no, key, data in _iter_json_records(src):
        if line_no <= start_skip:
            continue
        if not _worker_keeps(line_no, worker_id, workers):
            continue
        scanned += 1
        olid = key.rstrip("/").rsplit("/", 1)[-1]
        if not _QID_WORK.match(olid) or olid in known:
            skipped += 1
            continue
        title = (data.get("title") or "").strip()
        if not is_human_label(title):
            skipped += 1
            continue
        akeys = _author_keys_from_record(data)
        authors = _resolve_authors(akeys[:3], cache) if akeys else []
        if not authors:
            skipped += 1
            continue
        author = authors[0]
        cover = usable_cover(_cover_from_record(data)) or ""
        cat, genre = _cat_from_subjects(list(data.get("subjects") or [])[:12])
        year = _year_from_record(data)
        cand = {
            "qid": olid,
            "name": title,
            "name_en": title,
            "author": author,
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
        if len(batch_entries) >= BULK_SIZE:
            promoted += _flush_entries(batch_entries)
            batch_entries = []
            if promoted % 2000 < BULK_SIZE:
                if worker_id == 0:
                    prog["works_lines"] = max(int(prog.get("works_lines") or 0), line_no)
                    save_progress(prog)
                logger.info(
                    "OL works w%d : +%d scanned=%d line=%d %.0fs",
                    worker_id,
                    promoted,
                    scanned,
                    line_no,
                    time.time() - t0,
                )
        if promoted >= limit:
            break

    promoted += _flush_entries(batch_entries)
    if worker_id == 0:
        prog = load_progress()
        prog["works_lines"] = max(int(prog.get("works_lines") or 0), line_no)
        prog["promoted"] = int(prog.get("promoted") or 0) + promoted
        save_progress(prog)
    return {
        "promoted": promoted,
        "scanned": scanned,
        "skipped": skipped,
        "works_lines": line_no,
        "worker_id": worker_id,
        "workers": workers,
        "source": src,
        "elapsed": int(time.time() - t0),
    }


def import_editions_dump(
    source: str | None = None,
    *,
    limit: int = 50000,
    skip_lines: int | None = None,
    worker_id: int = 0,
    workers: int = 1,
) -> dict[str, Any]:
    """Éditions OL : titre + auteur + ISBN/jaquette plus souvent que works."""
    from .daily_ingest import build_complete_entry

    src = resolve_dump_source("editions", source)
    prog = load_progress()
    start_skip = int(skip_lines if skip_lines is not None else prog.get("editions_lines") or 0)
    known = _known_qids()
    cache: dict[str, str] = {}
    batch_entries: list[dict[str, Any]] = []
    promoted = scanned = skipped = 0
    line_no = 0
    t0 = time.time()

    for line_no, key, data in _iter_json_records(src):
        if line_no <= start_skip:
            continue
        if not _worker_keeps(line_no, worker_id, workers):
            continue
        scanned += 1
        olid = key.rstrip("/").rsplit("/", 1)[-1]
        if not _QID_EDITION.match(olid) or olid in known:
            skipped += 1
            continue
        title = (data.get("title") or "").strip()
        if not is_human_label(title):
            skipped += 1
            continue
        akeys = _author_keys_from_record(data)
        authors = _resolve_authors(akeys[:3], cache) if akeys else []
        if not authors:
            skipped += 1
            continue
        author = authors[0]
        isbn = pick_isbn((data.get("isbn_13") or []) + (data.get("isbn_10") or []))
        cover = usable_cover(_cover_from_record(data)) or ""
        if not cover and isbn:
            cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        work_key = ""
        for w in data.get("works") or []:
            if isinstance(w, dict) and w.get("key"):
                work_key = str(w["key"]).rstrip("/").rsplit("/", 1)[-1]
                break
        cat, genre = _cat_from_subjects(list(data.get("subjects") or [])[:8])
        year = _year_from_record(data)
        cand = {
            "qid": olid,
            "name": title,
            "name_en": title,
            "author": author,
            "cover_url": cover if usable_cover(cover) else "",
            "category": cat,
            "genre": genre,
        }
        work = {
            "title": title,
            "author": author,
            "published_year": year,
            "isbn": isbn or "",
            "work_qid": work_key or olid,
            "ol_key": f"/works/{work_key}" if work_key.endswith("W") else (f"/books/{olid}"),
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            skipped += 1
            continue
        entry["source"] = "openlibrary_editions_dump"
        batch_entries.append(entry)
        known.add(olid)
        if len(batch_entries) >= BULK_SIZE:
            promoted += _flush_entries(batch_entries)
            batch_entries = []
            if worker_id == 0:
                prog["editions_lines"] = max(int(prog.get("editions_lines") or 0), line_no)
                save_progress(prog)
            if promoted % 2000 < BULK_SIZE:
                logger.info(
                    "OL editions w%d : +%d scanned=%d line=%d %.0fs",
                    worker_id,
                    promoted,
                    scanned,
                    line_no,
                    time.time() - t0,
                )
        if promoted >= limit:
            break

    promoted += _flush_entries(batch_entries)
    if worker_id == 0:
        prog = load_progress()
        prog["editions_lines"] = max(int(prog.get("editions_lines") or 0), line_no)
        prog["promoted"] = int(prog.get("promoted") or 0) + promoted
        save_progress(prog)
    return {
        "promoted": promoted,
        "scanned": scanned,
        "skipped": skipped,
        "editions_lines": line_no,
        "worker_id": worker_id,
        "workers": workers,
        "source": src,
        "elapsed": int(time.time() - t0),
    }


# rétrocompat tests
def _work_author_keys(data: dict[str, Any]) -> list[str]:
    return _author_keys_from_record(data)


def _cover_from_work(data: dict[str, Any]) -> str:
    return _cover_from_record(data)


def _year_from_work(data: dict[str, Any]) -> int | None:
    return _year_from_record(data)
