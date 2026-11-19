"""Trouve et applique les titres français sur TOUTES les fiches SQLite (hors daily).

  python scripts/backfill_french_titles.py --phase all
  python scripts/backfill_french_titles.py --phase wikidata
  python scripts/backfill_french_titles.py --phase ol --workers 8 --limit 0
  python scripts/backfill_french_titles.py --phase aliases
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


def _db_path() -> Path:
    raw = (os.environ.get("CATALOG_LOCAL_SQLITE") or "").strip()
    return Path(raw) if raw else ROOT / "data" / "local_catalog.sqlite"


def _connect(*, readonly: bool = False) -> sqlite3.Connection:
    path = _db_path()
    if readonly:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=60)
    else:
        con = sqlite3.connect(str(path), timeout=180)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=180000")
    con.row_factory = sqlite3.Row
    return con


def _flush(updates: list[tuple]) -> None:
    if not updates:
        return
    con = _connect(readonly=False)
    try:
        for attempt in range(12):
            try:
                con.executemany(
                    """
                    UPDATE catalog_daily_series
                    SET name=?, name_norm=?, doc_json=?, synced=0
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


def _row_update(qid: str, doc: dict) -> tuple:
    return (
        str(doc.get("name") or ""),
        str(doc.get("name_norm") or ""),
        json.dumps(doc, ensure_ascii=False, default=str),
        qid,
    )


def phase_aliases(limit: int = 0) -> dict:
    from app.catalog.catalog_titles_fr import (
        apply_french_title,
        alias_french_title,
        needs_french_title,
    )

    con = _connect(readonly=True)
    rows = con.execute("SELECT qid, doc_json FROM catalog_daily_series").fetchall()
    con.close()
    updates: list[tuple] = []
    changed = scanned = 0
    for row in rows:
        if limit and scanned >= limit:
            break
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        if not needs_french_title(doc):
            continue
        scanned += 1
        fr = alias_french_title(doc.get("name") or "")
        if not fr:
            continue
        if apply_french_title(doc, fr, "alias"):
            updates.append(_row_update(row["qid"], doc))
            changed += 1
        if len(updates) >= 200:
            _flush(updates)
            updates.clear()
            print(f"  aliases changed={changed} scanned={scanned}", flush=True)
    _flush(updates)
    return {"scanned": scanned, "changed": changed}


def phase_wikidata(limit: int = 0) -> dict:
    from app.catalog.catalog_titles_fr import (
        apply_french_title,
        needs_french_title,
        wikidata_labels_fr,
        looks_french,
    )

    con = _connect(readonly=True)
    rows = con.execute(
        "SELECT qid, doc_json FROM catalog_daily_series WHERE qid LIKE 'Q%'"
    ).fetchall()
    con.close()

    need: list[tuple[str, dict]] = []
    for row in rows:
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        if not needs_french_title(doc):
            continue
        need.append((row["qid"], doc))
        if limit and len(need) >= limit:
            break

    print(f"wikidata candidates={len(need)}", flush=True)
    changed = 0
    updates: list[tuple] = []
    for i in range(0, len(need), 50):
        batch = need[i : i + 50]
        labels = wikidata_labels_fr([q for q, _ in batch])
        batch_hits = 0
        for qid, doc in batch:
            pair = labels.get(qid)
            if not pair:
                continue
            fr, en = pair
            if not fr:
                continue
            if fr.lower() == (doc.get("name") or "").lower() and not looks_french(fr):
                continue
            if apply_french_title(doc, fr, "wikidata"):
                if en and not (doc.get("name_en") or "").strip():
                    doc["name_en"] = en
                updates.append(_row_update(qid, doc))
                changed += 1
                batch_hits += 1
        done = min(i + 50, len(need))
        if done % 500 == 0 or done == len(need) or batch_hits:
            print(
                f"  wikidata {done}/{len(need)} hits+={batch_hits} changed={changed}",
                flush=True,
            )
        # flush périodique pour ne pas tout perdre si crash
        if len(updates) >= 500:
            print(f"  flush {len(updates)}…", flush=True)
            _flush(updates)
            updates.clear()
    if updates:
        print(f"  flush final {len(updates)}…", flush=True)
        _flush(updates)
    return {"candidates": len(need), "changed": changed}


