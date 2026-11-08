import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..security.rate_limit import ip_rate_limit
from ..utils.timeutils import utcnow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Les anciens endpoints /performance, /analytics, /abtest et /stats ne stockaient rien
# (ils renvoyaient des valeurs fictives) et étaient ouverts à tous : supprimés.

MAX_FIELD = 2000


class ErrorReport(BaseModel):
    """Rapport d'erreur envoyé par l'ErrorBoundary du front (bornes de taille obligatoires :
    la route est publique, un utilisateur qui plante n'est pas forcément connecté)."""

    errorId: str = Field(default="", max_length=64)
    message: str = Field(default="", max_length=MAX_FIELD)
    stack: str = Field(default="", max_length=MAX_FIELD * 2)
    componentStack: str = Field(default="", max_length=MAX_FIELD * 2)
    timestamp: str = Field(default="", max_length=64)
    userAgent: str = Field(default="", max_length=300)
    url: str = Field(default="", max_length=500)
    userId: Optional[str] = Field(default="", max_length=64)


def _one_line(value: Optional[str], limit: int = 300) -> str:
    """Neutralise les retours à la ligne : sans cela, un client pourrait fabriquer de fausses
    lignes de journal (injection de logs)."""
    text = (value or "").replace("\r", " ").replace("\n", " ")
    return text[:limit]


# 20 rapports par minute et par adresse : largement assez pour un vrai plantage
_error_limit = ip_rate_limit("monitoring-errors", 20, 60, "Trop de rapports d'erreur.")


@router.post("/errors", dependencies=[Depends(_error_limit)])
def log_error(error_report: ErrorReport):
    """Journalise une erreur capturée par le front."""
    logger.error(
        "Frontend Error [ID: %s] User: %s URL: %s Message: %s",
        _one_line(error_report.errorId, 64),
        _one_line(error_report.userId, 64),
        _one_line(error_report.url, 200),
        _one_line(error_report.message, 300),
    )
    return {"status": "success", "error_id": error_report.errorId}


@router.get("/health")
def monitoring_health():
    """Santé du service de rapports d'erreur."""
    return {"status": "healthy", "timestamp": utcnow().isoformat()}
