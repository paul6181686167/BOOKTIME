"""Routes proxy Google Books (clé serveur, JWT requis comme Open Library)."""

from __future__ import annotations

import logging

import requests
from fastapi import APIRouter, Depends, HTTPException, Query

from ..security.jwt import get_current_user
from .service import get_volume_by_id, lookup_isbn, search_volumes_simplified

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/google-books", tags=["google-books"])


@router.get("/volumes")
async def google_books_volumes(
    q: str = Query(..., min_length=1, max_length=500, description="Ex. titre, ou isbn:9782847893979"),
    limit: int = Query(10, ge=1, le=40),
    current_user: dict = Depends(get_current_user),
):
    """
    Recherche de volumes Google Books (3e source catalogue).
    Authentification requise : la clé API reste côté serveur.
    """
    try:
        return search_volumes_simplified(q, max_results=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        logger.warning("Google Books HTTP %s: %s", code, e)
        raise HTTPException(status_code=502, detail=f"Google Books: {e}") from e
    except requests.RequestException as e:
        logger.warning("Google Books requête: %s", e)
        raise HTTPException(status_code=502, detail="Erreur réseau vers Google Books") from e


@router.get("/volume/{volume_id}")
async def google_books_volume(
    volume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Métadonnées simplifiées pour un volume par son id Google Books."""
    try:
        return get_volume_by_id(volume_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        logger.warning("Google Books HTTP %s: %s", code, e)
        raise HTTPException(status_code=502, detail=f"Google Books: {e}") from e
    except requests.RequestException as e:
        logger.warning("Google Books requête: %s", e)
        raise HTTPException(status_code=502, detail="Erreur réseau vers Google Books") from e


@router.get("/isbn/{isbn}")
async def google_books_by_isbn(
    isbn: str,
    limit: int = Query(5, ge=1, le=10),
    current_user: dict = Depends(get_current_user),
):
    """Raccourci : recherche `isbn:{isbn_normalisé}`."""
    try:
        return lookup_isbn(isbn, max_results=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else 502
        logger.warning("Google Books HTTP %s: %s", code, e)
        raise HTTPException(status_code=502, detail=f"Google Books: {e}") from e
    except requests.RequestException as e:
        logger.warning("Google Books requête: %s", e)
        raise HTTPException(status_code=502, detail="Erreur réseau vers Google Books") from e
