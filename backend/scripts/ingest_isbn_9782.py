"""Ingère les livres dont l'ISBN commence par 9782 (groupe francophone).

Sources : BnF SRU (préfixe ISBN) + Open Library (langue fre, filtre ISBN).
Dédup SQLite (qid / name_norm / isbn). Progression par shards 97820–97829…

  python scripts/ingest_isbn_9782.py --batch 80 --loop
  python scripts/ingest_isbn_9782.py --shard 978207 --batch 100
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROGRESS = ROOT / "data" / "_isbn_9782_progress.json"
UA = {
    "User-Agent": "BooktimeIsbn9782/1.0 (catalog ingest; FR ISBN group 978-2)",
    "Accept": "application/json",
}
BNF_SRU = "https://catalogue.bnf.fr/api/SRU"
_DC = "{http://purl.org/dc/elements/1.1/}"

# Shards initiaux : 97820–97829 puis raffinés au fil des offsets
DEFAULT_SHARDS = tuple(f"9782{d}" for d in "0123456789")


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
    return {"shards": {}, "added": 0, "skipped": 0, "failed": 0, "rounds": 0}


def _save_prog(p: dict[str, Any]) -> None:
    p["updated_at"] = _utcnow()
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def _bnf_text(el: Any) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip() if hasattr(el, "itertext") else str(el.text or "").strip()


def _norm_isbn(raw: str) -> str:
    return re.sub(r"[^0-9Xx]", "", raw or "")


def _is_9782(isbn: str) -> bool:
    d = _norm_isbn(isbn)
    return d.startswith("9782") and len(d) in (10, 13)


def _bnf_isbn_query_term(prefix: str) -> str:
    """978207 → 978-2-07 ; 97820 → 978-2-0 (forme BnF productive)."""
    p = _norm_isbn(prefix)
    if p.startswith("9782") and len(p) >= 5:
        return f"978-2-{p[4:]}"
    if p.startswith("9782"):
        return "978-2"
    return prefix


def fetch_bnf_prefix(prefix: str, *, start: int, page_size: int = 50) -> tuple[list[dict[str, Any]], int]:
    """BnF : bib.isbn all \"978-2-07\" etc. + filtre client 9782*."""
    from app.catalog.daily_ingest import is_human_label
    from app.catalog.isbn_resolve import prefer_isbn

    term = _bnf_isbn_query_term(prefix)
    query = f'bib.isbn all "{term}" and bib.doctype any "a"'
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
        print(f"  bnf_fail {prefix}@{start}: {exc}", flush=True)
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
        isbn = prefer_isbn(idents) or ""
        if isbn and not _is_9782(isbn):
            # garder si un ident commence par le préfixe même sans checksum OK
            raw9782 = next(
                (x for x in idents if _norm_isbn(x).startswith("9782")),
                "",
            )
            isbn = prefer_isbn([raw9782]) if raw9782 else isbn
        if isbn and not _norm_isbn(isbn).startswith(prefix[: min(5, len(prefix))]):
            # assouplir : au moins 9782
            if not _is_9782(isbn):
                continue
        ark = next((x for x in idents if "ark:" in x or x.startswith("http")), "")
        year = None
        for d in dc.findall(f"{_DC}date"):
            m = re.search(r"(1[5-9]\d{2}|20[0-3]\d)", _bnf_text(d))
            if m:
                year = int(m.group(1))
                break
        qid = f"BNF-9782:{(_norm_isbn(isbn) or ark or title)[:90]}"
        out.append(
            {
                "qid": qid,
                "name": title,
                "name_en": title,
                "author": authors[0],
                "category": "roman",
                "genre": "Roman",
                "cover_url": f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg" if isbn else "",
                "isbn": isbn or "",
                "ol_key": "",
                "year": year,
                "publisher": "",
                "source": "bnf_isbn_9782",
                "language": "français",
            }
        )
    return out, start + page_size


def fetch_ol_fre(*, offset: int, page_size: int = 80, prefix: str = "9782") -> tuple[list[dict[str, Any]], int]:
    """OL langue fre — ne garde que les ISBN 9782*."""
    from app.catalog.daily_ingest import is_human_label
    from app.catalog.isbn_resolve import prefer_isbn

    try:
        # q=978-2 cible le groupe FR ; language=fre en plus
        r = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "q": "978-2",
                "language": "fre",
                "limit": page_size,
                "offset": max(0, offset),
                "fields": "key,title,author_name,isbn,first_publish_year,cover_i,publisher",
            },
            timeout=25,
            headers=UA,
        )
        if r.status_code != 200:
            return [], offset + page_size
        docs = (r.json() or {}).get("docs") or []
    except Exception as exc:
        print(f"  ol_fail @{offset}: {exc}", flush=True)
        return [], offset + page_size

    out: list[dict[str, Any]] = []
    for doc in docs:
        title = (doc.get("title") or "").strip()
        authors = [a for a in (doc.get("author_name") or []) if is_human_label(str(a))]
        if not title or not authors:
            continue
        raw_isbns = [str(x) for x in (doc.get("isbn") or [])]
        # préférer un ISBN 9782*
        fr = [x for x in raw_isbns if _norm_isbn(x).startswith(prefix)]
        if not fr:
            continue
        isbn = prefer_isbn(fr) or prefer_isbn(raw_isbns) or ""
        if not _is_9782(isbn) and not any(_norm_isbn(x).startswith("9782") for x in fr):
            continue
        key = (doc.get("key") or "").strip()
        olid = key.rsplit("/", 1)[-1] if key else ""
        qid = olid if olid.endswith("W") else f"OL-9782:{(_norm_isbn(isbn) or title)[:90]}"
        cover = ""
        if doc.get("cover_i"):
            cover = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
        elif isbn:
            cover = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
        pubs = doc.get("publisher") or []
        publisher = str(pubs[0]) if pubs else ""
        out.append(
            {
                "qid": qid if str(qid).startswith("OL") else f"OL-9782:{qid}",
                "name": title,
                "name_en": title,
                "author": authors[0],
                "category": "roman",
                "genre": "Roman",
                "cover_url": cover,
                "isbn": isbn or _norm_isbn(fr[0]),
                "ol_key": key if key.startswith("/works/") else (f"/works/{olid}" if olid.endswith("W") else ""),
                "year": doc.get("first_publish_year"),
                "publisher": publisher,
                "source": "ol_isbn_9782",
                "language": "français",
            }
        )
    return out, offset + page_size


