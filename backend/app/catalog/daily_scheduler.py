"""Job quotidien : nouvelles fiches complètes dans le noyau curé."""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_scheduler = None


def _run_job() -> None:
    try:
        from .daily_ingest import run_daily_ingest

        result = run_daily_ingest()
        logger.info("Job fiches quotidiennes : %s", result)
    except Exception as exc:
        logger.warning("Job fiches quotidiennes échoué : %s", exc)


def start_daily_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    if os.getenv("ENABLE_CATALOG_DAILY", "true").lower() == "false":
        logger.info("Scheduler fiches quotidiennes désactivé (ENABLE_CATALOG_DAILY=false)")
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        hour = int(os.getenv("CATALOG_DAILY_HOUR_UTC", "3"))
        minute = int(os.getenv("CATALOG_DAILY_MINUTE_UTC", "30"))
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _run_job,
            "cron",
            hour=hour,
            minute=minute,
            id="catalog_daily_ingest",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        _scheduler.start()
        logger.info("Scheduler fiches quotidiennes démarré (cron %02d:%02d UTC)", hour, minute)
    except Exception as exc:  # pragma: no cover
        logger.warning("Impossible de démarrer le scheduler fiches quotidiennes : %s", exc)
        _scheduler = None


def shutdown_daily_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None
