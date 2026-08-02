"""
Charge paresseuse de wikidata_series_db.json et popular_standalone_books.json.
Thread-safe ; pas de rechargement automatique (redémarrage serveur ou clear_cache).
"""

from __future__ import annotations

import json
import re
import threading
import unicodedata
from typing import Any

from ..config import WIKIDATA_SERIES_DB_PATH, WIKIDATA_STANDALONE_CACHE_PATH
from ..db_config import Database

# Collection MongoDB alimentee par scripts/import_wikidata_to_mongo.py.
# Preferee au fichier (255 Mo) : evite l'OOM sur Render free (512 Mo de RAM).
MONGO_COLLECTION = "wikidata_series"

# Champs "lite" renvoyes pour la recherche / le top (sans works, allege le payload).
_LITE_PROJECTION = {
    "qid": 1,
    "name": 1,
    "name_fr": 1,
    "name_en": 1,
    "type": 1,
    "work_count": 1,
    "category": 1,
}

# Doit rester aligné avec extract_wikidata_series.norm (clés title_index).
_LIGATURES = {"œ": "oe", "æ": "ae", "ø": "o", "ß": "ss"}
_STOP = re.compile(
    r"\b(le|la|les|l|the|a|an|de|du|des|un|une|of|in|to|for|on|at|by|with|and|et|au|aux|no)\b"
)


