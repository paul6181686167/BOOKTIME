"""
Niveau "référence/officiel" : référentiel curé des grandes séries.

Données générées depuis la base du front (EXTENDED_SERIES_DATABASE) via
`scripts/export_curated_series.mjs` -> curated_series.json.

C'est le niveau de vérification le plus fiable : quand une série y figure, son
nombre de tomes et (si disponibles) ses titres font autorité, sans fluctuation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .consensus import normalize_title_key

logger = logging.getLogger("booktime.series_verification")

_CURATED_PATH = Path(__file__).with_name("curated_series.json")

_loaded = False
_series: list[dict[str, Any]] = []
_by_key: dict[str, dict[str, Any]] = {}      # nom/variation normalisé -> série
_keyword_index: dict[str, list[dict[str, Any]]] = {}


def _norm(s: str) -> str:
    return normalize_title_key(s)


def ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        data = json.loads(_CURATED_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("Référentiel curé absent: %s", _CURATED_PATH)
        return
    except Exception as e:  # noqa: BLE001
        logger.warning("Référentiel curé illisible: %s", e)
        return

    _series.clear()
    _by_key.clear()
    _keyword_index.clear()
    for s in data.get("series") or []:
        if not isinstance(s, dict):
            continue
        _series.append(s)
        names = [s.get("name", "")] + list(s.get("variations") or [])
        for nm in names:
            key = _norm(nm)
            if key:
                _by_key.setdefault(key, s)
        for kw in s.get("keywords") or []:
            key = _norm(kw)
            if key:
                _keyword_index.setdefault(key, []).append(s)


def _author_matches(entry: dict[str, Any], author: str | None) -> bool:
    """Soft-check : si un auteur est fourni, il doit recouper celui du référentiel."""
    if not author:
        return True
    a = _norm(author)
    if not a:
        return True
    for ref_author in entry.get("authors") or []:
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
    Renvoie l'entrée curée correspondant à la série (nom exact ou variation),
    en respectant les exclusions et (si fourni) l'auteur. None sinon.
    """
    ensure_loaded()
    if not name:
        return None
    q = _norm(name)
    if not q:
        return None

    # 1) Correspondance exacte nom / variation.
    entry = _by_key.get(q)
    if entry and not _is_excluded(entry, q) and _author_matches(entry, author):
        return entry

    # 2) Tous les mots du nom de référence présents dans la requête (ou inverse),
    #    pour absorber les suffixes ("Harry Potter (series)", "One Piece manga").
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
        # On préfère la correspondance dont le nom est le plus long (plus spécifique).
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
    titles_by_num = {
        int(t["volume_number"]): t.get("title", "")
        for t in (entry.get("volume_titles") or [])
        if isinstance(t, dict) and t.get("volume_number") is not None
    }
    vols = int(entry.get("volumes") or 0)
    if vols > 0:
        return [{"title": titles_by_num.get(n, ""), "volume_number": n} for n in range(1, vols + 1)]
    # Pas de compte explicite : on retombe sur les titres connus.
    return [{"title": titles_by_num[n], "volume_number": n} for n in sorted(titles_by_num)]
