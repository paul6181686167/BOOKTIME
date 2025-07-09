# Modèles série pour BOOKTIME
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SeriesCreate(BaseModel):
    """Modèle pour la création d'une série"""
    series_name: str = Field(..., min_length=1, max_length=200, description="Nom de la série")
    authors: List[str] = Field(..., min_items=1, description="Liste des auteurs")
    category: str = Field(..., description="Catégorie de la série (roman, bd, manga)")
    volumes: int = Field(..., ge=1, le=1000, description="Nombre de volumes")
    description: Optional[str] = Field(None, max_length=5000, description="Description de la série")
    cover_url: Optional[str] = Field(None, description="URL de la couverture")
    
    # Métadonnées
    first_published: Optional[int] = Field(None, ge=1000, le=2030, description="Année de première publication")
    last_published: Optional[int] = Field(None, ge=1000, le=2030, description="Année de dernière publication")
    publisher: Optional[str] = Field(None, max_length=100, description="Éditeur")
    language: Optional[str] = Field("fr", max_length=5, description="Langue de la série")
    
    # Champs Open Library
    ol_key: Optional[str] = Field(None, description="Clé Open Library")
    ol_work_id: Optional[str] = Field(None, description="ID de l'œuvre Open Library")

class SeriesUpdate(BaseModel):
    """Modèle pour la mise à jour d'une série"""
    series_name: Optional[str] = Field(None, min_length=1, max_length=200)
    authors: Optional[List[str]] = Field(None, min_items=1)
    category: Optional[str] = Field(None)
    volumes: Optional[int] = Field(None, ge=1, le=1000)
    description: Optional[str] = Field(None, max_length=5000)
    cover_url: Optional[str] = Field(None)
    
    # Métadonnées
    first_published: Optional[int] = Field(None, ge=1000, le=2030)
    last_published: Optional[int] = Field(None, ge=1000, le=2030)
    publisher: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=5)

class VolumeStatus(BaseModel):
    """Modèle pour le statut d'un volume"""
    volume_number: int
    is_read: bool
    date_read: Optional[datetime] = None

class SeriesResponse(BaseModel):
    """Modèle pour la réponse série"""
    id: str
    series_name: str
    authors: List[str]
    category: str
    volumes: int
    description: Optional[str] = None
    cover_url: Optional[str] = None
    
    # Progression
    volumes_read: List[VolumeStatus]
    completion_percentage: float
    status: str  # to_read, reading, completed
    
    # Métadonnées
    first_published: Optional[int] = None
    last_published: Optional[int] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    
    # Dates
    date_added: datetime
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    
    # Champs système
    user_id: str
    
    # Champs Open Library
    ol_key: Optional[str] = None
    ol_work_id: Optional[str] = None
    
    class Config:
        from_attributes = True

class SeriesSearchResult(BaseModel):
    """Modèle pour un résultat de recherche de série"""
    name: str
    category: str
    score: float
    keywords: List[str]
    authors: List[str]
    variations: List[str]
    volumes: int
    languages: List[str]
    description: Optional[str] = None
    first_published: Optional[int] = None
    status: str
    
    # Données de recherche
    search_score: Optional[float] = None
    match_reasons: Optional[List[str]] = None

class SeriesSearchResponse(BaseModel):
    """Modèle pour la réponse de recherche de séries"""
    series: List[SeriesSearchResult]
    total: int
    search_term: str

class SeriesDetectionResult(BaseModel):
    """Modèle pour le résultat de détection de série"""
    series_name: str
    category: str
    authors: List[str]
    volumes: int
    description: Optional[str] = None
    confidence: float
    match_reasons: List[str]

class SeriesCompletionRequest(BaseModel):
    """Modèle pour la requête d'auto-complétion de série"""
    series_name: str = Field(..., min_length=1, max_length=200)
    volumes_to_add: int = Field(..., ge=1, le=50, description="Nombre de volumes à ajouter")

class SeriesCompletionResponse(BaseModel):
    """Modèle pour la réponse d'auto-complétion de série"""
    series_name: str
    volumes_added: int
    books_created: List[str]  # IDs des livres créés
    message: str