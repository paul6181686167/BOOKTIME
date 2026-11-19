"""Regroupe standalones multi-tomes en vraies séries (auteur + stem + n°).

Ignore magazines / manuels / ACCA / bruit (via catalog_quality_filters).

  python scripts/regroup_standalone_series.py --dry-run
  python scripts/regroup_standalone_series.py --mongo
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog.catalog_quality_filters import is_catalog_noise_doc, is_catalog_noise_title

VOL_NUM = re.compile(
    r"""
    (?:^|[\s\-–—:,\(\[])
    (?:
      (?:tome|vol(?:ume)?|book|part)\s*[#.]?\s*(\d{1,3})
      | \#\s*(\d{1,3})\b
      | \b(?:t|v)\s*\.?\s*(\d{1,3})\b
    )
    """,
    re.I | re.X,
)

STEM_STRIP = re.compile(
    r"""
    [\s\-–—:,\(\[]*
    (?:
      (?:tome|vol(?:ume)?|book|part)\s*[#.]?\s*\d{1,3}
      | \#\s*\d{1,3}
      | \b(?:t|v)\s*\.?\s*\d{1,3}\b
    )
    \s*[\)\]]*
    \s*$
    """,
    re.I | re.X,
)

# Fascicules / non-séries fiction même si numérotés
NOT_SERIES = re.compile(
    r"""
    \b(
      magazine|journal|periodical|newsletter|review\b|papers?\b|
      issue\s*\d+|splice|acca|cfa\b|cpa\b|exam\b|workbook|
      anthropological|law\s+review|to\s+do\s+today|turn\s*\d+|
      year\s+\d+\s+book|maths?\s+year|curriculum|proceedings
    )\b
    """,
    re.I | re.X,
)

# Essais / manuels académiques numérotés ≠ séries de lecture
ACADEMIC_SERIES = re.compile(
    r"""
    \b(
      theories?\s+of|quantum|mechanics|routledge|disease\b|
      econom(?:y|ics)|political\s+history|library\s+of|
      physics|chemistry|mathematics|algebra|calculus|biology|
      medicine|pathology|epidemiolog|sociology|anthropology|
      mixed\s+economy|keeping\s+life\s+honest|
      word\s+search|sudoku|crossword|piano\s+concerto|
      sheet\s+music|ministry\s+years|score\s+and\s+parts|
      coloring\s+book|colouring\s+book|handwriting|mathematische
    )\b
    """,
    re.I | re.X,
)


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


def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.U)
    return re.sub(r"\s+", " ", s).strip()


def _vol_num(title: str) -> int | None:
    m = VOL_NUM.search(title or "")
    if not m:
        return None
    for g in m.groups():
        if g:
            n = int(g)
            if 1 <= n <= 200:
                return n
    return None


def _stem(title: str) -> str:
    s = STEM_STRIP.sub("", (title or "").strip()).strip(" -–—:,()")
    return _norm(s)


def _is_genuine_group(titles: list[str], docs: list[dict] | None = None) -> bool:
    if len(titles) < 2:
        return False
    if any(
        is_catalog_noise_title(t) or NOT_SERIES.search(t or "") or ACADEMIC_SERIES.search(t or "")
        for t in titles
    ):
        return False
    nums = []
    for t in titles:
        n = _vol_num(t)
        if n is None:
            return False
        nums.append(n)
    if len(set(nums)) < 2:
        return False
    markers = sum(
        1
        for t in titles
        if re.search(r"(?:#\s*\d+|\btome\b|\bvol(?:ume)?\b|\bbook\s*\d+)", t or "", re.I)
    )
    if markers < max(2, len(titles) // 2):
        return False

    cats = set()
    if docs:
        for d in docs:
            c = (d.get("category") or "").strip().lower()
            if c:
                cats.add(c)
    comic_hash = sum(1 for t in titles if re.search(r"#\s*\d+", t or ""))
    fiction_word = any(
        re.search(r"\b(manga|novel|comics?|batman|superman|one\s*piece)\b", t or "", re.I)
        for t in titles
    )
    # BD/manga ou comics #N ou signal fiction explicite, ou roman avec tome/vol
    if cats & {"bd", "manga"}:
        return True
    if comic_hash >= 2 or fiction_word:
        return True
    if "roman" in cats or not cats:
        # romans multi-tomes OK si marqueurs tome/vol/book (pas seulement académique)
        if any(re.search(r"\b(tome|vol(?:ume)?|book)\s*\d+", t or "", re.I) for t in titles):
            return True
        if comic_hash >= 1:
            return True
        return False
    return False


def _score_doc(doc: dict) -> tuple:
    cover = 1 if (doc.get("cover_url") or "").strip() else 0
    desc = 1 if (doc.get("description") or "").strip() else 0
    return (cover, desc, -len(str(doc.get("name") or "")))


def regroup_sqlite(*, dry_run: bool) -> dict:
    path = Path(os.environ.get("CATALOG_LOCAL_SQLITE") or ROOT / "data" / "local_catalog.sqlite")
    con = sqlite3.connect(str(path), timeout=180)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=180000")

    groups: dict[tuple[str, str], list[tuple[str, dict]]] = defaultdict(list)
    for qid, name, raw in con.execute("SELECT qid, name, doc_json FROM catalog_daily_series"):
        try:
            doc = json.loads(raw or "{}")
        except Exception:
            continue
        if is_catalog_noise_doc(doc):
            continue
        typ = (doc.get("type") or "").strip()
        vols = doc.get("volumes")
        try:
            vn = int(vols) if vols is not None else 1
        except Exception:
            vn = 1
        if typ not in ("standalone", "", "empty") and vn > 1:
            continue
        if typ in (
            "daily",
            "novel series",
            "book series",
            "literary series hub",
            "comics series",
            "manga series",
        ):
            continue
        title = name or doc.get("name") or ""
        if NOT_SERIES.search(title) or is_catalog_noise_title(title):
            continue
        authors = doc.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        author = _norm(str(authors[0] if authors else ""))
        if not author or len(author) < 3:
            continue
        # auteurs « publishing / syndicate » trop collectifs → souvent fascicules
        if re.search(r"\b(publishing|publisher|publications|syndicate|press)\b", author):
            continue
        st = _stem(title)
        if not st or len(st) < 4:
            continue
        if _vol_num(title) is None:
            continue
        groups[(author, st)].append((qid, doc))

    merged = 0
    deleted = 0
    samples: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    for (author, st), items in groups.items():
        if len(items) < 2:
            continue
        titles = [(d.get("name") or "") for _, d in items]
        docs_only = [d for _, d in items]
        if not _is_genuine_group(titles, docs_only):
            continue
        # dédupliquer par n° de volume (garder le meilleur doc par n°)
        by_vol: dict[int, tuple[str, dict]] = {}
        for qid, doc in items:
            n = _vol_num(doc.get("name") or "")
            if n is None:
                continue
            prev = by_vol.get(n)
            if prev is None or _score_doc(doc) > _score_doc(prev[1]):
                by_vol[n] = (qid, doc)
        if len(by_vol) < 2:
            continue

        ordered = sorted(by_vol.items(), key=lambda x: x[0])
        winner_qid, winner = ordered[0][1]
        # préférer le doc au meilleur score global comme hub
        for _, (qid, doc) in ordered:
            if _score_doc(doc) > _score_doc(winner):
                winner_qid, winner = qid, doc

        volume_titles = {str(n): (doc.get("name") or "") for n, (_q, doc) in ordered}
        volume_details = {}
        for n, (_q, doc) in ordered:
            vd = doc.get("volume_details") or {}
            if isinstance(vd, dict) and vd.get("1"):
                volume_details[str(n)] = vd["1"]
            else:
                volume_details[str(n)] = {
                    "author": (doc.get("authors") or [None])[0] if doc.get("authors") else None,
                    "cover_url": doc.get("cover_url") or "",
                    "description": doc.get("description") or "",
                    "ol_key": doc.get("key") or doc.get("ol_key"),
                }

        hub = dict(winner)
        hub["type"] = "daily"
        hub["volumes"] = len(ordered)
        hub["volume_titles"] = volume_titles
        hub["volume_details"] = volume_details
        hub["name"] = re.sub(
            r"[\s\-–—:,\(]*(?:#\s*\d+|(?:tome|vol(?:ume)?|book|part)\s*[#.]?\s*\d+)\s*[\)\]]*\s*$",
            "",
            hub.get("name") or "",
            flags=re.I,
        ).strip() or hub.get("name")
        hub["regrouped_at"] = now
        hub["regrouped_from"] = [q for _, (q, _) in ordered]

        losers = [q for _, (q, _) in ordered if q != winner_qid]
        if len(samples) < 12:
            samples.append(
                f"{hub.get('name')} [{author}] vols={sorted(by_vol)} keep={winner_qid} drop={len(losers)}"
            )

        if dry_run:
            merged += 1
            deleted += len(losers)
            continue

        con.execute(
            "UPDATE catalog_daily_series SET name=?, name_norm=?, doc_json=?, synced=0 WHERE qid=?",
            (
                hub.get("name"),
                hub.get("name_norm") or _norm(hub.get("name") or ""),
                json.dumps(hub, ensure_ascii=False),
                winner_qid,
            ),
        )
        for q in losers:
            con.execute("DELETE FROM catalog_daily_series WHERE qid=?", (q,))
        merged += 1
        deleted += len(losers)

    if not dry_run:
        con.commit()
    after = con.execute("SELECT COUNT(*) FROM catalog_daily_series").fetchone()[0]
    con.close()
    return {"merged_series": merged, "deleted_volumes": deleted, "after": after, "samples": samples, "dry_run": dry_run}


def regroup_mongo(*, dry_run: bool) -> dict:
    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=30000)
    coll = client[os.environ.get("DATABASE_NAME") or os.environ.get("DB_NAME") or "booktime"][
        "catalog_daily_series"
    ]
    # Appliquer la même logique en relisant SQLite hub déjà fait est plus simple :
    # ici on ne fait que supprimer les losers déjà absents du PC si sync — skip for safety.
    # Regroup Mongo mirror: scan standalone same way.
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for doc in coll.find(
        {"$or": [{"type": "standalone"}, {"type": {"$in": [None, ""]}}, {"volumes": {"$lte": 1}}]},
        {"qid": 1, "name": 1, "authors": 1, "type": 1, "volumes": 1, "cover_url": 1, "description": 1, "volume_details": 1, "name_norm": 1, "key": 1, "ol_key": 1, "category": 1, "genre": 1},
    ):
        if is_catalog_noise_doc(doc):
            continue
        title = doc.get("name") or ""
        if NOT_SERIES.search(title) or is_catalog_noise_title(title):
            continue
        authors = doc.get("authors") or []
        author = _norm(str(authors[0] if authors else ""))
        if not author or re.search(
            r"\b(publishing|publisher|publications|syndicate|press)\b", author
        ):
            continue
        st = _stem(title)
        if not st or len(st) < 4 or _vol_num(title) is None:
            continue
        groups[(author, st)].append(doc)

    merged = deleted = 0
    samples: list[str] = []
    now = datetime.now(timezone.utc).isoformat()
    for (author, st), items in groups.items():
        titles = [d.get("name") or "" for d in items]
        if not _is_genuine_group(titles, items):
            continue
        by_vol: dict[int, dict] = {}
        for doc in items:
            n = _vol_num(doc.get("name") or "")
            if n is None:
                continue
            prev = by_vol.get(n)
            if prev is None or _score_doc(doc) > _score_doc(prev):
                by_vol[n] = doc
        if len(by_vol) < 2:
            continue
        ordered = sorted(by_vol.items(), key=lambda x: x[0])
        winner = max((d for _, d in ordered), key=_score_doc)
        volume_titles = {str(n): (d.get("name") or "") for n, d in ordered}
        hub = dict(winner)
        hub["type"] = "daily"
        hub["volumes"] = len(ordered)
        hub["volume_titles"] = volume_titles
        hub["name"] = re.sub(
            r"[\s\-–—:,\(]*(?:#\s*\d+|(?:tome|vol(?:ume)?|book|part)\s*[#.]?\s*\d+)\s*[\)\]]*\s*$",
            "",
            hub.get("name") or "",
            flags=re.I,
        ).strip() or hub.get("name")
        hub["regrouped_at"] = now
        losers = [d.get("qid") for _, d in ordered if d.get("qid") != winner.get("qid")]
        if len(samples) < 8:
            samples.append(f"{hub.get('name')} vols={sorted(by_vol)} drop={len(losers)}")
        if dry_run:
            merged += 1
            deleted += len(losers)
            continue
        coll.replace_one({"qid": winner["qid"]}, hub, upsert=True)
        if losers:
            coll.delete_many({"qid": {"$in": losers}})
        merged += 1
        deleted += len(losers)
    return {
        "merged_series": merged,
        "deleted_volumes": deleted,
        "after": coll.estimated_document_count(),
        "samples": samples,
        "dry_run": dry_run,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--mongo", action="store_true")
    args = p.parse_args()
    _load_env()
    print(regroup_sqlite(dry_run=args.dry_run), flush=True)
    if args.mongo:
        print(regroup_mongo(dry_run=args.dry_run), flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
