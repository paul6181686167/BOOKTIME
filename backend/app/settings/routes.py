"""Réglages utilisateur — préférences de notification des prochaines sorties."""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException

from ..database.connection import users_collection
from ..security.jwt import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings", tags=["settings"])

# none = aucune ; in_app = notifications dans l'app ; email = e-mail ;
# push = notifications navigateur (le front lit les notifications in-app via un SW).
VALID_MODES = {"none", "in_app", "email", "push"}
DEFAULT_MODE = "in_app"


@router.get("/notifications")
async def get_notification_settings(current_user: dict = Depends(get_current_user)):
    user = users_collection.find_one(
        {"id": current_user["id"]}, {"_id": 0, "notif_upcoming": 1, "email": 1}
    ) or {}
    return {
        "notif_upcoming": user.get("notif_upcoming", DEFAULT_MODE),
        "email": user.get("email") or current_user.get("email"),
    }


@router.put("/notifications")
async def update_notification_settings(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):
    mode = (payload.get("notif_upcoming") or "").strip()
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Mode invalide. Attendu : {', '.join(sorted(VALID_MODES))}",
        )
    users_collection.update_one(
        {"id": current_user["id"]}, {"$set": {"notif_upcoming": mode}}
    )
    return {"success": True, "notif_upcoming": mode}
