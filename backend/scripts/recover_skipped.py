"""Récupère catalog_daily_skip hors lots quotidiens."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _load_env() -> None:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _log(msg: str) -> None:
    print(msg, flush=True)


def _clean_url(url: str) -> str:
    return (url or "").split("?", 1)[0]


def main() -> int:
    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    import requests
    from pymongo import MongoClient
    from app.db_config import database
    from app.catalog import daily_pending, daily_store
    from app.catalog.daily_ingest import (
        UA,
        build_complete_entry,
        is_human_label,
        usable_cover,
    )

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=20000)
    db = client[os.environ.get("DATABASE_NAME") or "booktime"]
    database._client = client
    database._db = db

    skip_coll = db["catalog_daily_skip"]
    docs = list(skip_coll.find({}))
    _log(f"skip_total={len(docs)}")

    recovered = 0
    kept = 0
    dropped = 0

    for doc in docs:
        qid = (doc.get("qid") or "").strip()
        reason = doc.get("reason") or ""
        _log(f"--- {qid} reason={reason}")

        if not qid.startswith("Q") or not qid[1:].isdigit():
            skip_coll.delete_one({"qid": qid})
            dropped += 1
            _log(f"drop_invalid={qid}")
            continue

        r = requests.get(
            f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
            timeout=30,
            headers=UA,
        )
        if r.status_code != 200:
            _log(f"wd_fail={qid}|{r.status_code}")
            kept += 1
            continue
        ent = (r.json().get("entities") or {}).get(qid) or {}
        labels = {k: v.get("value") for k, v in (ent.get("labels") or {}).items()}
        claims = ent.get("claims") or {}

        def _claim_ids(pid: str) -> list[str]:
            out: list[str] = []
            for c in claims.get(pid) or []:
                v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if isinstance(v, dict) and v.get("id"):
                    out.append(v["id"])
            return out

        def _claim_time(pid: str) -> int | None:
            for c in claims.get(pid) or []:
                v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if isinstance(v, dict) and v.get("time"):
                    try:
                        return int(str(v["time"])[1:5])
                    except Exception:
                        return None
            return None

        def _claim_image(pid: str) -> str:
            for c in claims.get(pid) or []:
                v = ((c.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return ""

        p31 = set(_claim_ids("P31"))
        # entreprise / studio / organisation → garder en skip
        org_types = {"Q4830453", "Q43229", "Q891723", "Q161726", "Q2085381"}
        if p31 & org_types and not _claim_ids("P50"):
            _log(f"keep_org={qid}|{labels.get('en') or labels.get('fr') or labels}")
            kept += 1
            continue

        author_qids = _claim_ids("P50") or _claim_ids("P170") or _claim_ids("P57")
        title = (
            labels.get("fr")
            or labels.get("en")
            or labels.get("eu")
            or labels.get("es")
            or next(iter(labels.values()), "")
        )
        if not is_human_label(title):
            _log(f"keep_no_title={qid}")
            kept += 1
            continue

        author = ""
        author_qid = ""
        if author_qids:
            ids = "|".join(author_qids[:5])
            ar = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbgetentities",
                    "ids": ids,
                    "props": "labels",
                    "languages": "fr|en|eu|es",
                    "format": "json",
                },
                timeout=30,
                headers=UA,
            )
            entities = (ar.json().get("entities") or {}) if ar.status_code == 200 else {}
            for aq in author_qids:
                labs = {
                    k: v.get("value")
                    for k, v in ((entities.get(aq) or {}).get("labels") or {}).items()
                }
                name = labs.get("fr") or labs.get("en") or labs.get("eu") or labs.get("es") or ""
                if is_human_label(name):
                    author = name
                    author_qid = aq
                    break

        if not is_human_label(author):
            _log(f"keep_no_author={qid}|title={title}")
            kept += 1
            continue

        cover = ""
        img = _claim_image("P18")
        if img:
            ir = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": f"File:{img}",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "format": "json",
                },
                timeout=30,
                headers=UA,
            )
            pages = ((ir.json().get("query") or {}).get("pages") or {}) if ir.status_code == 200 else {}
            for page in pages.values():
                infos = page.get("imageinfo") or []
                if infos and infos[0].get("url"):
                    cover = _clean_url(infos[0]["url"])
                    break

        year = _claim_time("P577")
        cand = {
            "qid": qid,
            "name": title,
            "name_en": labels.get("en") or title,
            "author": author,
            "author_qid": author_qid,
            "cover_url": cover if usable_cover(cover) else "",
            "category": "bd",
            "genre": "BD",
        }
        work = {
            "title": title,
            "title_en": labels.get("en") or "",
            "author": author,
            "author_qid": author_qid,
            "published_year": year,
            "work_qid": qid,
        }
        entry = build_complete_entry(cand, [work], min_volumes=1, standalone=True)
        if not entry:
            _log(f"keep_incomplete={qid}")
            kept += 1
            continue
        daily_store.upsert_series(entry)
        skip_coll.delete_one({"qid": qid})
        recovered += 1
        _log(f"recovered={qid}|{title}|{author}|cover={bool(usable_cover(entry.get('cover_url')))}")

    _log(
        f"done recovered={recovered} kept={kept} dropped={dropped} "
        f"skip_left={skip_coll.count_documents({})}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
