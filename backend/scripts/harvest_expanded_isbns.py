#!/usr/bin/env python3
"""Récolte d'ISBN réels pour le noyau 50 000 (Wikidata, Open Library, Google Books).

N'invente aucun ISBN. Reprend là où il s'est arrêté (--resume).

Usage (depuis BOOKTIME-main) :
  python -u backend/scripts/harvest_expanded_isbns.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
load_dotenv(BACKEND / ".env")

from app.openlibrary.isbn_lookup import clean_isbn, is_valid_isbn, isbn10_to_13  # noqa: E402
from app.static_wikidata.service import norm_title  # noqa: E402

CATALOG = BACKEND / "data" / "expanded_fiches_catalog.json"
PROGRESS = BACKEND / "data" / "_isbn_harvest_progress.json"
FALLBACK_COVER = "https://commons.wikimedia.org/wiki/Special:FilePath/Open_book_nae_02.svg"

UA = {
    "User-Agent": (
        "BooktimeCatalog/1.0 (https://github.com/paul6181686167/BOOKTIME; "
        "ISBN harvest for curated catalog)"
    ),
    "Accept": "application/json",
}
SPARQL_UA = {**UA, "Accept": "application/sparql-results+json"}
WD_SPARQL = "https://query.wikidata.org/sparql"
OL_SEARCH = "https://openlibrary.org/search.json"
GB_URL = "https://www.googleapis.com/books/v1/volumes"
GB_CAP = 8000
WD_BATCH = 40

session = requests.Session()
session.headers.update(UA)


def log(msg: str) -> None:
    print(msg, flush=True)


def prefer_isbn(candidates: list[Any]) -> str:
    cleaned: list[str] = []
    for raw in candidates:
        if not raw:
            continue
        if isinstance(raw, (list, tuple)):
            got = prefer_isbn(list(raw))
            if got:
                cleaned.append(got)
            continue
        d = clean_isbn(str(raw))
        if len(d) == 10 and d[:9].isdigit():
            d = isbn10_to_13(d)
        if len(d) == 13 and d.isdigit() and is_valid_isbn(d):
            cleaned.append(d)
    if not cleaned:
        return ""
    for prefix in ("9782", "978", "979"):
        for isbn in cleaned:
            if isbn.startswith(prefix):
                return isbn
    return cleaned[0]


def load_progress() -> dict[str, dict[str, str]]:
    if PROGRESS.is_file():
        try:
            data = json.loads(PROGRESS.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {
                    "by_qid": dict(data.get("by_qid") or {}),
                    "by_ol": dict(data.get("by_ol") or {}),
                    "by_title": dict(data.get("by_title") or {}),
                }
        except Exception:
            pass
    return {"by_qid": {}, "by_ol": {}, "by_title": {}}


def save_progress(prog: dict) -> None:
    PROGRESS.write_text(json.dumps(prog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def chunks(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def missing_volumes(catalog: dict) -> list[dict]:
    out = []
    for si, s in enumerate(catalog.get("series") or []):
        details = s.get("volume_details") or {}
        author = ""
        if isinstance(s.get("authors"), list) and s["authors"]:
            author = str(s["authors"][0] or "")
        titles_en = s.get("volume_titles_en") or {}
        for vn, title in (s.get("volume_titles") or {}).items():
            d = details.get(str(vn)) or {}
            if prefer_isbn([d.get("isbn")]):
                continue
            out.append(
                {
                    "si": si,
                    "vn": str(vn),
                    "title": title or "",
                    "title_en": titles_en.get(str(vn)) or "",
                    "author": (d.get("author") or author or "").strip(),
                    "work_qid": d.get("work_qid") or "",
                    "ol_key": (d.get("ol_key") or "").strip(),
                }
            )
    return out


def isbn_from_progress(row: dict, prog: dict) -> str:
    qid = row.get("work_qid") or ""
    if qid and prog["by_qid"].get(qid):
        return prog["by_qid"][qid]
    ol = row.get("ol_key") or ""
    if ol and prog["by_ol"].get(ol):
        return prog["by_ol"][ol]
    for title in (row.get("title"), row.get("title_en")):
        key = norm_title(title or "")
        if key and prog["by_title"].get(key):
            return prog["by_title"][key]
    return ""


def harvest_wikidata(qids: list[str], prog: dict) -> None:
    todo = [q for q in qids if q and q not in prog["by_qid"]]
    log(f"Wikidata SPARQL : {len(todo)} QID…")
    found0 = len(prog["by_qid"])
    for n, batch in enumerate(chunks(todo, WD_BATCH), start=1):
        values = " ".join(f"wd:{q}" for q in batch)
        query = f"""
