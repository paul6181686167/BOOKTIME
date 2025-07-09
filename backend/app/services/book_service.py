# Service de gestion des livres pour BOOKTIME
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from ..database import books_collection, authors_collection
from ..models.book import BookCreate, BookUpdate, BookResponse, BookSearchResponse
from ..models.common import StatsResponse, AuthorStats, SagaStats
from ..dependencies import build_search_query, get_pagination_params, build_pagination_response
from ..config import VALID_CATEGORIES, VALID_STATUSES

class BookService:
    
    @staticmethod
    def create_book(user_id: str, book_data: BookCreate) -> BookResponse:
        """Crée un nouveau livre"""
        # Valider la catégorie
        if book_data.category.lower() not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        
        # Créer le livre
        book_id = str(uuid.uuid4())
        book_doc = {
            "id": book_id,
            "user_id": user_id,
            "title": book_data.title,
            "author": book_data.author,
            "category": book_data.category.lower(),
            "description": book_data.description,
            "cover_url": book_data.cover_url,
            "pages": book_data.pages,
            "current_page": None,
            "status": "to_read",
            "rating": None,
            "review": None,
            "date_added": datetime.now(),
            "date_started": None,
            "date_completed": None,
            "saga": book_data.saga,
            "volume_number": book_data.volume_number,
            "publication_year": book_data.publication_year,
            "genre": book_data.genre,
            "publisher": book_data.publisher,
            "isbn": book_data.isbn,
            "language": book_data.language or "fr",
            "auto_added": False,
            "ol_key": book_data.ol_key,
            "ol_work_id": book_data.ol_work_id,
            "ol_edition_id": book_data.ol_edition_id
        }
        
        try:
            books_collection.insert_one(book_doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create book"
            )
        
        return BookResponse(**book_doc)
    
    @staticmethod
    def get_book_by_id(user_id: str, book_id: str) -> BookResponse:
        """Récupère un livre par son ID"""
        book = books_collection.find_one({"id": book_id, "user_id": user_id})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return BookResponse(**book)
    
    @staticmethod
    def get_books(user_id: str, category: Optional[str] = None, status: Optional[str] = None,
                  page: int = 1, limit: int = 10) -> BookSearchResponse:
        """Récupère les livres d'un utilisateur avec filtres"""
        # Construire la requête de filtrage
        query = {"user_id": user_id}
        
        if category:
            if category.lower() not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
                )
            query["category"] = category.lower()
        
        if status:
            if status.lower() not in VALID_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status must be one of: {', '.join(VALID_STATUSES)}"
                )
            query["status"] = status.lower()
        
        # Pagination
        pagination = get_pagination_params(page, limit)
        
        # Récupérer les livres
        try:
            total = books_collection.count_documents(query)
            books = list(books_collection.find(query)
                        .skip(pagination["skip"])
                        .limit(pagination["limit"])
                        .sort("date_added", -1))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve books"
            )
        
        # Convertir en réponses
        book_responses = [BookResponse(**book) for book in books]
        
        # Métadonnées de pagination
        pagination_meta = build_pagination_response(total, page, limit)
        
        return BookSearchResponse(
            books=book_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=pagination_meta["has_next"],
            has_previous=pagination_meta["has_previous"]
        )
    
    @staticmethod
    def update_book(user_id: str, book_id: str, update_data: BookUpdate) -> BookResponse:
        """Met à jour un livre"""
        # Vérifier si le livre existe
        book = books_collection.find_one({"id": book_id, "user_id": user_id})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Préparer les données de mise à jour
        update_dict = update_data.dict(exclude_unset=True)
        
        # Valider la catégorie si fournie
        if "category" in update_dict:
            if update_dict["category"].lower() not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
                )
            update_dict["category"] = update_dict["category"].lower()
        
        # Valider le statut si fourni
        if "status" in update_dict:
            if update_dict["status"].lower() not in VALID_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Status must be one of: {', '.join(VALID_STATUSES)}"
                )
            update_dict["status"] = update_dict["status"].lower()
            
            # Gérer les dates selon le statut
            if update_dict["status"] == "reading" and not book.get("date_started"):
                update_dict["date_started"] = datetime.now()
            elif update_dict["status"] == "completed":
                if not book.get("date_started"):
                    update_dict["date_started"] = datetime.now()
                update_dict["date_completed"] = datetime.now()
        
        # Mettre à jour le livre
        try:
            books_collection.update_one(
                {"id": book_id, "user_id": user_id},
                {"$set": update_dict}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update book"
            )
        
        # Récupérer le livre mis à jour
        updated_book = books_collection.find_one({"id": book_id, "user_id": user_id})
        return BookResponse(**updated_book)
    
    @staticmethod
    def delete_book(user_id: str, book_id: str) -> dict:
        """Supprime un livre"""
        # Vérifier si le livre existe
        book = books_collection.find_one({"id": book_id, "user_id": user_id})
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        
        # Supprimer le livre
        try:
            result = books_collection.delete_one({"id": book_id, "user_id": user_id})
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete book"
            )
        
        return {"message": "Book deleted successfully"}
    
    @staticmethod
    def get_stats(user_id: str) -> StatsResponse:
        """Récupère les statistiques d'un utilisateur"""
        try:
            # Statistiques globales
            total_books = books_collection.count_documents({"user_id": user_id})
            completed_books = books_collection.count_documents({"user_id": user_id, "status": "completed"})
            reading_books = books_collection.count_documents({"user_id": user_id, "status": "reading"})
            to_read_books = books_collection.count_documents({"user_id": user_id, "status": "to_read"})
            
            # Statistiques par catégorie
            categories = {}
            for category in VALID_CATEGORIES:
                count = books_collection.count_documents({"user_id": user_id, "category": category})
                categories[category] = count
            
            # Autres statistiques
            authors_count = len(books_collection.distinct("author", {"user_id": user_id}))
            sagas_count = len(books_collection.distinct("saga", {"user_id": user_id, "saga": {"$ne": None}}))
            auto_added_count = books_collection.count_documents({"user_id": user_id, "auto_added": True})
            
            return StatsResponse(
                total_books=total_books,
                completed_books=completed_books,
                reading_books=reading_books,
                to_read_books=to_read_books,
                categories=categories,
                authors_count=authors_count,
                sagas_count=sagas_count,
                auto_added_count=auto_added_count
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve statistics"
            )
    
    @staticmethod
    def get_authors(user_id: str) -> List[AuthorStats]:
        """Récupère les statistiques des auteurs"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$author",
                    "books_count": {"$sum": 1},
                    "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                    "categories": {"$addToSet": "$category"},
                    "sagas": {"$addToSet": "$saga"}
                }},
                {"$sort": {"books_count": -1}}
            ]
            
            authors = list(books_collection.aggregate(pipeline))
            
            return [
                AuthorStats(
                    author=author["_id"],
                    books_count=author["books_count"],
                    completed_books=author["completed_books"],
                    categories=[cat for cat in author["categories"] if cat],
                    sagas=[saga for saga in author["sagas"] if saga]
                )
                for author in authors
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve authors"
            )
    
    @staticmethod
    def get_sagas(user_id: str) -> List[SagaStats]:
        """Récupère les statistiques des sagas"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "saga": {"$ne": None}}},
                {"$group": {
                    "_id": "$saga",
                    "books_count": {"$sum": 1},
                    "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                    "author": {"$first": "$author"},
                    "category": {"$first": "$category"},
                    "volumes": {"$push": "$volume_number"}
                }},
                {"$sort": {"books_count": -1}}
            ]
            
            sagas = list(books_collection.aggregate(pipeline))
            
            saga_stats = []
            for saga in sagas:
                volumes = [v for v in saga["volumes"] if v is not None]
                next_volume = None
                if volumes:
                    volumes.sort()
                    next_volume = max(volumes) + 1
                
                completion_percentage = (saga["completed_books"] / saga["books_count"]) * 100
                
                saga_stats.append(SagaStats(
                    saga=saga["_id"],
                    books_count=saga["books_count"],
                    completed_books=saga["completed_books"],
                    next_volume=next_volume,
                    author=saga["author"],
                    category=saga["category"],
                    completion_percentage=completion_percentage
                ))
            
            return saga_stats
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sagas"
            )
    
    @staticmethod
    def search_books(user_id: str, query: str, page: int = 1, limit: int = 10) -> BookSearchResponse:
        """Recherche des livres"""
        if not query or len(query.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long"
            )
        
        # Construire la requête de recherche
        search_query = build_search_query(query, ["title", "author", "saga", "genre"])
        search_query["user_id"] = user_id
        
        # Pagination
        pagination = get_pagination_params(page, limit)
        
        try:
            total = books_collection.count_documents(search_query)
            books = list(books_collection.find(search_query)
                        .skip(pagination["skip"])
                        .limit(pagination["limit"])
                        .sort("date_added", -1))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search books"
            )
        
        # Convertir en réponses
        book_responses = [BookResponse(**book) for book in books]
        
        # Métadonnées de pagination
        pagination_meta = build_pagination_response(total, page, limit)
        
        return BookSearchResponse(
            books=book_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=pagination_meta["has_next"],
            has_previous=pagination_meta["has_previous"]
        )

# Instance du service
book_service = BookService()