def main() -> int:
    # Réutilise le pipeline d'upsert des maisons FR (script voisin)
    sys.path.insert(0, str(ROOT / "scripts"))
    from ingest_fr_publishers import ingest_candidates, load_known_from_sqlite  # type: ignore

    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, default=80, help="fiches visées par shard / tour")
    p.add_argument("--loop", action="store_true")
    p.add_argument("--rounds", type=int, default=1)
    p.add_argument("--shard", type=str, default="", help="ex. 978207 (sinon 97820–97829)")
    p.add_argument("--ol-only", action="store_true")
    p.add_argument("--bnf-only", action="store_true")
    args = p.parse_args()
    _load_env()
    os.environ.setdefault("CATALOG_DUMP_LOCAL", "1")
    os.environ.setdefault("CATALOG_LOCAL_SQLITE", str(_db()))
    os.environ.setdefault("CATALOG_DUMP_LOCAL_ONLY", "1")
    os.environ["CATALOG_SYNOPSIS_LOOKUPS"] = "0"
    os.environ["CATALOG_COVER_LOOKUPS"] = "0"
    os.environ["CATALOG_ISBN_LOOKUPS"] = "0"

    shards = [args.shard.strip()] if args.shard.strip() else list(DEFAULT_SHARDS)
    print(f"db={_db()} shards={shards}", flush=True)
    print("loading known…", flush=True)
    known_qids, known_names, known_isbns = load_known_from_sqlite()
    print(
        f"known qids={len(known_qids)} names={len(known_names)} isbns={len(known_isbns)}",
        flush=True,
    )

    rounds = 0
    while True:
        rounds += 1
        prog = _load_prog()
        shard_state: dict[str, Any] = (
            prog.get("shards") if isinstance(prog.get("shards"), dict) else {}
        )
        round_added = 0

        for shard in shards:
            st = shard_state.get(shard) or {"bnf": 1, "ol": 0}
            bnf_pos = int(st.get("bnf") or 1)
            ol_pos = int(st.get("ol") or 0)
            target = max(20, args.batch)
            added = skipped = failed = fetched = 0
            print(f"\n=== shard {shard} bnf@{bnf_pos} ol@{ol_pos} ===", flush=True)

            while fetched < target:
                need = min(50, target - fetched)
                batch: list[dict[str, Any]] = []
                if not args.ol_only:
                    bnf_batch, bnf_pos = fetch_bnf_prefix(shard, start=bnf_pos, page_size=need)
                    batch.extend(bnf_batch)
                if not args.bnf_only and len(batch) < need:
                    ol_batch, ol_pos = fetch_ol_fre(
                        offset=ol_pos, page_size=need + 20, prefix="9782"
                    )
                    batch.extend(ol_batch)
                if not batch:
                    print("  empty — next shard", flush=True)
                    break
                seen: set[str] = set()
                uniq: list[dict[str, Any]] = []
                for c in batch:
                    k = str(c.get("qid") or c.get("isbn") or c.get("name"))
                    if k in seen:
                        continue
                    seen.add(k)
                    uniq.append(c)
                res = ingest_candidates(
                    uniq[:need],
                    known_qids=known_qids,
                    known_names=known_names,
                    known_isbns=known_isbns,
                    resolve_isbn=False,
                )
                added += res["added"]
                skipped += res["skipped"]
                failed += res["failed"]
                fetched += len(uniq[:need])
                print(
                    f"  +{res['added']} skip={res['skipped']} fail={res['failed']} "
                    f"tot={added}/{target}",
                    flush=True,
                )
                if res["added"] == 0 and res["skipped"] >= max(1, len(uniq[:need]) * 0.85):
                    bnf_pos += 150
                    ol_pos += 80
                time.sleep(0.25)
                if bnf_pos > 12000 and ol_pos > 20000:
                    break

            shard_state[shard] = {"bnf": bnf_pos, "ol": ol_pos}
            prog["added"] = int(prog.get("added") or 0) + added
            prog["skipped"] = int(prog.get("skipped") or 0) + skipped
            prog["failed"] = int(prog.get("failed") or 0) + failed
            round_added += added
            prog["shards"] = shard_state
            prog["rounds"] = int(prog.get("rounds") or 0) + 1
            _save_prog(prog)

        print(f"\nROUND {rounds} added={round_added} cum={prog.get('added')}", flush=True)
        if not args.loop:
            break
        if args.rounds and rounds >= args.rounds:
            break
        time.sleep(2)

    print("DONE", json.dumps(prog, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