def _resolve_ol_one(qid: str, doc: dict) -> tuple[str, dict] | None:
    """Ordre : alias → Wikipédia langlink → Wikidata P648 → édition OL."""
    from app.catalog.catalog_titles_fr import (
        alias_french_title,
        apply_french_title,
        looks_french,
        openlibrary_french_title,
        wikidata_fr_from_olid,
        wikipedia_fr_title_from_en,
    )

    old = (doc.get("name") or "").strip()
    name_en = (doc.get("name_en") or "").strip() or old

    fr = alias_french_title(old) or alias_french_title(name_en)
    src = "alias"
    if not fr:
        fr = wikipedia_fr_title_from_en(old) or wikipedia_fr_title_from_en(name_en)
        src = "wikipedia_langlink"
    # Jaquette / ISBN = proxy « édition connue » ; sinon on tente quand même OL/WD
    # (le long-tail sans page FR restera vide — c'est la vraie limite des sources).
    popular = (
        bool((doc.get("cover_url") or "").strip())
        or bool(doc.get("needs_cover") is False)
        or bool((doc.get("isbn") or "").strip())
    )
    if not fr:
        fr = wikidata_fr_from_olid(qid)
        if fr:
            src = "wikidata_p648"
    if not fr and popular:
        fr = openlibrary_french_title(qid)
        if fr:
            src = "openlibrary_edition"
    if not fr:
        return None
    if fr.lower() == old.lower():
        return None
    # Accepter titres FR évidents, ou titre international différent (ex. Nineteen Eighty-Four → 1984)
    en_words = bool(__import__("re").search(r"\b(the|and|of|for|with|from|into)\b", fr, __import__("re").I))
    if not looks_french(fr) and en_words:
        return None
    if not looks_french(fr) and fr.lower() == name_en.lower():
        return None
    if apply_french_title(doc, fr, src):
        return qid, doc
    return None


def phase_ol(limit: int = 0, workers: int = 8) -> dict:
    from app.catalog.catalog_titles_fr import needs_french_title

    con = _connect(readonly=True)
    rows = con.execute(
        "SELECT qid, doc_json FROM catalog_daily_series "
        "WHERE qid LIKE 'OL%'"
    ).fetchall()
    con.close()

    jobs: list[tuple[str, dict]] = []
    for row in rows:
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        if not needs_french_title(doc):
            continue
        jobs.append((row["qid"], doc))
        if limit and len(jobs) >= limit:
            break

    print(f"ol candidates={len(jobs)} workers={workers}", flush=True)
    changed = 0
    tried = 0
    updates: list[tuple] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = {pool.submit(_resolve_ol_one, q, d): q for q, d in jobs}
        for fut in as_completed(futs):
            tried += 1
            try:
                got = fut.result()
            except Exception:
                got = None
            if got:
                qid, doc = got
                updates.append(_row_update(qid, doc))
                changed += 1
            if len(updates) >= 40:
                _flush(updates)
                updates.clear()
            if tried % 100 == 0:
                print(
                    f"  ol tried={tried}/{len(jobs)} changed={changed}",
                    flush=True,
                )
    _flush(updates)
    return {"candidates": len(jobs), "tried": tried, "changed": changed}


def phase_google_books(limit: int = 0, workers: int = 4) -> dict:
    """Titres FR via Google Books (langRestrict=fr), prioritairement ISBN."""
    from app.catalog.catalog_titles_fr import (
        apply_french_title,
        needs_french_title,
        looks_french,
    )
    from app.google_books import service as gb

    if not gb.is_enabled():
        print("google_books: API key manquante — skip", flush=True)
        return {"candidates": 0, "changed": 0, "skipped": "no_api_key"}

    con = _connect(readonly=True)
    rows = con.execute("SELECT qid, doc_json FROM catalog_daily_series").fetchall()
    con.close()

    jobs: list[tuple[str, dict, str]] = []
    for row in rows:
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        if not needs_french_title(doc):
            continue
        isbn = (doc.get("isbn") or "").strip()
        if not isbn:
            details = doc.get("volume_details")
            if isinstance(details, dict):
                for block in details.values():
                    if isinstance(block, dict) and (block.get("isbn") or "").strip():
                        isbn = str(block.get("isbn")).strip()
                        break
        # ISBN d'abord ; sinon titre+auteur si jaquette (proxy popularité)
        if not isbn and not (doc.get("cover_url") or "").strip():
            continue
        jobs.append((row["qid"], doc, isbn))
        if limit and len(jobs) >= limit:
            break

    # Prioriser ISBN
    jobs.sort(key=lambda x: (0 if x[2] else 1))
    print(f"google_books candidates={len(jobs)} workers={workers}", flush=True)

    def one(item: tuple[str, dict, str]):
        qid, doc, isbn = item
        try:
            if isbn:
                data = gb.search_volumes(f"isbn:{isbn}", max_results=3, lang_restrict="fr")
            else:
                title = (doc.get("name_en") or doc.get("name") or "").strip()
                authors = doc.get("authors") or []
                author = authors[0] if isinstance(authors, list) and authors else ""
                q = f"intitle:{title}"
                if author:
                    q += f" inauthor:{author}"
                data = gb.search_volumes(q, max_results=5, lang_restrict="fr")
            items = (data or {}).get("items") or []
            for it in items:
                vi = it.get("volumeInfo") or {}
                if str(vi.get("language") or "").lower()[:2] not in ("fr", ""):
                    # langRestrict devrait déjà filtrer
                    pass
                fr = (vi.get("title") or "").strip()
                if not fr or not looks_french(fr):
                    continue
                if fr.lower() == (doc.get("name") or "").lower():
                    continue
                if apply_french_title(doc, fr, "google_books"):
                    return qid, doc
        except Exception:
            return None
        return None

    changed = tried = 0
    updates: list[tuple] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = [pool.submit(one, j) for j in jobs]
        for fut in as_completed(futs):
            tried += 1
            got = fut.result()
            if got:
                qid, doc = got
                updates.append(_row_update(qid, doc))
                changed += 1
            if len(updates) >= 30:
                _flush(updates)
                updates.clear()
            if tried % 50 == 0:
                print(f"  gb tried={tried}/{len(jobs)} changed={changed}", flush=True)
    _flush(updates)
    return {"candidates": len(jobs), "tried": tried, "changed": changed}


