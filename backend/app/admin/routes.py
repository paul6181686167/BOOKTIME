"""
Administration : statistiques en direct, liste des utilisateurs, bannissement.

L'accès est réservé aux comptes dont l'email figure dans la variable d'environnement
ADMIN_EMAILS (séparés par des virgules), ou dont le champ `is_admin` vaut true en base.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..database.connection import (
    books_collection,
    db,
    series_library_collection,
    users_collection,
)
from ..friends.helpers import iso
from ..security.jwt import get_current_user
from .helpers import bucket_by_day, clean_reason, is_admin, is_online
from app.utils.timeutils import utcnow

router = APIRouter(prefix="/api/admin", tags=["admin"])

SIGNUP_CHART_DAYS = 14
PAGE_SIZE_MAX = 50


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs.")
    return current_user


class BanBody(BaseModel):
    reason: Optional[str] = None


def _count(collection, query: Optional[dict] = None) -> int:
    return collection.count_documents(query or {})


def _dates_since(collection, field: str, since: datetime) -> list:
    return [doc.get(field) for doc in collection.find({field: {"$gte": since}}, {"_id": 0, field: 1})]


@router.get("/stats")
def admin_stats(_: dict = Depends(require_admin)) -> Dict[str, Any]:
    """Chiffres globaux de l'application, calculés à chaque appel (donc « en direct »)."""
    now = utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=6)
    chart_start = day_start - timedelta(days=SIGNUP_CHART_DAYS - 1)
    online_since = now - timedelta(minutes=15)
    messages = db["friend_messages"]
    friendships = db["friendships"]

    signups = _dates_since(users_collection, "created_at", chart_start)
    books_added = _dates_since(books_collection, "date_added", chart_start)

    categories = {
        name: _count(books_collection, {"category": name}) for name in ("roman", "bd", "manga")
    }
    total_books = _count(books_collection)
    categories["autre"] = max(0, total_books - sum(categories.values()))

    return {
        "generated_at": iso(now),
        "users": {
            "total": _count(users_collection),
            "banned": _count(users_collection, {"banned": True}),
            "online": _count(users_collection, {"last_seen": {"$gte": online_since}}),
            "active_24h": _count(users_collection, {"last_seen": {"$gte": now - timedelta(hours=24)}}),
            "new_today": _count(users_collection, {"created_at": {"$gte": day_start}}),
            "new_7d": _count(users_collection, {"created_at": {"$gte": week_start}}),
            "signups_per_day": bucket_by_day(signups, SIGNUP_CHART_DAYS, now),
        },
        "books": {
            "total": total_books,
            "completed": _count(books_collection, {"status": "completed"}),
            "reading": _count(books_collection, {"status": "reading"}),
            "to_read": _count(books_collection, {"status": "to_read"}),
            "added_today": _count(books_collection, {"date_added": {"$gte": day_start}}),
            "added_7d": _count(books_collection, {"date_added": {"$gte": week_start}}),
            "by_category": categories,
            "added_per_day": bucket_by_day(books_added, SIGNUP_CHART_DAYS, now),
            "series_in_libraries": _count(series_library_collection),
        },
        "engagement": {
            "reviews": _count(books_collection, {"review": {"$type": "string", "$ne": ""}}),
            "ratings": _count(books_collection, {"rating": {"$gt": 0}}),
            "favorites": _count(books_collection, {"is_favorite": True}),
            "messages": _count(messages),
            "messages_24h": _count(messages, {"created_at": {"$gte": now - timedelta(hours=24)}}),
            "book_recommendations": _count(messages, {"book": {"$ne": None}}),
            "friendships": _count(friendships, {"status": "accepted"}),
            "friend_requests_pending": _count(friendships, {"status": "pending"}),
        },
    }


def _user_row(doc: dict, now: datetime) -> Dict[str, Any]:
    uid = doc.get("id")
    return {
        "id": uid,
        "email": doc.get("email") or "",
        "display_name": doc.get("display_name") or "",
        "created_at": iso(doc.get("created_at")),
        "last_seen": iso(doc.get("last_seen")),
        "online": is_online(doc.get("last_seen"), now),
        "books_count": _count(books_collection, {"user_id": uid}),
        "reviews_count": _count(
            books_collection, {"user_id": uid, "review": {"$type": "string", "$ne": ""}}
        ),
        "banned": bool(doc.get("banned")),
        "banned_reason": doc.get("banned_reason") or "",
        "banned_at": iso(doc.get("banned_at")),
        "is_admin": is_admin(doc),
    }


@router.get("/users")
def admin_users(
    q: str = Query("", max_length=80),
    status: str = Query("all", pattern="^(all|banned)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=PAGE_SIZE_MAX),
    _: dict = Depends(require_admin),
):
    """Utilisateurs, du plus récent au plus ancien. Recherche par email ou nom affiché."""
    query: Dict[str, Any] = {}
    needle = q.strip()
    if needle:
        pattern = {"$regex": re.escape(needle), "$options": "i"}
        query["$or"] = [{"email": pattern}, {"display_name": pattern}]
    if status == "banned":
        query["banned"] = True

    now = utcnow()
    projection = {"_id": 0, "password_hash": 0, "avatar_url": 0}
    docs = list(
        users_collection.find(query, projection).sort("created_at", -1).skip(skip).limit(limit)
    )
    return {
        "total": _count(users_collection, query),
        "users": [_user_row(doc, now) for doc in docs],
    }


@router.post("/users/{user_id}/ban")
def ban_user(user_id: str, body: BanBody, admin: dict = Depends(require_admin)):
    target = users_collection.find_one({"id": user_id}, {"_id": 0, "password_hash": 0, "avatar_url": 0})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if user_id == admin.get("id"):
        raise HTTPException(status_code=400, detail="Tu ne peux pas te bannir toi-même.")
    if is_admin(target):
        raise HTTPException(status_code=400, detail="Un administrateur ne peut pas être banni.")
    users_collection.update_one(
        {"id": user_id},
        {
            "$set": {
                "banned": True,
                "banned_at": utcnow(),
                "banned_reason": clean_reason(body.reason),
            }
        },
    )
    return {"success": True}


@router.post("/users/{user_id}/unban")
def unban_user(user_id: str, _: dict = Depends(require_admin)):
    result = users_collection.update_one(
        {"id": user_id},
        {"$set": {"banned": False}, "$unset": {"banned_at": "", "banned_reason": ""}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return {"success": True}
