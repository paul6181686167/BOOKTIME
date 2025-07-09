from pydantic import BaseModel
from typing import Optional, List

class UserAuth(BaseModel):
    first_name: str
    last_name: str

class BookCreate(BaseModel):
    title: str
    author: str
    category: str
    description: Optional[str] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = 0
    status: str = "to_read"
    rating: Optional[int] = None
    review: Optional[str] = None
    cover_url: Optional[str] = None
    saga: Optional[str] = None
    volume_number: Optional[int] = None
    genre: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    auto_added: bool = False

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    status: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    cover_url: Optional[str] = None
    saga: Optional[str] = None
    volume_number: Optional[int] = None
    genre: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None

class OpenLibraryImport(BaseModel):
    ol_key: str
    category: str

class SeriesComplete(BaseModel):
    series_name: str
    target_volumes: int
    template_book_id: str