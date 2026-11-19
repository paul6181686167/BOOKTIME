"""Remplit des ISBN réels (checksum OK) sur standalones + chaque tome.

Aucune invention : cascade Open Library → Google Books → BnF (isbn_resolve).
Purge aussi les ISBN invalides déjà stockés.

  python scripts/backfill_real_isbns.py --batch 80 --loop
  python scripts/backfill_real_isbns.py --purge-invalid-only
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROGRESS = ROOT / "data" / "_real_isbn_progress.json"


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
        "offset": 0,
        "filled": 0,
        "purged": 0,
        "tried": 0,
        "failed": 0,
        "rounds": 0,
    }


def _save_prog(p: dict[str, Any]) -> None:
    p["updated_at"] = _utcnow()
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


def _valid(isbn: str) -> str:
    from app.catalog.isbn_resolve import prefer_isbn

    return prefer_isbn([isbn]) if isbn else ""


def _authors(doc: dict) -> str:
    authors = doc.get("authors") or []
    if isinstance(authors, list) and authors:
        return str(authors[0] or "").strip()
    return str(doc.get("author") or "").strip()


def _ol_key_for(doc: dict, block: dict | None = None) -> str:
    for src in (block or {}, doc):
        for k in ("ol_key", "key"):
            v = str(src.get(k) or "").strip()
            if v:
                if v.startswith("OL") and v.endswith("W"):
                    return f"/works/{v}"
                if v.startswith("/"):
                    return v
    qid = str(doc.get("qid") or "").strip()
    if qid.startswith("OL") and qid.endswith("W"):
        return f"/works/{qid}"
    return ""


def purge_invalid() -> dict[str, int]:
    from app.openlibrary.isbn_lookup import clean_isbn, is_valid_isbn

    con = _connect(readonly=True)
    rows = con.execute("SELECT qid, doc_json FROM catalog_daily_series").fetchall()
    con.close()
    updates: list[tuple] = []
    purged = scanned = 0
    for row in rows:
        scanned += 1
        try:
            doc = json.loads(row["doc_json"])
        except Exception:
            continue
        dirty = False
        top = clean_isbn(str(doc.get("isbn") or ""))
        if top and not is_valid_isbn(top):
            doc.pop("isbn", None)
            purged += 1
            dirty = True
        details = doc.get("volume_details")
        if isinstance(details, dict):
            for block in details.values():
                if not isinstance(block, dict):
                    continue
                raw = clean_isbn(str(block.get("isbn") or ""))
                if raw and not is_valid_isbn(raw):
                    block.pop("isbn", None)
                    purged += 1
                    dirty = True
                elif raw:
                    # normaliser en ISBN-13 si possible
                    v = _valid(raw)
                    if v and v != raw:
                        block["isbn"] = v
                        dirty = True
        if dirty:
            updates.append(
                (
                    str(doc.get("name") or ""),
                    str(doc.get("name_norm") or ""),
                    json.dumps(doc, ensure_ascii=False, default=str),
                    row["qid"],
                )
            )
        if len(updates) >= 200:
            _flush(updates)
            updates.clear()
            print(f"  purge scanned={scanned} purged={purged}", flush=True)
    _flush(updates)
    return {"scanned": scanned, "purged": purged, "written": scanned and purged}


def _needs_isbn(doc: dict) -> list[tuple[str, dict]]:
    """Liste (volume_key|'__fiche__', block_or_doc) sans ISBN valide."""
    out: list[tuple[str, dict]] = []
    details = doc.get("volume_details")
    if isinstance(details, dict) and details:
        for vk, block in details.items():
            if not isinstance(block, dict):
                continue
            if _valid(block.get("isbn") or ""):
                continue
            out.append((str(vk), block))
    else:
        if not _valid(doc.get("isbn") or ""):
            out.append(("__fiche__", doc))
    return out


def collect_batch(offset: int, batch: int) -> tuple[list[tuple[str, dict]], int, int]:
    con = _connect(readonly=True)
    total = int(con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0])
    rows = con.execute(
        "SELECT qid, doc_json FROM catalog_daily_series ORDER BY rowid "
        "LIMIT ? OFFSET ?",
        (max(batch * 6, 200), offset),
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
        if not _needs_isbn(doc):
            continue
        # Priorité : clé OL (éditions) puis le reste
        doc["_qid"] = row["qid"]
        out.append((row["qid"], doc))
        if len(out) >= batch:
            break
    next_off = offset + scanned
    if next_off >= total:
        next_off = 0
    return out, next_off, total


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


def fill_doc(doc: dict, *, budget_per_doc: int = 8) -> tuple[int, int]:
    """Retourne (filled, tried)."""
    from app.catalog.isbn_resolve import reset_budget, resolve_isbn

    reset_budget(max(20, budget_per_doc * 3))
    author = _authors(doc)
    filled = tried = 0
    needs = _needs_isbn(doc)
    details = doc.get("volume_details")
    if not isinstance(details, dict):
        details = {}
        doc["volume_details"] = details

    for vk, block in needs:
        if tried >= budget_per_doc:
            break
        tried += 1
        if vk == "__fiche__":
            title = str(doc.get("name") or "")
            title_en = str(doc.get("name_en") or "")
            ol_key = _ol_key_for(doc)
            isbn = resolve_isbn(
                title=title, author=author, title_en=title_en, ol_key=ol_key
            )
            if not isbn:
                continue
            doc["isbn"] = isbn
            # créer tome 1 si absent
            if "1" not in details:
                details["1"] = {
                    "author": author,
                    "cover_url": doc.get("cover_url") or "",
                    "isbn": isbn,
                }
            else:
                details["1"]["isbn"] = isbn
            filled += 1
            continue

        title = str(
            (doc.get("volume_titles") or {}).get(vk)
            or block.get("title")
            or doc.get("name")
            or ""
        )
        title_en = str((doc.get("volume_titles_en") or {}).get(vk) or doc.get("name_en") or "")
        ol_key = _ol_key_for(doc, block)
        # Pour standalone mono-tome, la clé œuvre OL suffit
        isbn = resolve_isbn(
            title=title,
            author=str(block.get("author") or author),
            title_en=title_en,
            ol_key=ol_key if vk in ("1", "01") or len(needs) == 1 else (
                str(block.get("ol_key") or "") or (ol_key if vk == "1" else "")
            ),
        )
        if not isbn:
            # dernière chance : titre du tome sans ol_key (évite de coller l'ISBN du tome 1 à tous)
            if ol_key and vk not in ("1", "01"):
                isbn = resolve_isbn(
                    title=title,
                    author=str(block.get("author") or author),
                    title_en=title_en,
                    ol_key="",
                )
        if not isbn:
            continue
        block["isbn"] = isbn
        filled += 1

    # Remonter ISBN tome 1 au niveau fiche (pratique covers/synopsis)
    top = _valid(doc.get("isbn") or "")
    if not top:
        for key in ("1", "01"):
            b = details.get(key)
            if isinstance(b, dict):
                top = _valid(b.get("isbn") or "")
                if top:
                    doc["isbn"] = top
                    break
    if filled:
        doc["isbn_resolved_at"] = _utcnow()
    return filled, tried


def run_batch(candidates: list[tuple[str, dict]], *, per_doc: int) -> dict[str, int]:
    filled = tried = failed = 0
    updates: list[tuple] = []
    for i, (qid, doc) in enumerate(candidates, 1):
        got, did = fill_doc(doc, budget_per_doc=per_doc)
        tried += did
        filled += got
        if got:
            updates.append(
                (
                    str(doc.get("name") or ""),
                    str(doc.get("name_norm") or ""),
                    json.dumps(doc, ensure_ascii=False, default=str),
                    qid,
                )
            )
        else:
            failed += 1
        if i % 10 == 0 or got:
            print(
                f"  isbn {i}/{len(candidates)} filled+={got} tot_filled={filled} tried={tried}",
                flush=True,
            )
        if len(updates) >= 20:
            _flush(updates)
            updates.clear()
        time.sleep(0.05)
    _flush(updates)
    return {"filled": filled, "tried": tried, "failed_docs": failed}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=60)
    p.add_argument("--per-doc", type=int, default=6, help="résolutions max par fiche")
    p.add_argument("--loop", action="store_true")
    p.add_argument("--sleep", type=float, default=0.8)
    p.add_argument("--rounds", type=int, default=0)
    p.add_argument("--purge-invalid-only", action="store_true")
    p.add_argument("--skip-purge", action="store_true")
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    print(f"db={_db()}", flush=True)

    prog = _load_prog()
    if not args.skip_purge:
        print("=== purge ISBN invalides ===", flush=True)
        pr = purge_invalid()
        prog["purged"] = int(prog.get("purged") or 0) + int(pr.get("purged") or 0)
        _save_prog(prog)
        print(f"PURGE {pr}", flush=True)
    if args.purge_invalid_only:
        return 0

    rounds = 0
    while True:
        rounds += 1
        prog = _load_prog()
        offset = int(prog.get("offset") or 0)
        cands, next_off, total = collect_batch(offset, max(10, args.batch))
        print(
            f"round={rounds} offset={offset}/{total} candidates={len(cands)}",
            flush=True,
        )
        if not cands:
            prog["offset"] = next_off
            _save_prog(prog)
            print("fenêtre vide — advance", flush=True)
            if not args.loop:
                break
            time.sleep(max(2.0, args.sleep))
            if args.rounds and rounds >= args.rounds:
                break
            continue
        res = run_batch(cands, per_doc=max(1, args.per_doc))
        prog["filled"] = int(prog.get("filled") or 0) + int(res["filled"])
        prog["tried"] = int(prog.get("tried") or 0) + int(res["tried"])
        prog["failed"] = int(prog.get("failed") or 0) + int(res["failed_docs"])
        prog["offset"] = next_off
        prog["rounds"] = int(prog.get("rounds") or 0) + 1
        _save_prog(prog)
        print(f"done {res} tot_filled={prog['filled']}", flush=True)
        if not args.loop:
            break
        if args.rounds and rounds >= args.rounds:
            break
        time.sleep(max(0.3, args.sleep))
    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