def norm_title(s: str) -> str:
    if not s:
        return ""
    for src, dst in _LIGATURES.items():
        s = s.replace(src, dst).replace(src.upper(), dst)
    s = re.sub(r"'s\b", "s", s, flags=re.IGNORECASE)
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[''`\-]", " ", s.lower())
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = _STOP.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


_LITE_SERIES_KEYS = ("qid", "name", "name_fr", "name_en", "type", "work_count", "popularity")

def infer_series_category(row: dict[str, Any]) -> str:
    """
    Catégorie (roman | bd | manga) déduite du **type Wikidata** (P31) puis, à défaut,
    des **genres P136** des œuvres. Light novel → roman (prose).
    """
    from ..utils.category_detect import detect_category_from_wikidata_type_and_genres

    t = str((row or {}).get("type") or "")
    parts: list[str] = []
    for w in (row or {}).get("works") or []:
        if not isinstance(w, dict):
            continue
        g = w.get("genres_en")
        if isinstance(g, list):
            parts.extend(str(x) for x in g if x)
        elif g:
            parts.append(str(g))
    ms = (row or {}).get("main_subjects_en")
    if isinstance(ms, list):
        parts.extend(str(x) for x in ms if x)
    elif ms:
        parts.append(str(ms))
    return detect_category_from_wikidata_type_and_genres(
        type_label=t,
        genres_blob=" ".join(parts),
    )


def _series_lite(row: dict[str, Any]) -> dict[str, Any]:
    lite = {k: row[k] for k in _LITE_SERIES_KEYS if k in row}
    lite["category"] = infer_series_category(row)
    return lite


# Types génériques où Wikidata range souvent des LIVRES INDIVIDUELS mal étiquetés
# "série". Sans tome lié (work_count < 2), ce sont presque toujours des faux positifs
# (ex. "Harry Potter à l'école des sorciers" rangé en "book series").
_GENERIC_SERIES_TYPES = {"book series", "written work series", ""}
_MIN_GENERIC_WORKS = 2

# Types synthétiques issus de la découverte (franchises / hubs P179). Après filtrage des
# formats, beaucoup ne contiennent plus que des jeux/films -> 0 tome : ce sont alors des
# séries de jeux vidéo (Lego Harry Potter, One Piece: Grand Battle...) à écarter.
_DISCOVERY_TYPES = {"literary series hub", "literary franchise"}

# Types Wikidata curés : vraie classification de série, gardée même sans tome lié
# (ex. "manga series" Naruto, tomes absents de Wikidata mais série bien réelle).
_CURATED_TYPES = {
    "novel series",
    "manga series",
    "light novel series",
    "manhwa series",
    "comic book series",
    "comics series",
    "children's book series",
    "heptalogy",
    "seed series",
}


# Types curés où l'absence de tomes Wikidata est fréquente mais la série est réelle.
_CURATED_ALLOW_ZERO_WORKS = {
    "manga series",
    "manhwa series",
    "comic book series",
    "comics series",
    "seed series",
}


def is_real_series(row: dict[str, Any]) -> bool:
    """
    True si l'entrée est une vraie série (multi-tomes) et non un livre/jeu/film isolé.
    - Manga / BD / seed : acceptés même si work_count=0 (tomes souvent absents de WD).
    - novel / children's series : exigent >= 2 tomes (sinon = livre individuel mal tagué).
    - Types découverte (hub/franchise) : exigent >= 1 tome livre.
    - Types génériques : exigent >= 2 tomes liés.
    """
    if not isinstance(row, dict):
        return False
    t = str(row.get("type") or "").strip().lower()
    wc = int(row.get("work_count") or 0)
    if t in _CURATED_ALLOW_ZERO_WORKS:
        return True
    if t in _CURATED_TYPES:
        return wc >= _MIN_GENERIC_WORKS
    if t in _DISCOVERY_TYPES:
        return wc >= 1
    if t in _GENERIC_SERIES_TYPES:
        return wc >= _MIN_GENERIC_WORKS
    # Type inconnu : exiger multi-tomes (évite les livres seuls)
    return wc >= _MIN_GENERIC_WORKS

_lock = threading.Lock()
_series_db: dict[str, Any] | None = None
_standalone_doc: dict[str, Any] | None = None
_standalone_loaded_once = False
_load_error: str | None = None

# Backend de donnees series : "mongo" (Atlas) ou "file" (wikidata_series_db.json).
# Resolu une fois puis mis en cache.
_backend: str | None = None
_backend_lock = threading.Lock()


def _resolve_backend() -> str:
    """Choisit Mongo si la collection est peuplee, sinon le fichier local."""
    global _backend
    if _backend is not None:
        return _backend
    with _backend_lock:
        if _backend is not None:
            return _backend
        resolved = "file"
        try:
            dbo = Database()
            if not dbo.is_mock_mode():
                if dbo.db[MONGO_COLLECTION].estimated_document_count() > 0:
                    resolved = "mongo"
        except Exception:
            resolved = "file"
        _backend = resolved
        return _backend


def _collection():
    return Database().db[MONGO_COLLECTION]


def _clean_lite(doc: dict[str, Any]) -> dict[str, Any]:
    doc.pop("_id", None)
    if not doc.get("category"):
        doc["category"] = infer_series_category(doc)
    return doc


def clear_cache() -> None:
    global _series_db, _standalone_doc, _standalone_loaded_once, _load_error, _backend
    with _lock:
        _series_db = None
        _standalone_doc = None
        _standalone_loaded_once = False
        _load_error = None
    with _backend_lock:
        _backend = None


def _load_series_locked() -> None:
    global _series_db, _load_error
    path = WIKIDATA_SERIES_DB_PATH
    if not path.is_file():
        _series_db = None
        _load_error = f"Fichier séries absent : {path}"
        return
    try:
        with open(path, encoding="utf-8") as f:
            _series_db = json.load(f)
        _load_error = None
    except Exception as e:
        _series_db = None
        _load_error = str(e)


def _load_standalone_locked() -> None:
    global _standalone_doc
    path = WIKIDATA_STANDALONE_CACHE_PATH
    if not path.is_file():
        _standalone_doc = {"books": []}
        return
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        _standalone_doc = doc if isinstance(doc, dict) else {"books": []}
    except Exception:
        _standalone_doc = {"books": []}


def ensure_loaded() -> None:
    global _standalone_loaded_once
    backend = _resolve_backend()
    with _lock:
        # Le fichier series n'est charge que si Mongo n'est pas disponible.
        if backend == "file" and _series_db is None and _load_error is None:
            _load_series_locked()
        if not _standalone_loaded_once:
            _standalone_loaded_once = True
            _load_standalone_locked()


def status() -> dict[str, Any]:
    ensure_loaded()
    backend = _resolve_backend()
    with _lock:
        st = _standalone_doc or {}
        books = st.get("books") if isinstance(st, dict) else None
        nb = len(books) if isinstance(books, list) else 0

    if backend == "mongo":
        try:
            n = _collection().estimated_document_count()
            load_error = None
        except Exception as exc:
            n = 0
            load_error = str(exc)
        return {
            "backend": "mongo",
            "collection": MONGO_COLLECTION,
            "series_count": n,
            "standalone_count": nb,
            "standalone_cache_exists": WIKIDATA_STANDALONE_CACHE_PATH.is_file(),
            "load_error": load_error,
        }

    with _lock:
        by = (_series_db or {}).get("by_qid") or {}
        n = len(by)
        sample = next(iter(by.values()), {}) if by else {}
        has_pop = "popularity" in sample
        return {
            "backend": "file",
            "series_db_path": str(WIKIDATA_SERIES_DB_PATH),
            "series_db_exists": WIKIDATA_SERIES_DB_PATH.is_file(),
            "standalone_cache_path": str(WIKIDATA_STANDALONE_CACHE_PATH),
            "standalone_cache_exists": WIKIDATA_STANDALONE_CACHE_PATH.is_file(),
            "series_count": n,
            "standalone_count": nb,
            "index_has_popularity_field": has_pop,
            "load_error": _load_error,
        }


def get_series(qid: str) -> dict[str, Any] | None:
    if _resolve_backend() == "mongo":
        try:
            doc = _collection().find_one({"_id": qid})
        except Exception:
            doc = None
        if not doc:
            return None
        doc.pop("_id", None)
        doc.pop("title_keys", None)
        doc.pop("search_blob", None)
        if not doc.get("category"):
            doc["category"] = infer_series_category(doc)
        return doc

    ensure_loaded()
    with _lock:
        if not _series_db:
            return None
        row = (_series_db.get("by_qid") or {}).get(qid)
    if row is None:
        return None
    return {**row, "category": infer_series_category(row)}


def _search_mongo(qn: str, limit: int) -> list[dict[str, Any]]:
    """Recherche Mongo : exact (3) > prefixe (2) > mots via index texte (1)."""
    coll = _collection()
    best: dict[str, tuple[int, dict[str, Any]]] = {}

    def consider(doc: dict[str, Any], score: int) -> None:
        qid = doc.get("qid") or doc.get("_id")
        if not qid:
            return
        cur = best.get(qid)
        if cur is None or score > cur[0]:
            best[qid] = (score, doc)

    try:
        for doc in coll.find({"title_keys": qn}, _LITE_PROJECTION).limit(60):
            consider(doc, 3)
        prefix = {"$regex": f"^{re.escape(qn)}"}
        for doc in coll.find({"title_keys": prefix}, _LITE_PROJECTION).limit(200):
            consider(doc, 2)
        # Match par mots (index texte) : trie par work_count pour faire remonter
        # les series consistantes plutot que des homonymes a 0 tome.
        text_cur = (
            coll.find({"$text": {"$search": qn}}, _LITE_PROJECTION)
            .sort("work_count", -1)
            .limit(150)
        )
        for doc in text_cur:
            consider(doc, 1)
    except Exception:
        # Un souci Mongo ne doit pas casser la recherche : on renvoie ce qu'on a.
        pass

    rows: list[dict[str, Any]] = []
    for score, doc in best.values():
        doc = _clean_lite(doc)
        doc["_match"] = score
        rows.append(doc)
    rows.sort(
        key=lambda r: (int(r.get("_match") or 0), int(r.get("work_count") or 0)),
        reverse=True,
    )
    for r in rows:
        r.pop("_match", None)
    return rows[:limit]


def search_series_by_title(*, q: str, limit: int) -> list[dict[str, Any]]:
    """
    Recherche sur title_index (titres normalisés FR/EN + titres d'œuvres).
    Sous-chaîne sur les clés ; tri par popularity puis work_count.
    """
    qn = norm_title(q.strip())
    if len(qn) < 2:
        return []
    if _resolve_backend() == "mongo":
        return _search_mongo(qn, limit)
    ensure_loaded()
    with _lock:
        if not _series_db:
            return []
        ti = _series_db.get("title_index") or {}
        by = _series_db.get("by_qid") or {}

    # Qualité de correspondance par qid (exacte > préfixe > sous-chaîne) : on garde le
    # meilleur score rencontré. Sans ça, le tri popularité noie la correspondance exacte
    # derrière des œuvres dérivées plus "populaires".
    best: dict[str, int] = {}

    def consider(qid: str, score: int) -> None:
        if isinstance(qid, str) and qid.startswith("Q"):
            if score > best.get(qid, 0):
                best[qid] = score

    direct = ti.get(qn)
    if direct:
        consider(direct, 3)

    max_collect = 400
    if len(qn) >= 2:
        for k, qid in ti.items():
            if len(best) >= max_collect:
                break
            if not isinstance(k, str) or not isinstance(qid, str):
                continue
            if k == qn:
                consider(qid, 3)
            elif k.startswith(qn):
                consider(qid, 2)
            elif qn in k:
                consider(qid, 1)

    rows: list[dict[str, Any]] = []
    for qid, match in best.items():
        row = by.get(qid)
        if not row or not is_real_series(row):
            continue
        lite = _series_lite(row)
        lite["_match"] = match
        rows.append(lite)

    def sort_key(r: dict[str, Any]) -> tuple[int, int, int]:
        p = r.get("popularity")
        pi = int(p) if isinstance(p, int) else -1
        return (int(r.get("_match") or 0), pi, int(r.get("work_count") or 0))

    rows.sort(key=sort_key, reverse=True)
    for r in rows:
        r.pop("_match", None)
    return rows[:limit]


def top_series_by_popularity(*, limit: int) -> list[dict[str, Any]]:
    if _resolve_backend() == "mongo":
        try:
            cur = (
                _collection()
                .find({}, _LITE_PROJECTION)
                .sort("work_count", -1)
                .limit(limit)
            )
            return [_clean_lite(doc) for doc in cur]
        except Exception:
            return []

    ensure_loaded()
    with _lock:
        if not _series_db:
            return []
        by = _series_db.get("by_qid") or {}
        rows = list(by.values())

    def key(e: dict) -> tuple[int, int]:
        p = e.get("popularity")
        if isinstance(p, int):
            return (p, int(e.get("work_count") or 0))
        return (-1, int(e.get("work_count") or 0))

    rows.sort(key=key, reverse=True)
    return [{**r, "category": infer_series_category(r)} for r in rows[:limit]]


def popular_standalone(*, limit: int) -> list[dict[str, Any]]:
    ensure_loaded()
    with _lock:
        st = _standalone_doc or {}
        books = st.get("books")
        if not isinstance(books, list):
            return []
    return books[:limit]


def standalone_meta() -> dict[str, Any]:
    ensure_loaded()
    with _lock:
        st = _standalone_doc or {}
        if not isinstance(st, dict):
            return {}
        return {k: v for k, v in st.items() if k != "books"}
