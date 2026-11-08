"""Graine Mongo : le JSON 50k est importé une fois, puis relâché.

Le noyau vivant est Mongo. Le fichier git ne sert plus qu'au premier remplissage
et aux audits. Idempotent (qid unique). Ne bloque pas le ping.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_seeded = False
_seeded_path: str | None = None


def reset_seed_flag() -> None:
    global _seeded, _seeded_path
    _seeded = False
    _seeded_path = None


def json_catalog_path() -> Path:
    from . import expanded

    return expanded._PATH


def read_json_catalog() -> dict[str, Any]:
    path = json_catalog_path()
    if not path.is_file():
        return {"meta": {}, "series": []}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {"meta": {}, "series": []}
    series = data.get("series") if isinstance(data.get("series"), list) else []
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {"meta": meta, "series": series}


def core_already_in_mongo() -> bool:
    from . import daily_store

    try:
        return daily_store._coll().find_one({"source": "core"}, {"_id": 1}) is not None
    except Exception:
        return False


def ensure_seeded(*, force: bool = False) -> dict[str, Any]:
    """Importe le JSON dans Mongo s'il n'y a pas encore de docs `source=core`."""
    global _seeded, _seeded_path
    from . import expanded

    path = json_catalog_path()
    path_key = str(path.resolve()) if path else ""
    is_default = path.resolve() == expanded._DEFAULT_PATH.resolve()
    if _seeded_path == path_key and not force:
        return {"status": "already", "seeded": True}
    with _lock:
        if _seeded_path == path_key and not force:
            return {"status": "already", "seeded": True}
        if is_default and not force and core_already_in_mongo():
            _seeded = True
            _seeded_path = path_key
            return {"status": "present", "seeded": True}
        import os

        if is_default and not force and os.getenv("ENVIRONMENT", "").lower() == "test":
            # Les tests ne versent pas les 23 Mo dans le mock (trop lent).
            _seeded = True
            _seeded_path = path_key
            return {"status": "skipped_test", "seeded": False}
        from . import daily_store

        data = read_json_catalog()
        series = data.get("series") or []
        n = 0
        for raw in series:
            if not isinstance(raw, dict) or not (raw.get("qid") or raw.get("wikidata_qid") or raw.get("name")):
                continue
            entry = dict(raw)
            if not (entry.get("qid") or entry.get("wikidata_qid")):
                entry["qid"] = entry.get("key") or entry.get("name")
            entry["source"] = "core"
            daily_store.upsert_series(entry)
            n += 1
        _seeded = True
        _seeded_path = path_key
        logger.info("Graine catalogue Mongo : %d séries (JSON %s)", n, path.name)
        return {"status": "imported", "seeded": True, "series": n}
