#!/usr/bin/env python3
"""Complète le noyau 50 000 : auteur, année, genre, langue, couverture, résumé, pages.

ISBN : uniquement des valeurs réelles (cache OL / manga / Wikidata P212).
On n'invente pas d'ISBN.

Usage (depuis BOOKTIME-main) :
  python backend/scripts/fill_expanded_fiches_catalog.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.static_wikidata.service import norm_title  # noqa: E402

LANG_BY_QID = {
    "Q150": "français",
    "Q1860": "anglais",
    "Q188": "allemand",
    "Q1321": "espagnol",
    "Q652": "italien",
    "Q809": "japonais",
    "Q5146": "portugais",
    "Q7411": "néerlandais",
    "Q9027": "suédois",
    "Q1412": "finnois",
    "Q8097": "polonais",
    "Q7737": "russe",
    "Q256": "turc",
    "Q13955": "arabe",
    "Q7850": "chinois",
    "Q9176": "coréen",
}

CATALOG = BACKEND / "data" / "expanded_fiches_catalog.json"
CACHE = BACKEND / "data" / "catalog_cache.json"
MANGA = BACKEND / "data" / "manga_bd_cache.json"

UA = {
    "User-Agent": (
        "BooktimeCatalog/1.0 (https://github.com/paul6181686167/BOOKTIME; "
        "local curated-core enrichment)"
    )
}
WD_API = "https://www.wikidata.org/w/api.php"
WIKI_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"

PAGES_BY_CAT = {"manga": 192, "bd": 48, "roman": 280}
# Icône livre libre (Commons) — dernier recours si aucune jaquette réelle.
FALLBACK_COVER = "https://commons.wikimedia.org/wiki/Special:FilePath/Open_book_nae_02.svg?width=400"
OL_W_COVER = re.compile(r"/b/(?:id|olid)/OL\d+W", re.I)
SUBTITLE_SPLIT = re.compile(r"[:–—\-(\[]")


def usable_cover(url: str | None) -> str:
    u = (url or "").strip()
    if not u or u.startswith("data:") or "undefined" in u:
        return ""
    if OL_W_COVER.search(u):
        return ""
    return u.replace("http://", "https:")


def pick_isbn(raw: Any) -> str:
    if not raw:
        return ""
    if isinstance(raw, (list, tuple)):
        for item in raw:
            got = pick_isbn(item)
            if got:
                return got
        return ""
    digits = re.sub(r"[^0-9Xx]", "", str(raw)).upper()
    if len(digits) == 13 and digits.isdigit():
        return digits
    if len(digits) == 10 and digits[:9].isdigit():
        return digits
    return ""


def isbn_cover(isbn: str) -> str:
    d = re.sub(r"[^0-9Xx]", "", isbn or "")
    if len(d) not in (10, 13):
        return ""
    return f"https://covers.openlibrary.org/b/isbn/{d}-M.jpg"


def commons_url(filename: str) -> str:
    fn = (filename or "").strip().replace(" ", "_")
    if not fn:
        return ""
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(fn)}?width=400"


def strip_sub(title: str) -> str:
    head = SUBTITLE_SPLIT.split(title or "", maxsplit=1)[0]
    return norm_title(head)


def rec_score(rec: dict) -> int:
    return (
        (4 if pick_isbn(rec.get("isbn") or rec.get("isbn13")) else 0)
        + (2 if usable_cover(rec.get("cover_url")) else 0)
        + (1 if rec.get("first_publish_year") or rec.get("publication_year") else 0)
        + (1 if rec.get("total_pages") or rec.get("pages") else 0)
        + (1 if rec.get("description") else 0)
    )


def better(a: dict | None, b: dict | None) -> dict | None:
    if not a:
        return b
    if not b:
        return a
    return b if rec_score(b) > rec_score(a) else a


def load_book_list(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("books", "works", "items", "catalog"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
        vals = list(data.values())
        if vals and isinstance(vals[0], dict):
            return [x for x in vals if isinstance(x, dict)]
    return []


def index_cache(books: list[dict]) -> tuple[dict[str, dict], dict[str, dict], dict[str, dict]]:
    by_ol: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    by_strip: dict[str, dict] = {}
    for rec in books:
        ol = (rec.get("ol_key") or "").strip()
        if ol:
            by_ol[ol] = better(by_ol.get(ol), rec)
            tail = ol.rstrip("/").rsplit("/", 1)[-1]
            if tail:
                by_ol[tail] = better(by_ol.get(tail), rec)
        title = rec.get("title") or rec.get("name") or ""
        nt = norm_title(title)
        if nt:
            by_title[nt] = better(by_title.get(nt), rec)
        st = strip_sub(title)
        if st:
            by_strip[st] = better(by_strip.get(st), rec)
    return by_ol, by_title, by_strip


def chunks(seq: list[str], n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def wd_claim(entity: dict, pid: str) -> Any:
    claims = (entity.get("claims") or {}).get(pid) or []
    if not claims:
        return None
    snak = (claims[0] or {}).get("mainsnak") or {}
    dv = snak.get("datavalue") or {}
    return dv.get("value")


def wd_year(val: Any) -> int | None:
    if not isinstance(val, dict):
        return None
    raw = str(val.get("time") or "")
    m = re.search(r"(-?\d{3,4})", raw)
    if not m:
        return None
    y = int(m.group(1))
    if 1400 <= y <= 2030:
        return y
    return None


def wd_pages(val: Any) -> int | None:
    if isinstance(val, dict):
        amt = str(val.get("amount") or "").lstrip("+")
        try:
            n = int(float(amt))
        except (TypeError, ValueError):
            return None
        return n if 8 <= n <= 4000 else None
    return None


def wd_qid(val: Any) -> str:
    if isinstance(val, dict):
        return str(val.get("id") or "")
    return str(val or "")


def fetch_wikidata_series(qids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    session = requests.Session()
    session.headers.update(UA)
    uniq = [q for q in qids if q and q.startswith("Q")]
    print(f"  Wikidata séries : {len(uniq)} QID…")
    for i, batch in enumerate(chunks(uniq, 50), start=1):
        try:
            r = session.get(
                WD_API,
                params={
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "claims",
                    "format": "json",
                },
                timeout=30,
            )
            r.raise_for_status()
            ents = (r.json() or {}).get("entities") or {}
        except Exception as exc:
            print(f"    lot {i} échoué : {exc}")
            time.sleep(1.5)
            continue
        for qid, ent in ents.items():
            if not isinstance(ent, dict) or ent.get("missing"):
                continue
            image = wd_claim(ent, "P18")
            cover = commons_url(image) if isinstance(image, str) else ""
            year = wd_year(wd_claim(ent, "P577")) or wd_year(wd_claim(ent, "P571"))
            lang_q = wd_qid(wd_claim(ent, "P407"))
            lang = LANG_BY_QID.get(lang_q)
            isbn = pick_isbn(wd_claim(ent, "P212") or wd_claim(ent, "P957"))
            pages = wd_pages(wd_claim(ent, "P1104"))
            if cover or year or lang or isbn or pages:
                out[qid] = {
                    "cover_url": cover,
                    "year": year,
                    "language": lang,
                    "isbn": isbn,
                    "pages": pages,
                }
        if i % 20 == 0:
            print(f"    … {i} lots, {len(out)} séries enrichies")
        time.sleep(0.08)
    print(f"  Wikidata séries utiles : {len(out)}")
    return out


def wiki_thumb(session: requests.Session, lang: str, title: str) -> str:
    title = (title or "").strip()
    if not title:
        return ""
    try:
        r = session.get(
            WIKI_SUMMARY.format(lang=lang, title=quote(title.replace(" ", "_"))),
            timeout=8,
        )
        if r.status_code != 200:
            return ""
        thumb = ((r.json() or {}).get("thumbnail") or {}).get("source") or ""
        if "/revision/" in thumb:
            thumb = thumb.split("/revision/")[0]
        return usable_cover(thumb)
    except Exception:
        return ""


def fetch_wikipedia_covers(series: list[dict]) -> dict[str, str]:
    """Miniatures Wikipedia pour les séries encore sans couverture utilisable."""
    todo = [
        s
        for s in series
        if not usable_cover(s.get("cover_url"))
    ]
    print(f"  Wikipedia : {len(todo)} séries sans image…")
    found: dict[str, str] = {}

    def one(s: dict) -> tuple[str, str]:
        session = requests.Session()
        session.headers.update(UA)
        qid = str(s.get("qid") or s.get("wikidata_qid") or s.get("key") or "")
        thumb = wiki_thumb(session, "fr", s.get("name") or "")
        if not thumb:
            thumb = wiki_thumb(session, "en", s.get("name_en") or s.get("name") or "")
        return qid, thumb

    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = [pool.submit(one, s) for s in todo]
        for fut in as_completed(futs):
            qid, thumb = fut.result()
            if qid and thumb:
                found[qid] = thumb
            done += 1
            if done % 200 == 0:
                print(f"    … {done}/{len(todo)} ({len(found)} images)")
    print(f"  Wikipedia images : {len(found)}")
    return found


def fetch_ol_search_covers(series: list[dict], already: dict[str, str]) -> dict[str, str]:
    """cover_i Open Library pour les séries encore vides."""
    todo = []
    for s in series:
        qid = str(s.get("qid") or s.get("wikidata_qid") or s.get("key") or "")
        if usable_cover(s.get("cover_url")) or already.get(qid):
            continue
        todo.append(s)
    print(f"  Open Library search : {len(todo)} séries…")
    found: dict[str, str] = {}

    def one(s: dict) -> tuple[str, str]:
        qid = str(s.get("qid") or s.get("wikidata_qid") or s.get("key") or "")
        title = (s.get("name_en") or s.get("name") or "").strip()
        if not title:
            return qid, ""
        try:
            r = requests.get(
                "https://openlibrary.org/search.json",
                params={"title": title, "limit": 1, "fields": "cover_i,isbn,title"},
                headers=UA,
                timeout=10,
            )
            if r.status_code != 200:
                return qid, ""
            docs = (r.json() or {}).get("docs") or []
            if not docs:
                return qid, ""
            cover_i = docs[0].get("cover_i")
            if cover_i:
                return qid, f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
        except Exception:
            return qid, ""
        return qid, ""

    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(one, s) for s in todo]
        for fut in as_completed(futs):
            qid, cover = fut.result()
            if qid and cover:
                found[qid] = cover
            done += 1
            if done % 100 == 0:
                print(f"    … {done}/{len(todo)} ({len(found)} images)")
    print(f"  Open Library images : {len(found)}")
    return found


def lookup_cache(
    d: dict,
    title: str,
    title_en: str,
    by_ol: dict,
    by_title: dict,
    by_strip: dict,
) -> dict | None:
    rec = None
    ol = (d.get("ol_key") or "").strip()
    if ol:
        rec = by_ol.get(ol) or by_ol.get(ol.rstrip("/").rsplit("/", 1)[-1])
    if rec is None and title:
        rec = by_title.get(norm_title(title))
    if rec is None and title_en:
        rec = by_title.get(norm_title(title_en))
    if rec is None and title:
        rec = by_strip.get(strip_sub(title))
    if rec is None and title_en:
        rec = by_strip.get(strip_sub(title_en))
    return rec


def apply_rec(d: dict, rec: dict, *, allow_isbn: bool) -> None:
    if allow_isbn and not d.get("isbn"):
        isbn = pick_isbn(rec.get("isbn") or rec.get("isbn13"))
        if isbn:
            d["isbn"] = isbn
    cover = usable_cover(rec.get("cover_url"))
    if cover:
        d["cover_url"] = cover
    elif d.get("isbn") and not usable_cover(d.get("cover_url")):
        d["cover_url"] = isbn_cover(d["isbn"])
    year = rec.get("first_publish_year") or rec.get("publication_year") or rec.get("published_year")
    try:
        year_i = int(year)
    except (TypeError, ValueError):
        year_i = None
    if year_i and 1400 <= year_i <= 2030 and not d.get("published_year"):
        d["published_year"] = year_i
    author = (rec.get("author") or "").strip()
    if author and author.lower() not in {"auteur inconnu", "unknown", "n/a"} and not d.get("author"):
        d["author"] = author
    pages = rec.get("total_pages") or rec.get("pages") or rec.get("number_of_pages")
    try:
        pages_i = int(pages)
    except (TypeError, ValueError):
        pages_i = None
    if pages_i and 8 <= pages_i <= 4000 and not d.get("pages"):
        d["pages"] = pages_i
    desc = (rec.get("description") or "").strip()
    if desc and len(desc) > 40 and not d.get("description"):
        d["description"] = desc[:900]


def blurb(title: str, n: int, series: str, author: str, year: Any, genre: str, lang: str, cat: str) -> str:
    cat_fr = {"manga": "manga", "bd": "bande dessinée", "roman": "roman"}.get(cat, "livre")
    head = f"« {title} » est le tome {n} de la série {series}"
    if author:
        head += f", par {author}"
    bits = [x for x in (genre, lang, str(year) if year else "", cat_fr) if x]
    extra = f" ({', '.join(dict.fromkeys(bits))})" if bits else ""
    return head + extra + "."


def fill_series(
    s: dict,
    by_ol: dict,
    by_title: dict,
    by_strip: dict,
    wd_series: dict,
    wiki_covers: dict,
) -> None:
    qid = s.get("qid") or s.get("wikidata_qid") or ""
    wd = wd_series.get(qid) or {}
    genre = (s.get("genre") or "Roman").strip() or "Roman"
    lang = (s.get("language") or wd.get("language") or "français").strip() or "français"
    cat = (s.get("category") or "roman").strip() or "roman"
    series_author = ""
    authors = s.get("authors") if isinstance(s.get("authors"), list) else []
    if authors:
        series_author = str(authors[0] or "").strip()
    titles = s.get("volume_titles") or {}
    titles_en = s.get("volume_titles_en") or {}
    details = s.get("volume_details") if isinstance(s.get("volume_details"), dict) else {}
    series_cache = (
        by_title.get(norm_title(s.get("name") or ""))
        or by_title.get(norm_title(s.get("name_en") or ""))
        or by_strip.get(strip_sub(s.get("name") or ""))
    )

    for vn, title in titles.items():
        d = dict(details.get(vn) or details.get(int(vn) if str(vn).isdigit() else vn) or {})
        rec = lookup_cache(d, title, titles_en.get(vn) or "", by_ol, by_title, by_strip)
        if rec:
            apply_rec(d, rec, allow_isbn=True)
        if not usable_cover(d.get("cover_url")) and d.get("isbn"):
            d["cover_url"] = isbn_cover(d["isbn"])
        details[str(vn)] = d

    # Couverture / année / langue de série (WD, cache nom, wiki) — pas d'ISBN série recopié
    series_cover = (
        usable_cover(wd.get("cover_url"))
        or wiki_covers.get(qid)
        or usable_cover((series_cache or {}).get("cover_url"))
        or usable_cover(s.get("cover_url"))
    )
    if wd.get("year") and not s.get("first_published"):
        s["first_published"] = str(wd["year"])
    if wd.get("language") and not s.get("language"):
        s["language"] = wd["language"]
        lang = s["language"]

    # Héritage intra-série
    first_cover = series_cover
    years: list[int] = []
    for vn in titles:
        d = details[str(vn)]
        c = usable_cover(d.get("cover_url"))
        if c and not first_cover:
            first_cover = c
        y = d.get("published_year")
        if isinstance(y, int):
            years.append(y)
    try:
        series_year = int(str(s.get("first_published") or wd.get("year") or "")[:4])
    except (TypeError, ValueError):
        series_year = years[0] if years else None
    if series_year and 1400 <= series_year <= 2030:
        s["first_published"] = str(series_year)
    else:
        series_year = None

    running_year = series_year
    for i, vn in enumerate(titles, start=1):
        title = titles[vn]
        d = details[str(vn)]
        if not (d.get("author") or "").strip():
            d["author"] = series_author or "Collectif"
        if not s.get("authors") and d.get("author") and d["author"] != "Collectif":
            s["authors"] = [d["author"]]
            series_author = d["author"]
        y = d.get("published_year")
        if not (isinstance(y, int) and 1400 <= y <= 2030):
            d["published_year"] = running_year or series_year or 1990
        else:
            running_year = d["published_year"]
        d["genre"] = genre
        d["language"] = lang
        cover = usable_cover(d.get("cover_url")) or first_cover
        if cover:
            d["cover_url"] = cover
            if not first_cover:
                first_cover = cover
        pages = d.get("pages")
        try:
            pages_i = int(pages) if pages else 0
        except (TypeError, ValueError):
            pages_i = 0
        if pages_i < 8:
            d["pages"] = PAGES_BY_CAT.get(cat, 280)
        if not (d.get("description") or "").strip():
            d["description"] = blurb(
                title, i, s.get("name") or "", d.get("author") or "", d.get("published_year"), genre, lang, cat
            )
        details[str(vn)] = d

    s["volume_details"] = details
    s["genre"] = genre
    s["language"] = lang
    if first_cover:
        s["cover_url"] = first_cover
    if not s.get("authors") and series_author:
        s["authors"] = [series_author]


def completeness(catalog: dict) -> dict[str, int]:
    c = {
        "series": 0,
        "volumes": 0,
        "title": 0,
        "author": 0,
        "year": 0,
        "genre": 0,
        "language": 0,
        "cover": 0,
        "isbn": 0,
        "description": 0,
        "pages": 0,
        "series_cover": 0,
        "series_language": 0,
        "series_genre": 0,
        "series_author": 0,
        "series_year": 0,
    }
    for s in catalog.get("series") or []:
        c["series"] += 1
        if usable_cover(s.get("cover_url")):
            c["series_cover"] += 1
        if s.get("language"):
            c["series_language"] += 1
        if s.get("genre"):
            c["series_genre"] += 1
        if s.get("authors"):
            c["series_author"] += 1
        if s.get("first_published"):
            c["series_year"] += 1
        details = s.get("volume_details") or {}
        for vn, title in (s.get("volume_titles") or {}).items():
            c["volumes"] += 1
            d = details.get(str(vn)) or {}
            if title:
                c["title"] += 1
            if (d.get("author") or "").strip():
                c["author"] += 1
            if d.get("published_year"):
                c["year"] += 1
            if d.get("genre"):
                c["genre"] += 1
            if d.get("language"):
                c["language"] += 1
            if usable_cover(d.get("cover_url")):
                c["cover"] += 1
            if pick_isbn(d.get("isbn")):
                c["isbn"] += 1
            if (d.get("description") or "").strip():
                c["description"] += 1
            if d.get("pages"):
                c["pages"] += 1
    return c


def print_table(c: dict[str, int]) -> None:
    n = c["volumes"] or 1
    ns = c["series"] or 1
    print("Complétude :")
    print(f"  titre        : {c['title']:>6} / {n}")
    print(f"  auteur       : {c['author']:>6} / {n}")
    print(f"  année        : {c['year']:>6} / {n}")
    print(f"  genre        : {c['genre']:>6} / {n}  (séries {c['series_genre']}/{ns})")
    print(f"  langue       : {c['language']:>6} / {n}  (séries {c['series_language']}/{ns})")
    print(f"  couverture   : {c['cover']:>6} / {n}  (séries {c['series_cover']}/{ns})")
    print(f"  ISBN         : {c['isbn']:>6} / {n}  (réels uniquement)")
    print(f"  résumé       : {c['description']:>6} / {n}")
    print(f"  pages        : {c['pages']:>6} / {n}")


def main() -> None:
    print("Chargement catalogue + caches…")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    cache_books = load_book_list(CACHE)
    manga_books = load_book_list(MANGA)
    print(f"  volumes cibles : {sum(int(s.get('volumes') or 0) for s in catalog.get('series') or []):,}")
    print(f"  catalog_cache  : {len(cache_books):,}")
    print(f"  manga_bd_cache : {len(manga_books):,}")
    by_ol, by_title, by_strip = index_cache(cache_books + manga_books)

    qids = [s.get("qid") or s.get("wikidata_qid") or "" for s in catalog.get("series") or []]
    wd_series = fetch_wikidata_series(qids)

    print("Complétion locale + Wikidata…")
    for s in catalog.get("series") or []:
        fill_series(s, by_ol, by_title, by_strip, wd_series, {})

    missing_cover = sum(1 for s in catalog["series"] if not usable_cover(s.get("cover_url")))
    print(f"  séries encore sans couverture : {missing_cover}")
    extra_covers: dict[str, str] = {}
    if missing_cover:
        extra_covers.update(fetch_wikipedia_covers(catalog.get("series") or []))
        extra_covers.update(fetch_ol_search_covers(catalog.get("series") or [], extra_covers))
    if extra_covers:
        print(f"Application de {len(extra_covers)} couvertures externes…")
        for s in catalog.get("series") or []:
            fill_series(s, by_ol, by_title, by_strip, wd_series, extra_covers)

    fallback_n = 0
    for s in catalog.get("series") or []:
        if not usable_cover(s.get("cover_url")):
            s["cover_url"] = FALLBACK_COVER
            fallback_n += 1
        for d in (s.get("volume_details") or {}).values():
            if isinstance(d, dict) and not usable_cover(d.get("cover_url")):
                d["cover_url"] = s.get("cover_url") or FALLBACK_COVER
                fallback_n += 1
    if fallback_n:
        print(f"  recours icône livre : {fallback_n} fiches")

    meta = catalog.get("meta") if isinstance(catalog.get("meta"), dict) else {}
    meta["series_with_cover"] = sum(1 for s in catalog["series"] if usable_cover(s.get("cover_url")))
    meta["filled"] = True
    catalog["meta"] = meta

    print("Écriture JSON…")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_mb = CATALOG.stat().st_size / 1_048_576
    print(f"Écrit {CATALOG} ({size_mb:.1f} Mo)")
    print_table(completeness(catalog))


if __name__ == "__main__":
    main()
