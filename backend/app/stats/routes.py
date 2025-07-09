from fastapi import APIRouter, Depends
from ..database.connection import books_collection
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Obtenir les statistiques de l'utilisateur"""
    user_filter = {"user_id": current_user["id"]}
    
    total_books = books_collection.count_documents(user_filter)
    completed_books = books_collection.count_documents({**user_filter, "status": "completed"})
    reading_books = books_collection.count_documents({**user_filter, "status": "reading"})
    to_read_books = books_collection.count_documents({**user_filter, "status": "to_read"})
    
    # Compter par catégorie
    roman_count = books_collection.count_documents({**user_filter, "category": "roman"})
    bd_count = books_collection.count_documents({**user_filter, "category": "bd"})
    manga_count = books_collection.count_documents({**user_filter, "category": "manga"})
    
    # Compter les auteurs uniques
    authors = books_collection.distinct("author", user_filter)
    authors_count = len([a for a in authors if a])
    
    # Compter les sagas
    sagas = books_collection.distinct("saga", {**user_filter, "saga": {"$ne": ""}})
    sagas_count = len(sagas)
    
    # Compter les livres auto-ajoutés
    auto_added_count = books_collection.count_documents({**user_filter, "auto_added": True})
    
    return {
        "total_books": total_books,
        "completed_books": completed_books,
        "reading_books": reading_books,
        "to_read_books": to_read_books,
        "categories": {
            "roman": roman_count,
            "bd": bd_count,
            "manga": manga_count
        },
        "authors_count": authors_count,
        "sagas_count": sagas_count,
        "auto_added_count": auto_added_count
    }