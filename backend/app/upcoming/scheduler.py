"""
Job planifié de rafraîchissement des "prochaines sorties".

Pour chaque utilisateur ayant activé les notifications, recalcule ses sorties,
met à jour le cache, et notifie les nouvelles sorties devenues disponibles
(in-app toujours ; e-mail si le mode = "email" et un SMTP est configuré).

Bornes de charge : tous les comptes sont traités sauf ceux qui ont choisi "none"
(le mode par défaut est "in_app"), dans la limite de UPCOMING_MAX_USERS par passage.
Les autres voient malgré tout des données fraîches au chargement (cache reconstruit
à la demande).
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

from ..database.connection import users_collection
from ..notifications.service import create_notification, send_email
from . import cache
from .service import get_upcoming_for_user

logger = logging.getLogger(__name__)

_scheduler = None
REFRESH_HOURS = int(os.getenv("UPCOMING_REFRESH_HOURS", "12"))
DEFAULT_NOTIF_MODE = "in_app"
# Borne de charge par passage (chaque compte déclenche des appels à des API externes)
MAX_USERS_PER_RUN = int(os.getenv("UPCOMING_MAX_USERS", "300"))


def notif_mode(user: dict) -> str:
    """Mode de notification d'un utilisateur ; sans réglage = valeur par défaut (in_app)."""
    return (user.get("notif_upcoming") or DEFAULT_NOTIF_MODE).strip() or DEFAULT_NOTIF_MODE


def eligible_users_query() -> dict:
    """Tous les comptes sauf ceux qui ont explicitement désactivé les notifications.

    Un compte sans réglage a le mode par défaut (in_app) : il reçoit donc les
    notifications de sortie sans avoir à ouvrir le panneau « À venir ».
    """
    return {"notif_upcoming": {"$ne": "none"}}


def _process_user(user: dict) -> None:
    mode = notif_mode(user)
    if mode == "none":
        return

    payload = asyncio.run(get_upcoming_for_user(user))
    available = payload.get("groups", {}).get("available", []) or []
    notified = cache.get_notified_ids(user["id"])

    for item in available:
        item_id = item.get("id")
        if not item_id or item_id in notified:
            continue
        title = f"Disponible : {item.get('title', 'Nouvelle sortie')}"
        body = item.get("reason") or "Cette sortie est maintenant disponible."
        create_notification(
            user["id"],
            title=title,
            body=body,
            type="upcoming_release",
            dedup_key=item_id,
            data={
                "series_name": item.get("series_name"),
                "author": item.get("author"),
                "cover_url": item.get("cover_url"),
                "item_type": item.get("type"),
            },
        )
        if mode == "email":
            send_email(user.get("email"), title, body)

    new_notified = notified | {i.get("id") for i in available if i.get("id")}
    cache.set_cached(user["id"], payload, notified_ids=list(new_notified))


def _refresh_all_and_notify() -> None:
    logger.info("Job prochaines sorties : démarrage")
    try:
        users = list(
            users_collection.find(
                eligible_users_query(),
                {"_id": 0, "id": 1, "email": 1, "notif_upcoming": 1, "followed_authors": 1},
            ).limit(MAX_USERS_PER_RUN)
        )
    except Exception as exc:
        logger.warning("Job prochaines sorties : lecture users échouée : %s", exc)
        return

    for user in users:
        try:
            _process_user(user)
        except Exception as exc:
            logger.warning("Job prochaines sorties : user %s échoué : %s", user.get("id"), exc)
        time.sleep(0.5)  # limite la pression sur les APIs externes
    logger.info("Job prochaines sorties : terminé (%d utilisateur(s))", len(users))


def start_scheduler() -> None:
    """Démarre le scheduler (idempotent). Désactivable via ENABLE_UPCOMING_SCHEDULER=false."""
    global _scheduler
    if _scheduler is not None:
        return
    if os.getenv("ENABLE_UPCOMING_SCHEDULER", "true").lower() == "false":
        logger.info("Scheduler prochaines sorties désactivé (ENABLE_UPCOMING_SCHEDULER=false)")
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _refresh_all_and_notify,
            "interval",
            hours=REFRESH_HOURS,
            id="upcoming_refresh",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        _scheduler.start()
        logger.info("Scheduler prochaines sorties démarré (toutes les %d h)", REFRESH_HOURS)
    except Exception as exc:  # pragma: no cover
        logger.warning("Impossible de démarrer le scheduler prochaines sorties : %s", exc)
        _scheduler = None


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:  # pragma: no cover
            pass
        _scheduler = None
