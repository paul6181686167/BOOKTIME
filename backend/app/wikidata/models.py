"""
Modèles Pydantic pour Wikidata
Structures de données pour séries, livres et auteurs
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class WikidataEntity(BaseModel):
    """Entité Wikidata de base"""
    id: str = Field(..., description="Identifiant Wikidata (ex: Q8337)")
    label: str = Field(..., description="Libellé principal")
    description: Optional[str] = Field(None, description="Description courte")
    url: str = Field(..., description="URL Wikidata")

class WikidataAuthor(BaseModel):
    """Auteur depuis Wikidata"""
    id: str = Field(..., description="Identifiant Wikidata auteur")
    name: str = Field(..., description="Nom complet")
    birth_date: Optional[str] = Field(None, description="Date de naissance")
    death_date: Optional[str] = Field(None, description="Date de décès")
    nationality: Optional[str] = Field(None, description="Nationalité")
    occupation: List[str] = Field(default_factory=list, description="Occupations")
    genres: List[str] = Field(default_factory=list, description="Genres littéraires")
    awards: List[str] = Field(default_factory=list, description="Prix reçus")
    image_url: Optional[str] = Field(None, description="URL image")
    wikipedia_url: Optional[str] = Field(None, description="URL Wikipedia")
    series_count: int = Field(0, description="Nombre de séries")
    books_count: int = Field(0, description="Nombre de livres")

class WikidataBook(BaseModel):
    """Livre depuis Wikidata"""
    id: str = Field(..., description="Identifiant Wikidata livre")
    title: str = Field(..., description="Titre du livre")
    series_id: Optional[str] = Field(None, description="ID série parente")
    series_name: Optional[str] = Field(None, description="Nom série")
    volume_number: Optional[int] = Field(None, description="Numéro dans la série")
    publication_date: Optional[str] = Field(None, description="Date publication")
    genre: Optional[str] = Field(None, description="Genre littéraire")
    language: Optional[str] = Field(None, description="Langue")
    pages: Optional[int] = Field(None, description="Nombre de pages")
    isbn: Optional[str] = Field(None, description="ISBN")
    publisher: Optional[str] = Field(None, description="Éditeur")

class WikidataSeries(BaseModel):
    """Série depuis Wikidata"""
    id: str = Field(..., description="Identifiant Wikidata série")
    name: str = Field(..., description="Nom de la série")
    author_id: str = Field(..., description="ID auteur")
    author_name: str = Field(..., description="Nom auteur")
    genre: Optional[str] = Field(None, description="Genre principal")
    start_date: Optional[str] = Field(None, description="Date début")
    end_date: Optional[str] = Field(None, description="Date fin")
    status: Optional[str] = Field(None, description="Statut (terminée/en cours)")
    volumes_count: int = Field(0, description="Nombre de volumes")
    language: Optional[str] = Field(None, description="Langue principale")
    description: Optional[str] = Field(None, description="Description")
    books: List[WikidataBook] = Field(default_factory=list, description="Livres de la série")

class WikidataSearchResult(BaseModel):
    """Résultat de recherche Wikidata"""
    found: bool = Field(..., description="Résultat trouvé")
    source: str = Field(default="wikidata", description="Source des données")
    query_time: float = Field(..., description="Temps de requête en secondes")
    results_count: int = Field(0, description="Nombre de résultats")

class WikidataAuthorResponse(WikidataSearchResult):
    """Réponse pour un auteur"""
    author: Optional[WikidataAuthor] = Field(None, description="Données auteur")
    series: List[WikidataSeries] = Field(default_factory=list, description="Séries de l'auteur")

class WikidataSeriesResponse(WikidataSearchResult):
    """Réponse pour une série"""
    series: Optional[WikidataSeries] = Field(None, description="Données série")
    books: List[WikidataBook] = Field(default_factory=list, description="Livres de la série")

class WikidataSeriesSearchResponse(WikidataSearchResult):
    """Réponse pour recherche de séries"""
    series: List[WikidataSeries] = Field(default_factory=list, description="Séries trouvées")
    search_term: str = Field(..., description="Terme de recherche")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filtres appliqués")

class WikidataTestResponse(BaseModel):
    """Réponse pour tests de développement"""
    success: bool = Field(..., description="Test réussi")
    query: str = Field(..., description="Requête SPARQL exécutée")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Résultats bruts")
    processed_results: Dict[str, Any] = Field(default_factory=dict, description="Résultats traités")
    execution_time: float = Field(..., description="Temps d'exécution")
    error: Optional[str] = Field(None, description="Erreur éventuelle")