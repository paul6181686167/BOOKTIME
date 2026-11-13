"""Promote les 2 auteurs restants : photo OL + mention Wikidata factuelle."""
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


def main() -> int:
    _load_env()
    os.environ["RAILWAY_MONGODB_MOCK"] = "false"
    from pymongo import MongoClient
    from app.db_config import database
    from app.catalog import daily_authors, daily_pending
    from app.catalog.daily_ingest import usable_cover

    client = MongoClient(os.environ["MONGO_URL"], serverSelectionTimeoutMS=20000)
    db = client[os.environ.get("DATABASE_NAME") or "booktime"]
    database._client = client
    database._db = db

    docs = list(db["catalog_daily_pending"].find({"kind": "author"}))
    _log(f"authors_pending={len(docs)}")
    ok_n = 0
    for doc in docs:
        qid = (doc.get("qid") or "").strip()
        name = (doc.get("name") or "").strip()
        cand = daily_pending._cand_from_pending(doc)
        if not usable_cover(cand.get("photo_url")):
            from app.catalog import isbn_resolve

            ol = isbn_resolve.ol_author_photo(name)
            if usable_cover(ol):
                cand["photo_url"] = ol
                cand["image_url"] = ol
                cand["cover_url"] = ol
        if not (cand.get("bio") or "").strip():
            cand["bio"] = f"{name} — auteur référencé sur Wikidata ({qid})."
        entry = daily_authors.build_complete_author(cand)
        if not entry:
            _log(f"fail={qid}|{name}|photo={bool(usable_cover(cand.get('photo_url')))}")
            continue
        daily_authors.upsert_author(entry)
        daily_pending.drop(qid)
        ok_n += 1
        _log(f"ok={qid}|{name}")
    _log(f"promoted={ok_n} pending_left={daily_pending.count()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