SELECT ?work ?isbn WHERE {{
  VALUES ?work {{ {values} }}
  {{ ?work wdt:P212 ?isbn. }}
  UNION {{ ?work wdt:P957 ?isbn. }}
  UNION {{ ?ed wdt:P629 ?work ; wdt:P212 ?isbn. }}
  UNION {{ ?ed wdt:P629 ?work ; wdt:P957 ?isbn. }}
}}
"""
        grouped: dict[str, list[str]] = {q: [] for q in batch}
        try:
            r = session.get(
                WD_SPARQL,
                params={"query": query, "format": "json"},
                headers=SPARQL_UA,
                timeout=70,
            )
            if r.status_code == 429:
                log("  Wikidata 429 — pause 20 s")
                time.sleep(20)
                r = session.get(
                    WD_SPARQL,
                    params={"query": query, "format": "json"},
                    headers=SPARQL_UA,
                    timeout=70,
                )
            r.raise_for_status()
            for row in (r.json().get("results") or {}).get("bindings") or []:
                uri = (row.get("work") or {}).get("value") or ""
                qid = uri.rsplit("/", 1)[-1]
                isbn = (row.get("isbn") or {}).get("value") or ""
                if qid in grouped and isbn:
                    grouped[qid].append(isbn)
        except Exception as exc:
            log(f"  lot {n} échoué : {exc}")
            time.sleep(2)
            continue
        for qid, cands in grouped.items():
            isbn = prefer_isbn(cands)
            if isbn:
                prog["by_qid"][qid] = isbn
        if n % 15 == 0 or n == (len(todo) + WD_BATCH - 1) // WD_BATCH:
            save_progress(prog)
            log(f"  … {n} lots, ISBN Wikidata +{len(prog['by_qid']) - found0} (stock {len(prog['by_qid'])})")
        time.sleep(0.12)
    save_progress(prog)
    log(f"  Wikidata total mappés : {len(prog['by_qid'])}")


def ol_key_id(ol: str) -> str:
    raw = (ol or "").strip().replace("https://openlibrary.org", "")
    return raw.rstrip("/").rsplit("/", 1)[-1]


def fetch_ol_editions(ol_key: str) -> str:
    kid = ol_key_id(ol_key)
    if not kid:
        return ""
    if kid.endswith("M"):
        path = f"/books/{kid}.json"
        try:
            r = requests.get(f"https://openlibrary.org{path}", timeout=12, headers=UA)
            if r.status_code != 200:
                return ""
            data = r.json() or {}
            return prefer_isbn(data.get("isbn_13") or data.get("isbn_10") or [])
        except Exception:
            return ""
    path = f"/works/{kid}/editions.json" if kid.endswith("W") else f"{ol_key}/editions.json"
    if not path.startswith("/"):
        path = "/" + path.lstrip("/")
    try:
        r = requests.get(f"https://openlibrary.org{path}", params={"limit": 8}, timeout=15, headers=UA)
        if r.status_code != 200:
            return ""
        entries = (r.json() or {}).get("entries") or []
        cands = []
        for ed in entries:
            cands.extend(ed.get("isbn_13") or [])
            cands.extend(ed.get("isbn_10") or [])
        return prefer_isbn(cands)
    except Exception:
        return ""


def harvest_ol_editions(keys: list[str], prog: dict) -> None:
    todo = [k for k in keys if k and k not in prog["by_ol"]]
    log(f"Open Library éditions : {len(todo)} clés…")
    found0 = len(prog["by_ol"])

    def one(ol: str) -> tuple[str, str]:
        return ol, fetch_ol_editions(ol)

    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(one, k) for k in todo]
        for fut in as_completed(futs):
            ol, isbn = fut.result()
            if isbn:
                prog["by_ol"][ol] = isbn
            done += 1
            if done % 200 == 0:
                save_progress(prog)
                log(f"  … {done}/{len(todo)} (+{len(prog['by_ol']) - found0})")
    save_progress(prog)
    log(f"  Open Library éditions mappées : {len(prog['by_ol'])}")


def title_close(a: str, b: str) -> bool:
    na, nb = norm_title(a), norm_title(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if len(na) >= 8 and (na in nb or nb in na):
        return True
    return False


def fetch_ol_search(title: str, author: str) -> str:
    title = (title or "").strip()
    if len(title) < 3:
        return ""
    params = {"title": title, "limit": 5, "fields": "title,author_name,isbn,key"}
    if author:
        params["author"] = author
    try:
        r = requests.get(OL_SEARCH, params=params, timeout=6, headers=UA)
        if r.status_code == 429:
            time.sleep(4)
            r = requests.get(OL_SEARCH, params=params, timeout=6, headers=UA)
        if r.status_code != 200:
            return ""
        for doc in (r.json() or {}).get("docs") or []:
            if not title_close(title, doc.get("title") or ""):
                continue
            isbn = prefer_isbn(doc.get("isbn") or [])
            if isbn:
                return isbn
    except Exception:
        return ""
    return ""


def harvest_ol_search(rows: list[dict], prog: dict) -> None:
    seen: set[str] = set()
    todo: list[tuple[str, str, str]] = []
    for row in rows:
        if isbn_from_progress(row, prog):
            continue
        key = norm_title(row["title"] or row["title_en"] or "")
        if not key or key in seen or key in prog["by_title"]:
            continue
        seen.add(key)
        todo.append((key, row["title"] or row["title_en"], row["author"]))
    log(f"Open Library search : {len(todo)} titres…")
    found0 = len(prog["by_title"])

    def one(item: tuple[str, str, str]) -> tuple[str, str]:
        key, title, author = item
        return key, fetch_ol_search(title, author)

    done = 0
    for batch in chunks(todo, 40):
        with ThreadPoolExecutor(max_workers=8) as pool:
            futs = [pool.submit(one, t) for t in batch]
            for fut in as_completed(futs):
                key, isbn = fut.result()
                if isbn:
                    prog["by_title"][key] = isbn
                done += 1
        if done % 400 == 0:
            save_progress(prog)
            log(f"  … {done}/{len(todo)} (+{len(prog['by_title']) - found0})")
    save_progress(prog)
    log(f"  Open Library search mappés : {len(prog['by_title'])}")


def fetch_gb(title: str, author: str, api_key: str) -> str:
    title = (title or "").strip()
    if len(title) < 3:
        return ""
    q = f'intitle:"{title}"'
    if author:
        q += f' inauthor:"{author}"'
    try:
        r = requests.get(
            GB_URL,
            params={"q": q, "maxResults": 3, "printType": "books", "key": api_key},
            timeout=8,
            headers=UA,
        )
        if r.status_code in (403, 429):
            return "__QUOTA__"
        if r.status_code != 200:
            return ""
        for item in (r.json() or {}).get("items") or []:
            info = item.get("volumeInfo") or {}
            if not title_close(title, info.get("title") or ""):
                continue
            ids = info.get("industryIdentifiers") or []
            cands = [x.get("identifier") for x in ids if isinstance(x, dict)]
            isbn = prefer_isbn(cands)
            if isbn:
                return isbn
    except Exception:
        return ""
    return ""


def harvest_google(rows: list[dict], prog: dict) -> None:
    api_key = (os.environ.get("GOOGLE_BOOKS_API_KEY") or "").strip()
    if not api_key:
        log("Google Books : clé absente, étape ignorée")
        return
    seen: set[str] = set()
    todo: list[tuple[str, str, str]] = []
    for row in rows:
        if isbn_from_progress(row, prog):
            continue
        key = norm_title(row["title"] or row["title_en"] or "")
        if not key or key in seen or key in prog["by_title"]:
            continue
        seen.add(key)
        todo.append((key, row["title"] or row["title_en"], row["author"]))
        if len(todo) >= GB_CAP:
            break
    probe = fetch_gb("The Lord of the Rings", "Tolkien", api_key)
    if probe == "__QUOTA__":
        log("Google Books : quota du jour atteint, étape ignorée")
        return
    log(f"Google Books : {len(todo)} titres (plafond {GB_CAP})…")
    found0 = len(prog["by_title"])
    done = 0
    quota = False

    def one(item: tuple[str, str, str]) -> tuple[str, str]:
        key, title, author = item
        return key, fetch_gb(title, author, api_key)

    for batch in chunks(todo, 20):
        if quota:
            break
        with ThreadPoolExecutor(max_workers=4) as pool:
            futs = [pool.submit(one, t) for t in batch]
            for fut in as_completed(futs):
                key, isbn = fut.result()
                done += 1
                if isbn == "__QUOTA__":
                    quota = True
                elif isbn:
                    prog["by_title"][key] = isbn
        if done % 200 == 0 or quota:
            save_progress(prog)
            log(f"  … {done}/{len(todo)} (+{len(prog['by_title']) - found0})")
    save_progress(prog)
    if quota:
        log("  Google Books : quota atteint, on arrête cette source")
    log(f"  Google Books mappés titre : {len(prog['by_title'])}")


def apply_to_catalog(catalog: dict, prog: dict) -> int:
    added = 0
    for s in catalog.get("series") or []:
        details = s.get("volume_details") if isinstance(s.get("volume_details"), dict) else {}
        titles_en = s.get("volume_titles_en") or {}
        author = ""
        if isinstance(s.get("authors"), list) and s["authors"]:
            author = str(s["authors"][0] or "")
        for vn, title in (s.get("volume_titles") or {}).items():
            d = dict(details.get(str(vn)) or {})
            if prefer_isbn([d.get("isbn")]):
                details[str(vn)] = d
                continue
            row = {
                "title": title or "",
                "title_en": titles_en.get(str(vn)) or "",
                "author": (d.get("author") or author or "").strip(),
                "work_qid": d.get("work_qid") or "",
                "ol_key": (d.get("ol_key") or "").strip(),
            }
            isbn = isbn_from_progress(row, prog)
            if not isbn:
                continue
            d["isbn"] = isbn
            cover = (d.get("cover_url") or "")
            if FALLBACK_COVER in cover or not cover:
                d["cover_url"] = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            details[str(vn)] = d
            added += 1
        s["volume_details"] = details
        if FALLBACK_COVER in (s.get("cover_url") or ""):
            first = (details.get("1") or {}).get("cover_url")
            if first:
                s["cover_url"] = first
    return added


def count_isbn(catalog: dict) -> int:
    n = 0
    for s in catalog.get("series") or []:
        for d in (s.get("volume_details") or {}).values():
            if isinstance(d, dict) and prefer_isbn([d.get("isbn")]):
                n += 1
    return n


def main() -> None:
    log("Chargement catalogue…")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    prog = load_progress()
    rows = missing_volumes(catalog)
    log(f"  sans ISBN : {len(rows):,}")
    log(f"  déjà en cache récolte : qid={len(prog['by_qid'])} ol={len(prog['by_ol'])} titre={len(prog['by_title'])}")

    qids = []
    seen_q = set()
    ols = []
    seen_o = set()
    for row in rows:
        q = row["work_qid"]
        if q and q not in seen_q:
            seen_q.add(q)
            qids.append(q)
        ol = row["ol_key"]
        if ol and ol not in seen_o:
            seen_o.add(ol)
            ols.append(ol)

    if prog["by_qid"]:
        log("  Wikidata déjà en cache — étape sautée")
    else:
        harvest_wikidata(qids, prog)
    rows = [r for r in rows if not isbn_from_progress(r, prog)]
    log(f"  encore sans ISBN après Wikidata : {len(rows):,}")

    if prog["by_ol"]:
        log("  Open Library éditions déjà en cache — étape sautée")
    else:
        harvest_ol_editions(ols, prog)
    rows = [r for r in missing_volumes(catalog) if not isbn_from_progress(r, prog)]
    log(f"  encore sans ISBN après OL éditions : {len(rows):,}")

    harvest_google(rows, prog)
    added_mid = apply_to_catalog(catalog, prog)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    log(f"  sauvegarde intermédiaire : +{added_mid:,} → {count_isbn(catalog):,} ISBN")
    rows = [r for r in missing_volumes(catalog) if not isbn_from_progress(r, prog)]
    log(f"  encore sans ISBN après Google Books : {len(rows):,}")

    harvest_ol_search(rows, prog)
    rows = [r for r in missing_volumes(catalog) if not isbn_from_progress(r, prog)]
    log(f"  encore sans ISBN après OL search : {len(rows):,}")

    added = apply_to_catalog(catalog, prog)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    total = count_isbn(catalog)
    size_mb = CATALOG.stat().st_size / 1_048_576
    log(f"Écrit {CATALOG} ({size_mb:.1f} Mo)")
    log(f"  ISBN ajoutés ce passage : {added:,}")
    log(f"  ISBN totaux : {total:,} / 50 000")


if __name__ == "__main__":
    main()
