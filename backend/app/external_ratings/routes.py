"""Route : notes d'autres sites pour une fiche livre / série."""

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool

from ..security.jwt import get_current_user
from . import service

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.get("/external")
async def external_ratings(
    title: str = Query("", max_length=300),
    author: str = Query("", max_length=200),
    isbn: str = Query("", max_length=32),
    kind: str = Query("book", pattern="^(book|series)$"),
    category: str = Query("", max_length=30),
    current_user: dict = Depends(get_current_user),
):
    return await run_in_threadpool(
        service.get_external_ratings, title, author, isbn, kind, category
    )
