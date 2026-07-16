"""Tests unitaires du mapper Google Books (sans appel réseau).

Exemple sans charger conftest (dépendances Mongo, etc.) :

    cd backend && set PYTHONPATH=. && python -m pytest tests/test_google_books_simplify.py -q --noconftest
"""

from app.google_books.service import normalize_isbn, simplify_item


def test_normalize_isbn_strips_non_digits():
    assert normalize_isbn("978-0-12-345678-9") == "9780123456789"
    assert normalize_isbn("") == ""


def test_simplify_item_maps_volume_info():
    item = {
        "id": "volId42",
        "volumeInfo": {
            "title": "Livre test",
            "subtitle": "Sous-titre",
            "authors": ["A. Auteur"],
            "publisher": "Éditeur",
            "publishedDate": "2020-03",
            "pageCount": 200,
            "description": "D" * 2500,
            "language": "fr",
            "industryIdentifiers": [
                {"type": "ISBN_13", "identifier": "9781234567890"},
                {"type": "ISBN_10", "identifier": "123456789X"},
            ],
            "imageLinks": {"thumbnail": "http://books.google.com/thumb.jpg"},
            "previewLink": "https://preview",
            "infoLink": "https://info",
        },
    }
    out = simplify_item(item)
    assert out["google_books_id"] == "volId42"
    assert out["title"] == "Livre test"
    assert out["subtitle"] == "Sous-titre"
    assert out["authors"] == ["A. Auteur"]
    assert out["published_date"] == "2020-03"
    assert out["page_count"] == 200
    assert out["isbn_13"] == "9781234567890"
    assert out["isbn_10"] == "123456789X"
    assert out["thumbnail"] == "http://books.google.com/thumb.jpg"
    assert len(out["description"]) == 2000
    assert out["preview_link"] == "https://preview"
    assert out["info_link"] == "https://info"
    assert out["categories"] == []
