"""
Amis : demandes, profil visible par les amis (avis, livres préférés) et messagerie
avec recommandations de livres.

Collections :
- friendships      {id, requester_id, addressee_id, status: pending|accepted, created_at, updated_at}
- friend_messages  {id, conv, sender_id, recipient_id, text, book, created_at, read_at}
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..auth.routes import public_settings
from ..database.connection import books_collection, db, users_collection
from ..security.jwt import get_current_user
from .helpers import (
    MAX_SEARCH_RESULTS,
    clean_message,
    display_label,
    iso,
    pair_key,
    parse_iso,
    search_filter,
    search_rank,
)
from .identity import normalize_friend_code, new_friend_code, safe_label
from app.utils.timeutils import utcnow

router = APIRouter(prefix="/api/friends", tags=["friends"])

friendships = db["friendships"]
messages = db["friend_messages"]

_indexes_ready = False


def _ensure_indexes() -> None:
    global _indexes_ready
    if _indexes_ready:
        return
    try:
        friendships.create_index([("requester_id", 1), ("addressee_id", 1)])
        friendships.create_index("addressee_id")
        messages.create_index([("conv", 1), ("created_at", 1)])
        messages.create_index([("recipient_id", 1), ("read_at", 1)])
        _indexes_ready = True
    except Exception:
        # Les index sont une optimisation : leur absence ne doit pas bloquer l'API.
        pass


class RequestBody(BaseModel):
    user_id: str


class MessageBody(BaseModel):
    text: Optional[str] = None
    book: Optional[Dict[str, Any]] = None


# ---------- utilitaires ----------


def _me(current_user: dict) -> str:
    return current_user["id"]


def _user_card(doc: Optional[dict]) -> Dict[str, Any]:
    doc = doc or {}
    return {
        "id": doc.get("id"),
        "display_name": display_label(doc),
        "username": doc.get("username") or "",
        "bio": doc.get("bio") or "",
        "avatar_url": doc.get("avatar_url") or "",
    }


def _find_user(user_id: str, projection: Optional[dict] = None) -> Optional[dict]:
    return users_collection.find_one(
        {"id": user_id}, projection or {"_id": 0, "password_hash": 0}
    )


def _relation(a: str, b: str) -> Optional[dict]:
    return friendships.find_one(
        {
            "$or": [
                {"requester_id": a, "addressee_id": b},
                {"requester_id": b, "addressee_id": a},
            ]
        }
    )


def _are_friends(a: str, b: str) -> bool:
    rel = _relation(a, b)
    return bool(rel and rel.get("status") == "accepted")


def _require_friend(me: str, other: str) -> None:
    if not _are_friends(me, other):
        raise HTTPException(status_code=403, detail="Vous n'êtes pas amis.")


def _relation_state(me: str, rel: Optional[dict]) -> str:
    if not rel:
        return "none"
    if rel.get("status") == "accepted":
        return "friends"
    return "pending_out" if rel.get("requester_id") == me else "pending_in"


def _message_out(doc: dict, me: str) -> Dict[str, Any]:
    return {
        "id": doc["id"],
        "mine": doc.get("sender_id") == me,
        "text": doc.get("text") or "",
        "book": doc.get("book"),
        "created_at": iso(doc.get("created_at")),
    }


def _book_summary(doc: dict) -> Dict[str, Any]:
    return {
        "id": doc.get("id"),
        "title": doc.get("title") or "",
        "author": doc.get("author") or "",
        "category": doc.get("category") or "roman",
        "cover_url": doc.get("cover_url") or "",
        "rating": doc.get("rating") or 0,
        "review": (doc.get("review") or "").strip(),
        "ol_key": doc.get("ol_key") or "",
        "isbn": doc.get("isbn") or "",
        "total_pages": doc.get("total_pages"),
        "description": (doc.get("description") or "")[:600],
    }


# ---------- partage de profil (code d'ami, lien, QR code) ----------


@router.get("/me/code")
def my_friend_code(current_user: dict = Depends(get_current_user)):
    """Code d'ami personnel, créé à la première demande. Sert au lien et au QR code."""
    me = _me(current_user)
    doc = (
        users_collection.find_one(
            {"id": me}, {"_id": 0, "friend_code": 1, "username": 1, "display_name": 1}
        )
        or {}
    )
    code = normalize_friend_code(doc.get("friend_code"))
    if not code:
        for _ in range(8):
            candidate = new_friend_code()
            if not users_collection.find_one({"friend_code": candidate}, {"id": 1}):
                code = candidate
                break
        if not code:
            raise HTTPException(status_code=503, detail="Impossible de créer le code, réessaie.")
        users_collection.update_one({"id": me}, {"$set": {"friend_code": code}})
    return {
        "code": code,
        "username": doc.get("username") or "",
        "display_name": doc.get("display_name") or "",
    }


