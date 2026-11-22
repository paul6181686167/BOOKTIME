"""Ingère les livres des 20 plus grandes maisons d'édition françaises.

Sources : BnF SRU (publisher) + Open Library search (publisher, langue fre).
Dédup : qid / name_norm / ISBN déjà présents dans local_catalog.sqlite.

  python scripts/ingest_fr_publishers.py --per-publisher 200 --loop
  python scripts/ingest_fr_publishers.py --publisher Gallimard --per-publisher 500
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROGRESS = ROOT / "data" / "_fr_publishers_progress.json"
UA = {
    "User-Agent": "BooktimeFrPublishers/1.0 (catalog ingest; French trade publishers)",
    "Accept": "application/json",
}

# 20 plus grandes maisons / imprints FR (marché trade + grands poches / BD)
TOP_FR_PUBLISHERS: tuple[str, ...] = (
    "Gallimard",
    "Flammarion",
    "Albin Michel",
    "Grasset",
    "Fayard",
    "Seuil",
    "Actes Sud",
    "Robert Laffont",
    "Stock",
    "Plon",
    "Calmann-Lévy",
    "JC Lattès",
    "Pocket",
    "Le Livre de Poche",
    "J'ai lu",
    "10/18",
    "Glénat",
    "Delcourt",
    "Michel Lafon",
    "Denoël",
)

BNF_SRU = "https://catalogue.bnf.fr/api/SRU"
_DC = "{http://purl.org/dc/elements/1.1/}"


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
        "publisher_idx": 0,
        "offsets": {},
        "added": 0,
        "skipped": 0,
        "failed": 0,
        "rounds": 0,
    }


def _save_prog(p: dict[str, Any]) -> None:
    p["updated_at"] = _utcnow()
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def _bnf_text(el: Any) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip() if hasattr(el, "itertext") else str(el.text or "").strip()


def _pick_isbn(idents: list[str]) -> str:
    from app.catalog.isbn_resolve import prefer_isbn

    return prefer_isbn(idents) or ""


def load_known_from_sqlite() -> tuple[set[str], set[str], set[str]]:
    """qid, name_norm, isbn déjà en base."""
    from app.static_wikidata.service import norm_title

    qids: set[str] = set()
    names: set[str] = set()
    isbns: set[str] = set()
    path = _db()
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=60)
    try:
        for qid, nn, raw in con.execute(
            "SELECT qid, name_norm, doc_json FROM catalog_daily_series"
        ):
            if qid:
                qids.add(str(qid))
            if nn:
                names.add(str(nn))
            try:
                d = json.loads(raw or "{}")
            except Exception:
                continue
            isbn = (d.get("isbn") or "").strip()
            if isbn:
                isbns.add(re.sub(r"[^0-9Xx]", "", isbn))
            details = d.get("volume_details")
            if isinstance(details, dict):
                for b in details.values():
                    if isinstance(b, dict) and b.get("isbn"):
                        isbns.add(re.sub(r"[^0-9Xx]", "", str(b["isbn"])))
            n2 = norm_title(str(d.get("name") or ""))
            if n2:
                names.add(n2)
    finally:
        con.close()
    return qids, names, isbns


def fetch_bnf_publisher(
    publisher: str, *, start: int, page_size: int = 50
) -> tuple[list[dict[str, Any]], int]:
    """Retourne (candidates, next_start)."""
    from app.catalog.daily_ingest import is_human_label

    safe = publisher.replace('"', " ")
    query = f'bib.publisher all "{safe}" and bib.doctype any "a"'
    try:
        r = requests.get(
            BNF_SRU,
            params={
                "version": "1.2",
                "operation": "searchRetrieve",
                "query": query,
                "recordSchema": "dublincore",
                "maximumRecords": str(page_size),
                "startRecord": str(max(1, start)),
            },
            timeout=20,
            headers={**UA, "Accept": "application/xml"},
        )
        if r.status_code != 200:
            return [], start + page_size
        root = ET.fromstring(r.content)
    except Exception as exc:
        print(f"  bnf_fail {publisher}: {exc}", flush=True)
        return [], start + page_size

    out: list[dict[str, Any]] = []
    for dc in root.findall(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc"):
        title = _bnf_text(dc.find(f"{_DC}title")).split(" / ")[0].strip()
        creators = [
            _bnf_text(c).split("(")[0].strip() for c in dc.findall(f"{_DC}creator")
        ]
        authors = [a for a in creators if is_human_label(a)]
        if not title or not authors:
            continue
        idents = [_bnf_text(i) for i in dc.findall(f"{_DC}identifier")]
        isbn = _pick_isbn(idents)
        ark = next((x for x in idents if "ark:" in x or x.startswith("http")), "")
        year = None
        for d in dc.findall(f"{_DC}date"):
            m = re.search(r"(1[5-9]\d{2}|20[0-3]\d)", _bnf_text(d))
            if m:
                year = int(m.group(1))
                break
        qid = f"BNF-PUB:{(isbn or ark or title)[:90]}"
        out.append(
            {
                "qid": qid,
                "name": title,
                "name_en": title,
                "author": authors[0],
                "author_qid": "",
                "category": "roman",
                "genre": "Roman",
                "cover_url": f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
                if isbn
                else "",
                "isbn": isbn or "",
                "ol_key": "",
                "year": year,
                "publisher": publisher,
                "source": "bnf_publisher",
                "language": "français",
            }
        )
    return out, start + page_size


def fetch_ol_publisher(
    publisher: str, *, offset: int, page_size: int = 50
) -> tuple[list[dict[str, Any]], int]:
    from app.catalog.daily_ingest import is_human_label

    try:
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "publisher": publisher,
                "language": "fre",
                "limit": page_size,
                "offset": max(0, offset),
                "fields": "key,title,author_name,isbn,first_publish_year,publisher,language,cover_i",
            },
            timeout=20,
            headers=UA,
        )
        if r.status_code != 200:
            return [], offset + page_size
        docs = (r.json() or {}).get("docs") or []
    except Exception as exc:
        print(f"  ol_fail {publisher}: {exc}", flush=True)
        return [], offset + page_size

    out: list[dict[str, Any]] = []
    for doc in docs:
        title = (doc.get("title") or "").strip()
        authors = [a for a in (doc.get("author_name") or []) if is_human_label(str(a))]
        if not title or not authors:
            continue
        isbns = doc.get("isbn") or []
        isbn = _pick_isbn([str(x) for x in isbns]) if isbns else ""
        key = (doc.get("key") or "").strip()
        olid = key.rsplit("/", 1)[-1] if key else ""
        qid = olid if olid.endswith("W") else f"OL-PUB:{(isbn or title)[:90]}"
        cover = ""
        if doc.get("cover_i"):
            cover = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
        elif isbn:
            cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        out.append(
            {
                "qid": qid if qid.startswith("OL") else f"OL-PUB:{qid}",
                "name": title,
                "name_en": title,
                "author": authors[0],
                "author_qid": "",
                "category": "roman",
                "genre": "Roman",
                "cover_url": cover,
                "isbn": isbn or "",
                "ol_key": key if key.startswith("/works/") else (f"/works/{olid}" if olid.endswith("W") else ""),
                "year": doc.get("first_publish_year"),
                "publisher": publisher,
                "source": "ol_publisher",
                "language": "français",
            }
        )
    return out, offset + page_size


def _already(
    cand: dict[str, Any],
    known_qids: set[str],
    known_names: set[str],
    known_isbns: set[str],
) -> bool:
    from app.static_wikidata.service import norm_title

    qid = (cand.get("qid") or "").strip()
    if qid and qid in known_qids:
        return True
    nn = norm_title(str(cand.get("name") or ""))
    if nn and nn in known_names:
        return True
    isbn = re.sub(r"[^0-9Xx]", "", str(cand.get("isbn") or ""))
    if isbn and isbn in known_isbns:
        return True
    return False


def ingest_candidates(
    cands: list[dict[str, Any]],
    *,
    known_qids: set[str],
    known_names: set[str],
    known_isbns: set[str],
    resolve_isbn: bool,
) -> dict[str, int]:
    from app.catalog.daily_ingest import (
        _already_catalogued,
        _persist,
        build_complete_entry,
        is_human_label,
    )
    from app.static_wikidata.service import norm_title

    added = skipped = failed = 0
    for cand in cands:
        if _already(cand, known_qids, known_names, known_isbns):
            skipped += 1
            continue
        if _already_catalogued(cand, known_qids, known_names):
            skipped += 1
            continue
        author = (cand.get("author") or "").strip()
        title = (cand.get("name") or "").strip()
        if not is_human_label(author) or not is_human_label(title):
            skipped += 1
            continue
        work = {
            "title": title,
            "title_en": cand.get("name_en") or title,
            "author": author,
            "published_year": cand.get("year"),
            "isbn": cand.get("isbn") or "",
            "ol_key": cand.get("ol_key") or "",
            "work_qid": cand.get("qid") or "",
            "author_qid": "",
        }
        # Éviter resolve_isbn massif (lent) sauf demandé
        if not resolve_isbn:
            os.environ["CATALOG_ISBN_LOOKUPS"] = "0"
        try:
            # Forcer budget ISBN à 0 via env pendant build si --no-isbn
            if not resolve_isbn:
                from app.catalog import isbn_resolve

                isbn_resolve.reset_budget(0)
            entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        except Exception as exc:
            print(f"  build_fail {title[:60]}: {exc}", flush=True)
            failed += 1
            continue
        if not entry:
            failed += 1
            continue
        # Enrichir métadonnées éditeur
        entry["publisher"] = cand.get("publisher") or entry.get("publisher")
        entry["language"] = "français"
        entry["sources"] = {
            **(entry.get("sources") if isinstance(entry.get("sources"), dict) else {}),
            "fr_publisher_ingest": True,
            "publisher": cand.get("publisher"),
        }
        try:
            n = _persist(entry, known_qids, [], None, known_names)
        except Exception as exc:
            print(f"  persist_fail {title[:60]}: {exc}", flush=True)
            failed += 1
            continue
        if n:
            added += 1
            isbn = re.sub(r"[^0-9Xx]", "", str(entry.get("isbn") or work.get("isbn") or ""))
            if isbn:
                known_isbns.add(isbn)
            nn = norm_title(str(entry.get("name") or ""))
            if nn:
                known_names.add(nn)
            if entry.get("qid"):
                known_qids.add(str(entry["qid"]))
        else:
            skipped += 1
    return {"added": added, "skipped": skipped, "failed": failed}


def run_publisher(
    publisher: str,
    *,
    per_publisher: int,
    bnf_start: int,
    ol_offset: int,
    known_qids: set[str],
    known_names: set[str],
    known_isbns: set[str],
    resolve_isbn: bool,
) -> dict[str, Any]:
    target = max(10, per_publisher)
    added = skipped = failed = 0
    bnf_pos, ol_pos = bnf_start, ol_offset
    fetched = 0
    print(f"\n=== {publisher} (bnf@{bnf_pos} ol@{ol_pos}) ===", flush=True)

    while fetched < target:
        need = min(50, target - fetched)
        batch: list[dict[str, Any]] = []
        # Alterner BnF / OL
        bnf_batch, bnf_pos = fetch_bnf_publisher(publisher, start=bnf_pos, page_size=need)
        batch.extend(bnf_batch)
        if len(batch) < need:
            ol_batch, ol_pos = fetch_ol_publisher(
                publisher, offset=ol_pos, page_size=need - len(batch) + 10
            )
            batch.extend(ol_batch)
        if not batch:
            print(f"  empty page — stop {publisher}", flush=True)
            break
        # dédup interne lot
        seen: set[str] = set()
        uniq: list[dict[str, Any]] = []
        for c in batch:
            k = c.get("qid") or c.get("name")
            if k in seen:
                continue
            seen.add(str(k))
            uniq.append(c)
        res = ingest_candidates(
            uniq[:need],
            known_qids=known_qids,
            known_names=known_names,
            known_isbns=known_isbns,
            resolve_isbn=resolve_isbn,
        )
        added += res["added"]
        skipped += res["skipped"]
        failed += res["failed"]
        fetched += len(uniq[:need])
        print(
            f"  +{res['added']} skip={res['skipped']} fail={res['failed']} "
            f"tot_added={added}/{target}",
            flush=True,
        )
        if res["added"] == 0 and res["skipped"] >= len(uniq[:need]) * 0.9:
            # Zone saturée : avancer plus vite
            bnf_pos += 200
            ol_pos += 100
        time.sleep(0.3)
        if bnf_pos > 9000 and ol_pos > 5000:
            break

    return {
        "publisher": publisher,
        "added": added,
        "skipped": skipped,
        "failed": failed,
        "bnf_start": bnf_pos,
        "ol_offset": ol_pos,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--per-publisher", type=int, default=150)
    p.add_argument("--loop", action="store_true")
    p.add_argument("--rounds", type=int, default=1)
    p.add_argument("--publisher", type=str, default="", help="Une maison seule")
    p.add_argument("--resolve-isbn", action="store_true", help="Résoudre ISBN manquants (lent)")
    p.add_argument("--list", action="store_true", help="Afficher les 20 maisons")
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    os.environ.setdefault("CATALOG_LOCAL_SQLITE", str(_db()))
    os.environ.setdefault("CATALOG_DUMP_LOCAL_ONLY", "1")
    # Couper synopsis live pendant ingest massif (trop lent)
    os.environ["CATALOG_SYNOPSIS_LOOKUPS"] = "0"
    os.environ["CATALOG_COVER_LOOKUPS"] = "0"
    if not args.resolve_isbn:
        os.environ["CATALOG_ISBN_LOOKUPS"] = "0"

    if args.list:
        for i, name in enumerate(TOP_FR_PUBLISHERS, 1):
            print(f"{i:2d}. {name}")
        return 0

    pubs = (
        [args.publisher.strip()]
        if args.publisher.strip()
        else list(TOP_FR_PUBLISHERS)
    )
    print(f"db={_db()}", flush=True)
    print(f"publishers={len(pubs)} per={args.per_publisher}", flush=True)
    print("loading known keys…", flush=True)
    known_qids, known_names, known_isbns = load_known_from_sqlite()
    print(
        f"known qids={len(known_qids)} names={len(known_names)} isbns={len(known_isbns)}",
        flush=True,
    )

    rounds = 0
    while True:
        rounds += 1
        prog = _load_prog()
        offsets: dict[str, Any] = prog.get("offsets") if isinstance(prog.get("offsets"), dict) else {}
        round_added = 0
        for pub in pubs:
            off = offsets.get(pub) or {"bnf": 1, "ol": 0}
            res = run_publisher(
                pub,
                per_publisher=args.per_publisher,
                bnf_start=int(off.get("bnf") or 1),
                ol_offset=int(off.get("ol") or 0),
                known_qids=known_qids,
                known_names=known_names,
                known_isbns=known_isbns,
                resolve_isbn=bool(args.resolve_isbn),
            )
            offsets[pub] = {"bnf": res["bnf_start"], "ol": res["ol_offset"]}
            prog["added"] = int(prog.get("added") or 0) + int(res["added"])
            prog["skipped"] = int(prog.get("skipped") or 0) + int(res["skipped"])
            prog["failed"] = int(prog.get("failed") or 0) + int(res["failed"])
            round_added += int(res["added"])
            prog["offsets"] = offsets
            prog["rounds"] = int(prog.get("rounds") or 0) + 1
            _save_prog(prog)
        print(
            f"\nROUND {rounds} added={round_added} cum={prog.get('added')}",
            flush=True,
        )
        if not args.loop:
            break
        if args.rounds and rounds >= args.rounds:
            break
        time.sleep(2)
    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
