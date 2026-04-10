# Modèles communs pour BOOKTIME
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class HealthResponse(BaseModel):
    """Modèle pour la réponse de santé"""
    status: str = "ok"
    database: str = "connected"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"

class StatsResponse(BaseModel):
    """Modèle pour les statistiques"""
    total_books: int
    completed_books: int
    reading_books: int
    to_read_books: int
    categories: Dict[str, int]
    authors_count: int
    sagas_count: int
    auto_added_count: int

class AuthorStats(BaseModel):
    """Modèle pour les statistiques d'auteur"""
    author: str
    books_count: int
    completed_books: int
    categories: List[str]
    sagas: List[str]

class SagaStats(BaseModel):
    """Modèle pour les statistiques de saga"""
    saga: str
    books_count: int
    completed_books: int
    next_volume: Optional[int] = None
    author: str
    category: str
    completion_percentage: float

class OpenLibraryBook(BaseModel):
    """Modèle pour un livre Open Library"""
    title: str
    author: str
    category: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    pages: Optional[int] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    language: Optional[str] = None
    
    # Champs Open Library
    ol_key: str
    ol_work_id: Optional[str] = None
    ol_edition_id: Optional[str] = None
    
    # Métadonnées de recherche
    search_score: Optional[float] = None
    relevance_level: Optional[str] = None

class OpenLibrarySearchResponse(BaseModel):
    """Modèle pour la réponse de recherche Open Library"""
    books: List[OpenLibraryBook]
    total: int
    query: str
    page: int
    limit: int
    has_next: bool
    has_previous: bool

class ErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class SuccessResponse(BaseModel):
    """Modèle pour les réponses de succès"""
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginationParams(BaseModel):
    """Modèle pour les paramètres de pagination"""
    page: int = Field(1, ge=1, description="Numéro de page")
    limit: int = Field(10, ge=1, le=100, description="Nombre d'éléments par page")
    offset: int = Field(0, ge=0, description="Décalage")

class FilterParams(BaseModel):
    """Modèle pour les paramètres de filtrage"""
    category: Optional[str] = Field(None, description="Filtrer par catégorie")
    status: Optional[str] = Field(None, description="Filtrer par statut")
    author: Optional[str] = Field(None, description="Filtrer par auteur")
    saga: Optional[str] = Field(None, description="Filtrer par saga")
    genre: Optional[str] = Field(None, description="Filtrer par genre")
    language: Optional[str] = Field(None, description="Filtrer par langue")
    year_start: Optional[int] = Field(None, ge=1000, le=2030, description="Année de début")
    year_end: Optional[int] = Field(None, ge=1000, le=2030, description="Année de fin")

class SearchParams(BaseModel):
    """Modèle pour les paramètres de recherche"""
    q: str = Field(..., min_length=1, max_length=100, description="Terme de recherche")
    category: Optional[str] = Field(None, description="Filtrer par catégorie")
    author: Optional[str] = Field(None, description="Filtrer par auteur")
    language: Optional[str] = Field(None, description="Filtrer par langue")
    year_start: Optional[int] = Field(None, ge=1000, le=2030, description="Année de début")
    year_end: Optional[int] = Field(None, ge=1000, le=2030, description="Année de fin")
    min_pages: Optional[int] = Field(None, ge=1, description="Nombre minimum de pages")
    max_pages: Optional[int] = Field(None, ge=1, description="Nombre maximum de pages")
    limit: int = Field(10, ge=1, le=100, description="Nombre de résultats")
    offset: int = Field(0, ge=0, description="Décalage")

class BulkOperationResult(BaseModel):
    """Modèle pour les résultats d'opérations en lot"""
    total: int
    successful: int
    failed: int
    errors: List[str]
    created_ids: List[str]
    updated_ids: List[str]
    deleted_ids: List[str]

class ValidationError(BaseModel):
    """Modèle pour les erreurs de validation"""
    field: str
    message: str
    value: Optional[Any] = None

class ValidationErrorResponse(BaseModel):
    """Modèle pour les réponses d'erreur de validation"""
    error: str = "Validation Error"
    details: List[ValidationError]
    timestamp: datetime = Field(default_factory=datetime.now)