def phase_wiki_langlinks(limit: int = 0, workers: int = 6) -> dict:
    """Pour fiches encore sans FR : langlinks Wikipédia (hors OL déjà traités aussi OK)."""
    from app.catalog.catalog_titles_fr import (
        apply_french_title,
        needs_french_title,
        wikipedia_fr_title_from_en,
        looks_french,
    )

    con = _connect(readonly=True)
    rows = con.execute("SELECT qid, doc_json FROM catalog_daily_series").fetchall()
    con.close()
    jobs = []
    for row in rows:
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        if not needs_french_title(doc):
            continue
        jobs.append((row["qid"], doc))
        if limit and len(jobs) >= limit:
            break
    print(f"langlinks candidates={len(jobs)}", flush=True)

    def one(item):
        qid, doc = item
        name = doc.get("name") or ""
        fr = wikipedia_fr_title_from_en(name)
        if not fr or not looks_french(fr) or fr.lower() == name.lower():
            en = (doc.get("name_en") or "").strip()
            if en:
                fr = wikipedia_fr_title_from_en(en)
        if not fr or not looks_french(fr):
            return None
        if apply_french_title(doc, fr, "wikipedia_langlink"):
            return qid, doc
        return None

    changed = tried = 0
    updates: list[tuple] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = [pool.submit(one, j) for j in jobs]
        for fut in as_completed(futs):
            tried += 1
            got = fut.result()
            if got:
                qid, doc = got
                updates.append(_row_update(qid, doc))
                changed += 1
            if len(updates) >= 40:
                _flush(updates)
                updates.clear()
            if tried % 100 == 0:
                print(f"  langlinks tried={tried} changed={changed}", flush=True)
    _flush(updates)
    return {"candidates": len(jobs), "tried": tried, "changed": changed}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--phase",
        choices=["aliases", "wikidata", "ol", "langlinks", "google", "all"],
        default="all",
    )
    p.add_argument("--limit", type=int, default=0, help="0 = pas de limite")
    p.add_argument("--workers", type=int, default=10)
    args = p.parse_args()
    _load_env()
    print(f"db={_db_path()}", flush=True)

    if args.phase in ("aliases", "all"):
        print("=== aliases ===", flush=True)
        print(phase_aliases(args.limit), flush=True)
    if args.phase in ("wikidata", "all"):
        print("=== wikidata ===", flush=True)
        print(phase_wikidata(args.limit), flush=True)
    if args.phase in ("ol", "all"):
        print("=== openlibrary ===", flush=True)
        print(phase_ol(args.limit, args.workers), flush=True)
    if args.phase in ("google", "all"):
        print("=== google_books FR ===", flush=True)
        print(phase_google_books(args.limit, max(2, min(6, args.workers // 2))), flush=True)
    if args.phase == "langlinks":
        print("=== wikipedia langlinks ===", flush=True)
        print(phase_wiki_langlinks(args.limit, max(4, args.workers // 2)), flush=True)
    elif args.phase == "all":
        # Secours langlinks seulement sur le reliquat (après OL)
        print("=== wikipedia langlinks (reliquat) ===", flush=True)
        print(phase_wiki_langlinks(args.limit, max(4, args.workers // 2)), flush=True)

    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
