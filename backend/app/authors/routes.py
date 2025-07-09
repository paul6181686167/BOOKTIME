from fastapi import APIRouter, Depends
from ..database.connection import books_collection
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/authors", tags=["authors"])

@router.get("")
async def get_authors(current_user: dict = Depends(get_current_user)):
    """Obtenir la liste des auteurs avec leurs livres"""
    user_filter = {"user_id": current_user["id"]}
    
    # Grouper les livres par auteur
    pipeline = [
        {"$match": user_filter},
        {"$group": {
            "_id": "$author",
            "total_books": {"$sum": 1},
            "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "reading_books": {"$sum": {"$cond": [{"$eq": ["$status", "reading"]}, 1, 0]}},
            "to_read_books": {"$sum": {"$cond": [{"$eq": ["$status", "to_read"]}, 1, 0]}},
            "categories": {"$addToSet": "$category"},
            "last_read": {"$max": "$date_completed"}
        }},
        {"$sort": {"total_books": -1}}
    ]
    
    authors_data = list(books_collection.aggregate(pipeline))
    
    # Nettoyer les données
    authors = []
    for author_data in authors_data:
        if author_data["_id"]:  # Exclure les auteurs vides
            authors.append({
                "name": author_data["_id"],
                "total_books": author_data["total_books"],
                "completed_books": author_data["completed_books"],
                "reading_books": author_data["reading_books"],
                "to_read_books": author_data["to_read_books"],
                "categories": author_data["categories"],
                "last_read": author_data["last_read"]
            })
    
    return authors

@router.get("/{author_name}/books")
async def get_author_books(author_name: str, current_user: dict = Depends(get_current_user)):
    """Obtenir les livres d'un auteur spécifique"""
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "author": author_name
    }, {"_id": 0}))
    
    return books