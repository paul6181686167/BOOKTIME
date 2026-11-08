#!/usr/bin/env python3
"""Construit un catalogue de 50 000 fiches tomes à partir de Wikidata.

Les 103 séries curées (frontend) restent la couche qualité : elles sont
exclues du JSON pour éviter les doublons. Le fichier généré alimente
GET /api/catalog/expanded.

Usage (depuis BOOKTIME-main) :
  python backend/scripts/build_expanded_fiches_catalog.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.static_wikidata.service import infer_series_category, is_real_series, norm_title  # noqa: E402

WD_PATH = ROOT / "wikidata_series_db.json"
CURATED_PATH = BACKEND / "app" / "series_verification" / "curated_series.json"
OUT_PATH = BACKEND / "data" / "expanded_fiches_catalog.json"
TARGET_BOOKS = 50_000
MAX_WORKS_PER_SERIES = 120

PREFERRED_TYPES = {
    "novel series",
    "manga series",
    "comics series",
    "comic book series",
    "children's book series",
    "light novel series",
    "manhwa series",
    "heptalogy",
    "seed series",
}
FILL_TYPES = {
    "book series",
    "written work series",
    "literary series hub",
    "literary franchise",
}
KEEP_TYPES = PREFERRED_TYPES | FILL_TYPES

JUNK = re.compile(
    r"gazette|working paper|statutory|proceedings|saturday night live|"
    r"health hazard|fatality assessment|ceur |nber |journal of|bulletin of|"
    r"report series|lecture notes|ieee |acm |legislation|acts of |"
    r"papers of |working papers|discussion paper|technical report|"
    r"official journal|hansard|congressional|federal register|"
    r"handbook|wildlife|rodenticide|studies in |issn|springer|"
    r"collected papers|selected papers|annual review|"
    r"nasa |niosh|contractor report|studies collection|"
    r"intelligence bulletin|african studies|oecd |unesco |"
    r"university press|research report|working group",
    re.I,
)
GENERIC_NAME = re.compile(
    r"^(satires|poems|novels|works|series|collection|stories|essays|"
    r"plays|letters|omnibus|anthology)$",
    re.I,
)

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

GENRE_FR = (
    ("science fiction", "Science-fiction"),
    ("speculative fiction", "Science-fiction"),
    ("fantasy", "Fantasy"),
    ("dark fantasy", "Fantasy"),
    ("horror", "Horreur"),
    ("mystery", "Policier"),
    ("detective", "Policier"),
    ("crime", "Policier"),
    ("thriller", "Thriller"),
    ("romance", "Romance"),
    ("historical", "Historique"),
    ("adventure", "Aventure"),
    ("young adult", "Young adult"),
    ("children", "Jeunesse"),
    ("comic", "BD"),
    ("manga", "Manga"),
)


def work_title(w: dict) -> str:
    return ((w.get("title_fr") or w.get("title_en") or "").strip())


def work_author(w: dict) -> str:
    for key in ("authors_fr", "authors_en"):
        arr = w.get(key)
        if isinstance(arr, list) and arr:
            first = str(arr[0]).strip()
            if first:
                return first
    return ""


def series_author(works: list[dict]) -> str:
    for w in works:
        a = work_author(w)
        if a:
            return a
    return ""


def ol_id(w: dict) -> str:
    raw = (w.get("open_library_id") or "").strip()
    if not raw:
        return ""
    raw = raw.replace("https://openlibrary.org/", "").strip("/")
    if "/" in raw:
        raw = raw.rsplit("/", 1)[-1]
    return raw


def ol_key(olid: str) -> str | None:
    if not olid:
        return None
    if olid.endswith("W"):
        return f"/works/{olid}"
    if olid.endswith("M"):
        return f"/books/{olid}"
    return f"/works/{olid}"


def ol_cover_url(olid: str) -> str | None:
    if not olid:
        return None
    return f"https://covers.openlibrary.org/b/olid/{olid}-L.jpg"


def load_curated_names() -> set[str]:
    names: set[str] = set()
    if not CURATED_PATH.is_file():
        return names
    data = json.loads(CURATED_PATH.read_text(encoding="utf-8"))
    for s in data.get("series") or []:
        if not isinstance(s, dict):
            continue
        for nm in [s.get("name"), *(s.get("variations") or [])]:
            key = norm_title(str(nm or ""))
            if key:
                names.add(key)
    return names


def quality_score(row: dict, works: list[dict], type_label: str) -> tuple:
    n = len(works)
    n_auth = sum(1 for w in works if work_author(w))
    n_fr = sum(1 for w in works if (w.get("title_fr") or "").strip())
    n_ol = sum(1 for w in works if ol_id(w))
    preferred = 1 if type_label in PREFERRED_TYPES else 0
    author_ratio = n_auth / n if n else 0
    sweet = 1 if 3 <= n <= 40 else 0
    return (
        preferred,
        1 if author_ratio >= 0.5 else 0,
        1 if n_fr else 0,
        1 if n_ol else 0,
        sweet,
        min(n, 25),
        n_auth,
    )


def infer_language(works: list[dict]) -> str | None:
    votes: Counter[str] = Counter()
    for w in works:
        for qid in w.get("language_qids") or []:
            lang = LANG_BY_QID.get(str(qid))
            if lang:
                votes[lang] += 1
        if (w.get("title_fr") or "").strip():
            votes["français"] += 1
    if not votes:
        return None
    return votes.most_common(1)[0][0]


def infer_genre(category: str, works: list[dict]) -> str | None:
    if category == "manga":
        return "Manga"
    if category == "bd":
        return "BD"
    blob = " ".join(
        str(g).lower()
        for w in works
        for g in (w.get("genres_en") or [])
        if g
    )
    for needle, label in GENRE_FR:
        if needle in blob:
            return label
    return "Roman"


def select_candidates(by_qid: dict, curated_names: set[str]) -> list[dict]:
    preferred: list[dict] = []
    fill_good: list[dict] = []
    fill_weak: list[dict] = []
    fill_last: list[dict] = []
    seen_names: set[str] = set(curated_names)
    for qid, row in by_qid.items():
        if not isinstance(row, dict):
            continue
        t = str(row.get("type") or "").strip().lower()
        if t not in KEEP_TYPES:
            continue
        if not is_real_series(row):
            continue
        name = (row.get("name_fr") or row.get("name") or row.get("name_en") or "").strip()
        if not name or len(name) < 4 or JUNK.search(name) or GENERIC_NAME.match(name):
            continue
        key = norm_title(name)
        if not key or key in seen_names:
            continue
        raw_works = [w for w in (row.get("works") or []) if isinstance(w, dict) and work_title(w)]
        if len(raw_works) < 2:
            continue
        raw_works.sort(
            key=lambda w: (
                str(w.get("publication_date") or "9999"),
                work_title(w).lower(),
            )
        )
        raw_works = raw_works[:MAX_WORKS_PER_SERIES]
        n_auth = sum(1 for w in raw_works if work_author(w))
        n_fr = sum(1 for w in raw_works if (w.get("title_fr") or "").strip())
        seen_names.add(key)
        cand = {
            "qid": qid,
            "row": row,
            "works": raw_works,
            "name": name,
            "type": t,
            "score": quality_score(row, raw_works, t),
        }
        if t in PREFERRED_TYPES:
            preferred.append(cand)
        elif n_auth >= max(2, len(raw_works) * 0.35):
            fill_good.append(cand)
        elif n_auth >= 1 or n_fr >= 2:
            fill_weak.append(cand)
        else:
            fill_last.append(cand)
    preferred.sort(key=lambda x: x["score"], reverse=True)
    fill_good.sort(key=lambda x: x["score"], reverse=True)
    fill_weak.sort(key=lambda x: x["score"], reverse=True)
    fill_last.sort(key=lambda x: x["score"], reverse=True)
    return preferred + fill_good + fill_weak + fill_last


def build_series_entry(cand: dict, works: list[dict]) -> dict:
    row = cand["row"]
    author = series_author(works)
    category = infer_series_category(row)
    genre = infer_genre(category, works) or "Roman"
    language = infer_language(works) or "français"
    volume_titles: dict[str, str] = {}
    volume_titles_en: dict[str, str] = {}
    volume_details: dict[str, dict] = {}
    cover_url = None
    first_year = None
    for i, w in enumerate(works, start=1):
        vn = str(i)
        title = work_title(w)
        volume_titles[vn] = title
        en = (w.get("title_en") or "").strip()
        fr = (w.get("title_fr") or "").strip()
        if en and en != fr:
            volume_titles_en[vn] = en
        year = str(w.get("publication_date") or "")[:4]
        if year.isdigit() and first_year is None:
            first_year = year
        olid = ol_id(w)
        detail = {
            "author": work_author(w) or author or "Collectif",
            "genre": genre,
            "language": language,
        }
        if year.isdigit():
            detail["published_year"] = int(year)
        if olid:
            detail["ol_key"] = ol_key(olid)
            cover = ol_cover_url(olid)
            if cover and not re.search(r"OL\d+W", cover):
                detail["cover_url"] = cover
                if not cover_url:
                    cover_url = cover
        if w.get("work_qid"):
            detail["work_qid"] = w.get("work_qid")
        isbn_list = w.get("isbns") or []
        if isinstance(isbn_list, list) and isbn_list:
            detail["isbn"] = str(isbn_list[0])
        volume_details[vn] = detail
    entry = {
        "key": (norm_title(cand["name"]).replace(" ", "_")[:80] or cand["qid"]),
        "qid": cand["qid"],
        "name": cand["name"],
        "name_en": (row.get("name_en") or "").strip() or None,
        "authors": [author] if author else [],
        "category": category,
        "type": cand["type"],
        "volumes": len(volume_titles),
        "volume_titles": volume_titles,
        "volume_details": volume_details,
        "first_published": first_year,
        "status": "ongoing" if len(works) >= 20 else "completed",
        "wikidata_qid": cand["qid"],
        "cover_url": cover_url,
        "language": language,
        "genre": genre,
        "source": "wikidata",
    }
    if volume_titles_en:
        entry["volume_titles_en"] = volume_titles_en
    return entry


def build_catalog(candidates: list[dict]) -> dict:
    series: list[dict] = []
    book_count = 0
    for cand in candidates:
        remaining = TARGET_BOOKS - book_count
        if remaining <= 0:
            break
        works = cand["works"][:remaining]
        if len(works) < 2:
            continue
        entry = build_series_entry(cand, works)
        series.append(entry)
        book_count += entry["volumes"]
    cats = Counter(s["category"] for s in series)
    with_cover = sum(1 for s in series if s.get("cover_url"))
    return {
        "meta": {
            "target_books": TARGET_BOOKS,
            "series_count": len(series),
            "book_count": book_count,
            "series_with_cover": with_cover,
            "categories": dict(cats),
            "source": "wikidata_series_db.json",
            "skips_curated": True,
        },
        "series": series,
    }


def main() -> None:
    print("Chargement Wikidata…")
    with open(WD_PATH, encoding="utf-8") as f:
        db = json.load(f)
    by = db.get("by_qid") or {}
    print(f"  by_qid = {len(by):,}")
    curated_names = load_curated_names()
    print(f"  noms curés exclus = {len(curated_names):,}")
    candidates = select_candidates(by, curated_names)
    print(f"  candidats = {len(candidates):,}")
    print(f"  tomes dispo = {sum(len(c['works']) for c in candidates):,}")
    catalog = build_catalog(candidates)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = OUT_PATH.stat().st_size / 1_048_576
    print(f"Écrit {OUT_PATH} ({size_mb:.1f} Mo)")
    print("Ensuite : python backend/scripts/fill_expanded_fiches_catalog.py")
    print(f"  fiches séries : {catalog['meta']['series_count']}")
    print(f"  fiches livres : {catalog['meta']['book_count']}")
    print(f"  avec couverture : {catalog['meta']['series_with_cover']}")
    print(f"  catégories    : {catalog['meta']['categories']}")
    print("  top 12 :")
    for s in catalog["series"][:12]:
        authors = s["authors"][:1] or ["?"]
        print(f"    {s['name']} — {s['volumes']} tomes — {authors[0]} [{s['category']}]")


if __name__ == "__main__":
    main()
