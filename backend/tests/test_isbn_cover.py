"""Couverture trouvée par ISBN : jamais une image vide."""

import pytest

from app.openlibrary import isbn_lookup


def test_cover_of_the_source_is_kept(monkeypatch):
    monkeypatch.setattr(isbn_lookup, "_is_real_image", lambda url: pytest.fail("pas de requête"))
    found = {"cover_url": "https://exemple.test/c.jpg", "source": "bnf"}
    assert isbn_lookup.find_cover(found, ["9782070360024"]) == "https://exemple.test/c.jpg"


def test_open_library_cover_is_used_only_when_it_really_exists(monkeypatch):
    seen = []

    def fake(url):
        seen.append(url)
        return "/2070360024-M" in url

    monkeypatch.setattr(isbn_lookup, "_is_real_image", fake)
    cover = isbn_lookup.find_cover({"cover_url": "", "source": "bnf"}, ["9782070360024", "2070360024"])
    assert cover == "https://covers.openlibrary.org/b/isbn/2070360024-M.jpg?default=false"
    assert "9782070360024" in seen[0]


def test_google_books_cover_is_the_fallback(monkeypatch):
    monkeypatch.setattr(isbn_lookup, "_is_real_image", lambda url: False)
    monkeypatch.setattr(
        isbn_lookup, "_from_google_books", lambda isbn, detect: {"cover_url": "https://g.test/t.jpg"}
    )
    found = {"cover_url": "", "source": "bnf"}
    assert isbn_lookup.find_cover(found, ["9782070360024"]) == "https://g.test/t.jpg"


def test_no_cover_gives_an_empty_string_not_a_blank_image(monkeypatch):
    monkeypatch.setattr(isbn_lookup, "_is_real_image", lambda url: False)
    monkeypatch.setattr(isbn_lookup, "_from_google_books", lambda isbn, detect: None)
    assert isbn_lookup.find_cover({"cover_url": "", "source": "bnf"}, ["9782070360024"]) == ""


def test_book_has_no_fake_default_cover():
    book = isbn_lookup._book(isbn="9782070360024", title="Titre")
    assert book["cover_url"] == ""
