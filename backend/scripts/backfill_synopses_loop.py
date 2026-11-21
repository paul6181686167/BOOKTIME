"""Boucle résumés / 4ᵉ de couverture sur le catalogue SQLite.

Priorité ISBN (Google Books / OL) = texte proche du dos du livre.
  python scripts/backfill_synopses_loop.py --batch 200 --loop
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

PROGRESS = ROOT / "data" / "_synopses_progress.json"


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


def _load_prog() -> dict:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"offset": 0, "filled": 0, "tried": 0, "rounds": 0}


def _save_prog(p: dict) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def _connect(*, readonly: bool = False) -> sqlite3.Connection:
    path = _db()
    if readonly:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=60)
    else:
        con = sqlite3.connect(str(path), timeout=180)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=180000")
    con.row_factory = sqlite3.Row
    return con


def _pick_isbn(doc: dict) -> str:
    isbn = (doc.get("isbn") or "").strip()
    if isbn:
        return isbn
    details = doc.get("volume_details")
    if isinstance(details, dict):
        for block in details.values():
            if isinstance(block, dict) and (block.get("isbn") or "").strip():
                return str(block.get("isbn")).strip()
    return ""


def collect_batch(offset: int, batch: int) -> tuple[list[tuple[str, dict]], int, int]:
    """Retourne (candidates, next_offset, total_rows_seen_in_pass)."""
    from app.catalog import catalog_media

    con = _connect(readonly=True)
    total = int(con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0])
    rows = con.execute(
        "SELECT qid, doc_json FROM catalog_daily_series ORDER BY rowid "
        "LIMIT ? OFFSET ?",
        (batch * 8, offset),
    ).fetchall()
    con.close()
    out: list[tuple[str, dict]] = []
    scanned = 0
    for row in rows:
        scanned += 1
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        if catalog_media.has_real_synopsis(doc):
            continue
        # Prioriser ISBN puis clé OL puis titre (wiki/GB/BnF)
        isbn = _pick_isbn(doc)
        qid = str(doc.get("qid") or row["qid"] or "")
        title = (doc.get("name") or doc.get("title") or "").strip()
        if not isbn and not (qid.startswith("OL") and qid.endswith("W")) and len(title) < 3:
            continue
        if isbn:
            doc["isbn"] = isbn
        out.append((row["qid"], doc))
        if len(out) >= batch * 2:
            break
    out.sort(
        key=lambda x: (
            0 if _pick_isbn(x[1]) else 1,
            0 if str(x[1].get("qid") or "").endswith("W") else 1,
        )
    )
    out = out[:batch]
    next_off = offset + scanned
    if next_off >= total:
        next_off = 0
    return out, next_off, total


def run_batch(candidates: list[tuple[str, dict]]) -> dict:
    """ISBN (GB/OL/BnF) → OL work → Wikipedia → pipeline heavy titre/auteur."""
    from app.catalog import catalog_media
    from app.utils.book_synopsis import (
        _ol_work_description_only,
        fetch_back_cover_by_isbn,
        is_usable_synopsis,
    )

    catalog_media.reset_budgets(synopsis=max(len(candidates) * 2, 40), covers=0)
    filled = tried = 0
    by_src: dict[str, int] = {}
    updates: list[tuple] = []
    for qid, doc in candidates:
        tried += 1
        text = ""
        src = ""
        isbn = _pick_isbn(doc)
        if isbn:
            text, src = fetch_back_cover_by_isbn(isbn)
            if not is_usable_synopsis(text) or catalog_media.is_template_blurb(text):
                text, src = "", ""
        if not text:
            ol_key = (doc.get("key") or "").strip()
            q = str(doc.get("qid") or qid or "")
            if not ol_key and q.startswith("OL") and q.endswith("W"):
                ol_key = f"/works/{q}"
            if ol_key:
                ol_text = (_ol_work_description_only(ol_key) or "").strip()
                if is_usable_synopsis(ol_text) and not catalog_media.is_template_blurb(ol_text):
                    text, src = ol_text, "openlibrary"
        if not text:
            # Pipeline élargi : wiki + GB titre/auteur + BnF via fetch_synopsis heavy
            title = (doc.get("name") or doc.get("title") or "").strip()
            author = ""
            authors = doc.get("authors") or doc.get("author") or []
            if isinstance(authors, list) and authors:
                a0 = authors[0]
                author = a0.get("name") if isinstance(a0, dict) else str(a0)
            elif isinstance(authors, str):
                author = authors
            try:
                text, src = catalog_media.fetch_synopsis(
                    title=title,
                    author=author or "",
                    isbn=isbn or "",
                    ol_key=(doc.get("key") or ""),
                    heavy=True,
                    prefer_back_cover=False,
                )
            except Exception:
                text, src = "", ""
            if not is_usable_synopsis(text) or catalog_media.is_template_blurb(text):
                text, src = "", ""
        if not text or not catalog_media.apply_synopsis(doc, text, src):
            if tried % 10 == 0:
                print(f"  synopsis tried={tried} filled={filled}", flush=True)
            continue
        filled += 1
        by_src[src] = by_src.get(src, 0) + 1
        updates.append(
            (
                str(doc.get("name") or ""),
                str(doc.get("name_norm") or ""),
                json.dumps(doc, ensure_ascii=False, default=str),
                qid,
            )
        )
        if len(updates) >= 15:
            _flush(updates)
            updates.clear()
            print(f"  synopsis filled={filled}/{tried} src={by_src}", flush=True)
    _flush(updates)
    return {"filled": filled, "tried": tried, "by_src": by_src}


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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=120)
    p.add_argument("--loop", action="store_true")
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--rounds", type=int, default=0, help="0=illimité si --loop")
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    print(f"db={_db()}", flush=True)

    rounds = 0
    while True:
        rounds += 1
        prog = _load_prog()
        offset = int(prog.get("offset") or 0)
        cands, next_off, total = collect_batch(offset, max(20, args.batch))
        print(
            f"round={rounds} offset={offset}/{total} candidates={len(cands)}",
            flush=True,
        )
        if not cands:
            prog["offset"] = next_off
            _save_prog(prog)
            print("no candidates in window — advance", flush=True)
            if not args.loop:
                break
            time.sleep(max(2.0, args.sleep))
            if args.rounds and rounds >= args.rounds:
                break
            continue
        res = run_batch(cands)
        prog["filled"] = int(prog.get("filled") or 0) + int(res["filled"])
        prog["tried"] = int(prog.get("tried") or 0) + int(res["tried"])
        prog["offset"] = next_off
        prog["rounds"] = int(prog.get("rounds") or 0) + 1
        _save_prog(prog)
        print(f"done {res} tot_filled={prog['filled']}", flush=True)
        if not args.loop:
            break
        if args.rounds and rounds >= args.rounds:
            break
        time.sleep(max(0.3, args.sleep))
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
