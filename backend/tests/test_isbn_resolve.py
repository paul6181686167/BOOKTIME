"""ISBN titre → sources OL / Google / BnF, jamais inventé."""
from __future__ import annotations

from app.catalog import isbn_resolve

VALID = "9782070360024"
INVALID = "9782070123456"

BNF_XML = """<?xml version="1.0"?>
<srw:searchRetrieveResponse xmlns:srw="http://www.loc.gov/zing/srw/">
  <srw:records>
    <srw:record>
      <srw:recordData>
        <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>L'Étranger / Albert Camus</dc:title>
          <dc:identifier>ISBN 978-2-07-036002-4</dc:identifier>
        </oai_dc:dc>
      </srw:recordData>
    </srw:record>
  </srw:records>
</srw:searchRetrieveResponse>
"""


class _Resp:
    def __init__(self, status: int, data=None, content: bytes = b""):
        self.status_code = status
        self._data = data if data is not None else {}
        self.content = content

    def json(self):
        return self._data


def test_prefer_isbn_rejects_bad_checksum_and_prefers_french():
    assert isbn_resolve.prefer_isbn([INVALID]) == ""
    assert isbn_resolve.prefer_isbn(["2070360024"]) == VALID
    assert isbn_resolve.prefer_isbn(["9780007117116", VALID]) == VALID


def test_resolve_isbn_open_library_search(monkeypatch):
    isbn_resolve.reset_budget(10)
    calls: list[str] = []

    def fake_get(url, **kwargs):
        calls.append(url)
        if "openlibrary.org/search" in url:
            return _Resp(200, {"docs": [{"title": "L'Étranger", "isbn": [VALID]}]})
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    assert isbn_resolve.resolve_isbn(title="L'Étranger", author="Camus") == VALID
    assert calls == ["https://openlibrary.org/search.json"]


def test_resolve_isbn_falls_back_to_bnf(monkeypatch):
    isbn_resolve.reset_budget(10)

    def fake_get(url, **kwargs):
        if "openlibrary.org/search" in url:
            return _Resp(200, {"docs": []})
        if "googleapis.com" in url:
            return _Resp(200, {"items": []})
        if "catalogue.bnf.fr" in url:
            return _Resp(200, content=BNF_XML.encode("utf-8"))
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    assert isbn_resolve.resolve_isbn(title="L'Étranger", author="Camus") == VALID


def test_resolve_isbn_skips_title_mismatch_and_invalid_checksum(monkeypatch):
    isbn_resolve.reset_budget(10)

    def fake_get(url, **kwargs):
        if "openlibrary.org/search" in url:
            return _Resp(200, {"docs": [{"title": "Autre Livre", "isbn": [VALID]}]})
        if "googleapis.com" in url:
            return _Resp(
                200,
                {
                    "items": [
                        {
                            "volumeInfo": {
                                "title": "L'Étranger",
                                "industryIdentifiers": [{"type": "ISBN_13", "identifier": INVALID}],
                            }
                        }
                    ]
                },
            )
        if "catalogue.bnf.fr" in url:
            return _Resp(200, content=BNF_XML.encode("utf-8"))
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    assert isbn_resolve.resolve_isbn(title="L'Étranger") == VALID


def test_resolve_isbn_ol_editions_first(monkeypatch):
    isbn_resolve.reset_budget(10)

    def fake_get(url, **kwargs):
        if "openlibrary.org/works/OL1W/editions.json" in url:
            return _Resp(200, {"entries": [{"isbn_13": [VALID]}]})
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    assert isbn_resolve.resolve_isbn(title="L'Étranger", ol_key="/works/OL1W") == VALID


def test_resolve_isbn_budget_zero_no_http(monkeypatch):
    isbn_resolve.reset_budget(0)

    def boom(*a, **k):
        raise AssertionError("HTTP interdit sans budget")

    monkeypatch.setattr(isbn_resolve.requests, "get", boom)
    assert isbn_resolve.resolve_isbn(title="L'Étranger") == ""


def test_find_cover_from_openlibrary_cover_i(monkeypatch):
    isbn_resolve.reset_cover_budget(5)

    def fake_get(url, **kwargs):
        if "openlibrary.org/search" in url:
            return _Resp(200, {"docs": [{"title": "L'Étranger", "cover_i": 12345, "isbn": [VALID]}]})
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    cover, isbn = isbn_resolve.find_cover(title="L'Étranger", author="Camus")
    assert cover == "https://covers.openlibrary.org/b/id/12345-M.jpg"
    assert isbn == VALID


def test_find_cover_google_thumbnail(monkeypatch):
    isbn_resolve.reset_cover_budget(5)

    def fake_get(url, **kwargs):
        if "openlibrary.org/search" in url:
            return _Resp(200, {"docs": []})
        if "googleapis.com" in url:
            return _Resp(
                200,
                {
                    "items": [
                        {
                            "volumeInfo": {
                                "title": "L'Étranger",
                                "imageLinks": {
                                    "thumbnail": "http://books.google.com/books/content?id=x&img=1"
                                },
                            }
                        }
                    ]
                },
            )
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    cover, isbn = isbn_resolve.find_cover(title="L'Étranger")
    assert cover.startswith("https://")
    assert "books.google.com" in cover
    assert isbn == ""


def test_ol_author_photo_from_olid(monkeypatch):
    isbn_resolve.reset_cover_budget(3)

    def fake_get(url, **kwargs):
        if "search/authors" in url:
            return _Resp(200, {"docs": [{"name": "Ada Lovelace", "key": "OL23919A"}]})
        raise AssertionError(url)

    monkeypatch.setattr(isbn_resolve.requests, "get", fake_get)
    url = isbn_resolve.ol_author_photo("Ada Lovelace")
    assert url == "https://covers.openlibrary.org/a/olid/OL23919A-M.jpg"


def test_find_cover_budget_zero_no_http(monkeypatch):
    isbn_resolve.reset_cover_budget(0)

    def boom(*a, **k):
        raise AssertionError("HTTP interdit sans budget jaquette")

    monkeypatch.setattr(isbn_resolve.requests, "get", boom)
    cover, isbn = isbn_resolve.find_cover(title="L'Étranger")
    assert cover == ""
    assert isbn == ""
