"""Enrichit les fiches EXISTANTES via dumps OL locaux (0 API, 0 nouvelles fiches).

Passe works  → description / couverture
Passe editions → ISBN / couverture (match work OLID)

  python scripts/enrich_existing_from_ol_dumps.py --phase both
  python scripts/enrich_existing_from_ol_dumps.py --phase editions --max-lines 2000000
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROGRESS = ROOT / "data" / "_enrich_from_dumps_progress.json"
DUMPS = ROOT / "data" / "ol_dumps"


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


def _load_prog() -> dict[str, Any]:
    if PROGRESS.exists():
        try:
            return json.loads(PROGRESS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "works_line": 0,
        "editions_line": 0,
        "isbn": 0,
        "cover": 0,
        "synopsis": 0,
        "updated": 0,
    }


def _save_prog(p: dict[str, Any]) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def _text_field(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("value") or "").strip()
    return str(val or "").strip()


def _pick_isbn(data: dict) -> str:
    from app.catalog.daily_ingest import pick_isbn

    return pick_isbn((data.get("isbn_13") or []) + (data.get("isbn_10") or [])) or ""


def _cover_url(data: dict, isbn: str = "") -> str:
    from app.catalog.daily_ingest import usable_cover
    from app.catalog.ol_dump_import import _cover_from_record

    cover = usable_cover(_cover_from_record(data)) or ""
    if not cover and isbn:
        cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
    return cover or ""


def _build_needs() -> dict[str, dict[str, Any]]:
    """olid (OLxxxW) → flags besoins + qid sqlite."""
    from app.catalog.catalog_media import has_real_synopsis
    from app.catalog.daily_ingest import usable_cover

    con = sqlite3.connect(f"file:{_db().as_posix()}?mode=ro", uri=True, timeout=120)
    needs: dict[str, dict[str, Any]] = {}
    n = 0
    for qid, raw in con.execute("SELECT qid, doc_json FROM catalog_daily_series"):
        n += 1
        try:
            doc = json.loads(raw or "{}")
        except Exception:
            continue
        olid = str(qid or doc.get("qid") or "").strip()
        if not olid.endswith("W"):
            # editions-as-fiche : tenter work_qid / key
            wk = str(doc.get("work_qid") or "").strip()
            if not wk.endswith("W"):
                key = str(doc.get("key") or doc.get("ol_key") or "")
                if "/works/" in key:
                    wk = key.rstrip("/").rsplit("/", 1)[-1]
            if wk.endswith("W"):
                olid = wk
            else:
                continue
        need_isbn = not bool(str(doc.get("isbn") or "").strip())
        need_cover = not bool(usable_cover(doc.get("cover_url")))
        need_syn = not has_real_synopsis(doc)
        if not (need_isbn or need_cover or need_syn):
            continue
        prev = needs.get(olid)
        if prev:
            prev["need_isbn"] = prev["need_isbn"] or need_isbn
            prev["need_cover"] = prev["need_cover"] or need_cover
            prev["need_syn"] = prev["need_syn"] or need_syn
            continue
        needs[olid] = {
            "qid": str(qid),
            "need_isbn": need_isbn,
            "need_cover": need_cover,
            "need_syn": need_syn,
        }
        if n % 200000 == 0:
            print(f"  index_scan {n} needs={len(needs)}", flush=True)
    con.close()
    print(f"needs_works={len(needs)} scanned_rows={n}", flush=True)
    return needs


def _flush_updates(updates: dict[str, dict[str, str]], prog: dict[str, Any]) -> int:
    """updates[qid] = {isbn?, cover?, synopsis?, source?}"""
    if not updates:
        return 0
    from app.catalog.catalog_media import apply_synopsis, has_real_synopsis
    from app.catalog.daily_ingest import usable_cover

    con = sqlite3.connect(str(_db()), timeout=180)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=180000")
    written = 0
    rows: list[tuple[str, str]] = []
    try:
        for qid, patch in updates.items():
            row = con.execute(
                "SELECT doc_json FROM catalog_daily_series WHERE qid=?", (qid,)
            ).fetchone()
            if not row:
                continue
            try:
                doc = json.loads(row[0] or "{}")
            except Exception:
                continue
            changed = False
            isbn = (patch.get("isbn") or "").strip()
            if isbn and not str(doc.get("isbn") or "").strip():
                doc["isbn"] = isbn
                details = doc.get("volume_details")
                if isinstance(details, dict):
                    for block in details.values():
                        if isinstance(block, dict) and not block.get("isbn"):
                            block["isbn"] = isbn
                prog["isbn"] = int(prog.get("isbn") or 0) + 1
                changed = True
            cover = (patch.get("cover") or "").strip()
            if cover and not usable_cover(doc.get("cover_url")):
                doc["cover_url"] = cover
                doc["needs_cover"] = False
                doc["cover_source"] = patch.get("cover_src") or "ol_dump"
                prog["cover"] = int(prog.get("cover") or 0) + 1
                changed = True
            syn = (patch.get("synopsis") or "").strip()
            if syn and not has_real_synopsis(doc):
                if apply_synopsis(doc, syn, patch.get("syn_src") or "ol_works_dump"):
                    prog["synopsis"] = int(prog.get("synopsis") or 0) + 1
                    changed = True
            if not changed:
                continue
            rows.append((json.dumps(doc, ensure_ascii=False, default=str), qid))
        if rows:
            for attempt in range(10):
                try:
                    con.executemany(
                        "UPDATE catalog_daily_series SET doc_json=?, synced=0 WHERE qid=?",
                        rows,
                    )
                    con.commit()
                    written = len(rows)
                    break
                except sqlite3.OperationalError as exc:
                    if "locked" not in str(exc).lower() or attempt >= 9:
                        raise
                    time.sleep(1.2 * (attempt + 1))
    finally:
        con.close()
    prog["updated"] = int(prog.get("updated") or 0) + written
    return written


def _run_phase(
    *,
    phase: str,
    needs: dict[str, dict[str, Any]],
    prog: dict[str, Any],
    max_lines: int,
    start_line: int,
) -> None:
    from app.catalog.ol_dump_import import _iter_json_records, resolve_dump_source
    from app.utils.book_synopsis import is_usable_synopsis

    src = resolve_dump_source(phase)
    print(f"phase={phase} source={src} start_after={start_line}", flush=True)
    pending: dict[str, dict[str, str]] = {}  # qid → patch
    scanned = matched = 0
    t0 = time.time()
    line_key = f"{phase}_line"

    for line_no, key, data in _iter_json_records(src, start_after=start_line):
        scanned += 1
        if max_lines and scanned > max_lines:
            break

        if phase == "works":
            olid = key.rstrip("/").rsplit("/", 1)[-1]
            info = needs.get(olid)
            if not info:
                continue
            matched += 1
            patch = pending.setdefault(info["qid"], {})
            if info["need_syn"] and "synopsis" not in patch:
                desc = _text_field(data.get("description"))
                if is_usable_synopsis(desc):
                    patch["synopsis"] = desc[:2000]
                    patch["syn_src"] = "ol_works_dump"
            if info["need_cover"] and "cover" not in patch:
                cover = _cover_url(data)
                if cover:
                    patch["cover"] = cover
                    patch["cover_src"] = "ol_works_dump"
        else:
            # editions → ISBN/cover via work key
            work_olid = ""
            for w in data.get("works") or []:
                if isinstance(w, dict) and w.get("key"):
                    work_olid = str(w["key"]).rstrip("/").rsplit("/", 1)[-1]
                    break
            if not work_olid.endswith("W"):
                continue
            info = needs.get(work_olid)
            if not info:
                continue
            matched += 1
            patch = pending.setdefault(info["qid"], {})
            if info["need_isbn"] and "isbn" not in patch:
                isbn = _pick_isbn(data)
                if isbn:
                    patch["isbn"] = isbn
            if info["need_cover"] and "cover" not in patch:
                isbn = patch.get("isbn") or _pick_isbn(data)
                cover = _cover_url(data, isbn)
                if cover:
                    patch["cover"] = cover
                    patch["cover_src"] = "ol_editions_dump"
            if info["need_syn"] and "synopsis" not in patch:
                desc = _text_field(data.get("description"))
                if is_usable_synopsis(desc):
                    patch["synopsis"] = desc[:2000]
                    patch["syn_src"] = "ol_editions_dump"

        if len(pending) >= 400:
            w = _flush_updates(pending, prog)
            pending.clear()
            prog[line_key] = line_no
            _save_prog(prog)
            print(
                f"  {phase} line={line_no} scanned={scanned} matched={matched} "
                f"flushed+={w} tot_upd={prog['updated']} "
                f"isbn={prog['isbn']} cover={prog['cover']} syn={prog['synopsis']} "
                f"{time.time()-t0:.0f}s",
                flush=True,
            )

        if scanned % 200000 == 0:
            prog[line_key] = line_no
            _save_prog(prog)
            print(
                f"  {phase} heartbeat line={line_no} scanned={scanned} matched={matched}",
                flush=True,
            )

    if pending:
        _flush_updates(pending, prog)
    prog[line_key] = max(int(prog.get(line_key) or 0), start_line + scanned)
    _save_prog(prog)
    print(
        f"DONE {phase} scanned={scanned} matched={matched} updated={prog['updated']}",
        flush=True,
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("works", "editions", "both"), default="both")
    p.add_argument("--max-lines", type=int, default=0, help="0 = dump entier")
    p.add_argument("--reset-progress", action="store_true")
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    os.environ.setdefault("CATALOG_LOCAL_SQLITE", str(_db()))

    prog = {} if args.reset_progress else _load_prog()
    if args.reset_progress:
        prog = _load_prog()
        prog.update(
            {
                "works_line": 0,
                "editions_line": 0,
                "isbn": 0,
                "cover": 0,
                "synopsis": 0,
                "updated": 0,
            }
        )

    print("building needs index…", flush=True)
    needs = _build_needs()
    if not needs:
        print("nothing to enrich", flush=True)
        return 0

    phases = ["works", "editions"] if args.phase == "both" else [args.phase]
    for phase in phases:
        start = int(prog.get(f"{phase}_line") or 0)
        _run_phase(
            phase=phase,
            needs=needs,
            prog=prog,
            max_lines=args.max_lines,
            start_line=start,
        )
    print("ALL_DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
