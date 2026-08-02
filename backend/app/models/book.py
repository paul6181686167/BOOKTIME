from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BookCreate(BaseModel):
    title: str
    author: str
    original_title: Optional[str] = None   # Titre dans la langue d'origine
    category: str = "roman"
    description: str = ""
    total_pages: Optional[int] = None
    status: str = "to_read"
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: str = ""
    cover_url: str = ""
    saga: str = ""
    volume_number: Optional[int] = None
    genre: str = ""
    publication_year: Optional[int] = None
    publish_date: Optional[str] = None       # Date de sortie complète ISO (jour/mois si connus)
    date_confidence: Optional[str] = None    # exact | month | year | estimated | unknown
    watchlist: bool = False                  # Livre "à surveiller" (sortie à venir)
    publisher: str = ""
    isbn: str = ""
    auto_added: bool = False
    is_series: Optional[bool] = False
    language: Optional[str] = "fr"
    ol_key: Optional[str] = None
    ol_work_id: Optional[str] = None
    ol_edition_id: Optional[str] = None

class BookUpdate(BaseModel):
    title: Optional[str] = None
    original_title: Optional[str] = None
    status: Optional[str] = None
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    notes: Optional[str] = None
    description: Optional[str] = None
    total_pages: Optional[int] = None
    category: Optional[str] = None
    cover_url: Optional[str] = None
    language: Optional[str] = None
    publish_date: Optional[str] = None
    date_confidence: Optional[str] = None
    watchlist: Optional[bool] = None

class BookResponse(BaseModel):
    id: str
    user_id: str
    title: str
    original_title: Optional[str] = None
    author: str
    category: str
    description: str
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    status: str
    rating: Optional[int] = None
    review: str
    cover_url: str
    saga: str
    volume_number: Optional[int] = None
    genre: str
    publication_year: Optional[int] = None
    publish_date: Optional[str] = None
    date_confidence: Optional[str] = None
    watchlist: bool = False
    publisher: str
    isbn: str
    auto_added: bool
    is_series: Optional[bool] = False  # CORRECTION: Ajout champ is_series manquant
    language: str
    ol_key: Optional[str] = None
    ol_work_id: Optional[str] = None
    ol_edition_id: Optional[str] = None
    date_added: datetime
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    reading_history: Optional[List[dict]] = None  # lectures précédentes [{date_started, date_completed, rating}]

class BookSearchResponse(BaseModel):
    books: List[BookResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool