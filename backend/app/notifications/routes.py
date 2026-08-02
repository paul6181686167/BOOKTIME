"""Routes API notifications utilisateur."""

import logging

from fastapi import APIRouter, Depends, Query

from ..security.jwt import get_current_user
from . import service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    items = service.list_notifications(user_id, limit=limit)
    return {"notifications": items, "unread": service.unread_count(user_id)}


@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    return {"unread": service.unread_count(current_user["id"])}


@router.post("/{notif_id}/read")
async def read_notification(notif_id: str, current_user: dict = Depends(get_current_user)):
    ok = service.mark_read(current_user["id"], notif_id)
    return {"success": ok}


@router.post("/read-all")
async def read_all_notifications(current_user: dict = Depends(get_current_user)):
    count = service.mark_all_read(current_user["id"])
    return {"success": True, "marked": count}
