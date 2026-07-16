"""Inférence catégorie (roman / bd / manga) pour les livres Google Books simplifiés."""

from app.google_books.service import infer_book_category_from_google_item, simplified_volume_to_integration_book


def test_infer_manga_from_categories():
    it = {
        "title": "Tome 1",
        "subtitle": "",
        "description": "",
        "categories": ["Comics & Graphic Novels / Manga / Action & Adventure"],
    }
    assert infer_book_category_from_google_item(it) == "manga"


def test_infer_bd_from_title():
    it = {
        "title": "Batman: Year One — Graphic Novel",
        "subtitle": "",
        "description": "",
        "categories": [],
    }
    assert infer_book_category_from_google_item(it) == "bd"


def test_infer_roman_default():
    it = {
        "title": "Les Misérables",
        "subtitle": "",
        "description": "Roman historique",
        "categories": ["Fiction"],
    }
    assert infer_book_category_from_google_item(it) == "roman"


def test_simplified_volume_to_integration_book_uses_infer():
    it = {
        "google_books_id": "abc",
        "title": "One Piece 1",
        "subtitle": "",
        "authors": ["Oda"],
        "publisher": "",
        "published_date": "2000",
        "page_count": 200,
        "description": "",
        "language": "ja",
        "isbn_13": None,
        "isbn_10": None,
        "thumbnail": "",
        "preview_link": "",
        "info_link": "",
        "categories": ["Comics & Graphic Novels / Manga"],
    }
    book = simplified_volume_to_integration_book(it)
    assert book["category"] == "manga"
