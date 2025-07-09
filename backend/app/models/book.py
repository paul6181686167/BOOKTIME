from pydantic import BaseModel
from typing import Optional

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

class BookUpdate(BaseModel):
    status: Optional[str] = None
    current_page: Optional[int] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    description: Optional[str] = None
    total_pages: Optional[int] = None