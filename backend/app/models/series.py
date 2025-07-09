from pydantic import BaseModel
from typing import Optional, List

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