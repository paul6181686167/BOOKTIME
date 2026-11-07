import pytest

from app.utils import book_synopsis as bs

FR_BLURB = (
    "Aujourd'hui, maman est morte. Ou peut-être hier, je ne sais pas. "
    "Meursault, employé à Alger, assiste à l'enterrement puis retrouve sa vie."
)
FR_OTHER = (
    "Un roman d'Albert Camus publié en 1942 dans la collection Blanche, "
    "souvent présenté comme le récit de l'absurde."
)
EN_BLURB = (
    "The story of a man who is indifferent to the world around him and who is "
    "put on trial for a murder that he committed on a beach in Algeria."
)


def _boom(*_a, **_k):
    raise AssertionError("cette source ne devait pas être appelée")


# ---------- nettoyage ----------


def test_sanitize_keeps_paragraph_breaks():
    raw = "<p>Premier paragraphe de la quatrième.</p><p>Second paragraphe du texte.</p>"
    assert bs._sanitize_synopsis(raw) == (
        "Premier paragraphe de la quatrième.\n\nSecond paragraphe du texte."
    )
    assert bs._sanitize_synopsis("Ligne un<br>Ligne deux<br/><br/>Ligne trois") == (
        "Ligne un\n\nLigne deux\n\nLigne trois"
    )


def test_sanitize_joins_hard_wrapped_lines():
    assert bs._sanitize_synopsis("Une phrase coupée\nen deux lignes.") == (
        "Une phrase coupée en deux lignes."
    )


# ---------- ordre des sources ----------


def test_isbn_back_cover_wins_over_everything(monkeypatch):
    monkeypatch.setattr(bs, "fetch_back_cover_by_isbn", lambda isbn: (FR_BLURB, "google_books_isbn"))
    monkeypatch.setattr(bs, "_description_from_google_books", _boom)
    monkeypatch.setattr(bs, "_ol_work_description_only", _boom)
    monkeypatch.setattr(bs, "_description_from_wikipedia", _boom)
    text, source, _ = bs._fast_book_description(
        title="L'Étranger", author="Albert Camus", isbn="9782070360024", ol_key="/works/OL1W"
    )
    assert (text, source) == (FR_BLURB, "google_books_isbn")


def test_google_books_by_title_precedes_open_library_work(monkeypatch):
    monkeypatch.setattr(bs, "fetch_back_cover_by_isbn", lambda isbn: ("", "none"))
    monkeypatch.setattr(bs, "_description_from_google_books", lambda **k: {"description": FR_BLURB})
    monkeypatch.setattr(bs, "_ol_work_description_only", _boom)
    monkeypatch.setattr(bs, "_description_from_wikipedia", _boom)
    text, source, _ = bs._fast_book_description(
        title="L'Étranger", author="Albert Camus", ol_key="/works/OL1W"
    )
    assert (text, source) == (FR_BLURB, "google_books")


def test_wikipedia_is_the_last_resort(monkeypatch):
    calls = []
    monkeypatch.setattr(bs, "_description_from_google_books", lambda **k: {"description": ""})
    monkeypatch.setattr(bs, "_ol_work_description_only", lambda key: "")
    monkeypatch.setattr(bs, "_ol_key_from_search", lambda *a, **k: "")

    def wiki(title, author="", langs=("fr", "en")):
        calls.append(langs)
        return FR_OTHER

    monkeypatch.setattr(bs, "_description_from_wikipedia", wiki)
    text, source, _ = bs._fast_book_description(title="L'Étranger", author="Albert Camus")
    assert (text, source) == (FR_OTHER, "wikipedia")
    assert calls  # n'est consultée qu'après les autres sources


def test_open_library_first_sentence_is_not_a_back_cover(monkeypatch):
    class Resp:
        ok = True

        def json(self):
            return {"first_sentence": {"value": "Aujourd'hui, maman est morte. Ou peut-être hier."}}

    monkeypatch.setattr(bs.requests, "get", lambda *a, **k: Resp())
    assert bs._ol_work_description_only("/works/OL1W") == ""


def test_fetch_back_cover_by_isbn_rejects_english_and_bad_isbn(monkeypatch):
    assert bs.fetch_back_cover_by_isbn("12") == ("", "none")
    monkeypatch.setattr(bs, "_description_from_google_books", lambda **k: {"description": EN_BLURB})
    monkeypatch.setattr(bs, "_from_openlibrary_isbn", lambda isbn: "")
    assert bs.fetch_back_cover_by_isbn("9782070360024") == ("", "none")
    monkeypatch.setattr(bs, "_description_from_google_books", lambda **k: {"description": FR_BLURB})
    assert bs.fetch_back_cover_by_isbn("978-2-07-036002-4") == (FR_BLURB, "google_books_isbn")


def test_fetch_back_cover_falls_back_to_open_library_edition(monkeypatch):
    monkeypatch.setattr(bs, "_description_from_google_books", lambda **k: {"description": ""})
    monkeypatch.setattr(bs, "_from_openlibrary_isbn", lambda isbn: FR_BLURB)
    assert bs.fetch_back_cover_by_isbn("9782070360024") == (FR_BLURB, "openlibrary_isbn")


# ---------- endpoint /api/books/{id}/synopsis ----------

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def api(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.books import routes
    from app.security.jwt import get_current_user

    db = mongomock.MongoClient().db
    monkeypatch.setattr(routes, "books_collection", db["books"])
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "u1", "email": "a@b.fr"}
    client = TestClient(app)
    return client, db["books"]


def _book(**extra):
    return {
        "id": "b1", "user_id": "u1", "title": "L'Étranger", "author": "Albert Camus",
        "isbn": "9782070360024", "total_pages": 186, "description": FR_OTHER, **extra,
    }


def test_legacy_summary_is_replaced_by_back_cover_once(api, monkeypatch):
    client, books = api
    books.insert_one(_book())
    monkeypatch.setattr(
        bs, "fetch_book_synopsis",
        lambda **k: {"description": FR_BLURB, "pages": None, "source": "google_books_isbn"},
    )
    first = client.get("/api/books/b1/synopsis?persist=true").json()
    assert first["description"] == FR_BLURB
    assert first["replaced"] is True
    stored = books.find_one({"id": "b1"})
    assert stored["description"] == FR_BLURB
    assert stored["description_source"] == "google_books_isbn"

    monkeypatch.setattr(bs, "fetch_book_synopsis", _boom)
    second = client.get("/api/books/b1/synopsis?persist=true").json()
    assert second["description"] == FR_BLURB
    assert second["source"] == "stored" and second["replaced"] is False


def test_legacy_summary_kept_when_only_encyclopedic_source_found(api, monkeypatch):
    client, books = api
    books.insert_one(_book())
    monkeypatch.setattr(
        bs, "fetch_book_synopsis",
        lambda **k: {"description": FR_BLURB, "pages": None, "source": "wikipedia"},
    )
    data = client.get("/api/books/b1/synopsis?persist=true").json()
    assert data["description"] == FR_OTHER
    assert data["replaced"] is False
    assert books.find_one({"id": "b1"})["description_source"] == "unverified"


def test_verified_summary_is_never_refetched(api, monkeypatch):
    client, books = api
    books.insert_one(_book(description=FR_BLURB, description_source="google_books"))
    monkeypatch.setattr(bs, "fetch_book_synopsis", _boom)
    data = client.get("/api/books/b1/synopsis?persist=true").json()
    assert data["description"] == FR_BLURB
    assert data["source"] == "stored"
