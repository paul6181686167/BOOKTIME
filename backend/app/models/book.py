from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BookCreate(BaseModel):
    title: str
    author: str
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
    publisher: str = ""
    isbn: str = ""
    auto_added: bool = False
    is_series: Optional[bool] = False  # CORRECTION: Ajout champ is_series manquant
    language: Optional[str] = "fr"
    ol_key: Optional[str] = None
    ol_work_id: Optional[str] = None
    ol_edition_id: Optional[str] = None

class BookUpdate(BaseModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    description: Optional[str] = None
    total_pages: Optional[int] = None

class BookResponse(BaseModel):
    id: str
    user_id: str
    title: str
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
    publisher: str
    isbn: str
    auto_added: bool
    language: str
    ol_key: Optional[str] = None
    ol_work_id: Optional[str] = None
    ol_edition_id: Optional[str] = None
    date_added: datetime
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None

class BookSearchResponse(BaseModel):
    books: List[BookResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool