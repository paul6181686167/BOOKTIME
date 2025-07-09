# Modèles livre pour BOOKTIME
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BookCreate(BaseModel):
    """Modèle pour la création d'un livre"""
    title: str = Field(..., min_length=1, max_length=200, description="Titre du livre")
    author: str = Field(..., min_length=1, max_length=100, description="Auteur du livre")
    category: str = Field(..., description="Catégorie du livre (roman, bd, manga)")
    description: Optional[str] = Field(None, max_length=2000, description="Description du livre")
    cover_url: Optional[str] = Field(None, description="URL de la couverture")
    pages: Optional[int] = Field(None, ge=1, le=10000, description="Nombre de pages")
    publication_year: Optional[int] = Field(None, ge=1000, le=2030, description="Année de publication")
    genre: Optional[str] = Field(None, max_length=50, description="Genre du livre")
    publisher: Optional[str] = Field(None, max_length=100, description="Éditeur")
    isbn: Optional[str] = Field(None, max_length=20, description="ISBN")
    language: Optional[str] = Field("fr", max_length=5, description="Langue du livre")
    
    # Champs spécifiques aux séries
    saga: Optional[str] = Field(None, max_length=200, description="Nom de la série/saga")
    volume_number: Optional[int] = Field(None, ge=1, le=1000, description="Numéro de volume")
    
    # Champs Open Library
    ol_key: Optional[str] = Field(None, description="Clé Open Library")
    ol_work_id: Optional[str] = Field(None, description="ID de l'œuvre Open Library")
    ol_edition_id: Optional[str] = Field(None, description="ID de l'édition Open Library")

class BookUpdate(BaseModel):
    """Modèle pour la mise à jour d'un livre"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, description="Catégorie du livre (roman, bd, manga)")
    description: Optional[str] = Field(None, max_length=2000)
    cover_url: Optional[str] = Field(None)
    pages: Optional[int] = Field(None, ge=1, le=10000)
    current_page: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, description="Statut de lecture (to_read, reading, completed)")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Note sur 5")
    review: Optional[str] = Field(None, max_length=2000, description="Avis sur le livre")
    
    # Dates
    date_started: Optional[datetime] = Field(None, description="Date de début de lecture")
    date_completed: Optional[datetime] = Field(None, description="Date de fin de lecture")
    
    # Champs série
    saga: Optional[str] = Field(None, max_length=200)
    volume_number: Optional[int] = Field(None, ge=1, le=1000)
    
    # Métadonnées
    publication_year: Optional[int] = Field(None, ge=1000, le=2030)
    genre: Optional[str] = Field(None, max_length=50)
    publisher: Optional[str] = Field(None, max_length=100)
    isbn: Optional[str] = Field(None, max_length=20)
    language: Optional[str] = Field(None, max_length=5)

class BookResponse(BaseModel):
    """Modèle pour la réponse livre"""
    id: str
    title: str
    author: str
    category: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    pages: Optional[int] = None
    current_page: Optional[int] = None
    status: str = "to_read"
    rating: Optional[int] = None
    review: Optional[str] = None
    
    # Dates
    date_added: datetime
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    
    # Champs série
    saga: Optional[str] = None
    volume_number: Optional[int] = None
    
    # Métadonnées
    publication_year: Optional[int] = None
    genre: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    language: Optional[str] = None
    
    # Champs système
    user_id: str
    auto_added: bool = False
    
    # Champs Open Library
    ol_key: Optional[str] = None
    ol_work_id: Optional[str] = None
    ol_edition_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class BookSearchResponse(BaseModel):
    """Modèle pour la réponse de recherche de livres"""
    books: List[BookResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool