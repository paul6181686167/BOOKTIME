from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import Optional
import uuid
import re
from ..models.book import BookCreate, BookUpdate
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from ..utils.validation import validate_category
from ..services.pagination import PaginatedResponse, PaginationService

router = APIRouter(prefix="/api/books", tags=["books"])

# Instance du service de pagination
pagination_service = PaginationService()

@router.get("", response_model=PaginatedResponse)
async def get_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    view_mode: Optional[str] = "books",  # "books" ou "series"
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    sort_by: str = Query("date_added", description="Champ de tri"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri"),
    current_user: dict = Depends(get_current_user)
):
    """
    Route mise à jour avec pagination optimisée par les indexes MongoDB.
    Utilise les indexes stratégiques créés en Phase 2.1.
    """
    # Si le mode série est demandé, déléguer aux séries avec pagination
    if view_mode == "series":
        from ..series.routes import get_library_series_paginated
        return await get_library_series_paginated(
            category=category,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user=current_user
        )
    
    # Mode livres avec pagination optimisée
    try:
        result = pagination_service.get_paginated_books(
            user_id=current_user["id"],
            category=category,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            exclude_series=True  # Exclure livres faisant partie d'une série
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération livres: {str(e)}")

@router.get("/all", response_model=PaginatedResponse)
async def get_all_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    saga: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments par page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    sort_by: str = Query("date_added", description="Champ de tri"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri"),
    current_user: dict = Depends(get_current_user)
):
    """
    Nouveau endpoint pour récupérer TOUS les livres (incluant ceux des séries) 
    avec pagination et filtres avancés optimisés par indexes.
    """
    try:
        result = pagination_service.get_paginated_books(
            user_id=current_user["id"],
            category=category,
            status=status,
            author=author,
            saga=saga,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            exclude_series=False  # Inclure tous les livres
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération livres: {str(e)}")

@router.get("/search-grouped")
async def search_books_grouped(
    q: str,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche de livres avec regroupement intelligent par saga - SÉRIE FIRST
    """
    if not q or len(q.strip()) < 2:
        return {"results": [], "total_books": 0, "total_sagas": 0, "search_term": q}
    
    search_term = q.strip().lower()
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    
    # Recherche dans tous les champs pertinents
    search_filter = {
        "$or": [
            {"title": {"$regex": re.escape(search_term), "$options": "i"}},
            {"author": {"$regex": re.escape(search_term), "$options": "i"}},
            {"saga": {"$regex": re.escape(search_term), "$options": "i"}},
            {"description": {"$regex": re.escape(search_term), "$options": "i"}},
            {"genre": {"$regex": re.escape(search_term), "$options": "i"}},
            {"publisher": {"$regex": re.escape(search_term), "$options": "i"}}
        ]
    }
    
    # Combiner les filtres
    final_filter = {"$and": [filter_dict, search_filter]}
    
    # Récupérer tous les livres qui correspondent
    matching_books = list(books_collection.find(final_filter, {"_id": 0}))
    
    # Grouper par saga en privilégiant les séries
    saga_groups = {}
    isolated_books = []
    
    for book in matching_books:
        saga = book.get("saga", "").strip()
        if saga:
            if saga not in saga_groups:
                saga_groups[saga] = []
            saga_groups[saga].append(book)
        else:
            isolated_books.append(book)
    
    # Construire les résultats avec les séries en premier
    results = []
    
    # Ajouter les séries comme entités uniques
    for saga_name, saga_books in saga_groups.items():
        saga_books_sorted = sorted(saga_books, key=lambda b: b.get("volume_number", 0))
        
        # Calculer la progression de la série
        total_books = len(saga_books)
        completed_books = len([b for b in saga_books if b.get("status") == "completed"])
        reading_books = len([b for b in saga_books if b.get("status") == "reading"])
        
        # Prendre les infos de base du premier livre
        first_book = saga_books_sorted[0]
        
        series_entity = {
            "id": f"series_{saga_name.replace(' ', '_').lower()}",
            "type": "series",
            "title": saga_name,
            "author": first_book.get("author"),
            "category": first_book.get("category"),
            "description": first_book.get("description", ""),
            "cover_url": first_book.get("cover_url", ""),
            "genre": first_book.get("genre", ""),
            "total_books": total_books,
            "completed_books": completed_books,
            "reading_books": reading_books,
            "progress_percentage": round((completed_books / total_books) * 100) if total_books > 0 else 0,
            "books": saga_books_sorted,
            "date_added": min(b.get("date_added", datetime.utcnow()) for b in saga_books),
            "last_updated": max(b.get("updated_at", b.get("date_added", datetime.utcnow())) for b in saga_books)
        }
        
        results.append(series_entity)
    
    # Ajouter les livres isolés
    for book in isolated_books:
        book["type"] = "book"
        results.append(book)
    
    # Trier les résultats par date de dernière mise à jour
    results.sort(key=lambda x: x.get("last_updated", x.get("date_added", datetime.utcnow())), reverse=True)
    
    return {
        "results": results,
        "total_books": len(matching_books),
        "total_sagas": len(saga_groups),
        "search_term": q,
        "grouped_by_saga": True,
        "series_first": True
    }

@router.get("/{book_id}")
async def get_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Obtenir un livre par son ID"""
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    return book

@router.post("")
async def create_book(book_data: BookCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouveau livre"""
    # Valider la catégorie
    validated_category = validate_category(book_data.category)
    
    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": current_user["id"],
        **book_data.model_dump(),
        "category": validated_category,
        "date_added": datetime.utcnow(),
        "date_started": None,
        "date_completed": None
    }
    
    # Définir les dates selon le statut
    if book_data.status == "reading":
        book["date_started"] = datetime.utcnow()
    elif book_data.status == "completed":
        book["date_started"] = datetime.utcnow()
        book["date_completed"] = datetime.utcnow()
    
    books_collection.insert_one(book)
    book.pop("_id", None)
    return book

@router.put("/{book_id}")
async def update_book(
    book_id: str, 
    book_update: BookUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un livre"""
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    })
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    update_data = book_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Gérer les changements de statut
    if "status" in update_data:
        current_status = book.get("status")
        new_status = update_data["status"]
        
        if current_status != "reading" and new_status == "reading":
            update_data["date_started"] = datetime.utcnow()
        elif current_status != "completed" and new_status == "completed":
            if not book.get("date_started"):
                update_data["date_started"] = datetime.utcnow()
            update_data["date_completed"] = datetime.utcnow()
    
    books_collection.update_one(
        {"id": book_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    updated_book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    return updated_book

@router.delete("/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un livre"""
    result = books_collection.delete_one({
        "id": book_id, 
        "user_id": current_user["id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    return {"message": "Livre supprimé avec succès"}