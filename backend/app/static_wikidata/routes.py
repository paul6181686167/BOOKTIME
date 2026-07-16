"""API lecture seule des exports Wikidata statiques (séries + livres hors série populaires)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends

from ..security.jwt import get_current_user
from . import service

router = APIRouter(prefix="/api/static-wikidata", tags=["static-wikidata"])


@router.get("/status")
async def static_wikidata_status(_user: dict = Depends(get_current_user)):
    """Chemins, compteurs, présence du champ popularity sur l'index."""
    return service.status()


@router.get("/series/search")
async def search_series(
    q: str = Query("", min_length=1, max_length=200),
    limit: int = Query(15, ge=1, le=50),
    _user: dict = Depends(get_current_user),
):
    """Recherche textuelle sur l'index title_index (normalisation alignée sur l'export)."""
    q = (q or "").strip()
    if len(q) < 2:
        return {"results": [], "query": q}
    return {"results": service.search_series_by_title(q=q, limit=limit), "query": q}


@router.get("/series/{qid}")
async def get_series(qid: str, _user: dict = Depends(get_current_user)):
    """Détail d'une série par QID (contenu tel quel dans wikidata_series_db.json)."""
    if not qid.startswith("Q"):
        raise HTTPException(status_code=400, detail="QID invalide")
    row = service.get_series(qid)
    if row is None:
        st = service.status()
        if st.get("load_error"):
            raise HTTPException(status_code=503, detail=st["load_error"])
        raise HTTPException(status_code=404, detail="Série inconnue ou index absent")
    return row


@router.get("/series/top/by-popularity")
async def top_series(
    limit: int = Query(30, ge=1, le=200),
    _user: dict = Depends(get_current_user),
):
    """Séries triées par popularity (0–100) puis work_count ; sans popularity, retombe sur work_count."""
    return {"results": service.top_series_by_popularity(limit=limit)}


@router.get("/standalone/popular")
async def standalone_popular(
    limit: int = Query(50, ge=1, le=500),
    _user: dict = Depends(get_current_user),
):
    """Entrées du cache popular_standalone_books.json (vide si pas encore généré)."""
    return {"meta": service.standalone_meta(), "books": service.popular_standalone(limit=limit)}
