from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any

class VolumeData(BaseModel):
    volume_number: int
    volume_title: str
    is_read: bool = False
    date_read: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None

class SeriesLibraryCreate(BaseModel):
    series_name: str
    authors: List[str]
    category: str
    volumes: List[VolumeData]
    total_volumes: int = 0
    description_fr: str = ""
    cover_image_url: str = ""
    first_published: str = ""
    last_published: str = ""
    publisher: str = ""
    series_status: str = "to_read"

class TomeStatus(BaseModel):
    """Statut d'un tome individuel (accepte camelCase du frontend)."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    status: str = "non_lu"   # "non_lu" | "en_cours" | "lu"
    current_page: Optional[int] = Field(default=None, alias="currentPage")
    rating: Optional[int] = None
    review: Optional[str] = None

class SeriesReadingPreferences(BaseModel):
    series_name: str
    read_tomes: List[int] = []          # Rétrocompatibilité
    tome_statuses: Optional[Dict[str, TomeStatus]] = None  # {"1": {status, current_page}, ...}

class SeriesReadingPreferencesUpdate(BaseModel):
    read_tomes: List[int] = []
    tome_statuses: Optional[Dict[str, TomeStatus]] = None