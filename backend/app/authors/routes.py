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
    """Obtenir les livres d'un auteur spécifique organisés par séries puis livres individuels"""
    
    # Récupérer tous les livres de l'auteur
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "author": author_name
    }, {"_id": 0}))
    
    # Organiser par séries et livres individuels
    series_books = {}
    individual_books = []
    
    for book in books:
        if book.get("saga") and book.get("saga").strip():
            # Livre faisant partie d'une série
            saga_name = book["saga"]
            if saga_name not in series_books:
                series_books[saga_name] = []
            series_books[saga_name].append(book)
        else:
            # Livre individuel
            individual_books.append(book)
    
    # Trier les livres de chaque série par volume_number puis par date de publication
    sorted_series = []
    for saga_name, saga_books in series_books.items():
        # Trier par volume_number d'abord, puis par publication_year
        saga_books.sort(key=lambda x: (
            x.get("volume_number", 0),
            x.get("publication_year", 0)
        ))
        
        # Calculer les statistiques de la série
        total_volumes = len(saga_books)
        completed_volumes = sum(1 for book in saga_books if book.get("status") == "completed")
        reading_volumes = sum(1 for book in saga_books if book.get("status") == "reading")
        to_read_volumes = sum(1 for book in saga_books if book.get("status") == "to_read")
        
        sorted_series.append({
            "name": saga_name,
            "type": "series",
            "books": saga_books,
            "total_volumes": total_volumes,
            "completed_volumes": completed_volumes,
            "reading_volumes": reading_volumes,
            "to_read_volumes": to_read_volumes,
            "first_published": min((book.get("publication_year", 9999) for book in saga_books if book.get("publication_year")), default=None),
            "last_published": max((book.get("publication_year", 0) for book in saga_books if book.get("publication_year")), default=None)
        })
    
    # Trier les séries par date de première publication
    sorted_series.sort(key=lambda x: x.get("first_published", 9999))
    
    # Trier les livres individuels par date de publication
    individual_books.sort(key=lambda x: x.get("publication_year", 9999))
    
    # Organiser les livres individuels
    organized_individual_books = []
    for book in individual_books:
        organized_individual_books.append({
            "type": "individual",
            "book": book
        })
    
    return {
        "author": author_name,
        "series": sorted_series,
        "individual_books": organized_individual_books,
        "total_books": len(books),
        "total_series": len(sorted_series),
        "total_individual_books": len(individual_books)
    }