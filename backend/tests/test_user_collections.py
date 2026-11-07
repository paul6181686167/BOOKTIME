import pytest
from fastapi import HTTPException

from app.user_collections.routes import sanitize_collections, sanitize_item

mongomock = pytest.importorskip("mongomock")


# ---------- validation ----------

def test_sanitize_item_builds_key_and_defaults():
    item = sanitize_item({"type": "series", "id": 12, "title": "  Dune  "})
    assert item == {
        "key": "series:12",
        "type": "series",
        "id": "12",
        "title": "Dune",
        "author": "",
        "cover_url": None,
    }
    # type inconnu -> livre ; sans identifiant -> ignoré
    assert sanitize_item({"type": "autre", "id": "x"})["key"] == "book:x"
    assert sanitize_item({"id": ""}) is None
    assert sanitize_item("pas un dict") is None


def test_sanitize_collections_cleans_everything():
    out = sanitize_collections(
        [
            {
                "id": 1,
                "name": " SF ",
                "color": "#A855F7",
                "items": [
                    {"type": "book", "id": "b1", "title": "Un"},
                    {"type": "book", "id": "b1", "title": "Doublon"},
                    {"id": ""},
                ],
            },
            {"id": 2, "name": "sf"},  # même nom (insensible à la casse) -> ignoré
            {"id": 3, "name": "Autre", "color": "rouge"},  # couleur invalide -> sans couleur
        ]
    )
    assert [c["name"] for c in out] == ["SF", "Autre"]
    assert out[0]["color"] == "#a855f7"
    assert [i["id"] for i in out[0]["items"]] == ["b1"]
    assert "color" not in out[1]
    assert out[1]["items"] == []


@pytest.mark.parametrize(
    "bad",
    [
        "texte",
        [{"id": 1}],  # nom manquant
        [{"name": "Sans id"}],
        [{"id": 1, "name": "A", "items": "non"}],
        ["pas un dict"],
    ],
)
def test_sanitize_collections_rejects_bad_structures(bad):
    with pytest.raises(HTTPException) as exc:
        sanitize_collections(bad)
    assert exc.value.status_code == 400


# ---------- API ----------

@pytest.fixture
def client(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.security.jwt import get_current_user
    from app.user_collections import routes

    mock_db = mongomock.MongoClient().db
    mock_db["users"].insert_many([{"id": "u1"}, {"id": "u2"}])
    monkeypatch.setattr(routes, "users_collection", mock_db["users"])

    app = FastAPI()
    app.include_router(routes.router)
    state = {"user": "u1"}
    app.dependency_overrides[get_current_user] = lambda: {"id": state["user"]}
    c = TestClient(app)
    c.state = state
    return c


def test_starts_empty(client):
    r = client.get("/api/collections")
    assert r.status_code == 200
    assert r.json() == {"collections": [], "version": 0}


def test_save_and_read_back_with_version(client):
    payload = {
        "base_version": 0,
        "collections": [
            {
                "id": 1,
                "name": "Coups de cœur",
                "color": "#22c55e",
                "items": [{"type": "book", "id": "b1", "title": "Dune", "author": "Herbert"}],
            }
        ],
    }
    r = client.put("/api/collections", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["version"] == 1

    got = client.get("/api/collections").json()
    assert got["version"] == 1
    assert got["collections"][0]["name"] == "Coups de cœur"
    assert got["collections"][0]["items"][0]["key"] == "book:b1"


def test_stale_version_gets_conflict_with_server_state(client):
    first = {"base_version": 0, "collections": [{"id": 1, "name": "A"}]}
    assert client.put("/api/collections", json=first).status_code == 200

    stale = {"base_version": 0, "collections": [{"id": 2, "name": "B"}]}
    r = client.put("/api/collections", json=stale)
    assert r.status_code == 409
    body = r.json()
    assert body["conflict"] is True
    assert body["version"] == 1
    assert body["collections"][0]["name"] == "A"
    # l'état du serveur n'a pas été écrasé
    assert client.get("/api/collections").json()["collections"][0]["name"] == "A"


def test_each_user_has_their_own_collections(client):
    client.put("/api/collections", json={"base_version": 0, "collections": [{"id": 1, "name": "Mienne"}]})
    client.state["user"] = "u2"
    assert client.get("/api/collections").json() == {"collections": [], "version": 0}


def test_invalid_payloads_are_rejected(client):
    assert client.put("/api/collections", json={"collections": "x"}).status_code == 400
    assert (
        client.put(
            "/api/collections", json={"base_version": "zéro", "collections": []}
        ).status_code
        == 400
    )
