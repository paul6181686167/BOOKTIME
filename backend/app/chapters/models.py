"""
Modèles Pydantic pour le système de chapitres
============================================

Définit les structures de données pour :
- Chapitres individuels
- Volumes/Tomes
- Séries avec chapitres
- Prédictions et métadonnées
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChapterStatus(str, Enum):
    """Statuts possibles des chapitres"""
    RELEASED = "released"
    UPCOMING = "upcoming" 
    PREDICTED = "predicted"
    DELAYED = "delayed"


class VolumeStatus(str, Enum):
    """Statuts possibles des volumes"""
    RELEASED = "released"
    UPCOMING = "upcoming"
    COLLECTING = "collecting"  # En cours de collection des chapitres
    EXPECTED = "expected"      # ✅ AJOUTÉ : Volume attendu mais pas encore de chapitres


class DateConfidence(str, Enum):
    """Niveau de fiabilité d'une date de sortie de tome."""
    CONFIRMED = "confirmed"   # Date officielle (Wikidata / Google Books)
    ESTIMATED = "estimated"   # Date déduite (heuristique)
    UNKNOWN = "unknown"       # Aucune date fiable


class ReleaseSchedule(str, Enum):
    """Types de planning de sortie"""
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    IRREGULAR = "irregular"


class SourceFormat(str, Enum):
    """Formats source de publication"""
    MANGA = "manga"        # ✅ AJOUTÉ : Format manga standard
    MAGAZINE = "magazine"
    WEBTOON = "webtoon" 
    ONESHOT = "oneshot"
    TANKOUBON = "tankoubon"


class Chapter(BaseModel):
    """Modèle pour un chapitre individuel"""
    id: str = Field(..., description="Identifiant unique du chapitre")
    chapter_number: float = Field(..., description="Numéro du chapitre (peut être décimal)")
    title: Optional[str] = Field(None, description="Titre du chapitre")
    release_date: Optional[datetime] = Field(None, description="Date de sortie")
    status: ChapterStatus = Field(ChapterStatus.RELEASED, description="Statut du chapitre")
    volume_number: Optional[int] = Field(None, description="Numéro du volume contenant ce chapitre")
    url: Optional[str] = Field(None, description="URL du chapitre")
    source_format: SourceFormat = Field(SourceFormat.MANGA, description="Format source")
    
    # Métadonnées supplémentaires  
    page_count: Optional[int] = Field(None, description="Nombre de pages")
    translated_languages: List[str] = Field(default_factory=list, description="Langues de traduction disponibles")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ch-1101-uuid",
                "chapter_number": 1101,
                "title": "Heavy Rotation",
                "release_date": "2024-01-15T00:00:00Z",
                "status": "released",
                "volume_number": None,
                "url": "https://example.com/chapter/1101",
                "source_format": "manga",
                "page_count": 17,
                "translated_languages": ["en", "fr"]
            }
        }
    )


class Volume(BaseModel):
    """Modèle pour un volume/tome"""
    volume_number: int = Field(..., description="Numéro du volume")
    chapters_range: str = Field(..., description="Range des chapitres (ex: '1095-1105')")
    chapters_included: List[float] = Field(default_factory=list, description="Liste des numéros de chapitres")
    release_date: Optional[datetime] = Field(None, description="Date de sortie (estimée ou confirmée) du volume")
    status: VolumeStatus = Field(VolumeStatus.UPCOMING, description="Statut du volume")

    # Sortie officielle confirmée (Wikidata / Google Books), distincte de l'estimation.
    confirmed_release_date: Optional[datetime] = Field(
        None, description="Date de publication officielle confirmée du tome"
    )
    date_confidence: DateConfidence = Field(
        DateConfidence.UNKNOWN, description="Fiabilité de la date de sortie"
    )
    date_source: Optional[str] = Field(
        None, description="Source de la date confirmée (ex: 'wikidata', 'google_books')"
    )

    # Métadonnées
    isbn: Optional[str] = Field(None, description="ISBN du volume")
    cover_url: Optional[str] = Field(None, description="URL de la couverture")
    page_count: Optional[int] = Field(None, description="Nombre de pages total")

    def is_released(self, as_of: Optional[datetime] = None) -> bool:
        """
        Vrai si le tome est réellement sorti : une date **confirmée** existe et
        est déjà passée. Les dates simplement estimées ne suffisent pas.
        """
        if self.date_confidence != DateConfidence.CONFIRMED or not self.confirmed_release_date:
            return False
        reference = as_of or datetime.now(self.confirmed_release_date.tzinfo)
        return self.confirmed_release_date <= reference

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "volume_number": 108,
                "chapters_range": "1095-1105",
                "chapters_included": [1095, 1096, 1097, 1098, 1099, 1100, 1101, 1102, 1103, 1104, 1105],
                "release_date": "2024-03-15T00:00:00Z",
                "confirmed_release_date": "2024-03-15T00:00:00Z",
                "date_confidence": "confirmed",
                "date_source": "wikidata",
                "status": "released",
                "isbn": "978-4-08-883066-2",
                "cover_url": None,
                "page_count": 192
            }
        }
    )


class ChapterPrediction(BaseModel):
    """Modèle pour les prédictions de chapitres"""
    estimated_number: float = Field(..., description="Numéro estimé du prochain chapitre")
    estimated_date: Optional[datetime] = Field(None, description="Date estimée de sortie")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance de la prédiction (0-1)")
    method: str = Field(..., description="Méthode utilisée pour la prédiction")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estimated_number": 1102,
                "estimated_date": "2024-01-22T00:00:00Z",
                "confidence": 0.95,
                "method": "weekly_pattern"
            }
        }
    )