@router.get("/by-code/{code}")
def reader_by_code(code: str, current_user: dict = Depends(get_current_user)):
    """Retrouve un lecteur grâce à son code d'ami (lien partagé ou QR code scanné).

    Fonctionne même si le lecteur a désactivé l'apparition dans la recherche : il a
    lui-même choisi de partager ce code.
    """
    me = _me(current_user)
    clean = normalize_friend_code(code)
    if not clean:
        raise HTTPException(status_code=400, detail="Code d'ami invalide.")
    doc = users_collection.find_one(
        {"friend_code": clean, "banned": {"$ne": True}}, {"_id": 0, "password_hash": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Ce code ne correspond à aucun lecteur.")
    card = _user_card(doc)
    card["display_name"] = safe_label(doc)
    is_me = doc["id"] == me
    card["state"] = "me" if is_me else _relation_state(me, _relation(me, doc["id"]))
    return {"user": card, "is_me": is_me}


# ---------- recherche et demandes ----------


@router.get("/search")
def search_readers(
    q: str = Query("", max_length=80),
    current_user: dict = Depends(get_current_user),
):
    """Cherche un lecteur par @pseudo, nom affiché, ou adresse email exacte."""
    me = _me(current_user)
    flt = search_filter(q, me)
    if not flt:
        return {"users": []}
    found = list(
        users_collection.find(flt, {"_id": 0, "password_hash": 0}).limit(MAX_SEARCH_RESULTS)
    )
    found.sort(key=lambda doc: search_rank(doc, q))
    out = []
    for doc in found:
        card = _user_card(doc)
        card["state"] = _relation_state(me, _relation(me, doc["id"]))
        out.append(card)
    return {"users": out}


@router.post("/requests")
def send_request(body: RequestBody, current_user: dict = Depends(get_current_user)):
    """Envoie une demande d'ami (ou l'accepte si l'autre en avait déjà envoyé une)."""
    _ensure_indexes()
    me = _me(current_user)
    target = body.user_id
    if target == me:
        raise HTTPException(status_code=400, detail="Tu ne peux pas t'ajouter toi-même.")
    if not _find_user(target, {"_id": 0, "id": 1}):
        raise HTTPException(status_code=404, detail="Lecteur introuvable.")

    rel = _relation(me, target)
    now = utcnow()
    if rel:
        if rel["status"] == "accepted":
            raise HTTPException(status_code=400, detail="Vous êtes déjà amis.")
        if rel["requester_id"] == me:
            return {"state": "pending_out"}
        friendships.update_one(
            {"id": rel["id"]}, {"$set": {"status": "accepted", "updated_at": now}}
        )
        return {"state": "friends"}

    friendships.insert_one(
        {
            "id": str(uuid.uuid4()),
            "requester_id": me,
            "addressee_id": target,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
    )
    return {"state": "pending_out"}


@router.get("/requests")
def list_requests(current_user: dict = Depends(get_current_user)):
    """Demandes reçues et envoyées en attente."""
    me = _me(current_user)
    incoming, outgoing = [], []
    pending = list(
        friendships.find(
            {
                "status": "pending",
                "$or": [{"requester_id": me}, {"addressee_id": me}],
            }
        ).sort("created_at", -1)
    )
    ids = {r["requester_id"] if r["addressee_id"] == me else r["addressee_id"] for r in pending}
    users = {
        u["id"]: u
        for u in users_collection.find(
            {"id": {"$in": list(ids)}}, {"_id": 0, "password_hash": 0}
        )
    }
    for rel in pending:
        incoming_req = rel["addressee_id"] == me
        other = users.get(rel["requester_id"] if incoming_req else rel["addressee_id"])
        if not other:
            continue
        entry = {
            "request_id": rel["id"],
            "created_at": iso(rel.get("created_at")),
            "user": _user_card(other),
        }
        (incoming if incoming_req else outgoing).append(entry)
    return {"incoming": incoming, "outgoing": outgoing}


@router.post("/requests/{request_id}/accept")
def accept_request(request_id: str, current_user: dict = Depends(get_current_user)):
    me = _me(current_user)
    rel = friendships.find_one({"id": request_id})
    if not rel or rel.get("addressee_id") != me or rel.get("status") != "pending":
        raise HTTPException(status_code=404, detail="Demande introuvable.")
    friendships.update_one(
        {"id": request_id}, {"$set": {"status": "accepted", "updated_at": utcnow()}}
    )
    return {"state": "friends"}


@router.delete("/requests/{request_id}")
def cancel_or_decline_request(
    request_id: str, current_user: dict = Depends(get_current_user)
):
    """Refuse une demande reçue ou annule une demande envoyée."""
    me = _me(current_user)
    rel = friendships.find_one({"id": request_id, "status": "pending"})
    if not rel or me not in (rel.get("requester_id"), rel.get("addressee_id")):
        raise HTTPException(status_code=404, detail="Demande introuvable.")
    friendships.delete_one({"id": request_id})
    return {"success": True}


# ---------- liste d'amis ----------


@router.get("")
def list_friends(current_user: dict = Depends(get_current_user)):
    """Amis avec dernier message et nombre de messages non lus."""
    me = _me(current_user)
    rels = list(
        friendships.find(
            {"status": "accepted", "$or": [{"requester_id": me}, {"addressee_id": me}]}
        )
    )
    friend_ids = [r["addressee_id"] if r["requester_id"] == me else r["requester_id"] for r in rels]
    users = {
        u["id"]: u
        for u in users_collection.find(
            {"id": {"$in": friend_ids}}, {"_id": 0, "password_hash": 0}
        )
    }
    out = []
    for fid in friend_ids:
        doc = users.get(fid)
        if not doc:
            continue
        card = _user_card(doc)
        last = messages.find_one({"conv": pair_key(me, fid)}, sort=[("created_at", -1)])
        card["last_message"] = (
            {
                "text": last.get("text") or "",
                "has_book": bool(last.get("book")),
                "book_title": (last.get("book") or {}).get("title", ""),
                "mine": last.get("sender_id") == me,
                "created_at": iso(last.get("created_at")),
            }
            if last
            else None
        )
        card["unread"] = messages.count_documents(
            {"sender_id": fid, "recipient_id": me, "read_at": None}
        )
        out.append(card)
    # Conversations récentes d'abord, puis ordre alphabétique
    out.sort(key=lambda c: c["display_name"].lower())
    out.sort(
        key=lambda c: (c["last_message"] or {}).get("created_at") or "",
        reverse=True,
    )
    return {"friends": out}


@router.get("/unread")
def unread_summary(current_user: dict = Depends(get_current_user)):
    """Pastille de notification : messages non lus et demandes reçues."""
    me = _me(current_user)
    return {
        "unread_messages": messages.count_documents({"recipient_id": me, "read_at": None}),
        "pending_requests": friendships.count_documents(
            {"addressee_id": me, "status": "pending"}
        ),
    }


@router.delete("/{user_id}")
def remove_friend(user_id: str, current_user: dict = Depends(get_current_user)):
    me = _me(current_user)
    rel = _relation(me, user_id)
    if not rel or rel.get("status") != "accepted":
        raise HTTPException(status_code=404, detail="Cet ami est introuvable.")
    friendships.delete_one({"id": rel["id"]})
    return {"success": True}


# ---------- profil d'un ami ----------


@router.get("/{user_id}/profile")
def friend_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Profil complet : bio, livres préférés, avis. Réservé aux amis (et à soi-même)."""
    me = _me(current_user)
    if user_id != me:
        _require_friend(me, user_id)
    doc = _find_user(user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Lecteur introuvable.")

    # Réglages de confidentialité du propriétaire : il choisit ce que ses amis voient
    # (lui-même voit toujours tout).
    is_me = user_id == me
    shared = {key: True for key in ("favorites", "reviews", "reading")} if is_me else {
        "favorites": public_settings(doc)["share_favorites"],
        "reviews": public_settings(doc)["share_reviews"],
        "reading": public_settings(doc)["share_reading"],
    }

    base = {"user_id": user_id}
    favorites = (
        [
            _book_summary(b)
            for b in books_collection.find({**base, "is_favorite": True}, {"_id": 0}).limit(60)
        ]
        if shared["favorites"]
        else []
    )
    reviewed = (
        list(
            books_collection.find(
                {
                    **base,
                    "$or": [
                        {"rating": {"$gt": 0}},
                        {"review": {"$type": "string", "$ne": ""}},
                    ],
                },
                {"_id": 0},
            )
            .sort("updated_at", -1)
            .limit(60)
        )
        if shared["reviews"]
        else []
    )
    reading = (
        [
            _book_summary(b)
            for b in books_collection.find({**base, "status": "reading"}, {"_id": 0}).limit(6)
        ]
        if shared["reading"]
        else []
    )
    return {
        "user": _user_card(doc),
        "stats": {
            "total_books": books_collection.count_documents(base),
            "completed_books": books_collection.count_documents({**base, "status": "completed"}),
        },
        "favorites": favorites,
        "reviews": [_book_summary(b) for b in reviewed],
        "reading": reading,
        # Sections que l'ami a choisi de ne pas montrer (affichage d'un message adapté)
        "hidden": [name for name, visible in shared.items() if not visible],
        "is_me": is_me,
    }


# ---------- messagerie ----------


@router.get("/{user_id}/messages")
def get_messages(
    user_id: str,
    after: Optional[str] = Query(None, description="Date ISO du dernier message déjà reçu"),
    current_user: dict = Depends(get_current_user),
):
    """Conversation avec un ami. Marque comme lus les messages reçus."""
    me = _me(current_user)
    _require_friend(me, user_id)

    query: Dict[str, Any] = {"conv": pair_key(me, user_id)}
    after_dt = parse_iso(after)
    if after_dt:
        query["created_at"] = {"$gt": after_dt}
    docs = list(messages.find(query, {"_id": 0}).sort("created_at", -1).limit(100))
    docs.reverse()

    messages.update_many(
        {"sender_id": user_id, "recipient_id": me, "read_at": None},
        {"$set": {"read_at": utcnow()}},
    )
    return {"messages": [_message_out(d, me) for d in docs]}


@router.post("/{user_id}/messages")
def send_message(
    user_id: str, body: MessageBody, current_user: dict = Depends(get_current_user)
):
    """Envoie un texte et/ou une recommandation de livre."""
    _ensure_indexes()
    me = _me(current_user)
    _require_friend(me, user_id)
    content = clean_message(body.text, body.book)
    doc = {
        "id": str(uuid.uuid4()),
        "conv": pair_key(me, user_id),
        "sender_id": me,
        "recipient_id": user_id,
        "text": content["text"],
        "book": content["book"],
        "created_at": utcnow(),
        "read_at": None,
    }
    messages.insert_one(doc)
    return {"message": _message_out(doc, me)}
