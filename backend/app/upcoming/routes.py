"""
Routes API "Prochaines sorties"
===============================

- GET /api/upcoming : agrégat personnalisé des sorties à venir (prochains tomes de
  séries, chapitres manga prédits, livres surveillés), groupé par échéance.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from ..security.jwt import get_current_user
from . import cache
from .service import get_upcoming_for_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upcoming", tags=["upcoming"])


@router.get("")
async def get_upcoming(
    refresh: bool = Query(False, description="Forcer le recalcul en ignorant le cache"),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère les prochaines sorties personnalisées de l'utilisateur (avec cache).

    Returns:
        {
          "items": [...],
          "groups": {"available", "this_week", "this_month", "later", "unknown"},
          "counts": {...},
          "generated_at": iso,
          "cached": bool
        }
    """
    try:
        if not refresh:
            cached = cache.get_cached(current_user["id"])
            if cached is not None:
                return cached

        payload = await get_upcoming_for_user(current_user)
        cache.set_cached(current_user["id"], payload)
        payload["cached"] = False
        return payload
    except Exception as exc:
        logger.error("Erreur récupération prochaines sorties: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des prochaines sorties.",
        )
