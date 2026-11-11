"""Index MongoDB créés au démarrage (idempotent).

Sans index, chaque requête `{"user_id": ...}` parcourt toute la collection : lent dès que la
base grossit, et facturé en lectures sur Atlas. `create_index` ne fait rien si l'index existe
déjà ; une erreur (doublons existants, index de même clé sous un autre nom…) est journalisée
sans jamais empêcher le serveur de démarrer.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from pymongo import ASCENDING, DESCENDING

logger = logging.getLogger(__name__)

# (collection, clés, options)
INDEXES: List[Tuple[str, Any, Dict[str, Any]]] = [
    # Comptes : `sparse` pour tolérer les anciens documents sans le champ
    ("users", "id", {"unique": True, "sparse": True}),
    ("users", "email", {"unique": True, "sparse": True}),
    ("users", "username", {"unique": True, "sparse": True}),
    ("users", "display_name", {"sparse": True}),
    ("users", "reset_token", {"sparse": True}),
    # Amis : recherche + état de relation (une requête $in au lieu de N)
    ("friendships", [("requester_id", ASCENDING), ("addressee_id", ASCENDING)], {}),
    ("friendships", "addressee_id", {}),
    # Livres : toutes les requêtes sont filtrées par user_id
    ("books", [("user_id", ASCENDING), ("id", ASCENDING)], {}),
    ("books", [("user_id", ASCENDING), ("date_added", DESCENDING)], {}),
    ("books", [("user_id", ASCENDING), ("category", ASCENDING), ("status", ASCENDING)], {}),
    ("books", [("user_id", ASCENDING), ("saga", ASCENDING)], {}),
    ("series_library", [("user_id", ASCENDING)], {}),
    ("notifications", [("user_id", ASCENDING), ("created_at", DESCENDING)], {}),
    ("catalog_daily_series", "qid", {"unique": True, "sparse": True}),
    ("catalog_daily_series", "name_norm", {}),
    ("catalog_daily_series", "name_en_norm", {}),
    ("catalog_daily_series", "title_norms", {}),
    ("catalog_daily_series", "source", {}),
    ("catalog_daily_series", "name", {}),
    ("catalog_daily_pending", "qid", {"unique": True, "sparse": True}),
    ("catalog_daily_pending", "kind", {}),
    ("authors", "name_normalized", {"unique": True, "sparse": True}),
    ("authors", "wikidata_qid", {"sparse": True}),
    ("authors", "name", {}),
]


def ensure_indexes(database=None) -> Dict[str, int]:
    """Crée les index manquants. Renvoie {"created_or_present": n, "failed": m}."""
    if database is None:
        from ..db_config import database as database  # import tardif : évite un cycle

    if database.is_mock_mode():
        return {"created_or_present": 0, "failed": 0}

    ok = failed = 0
    for collection, keys, options in INDEXES:
        try:
            database.db[collection].create_index(keys, **options)
            ok += 1
        except Exception as exc:  # doublons existants, conflit de nom, droits insuffisants…
            failed += 1
            logger.warning("Index ignoré sur %s %s : %s", collection, keys, exc)
    logger.info("Index MongoDB : %d en place, %d ignorés", ok, failed)
    return {"created_or_present": ok, "failed": failed}
