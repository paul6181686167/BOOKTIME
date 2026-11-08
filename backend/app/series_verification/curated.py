"""
Niveau "référence/officiel" : noyau curé.

Sources, dans cet ordre :
  1. `backend/data/expanded_fiches_catalog.json` (~50 000 tomes) — catalogue principal
  2. `curated_series.json` (export des ~103 séries riches du front) — écrase
     les homonymes : titres FR, ISBN, exclusions, mots-clés.

Quand une série y figure, son nombre de tomes et (si disponibles) ses titres
font autorité, sans fluctuation.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .consensus import normalize_title_key

logger = logging.getLogger("booktime.series_verification")

_CURATED_PATH = Path(__file__).with_name("curated_series.json")
_CORE_PATH = Path(__file__).resolve().parents[2] / "data" / "expanded_fiches_catalog.json"

_loaded = False
_series: list[dict[str, Any]] = []
_by_key: dict[str, dict[str, Any]] = {}  # nom/variation/titre de tome normalisé -> série
_keyword_index: dict[str, list[dict[str, Any]]] = {}
_by_canon: dict[str, dict[str, Any]] = {}  # nom canonique normalisé -> entrée dans _series


def _norm(s: str) -> str:
    return normalize_title_key(s)


def clear_cache() -> None:
    global _loaded
    _loaded = False
    _series.clear()
    _by_key.clear()
    _keyword_index.clear()
    _by_canon.clear()


def _titles_by_num(raw: Any) -> dict[int, str]:
    out: dict[int, str] = {}
    if isinstance(raw, dict):
        for k, title in raw.items():
            try:
                n = int(k)
            except (TypeError, ValueError):
                continue
            out[n] = str(title or "")
    elif isinstance(raw, list):
        for t in raw:
            if not isinstance(t, dict) or t.get("volume_number") is None:
                continue
            try:
                n = int(t["volume_number"])
            except (TypeError, ValueError):
                continue
            out[n] = str(t.get("title") or "")
    return out


def _as_title_list(raw: Any, volumes: int) -> list[dict[str, Any]]:
    by_num = _titles_by_num(raw)
    if volumes > 0:
        return [{"volume_number": n, "title": by_num.get(n, "")} for n in range(1, volumes + 1)]
    return [{"volume_number": n, "title": by_num[n]} for n in sorted(by_num)]


def _normalize_entry(raw: dict[str, Any], source: str) -> dict[str, Any] | None:
    name = (raw.get("name") or "").strip()
    if not name:
        return None
    volumes = int(raw.get("volumes") or 0)
    titles = _as_title_list(raw.get("volume_titles"), volumes)
    if volumes <= 0:
        volumes = len(titles)
    variations = list(raw.get("variations") or [])
    name_en = (raw.get("name_en") or "").strip()
    if name_en and name_en not in variations and name_en != name:
        variations.append(name_en)
    return {
        "key": raw.get("key"),
        "name": name,
        "name_en": name_en or None,
        "authors": list(raw.get("authors") or []),
        "category": raw.get("category"),
        "volumes": volumes,
        "volume_titles": titles,
        "volume_details": raw.get("volume_details") or {},
        "variations": variations,
        "keywords": list(raw.get("keywords") or []),
        "exclusions": list(raw.get("exclusions") or []),
        "cover_url": raw.get("cover_url"),
        "genre": raw.get("genre"),
        "language": raw.get("language"),
        "publisher": raw.get("publisher"),
        "first_published": raw.get("first_published"),
        "wikidata_qid": raw.get("wikidata_qid") or raw.get("qid"),
        "source": source,
    }


def _index_names(entry: dict[str, Any], *, overwrite: bool) -> None:
    names = [entry.get("name") or "", *(entry.get("variations") or [])]
    if entry.get("name_en"):
        names.append(entry["name_en"])
    for nm in names:
        key = _norm(nm)
        if not key:
            continue
        if overwrite:
            _by_key[key] = entry
        else:
            _by_key.setdefault(key, entry)
    for kw in entry.get("keywords") or []:
        key = _norm(kw)
        if key:
            bucket = _keyword_index.setdefault(key, [])
            if entry not in bucket:
                bucket.append(entry)


def _index_volume_titles(entry: dict[str, Any]) -> None:
    for t in entry.get("volume_titles") or []:
        if not isinstance(t, dict):
            continue
        key = _norm(t.get("title") or "")
        if key and len(key) >= 4:
            _by_key.setdefault(key, entry)


def _register(entry: dict[str, Any], *, overwrite: bool) -> None:
    canon = _norm(entry.get("name") or "")
    if overwrite and canon and canon in _by_canon:
        old = _by_canon[canon]
        if old in _series:
            _series.remove(old)
    _series.append(entry)
    if canon:
        _by_canon[canon] = entry
    _index_names(entry, overwrite=overwrite)


def _load_json(path: Path) -> dict[str, Any] | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("Référentiel curé absent: %s", path)
        return None
    except Exception as e:  # noqa: BLE001
        logger.warning("Référentiel curé illisible (%s): %s", path, e)
        return None


def ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    _series.clear()
    _by_key.clear()
    _keyword_index.clear()
    _by_canon.clear()

    core = _load_json(_CORE_PATH)
    if isinstance(core, dict):
        for raw in core.get("series") or []:
            if not isinstance(raw, dict):
                continue
            entry = _normalize_entry(raw, "curated_core")
            if entry:
                _register(entry, overwrite=False)

    overlay = _load_json(_CURATED_PATH)
    if isinstance(overlay, dict):
        for raw in overlay.get("series") or []:
            if not isinstance(raw, dict):
                continue
            entry = _normalize_entry(raw, "curated_overlay")
            if entry:
                _register(entry, overwrite=True)

    for entry in _series:
        _index_volume_titles(entry)


def _author_matches(entry: dict[str, Any], author: str | None) -> bool:
    """Soft-check : si un auteur est fourni, il doit recouper celui du référentiel."""
    if not author:
        return True
    a = _norm(author)
    if not a:
        return True
    authors = entry.get("authors") or []
    if not authors:
        return True
    for ref_author in authors:
        ra = _norm(ref_author)
        if ra and (ra in a or a in ra):
            return True
    return False


def _is_excluded(entry: dict[str, Any], query_norm: str) -> bool:
    for ex in entry.get("exclusions") or []:
        exn = _norm(ex)
        if exn and exn in query_norm:
            return True
    return False


def match_curated(name: str, author: str | None = None) -> dict[str, Any] | None:
    """
    Renvoie l'entrée curée correspondant à la série (nom exact, variation ou titre
    de tome), en respectant les exclusions et (si fourni) l'auteur. None sinon.
    """
    ensure_loaded()
    if not name:
        return None
    q = _norm(name)
    if not q:
        return None

    entry = _by_key.get(q)
    if entry and not _is_excluded(entry, q) and _author_matches(entry, author):
        return entry

    q_words = set(q.split())
    best: dict[str, Any] | None = None
    best_len = 0
    for cand in _series:
        cand_key = _norm(cand.get("name", ""))
        if not cand_key:
            continue
        cand_words = set(cand_key.split())
        if not cand_words:
            continue
        contained = cand_words.issubset(q_words) or q_words.issubset(cand_words)
        if not contained:
            continue
        if _is_excluded(cand, q) or not _author_matches(cand, author):
            continue
        if len(cand_key) > best_len:
            best, best_len = cand, len(cand_key)
    return best


def curated_to_source_rows(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Transforme l'entrée curée en lignes de tomes pour le moteur de consensus.
    On génère TOUJOURS une ligne par tome (1..volumes), en remplissant le titre
    quand il est connu — ainsi le niveau "Référence" reflète le total complet
    même si seuls quelques titres détaillés sont disponibles.
    """
    titles_by_num = _titles_by_num((entry or {}).get("volume_titles"))
    vols = int((entry or {}).get("volumes") or 0)
    if vols > 0:
        return [{"title": titles_by_num.get(n, ""), "volume_number": n} for n in range(1, vols + 1)]
    return [{"title": titles_by_num[n], "volume_number": n} for n in sorted(titles_by_num)]
