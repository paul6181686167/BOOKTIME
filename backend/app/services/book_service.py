from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional, List
from ..database import books_collection
from ..utils.security import generate_book_id
from ..models.common import BookCreate, BookUpdate

class BookService:
    
    @staticmethod
    def get_books(user_id: str, category: Optional[str] = None, status: Optional[str] = None, view_mode: Optional[str] = None):
        """Obtenir les livres d'un utilisateur"""
        query = {"user_id": user_id}
        
        if category:
            query["category"] = category
        
        if status:
            query["status"] = status
        
        books = list(books_collection.find(query).sort("date_added", -1))
        
        # Convertir ObjectId en string et nettoyer les données
        for book in books:
            book["_id"] = str(book["_id"])
        
        return books
    
    @staticmethod
    def create_book(user_id: str, book_data: BookCreate):
        """Créer un nouveau livre"""
        book_id = generate_book_id()
        
        book_doc = {
            "id": book_id,
            "user_id": user_id,
            "title": book_data.title,
            "author": book_data.author,
            "category": book_data.category,
            "description": book_data.description,
            "total_pages": book_data.total_pages,
            "current_page": book_data.current_page,
            "status": book_data.status,
            "rating": book_data.rating,
            "review": book_data.review,
            "cover_url": book_data.cover_url,
            "saga": book_data.saga,
            "volume_number": book_data.volume_number,
            "genre": book_data.genre,
            "publication_year": book_data.publication_year,
            "publisher": book_data.publisher,
            "isbn": book_data.isbn,
            "auto_added": book_data.auto_added,
            "date_added": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Ajouter dates conditionnelles
        if book_data.status == "reading":
            book_doc["date_started"] = datetime.utcnow()
        elif book_data.status == "completed":
            book_doc["date_completed"] = datetime.utcnow()
        
        books_collection.insert_one(book_doc)
        
        # Retourner le livre créé
        book_doc["_id"] = str(book_doc["_id"])
        return book_doc
    
    @staticmethod
    def update_book(user_id: str, book_id: str, book_data: BookUpdate):
        """Mettre à jour un livre"""
        # Vérifier que le livre appartient à l'utilisateur
        existing_book = books_collection.find_one({"id": book_id, "user_id": user_id})
        if not existing_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Livre non trouvé"
            )
        
        # Préparer les données de mise à jour
        update_data = {k: v for k, v in book_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        # Gérer les dates de statut
        if "status" in update_data:
            if update_data["status"] == "reading" and existing_book.get("status") != "reading":
                update_data["date_started"] = datetime.utcnow()
            elif update_data["status"] == "completed" and existing_book.get("status") != "completed":
                update_data["date_completed"] = datetime.utcnow()
        
        books_collection.update_one(
            {"id": book_id, "user_id": user_id},
            {"$set": update_data}
        )
        
        # Retourner le livre mis à jour
        updated_book = books_collection.find_one({"id": book_id, "user_id": user_id})
        updated_book["_id"] = str(updated_book["_id"])
        return updated_book
    
    @staticmethod
    def delete_book(user_id: str, book_id: str):
        """Supprimer un livre"""
        result = books_collection.delete_one({"id": book_id, "user_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Livre non trouvé"
            )
        
        return {"message": "Livre supprimé avec succès"}
    
    @staticmethod
    def get_book(user_id: str, book_id: str):
        """Obtenir un livre spécifique"""
        book = books_collection.find_one({"id": book_id, "user_id": user_id})
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Livre non trouvé"
            )
        
        book["_id"] = str(book["_id"])
        return book