from fastapi import APIRouter, Depends, Query
from typing import Optional
from ..services.book_service import BookService
from ..models.common import BookCreate, BookUpdate
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/books", tags=["books"])

@router.get("")
async def get_books(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    view_mode: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Obtenir les livres de l'utilisateur"""
    return BookService.get_books(current_user["id"], category, status, view_mode)

@router.post("")
async def create_book(
    book_data: BookCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau livre"""
    return BookService.create_book(current_user["id"], book_data)

@router.get("/{book_id}")
async def get_book(
    book_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtenir un livre spécifique"""
    return BookService.get_book(current_user["id"], book_id)

@router.put("/{book_id}")
async def update_book(
    book_id: str,
    book_data: BookUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un livre"""
    return BookService.update_book(current_user["id"], book_id, book_data)

@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer un livre"""
    return BookService.delete_book(current_user["id"], book_id)