class VolumePrediction(BaseModel):
    """Modèle pour les prédictions de volumes"""
    estimated_number: int = Field(..., description="Numéro estimé du prochain volume")
    estimated_date: Optional[datetime] = Field(None, description="Date estimée de sortie")
    estimated_chapters_range: Optional[str] = Field(None, description="Range estimée des chapitres")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiance de la prédiction")
    method: str = Field(..., description="Méthode utilisée pour la prédiction")


class SeriesChapters(BaseModel):
    """Modèle principal pour une série avec ses chapitres"""
    id: str = Field(..., description="Identifiant unique")
    series_name: str = Field(..., description="Nom de la série")
    
    # IDs externes pour mapping APIs
    manga_id_anilist: Optional[int] = Field(None, description="ID AniList")
    manga_id_mangaupdates: Optional[int] = Field(None, description="ID MangaUpdates")
    manga_id_mal: Optional[int] = Field(None, description="ID MyAnimeList")
    
    # Données chapitres
    current_chapters: List[Chapter] = Field(default_factory=list, description="Chapitres actuels")
    volumes: List[Volume] = Field(default_factory=list, description="Volumes/Tomes")
    
    # Prédictions
    predictions: Dict[str, Any] = Field(default_factory=dict, description="Prédictions diverses")
    next_chapter: Optional[ChapterPrediction] = Field(None, description="Prédiction prochain chapitre")
    next_volume: Optional[VolumePrediction] = Field(None, description="Prédiction prochain volume")
    
    # Métadonnées série
    release_schedule: ReleaseSchedule = Field(ReleaseSchedule.WEEKLY, description="Planning de sortie")
    source_format: SourceFormat = Field(SourceFormat.MAGAZINE, description="Format source")
    country_of_origin: Optional[str] = Field(None, description="Pays d'origine (JP, KR, CN, etc.)")
    
    # Statistiques
    total_chapters_released: int = Field(0, description="Total chapitres sortis")
    total_volumes_released: int = Field(0, description="Total volumes sortis")
    average_chapters_per_volume: Optional[float] = Field(None, description="Moyenne chapitres par volume")
    
    # Cache et timestamps
    last_updated: datetime = Field(default_factory=_utcnow, description="Dernière mise à jour")
    cache_expires: Optional[datetime] = Field(None, description="Expiration du cache")
    last_sync_anilist: Optional[datetime] = Field(None, description="Dernière sync AniList")
    last_sync_mangaupdates: Optional[datetime] = Field(None, description="Dernière sync MangaUpdates")
    
    # Flags de configuration
    enable_predictions: bool = Field(True, description="Activer les prédictions")
    auto_volume_grouping: bool = Field(True, description="Regroupement automatique en volumes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "uuid-string",
                "series_name": "One Piece",
                "manga_id_anilist": 30013,
                "manga_id_mangaupdates": 319,
                "current_chapters": [],
                "volumes": [],
                "predictions": {},
                "release_schedule": "weekly",
                "source_format": "magazine",
                "country_of_origin": "JP",
                "total_chapters_released": 1101,
                "total_volumes_released": 107,
                "average_chapters_per_volume": 10.3,
                "enable_predictions": True,
                "auto_volume_grouping": True
            }
        }
    )


class SeriesChaptersResponse(BaseModel):
    """Modèle de réponse pour l'API"""
    success: bool = Field(True, description="Succès de l'opération")
    data: Optional[SeriesChapters] = Field(None, description="Données de la série")
    message: Optional[str] = Field(None, description="Message d'information")
    last_updated: datetime = Field(default_factory=_utcnow, description="Timestamp de la réponse")
    cached: bool = Field(False, description="Données depuis le cache")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "series_name": "One Piece",
                    "current_chapters": [],
                    "volumes": []
                },
                "message": "Données récupérées avec succès",
                "cached": False
            }
        }
    )


class ChapterSearchResult(BaseModel):
    """Résultat de recherche dans les APIs externes"""
    anilist_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Résultats AniList")
    mangaupdates_matches: List[Dict[str, Any]] = Field(default_factory=list, description="Résultats MangaUpdates")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Scores de confiance")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "anilist_matches": [
                    {"id": 30013, "title": "One Piece", "confidence": 0.98}
                ],
                "mangaupdates_matches": [
                    {"id": 319, "title": "One Piece", "confidence": 0.95}
                ],
                "confidence_scores": {
                    "anilist": 0.98,
                    "mangaupdates": 0.95
                }
            }
        }
    )


class IntegrationStatus(BaseModel):
    """Statut des intégrations externes"""
    status: str = Field(..., description="Statut (ok, error, timeout)")
    response_time: Optional[int] = Field(None, description="Temps de réponse en ms")
    last_success: Optional[datetime] = Field(None, description="Dernière requête réussie")
    error_message: Optional[str] = Field(None, description="Message d'erreur si applicable")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "response_time": 150,
                "last_success": "2024-01-15T10:00:00Z",
                "error_message": None
            }
        }
    )


class UpcomingReleases(BaseModel):
    """Planning des sorties à venir"""
    this_week: List[Dict[str, Any]] = Field(default_factory=list, description="Sorties cette semaine")
    next_week: List[Dict[str, Any]] = Field(default_factory=list, description="Sorties semaine prochaine") 
    this_month: List[Dict[str, Any]] = Field(default_factory=list, description="Sorties ce mois")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "this_week": [
                    {
                        "series_name": "One Piece",
                        "chapter_number": 1102,
                        "estimated_date": "2024-01-22",
                        "confidence": 0.95
                    }
                ],
                "next_week": [],
                "this_month": []
            }
        }
    )