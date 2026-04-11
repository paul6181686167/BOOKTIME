from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class VolumeData(BaseModel):
    volume_number: int
    volume_title: str
    is_read: bool = False
    date_read: Optional[str] = None

class SeriesLibraryCreate(BaseModel):
    series_name: str
    authors: List[str]
    category: str
    volumes: List[VolumeData]
    description_fr: str = ""
    cover_image_url: str = ""
    first_published: str = ""
    last_published: str = ""
    publisher: str = ""
    series_status: str = "to_read"

class TomeStatus(BaseModel):
    """Statut d'un tome individuel."""
    status: str = "non_lu"   # "non_lu" | "en_cours" | "lu"
    current_page: Optional[int] = None

class SeriesReadingPreferences(BaseModel):
    series_name: str
    read_tomes: List[int] = []          # Rétrocompatibilité
    tome_statuses: Optional[Dict[str, TomeStatus]] = None  # {"1": {status, current_page}, ...}

class SeriesReadingPreferencesUpdate(BaseModel):
    read_tomes: List[int] = []
    tome_statuses: Optional[Dict[str, TomeStatus]] = None