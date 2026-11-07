import pytest

from app.external_ratings import service as svc


class Resp:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


OL = {"docs": [
    {"key": "/works/OL1W", "title": "La Peste", "author_name": ["Albert Camus"], "ratings_average": 4.2, "ratings_count": 321},
]}
GB = {"items": [{"volumeInfo": {"title": "La peste", "authors": ["Albert Camus"], "averageRating": 4, "ratingsCount": 12, "infoLink": "http://gb"}}]}
JIKAN = {"data": [{"title": "One Piece", "title_english": "One Piece", "titles": [], "score": 9.2, "scored_by": 1000, "url": "http://mal"}]}
ANILIST = {"data": {"Media": {"title": {"romaji": "One Piece", "english": "One Piece", "native": None}, "synonyms": [], "averageScore": 88, "siteUrl": "http://al"}}}


def fake_get(routes):
    def get(url, **kw):
        for part, resp in routes.items():
            if part in url:
                if isinstance(resp, Exception):
                    raise resp
                return resp
        raise AssertionError(f"URL inattendue {url}")
    return get


@pytest.fixture(autouse=True)
def clear_cache():
    svc._cache.clear()


def test_normalize_and_match():
    assert svc.normalize("  L'Étranger !! ") == "l etranger"
    assert svc.titles_match("la peste", "La Peste")
    assert svc.titles_match("La Peste, tome 2", "La peste")  # le numéro de tome est ignoré
    assert svc.titles_match("1984", "1984")
    assert not svc.titles_match("Dune", "Dune Messiah")  # une autre œuvre
    assert not svc.titles_match("One Piece - Tome 1", "One Piece Party")
    assert svc.titles_match("One Piece - Tome 1", "One Piece", loose=True)
    assert not svc.titles_match("ab", "ab")  # trop court


def test_book_ratings_scaled_on_five_with_links():
    get = fake_get({"openlibrary": Resp(OL), "googleapis": Resp(GB)})
    out = svc.get_external_ratings("La Peste", "Albert Camus", get=get)
    by = {r["source"]: r for r in out["ratings"]}
    assert by["openlibrary"]["score"] == 4.2 and by["openlibrary"]["count"] == 321
    assert by["googlebooks"]["score"] == 4.0
    assert [l["label"] for l in out["links"]] == ["Babelio", "Goodreads"]
    assert "La+Peste" in out["links"][0]["url"]


def test_wrong_work_is_rejected():
    ol = {"docs": [{"key": "/works/X", "title": "Tout autre livre", "author_name": ["Quelqu Un"], "ratings_average": 3, "ratings_count": 5}]}
    out = svc.get_external_ratings(
        "La Peste", "Albert Camus", get=fake_get({"openlibrary": Resp(ol), "googleapis": Resp({"items": []})})
    )
    assert out["ratings"] == []


def test_failing_source_does_not_block_others():
    get = fake_get({"openlibrary": RuntimeError("panne"), "googleapis": Resp(GB)})
    out = svc.get_external_ratings("La Peste", "Albert Camus", get=get)
    assert [r["source"] for r in out["ratings"]] == ["googlebooks"]


def test_manga_series_uses_anilist_and_mal_only():
    get = fake_get({"jikan": Resp(JIKAN)})
    post = lambda url, **kw: Resp(ANILIST)  # noqa: E731
    out = svc.get_external_ratings("One Piece", kind="series", category="manga", get=get, post=post)
    by = {r["source"]: r for r in out["ratings"]}
    assert set(by) == {"anilist", "myanimelist"}  # ni Open Library ni Google Books pour une série
    assert by["anilist"]["score"] == 4.4 and by["myanimelist"]["score"] == 4.6
    assert all(r["scope"] == "series" for r in out["ratings"])


def test_novel_series_has_no_ratings_but_links():
    out = svc.get_external_ratings("Harry Potter", kind="series", category="roman", get=fake_get({}))
    assert out["ratings"] == [] and out["links"]


def test_cache_avoids_second_call_and_skips_empty_results():
    calls = []

    def get(url, **kw):
        calls.append(url)
        return Resp(OL if "openlibrary" in url else {"items": []})

    svc.get_external_ratings("La Peste", "Albert Camus", get=get)
    n = len(calls)
    svc.get_external_ratings("La Peste", "Albert Camus", get=get)
    assert len(calls) == n  # servi depuis le cache

    empty = []
    svc.get_external_ratings("Inconnu Total", get=lambda url, **kw: (empty.append(1), Resp({"docs": [], "items": []}))[1])
    first = len(empty)
    svc.get_external_ratings("Inconnu Total", get=lambda url, **kw: (empty.append(1), Resp({"docs": [], "items": []}))[1])
    assert len(empty) > first  # un résultat vide n'est pas figé en cache


def test_route_requires_auth_and_validates_kind():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.external_ratings.routes import router
    from app.security.jwt import get_current_user

    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    assert c.get("/api/ratings/external?title=x").status_code == 401
    app.dependency_overrides[get_current_user] = lambda: {"id": "u"}
    assert c.get("/api/ratings/external?title=x&kind=bad").status_code == 422
