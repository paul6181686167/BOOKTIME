"""
Collections personnalisées (étagères) synchronisées sur le compte.

Stockage : champs `collections` (liste) et `collections_version` (entier) du document
utilisateur. Le client envoie la liste complète avec la version qu'il a lue ; si le
serveur a une version plus récente, la réponse est 409 avec l'état du serveur et le
client fusionne puis renvoie.

Collection : {id, name, color, items: [{key, type, id, title, author, cover_url}]}
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..database.connection import users_collection
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/collections", tags=["collections"])

MAX_COLLECTIONS = 100
MAX_ITEMS = 1000
MAX_NAME = 80
MAX_TEXT = 300
MAX_URL = 1000
ITEM_TYPES = {"book", "series"}
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _text(value: Any, limit: int) -> str:
    if value is None:
        return ""
    return str(value).strip()[:limit]


def sanitize_item(raw: Any) -> Optional[Dict[str, Any]]:
    """Normalise un élément ; None si invalide."""
    if not isinstance(raw, dict):
        return None
    item_type = "series" if raw.get("type") == "series" else "book"
    item_id = _text(raw.get("id"), MAX_TEXT)
    if not item_id:
        return None
    cover = raw.get("cover_url")
    return {
        "key": f"{item_type}:{item_id}",
        "type": item_type,
        "id": item_id,
        "title": _text(raw.get("title"), MAX_TEXT) or "Sans titre",
        "author": _text(raw.get("author"), MAX_TEXT),
        "cover_url": _text(cover, MAX_URL) if cover else None,
    }


def sanitize_collections(raw: Any) -> List[Dict[str, Any]]:
    """Valide et normalise la liste envoyée par le client (400 si structure invalide)."""
    if not isinstance(raw, list):
        raise HTTPException(status_code=400, detail="`collections` doit être une liste")
    if len(raw) > MAX_COLLECTIONS:
        raise HTTPException(
            status_code=400, detail=f"Maximum {MAX_COLLECTIONS} collections"
        )
    out: List[Dict[str, Any]] = []
    seen_ids = set()
    seen_names = set()
    for entry in raw:
        if not isinstance(entry, dict):
            raise HTTPException(status_code=400, detail="Collection invalide")
        cid = entry.get("id")
        if cid is None or isinstance(cid, bool) or str(cid).strip() == "":
            raise HTTPException(status_code=400, detail="Identifiant de collection manquant")
        name = _text(entry.get("name"), MAX_NAME)
        if not name:
            raise HTTPException(status_code=400, detail="Nom de collection manquant")
        if str(cid) in seen_ids or name.lower() in seen_names:
            # Doublon : on garde la première occurrence
            continue
        seen_ids.add(str(cid))
        seen_names.add(name.lower())

        items_raw = entry.get("items")
        if items_raw is None:
            items_raw = []
        if not isinstance(items_raw, list):
            raise HTTPException(status_code=400, detail="`items` doit être une liste")
        if len(items_raw) > MAX_ITEMS:
            raise HTTPException(
                status_code=400, detail=f"Maximum {MAX_ITEMS} éléments par collection"
            )
        items: List[Dict[str, Any]] = []
        keys = set()
        for it in items_raw:
            clean = sanitize_item(it)
            if clean and clean["key"] not in keys:
                keys.add(clean["key"])
                items.append(clean)

        color = entry.get("color")
        collection = {"id": cid if isinstance(cid, (int, str)) else str(cid), "name": name, "items": items}
        if isinstance(color, str) and HEX_COLOR.match(color):
            collection["color"] = color.lower()
        out.append(collection)
    return out


def _read(user_id: str) -> Dict[str, Any]:
    doc = users_collection.find_one(
        {"id": user_id}, {"_id": 0, "collections": 1, "collections_version": 1}
    ) or {}
    return {
        "collections": doc.get("collections") or [],
        "version": int(doc.get("collections_version") or 0),
    }


@router.get("")
def get_collections(current_user: dict = Depends(get_current_user)):
    return _read(current_user["id"])


@router.put("")
def put_collections(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    collections = sanitize_collections(payload.get("collections"))
    base = payload.get("base_version")
    if base is not None and (isinstance(base, bool) or not isinstance(base, int)):
        raise HTTPException(status_code=400, detail="`base_version` doit être un entier")

    current = _read(current_user["id"])
    if base is not None and base != current["version"]:
        return JSONResponse(status_code=409, content={"conflict": True, **current})

    # Mise à jour conditionnelle : évite d'écraser une écriture concurrente
    new_version = current["version"] + 1
    if current["version"] == 0:
        version_filter = {
            "$or": [
                {"collections_version": {"$exists": False}},
                {"collections_version": 0},
            ]
        }
    else:
        version_filter = {"collections_version": current["version"]}
    result = users_collection.update_one(
        {"id": current_user["id"], **version_filter},
        {"$set": {"collections": collections, "collections_version": new_version}},
    )
    if result.matched_count == 0:
        latest = _read(current_user["id"])
        return JSONResponse(status_code=409, content={"conflict": True, **latest})
    return {"collections": collections, "version": new_version}
