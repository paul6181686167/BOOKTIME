import pytest
from fastapi import HTTPException

from app.auth.routes import SETTINGS_DEFAULTS, clean_settings_update, public_settings
from app.friends.helpers import search_filter


def test_defaults_when_nothing_is_stored():
    assert public_settings({}) == SETTINGS_DEFAULTS
    assert public_settings(None) == SETTINGS_DEFAULTS
    assert all(public_settings({}).values())


def test_stored_values_override_defaults_partially():
    out = public_settings({"settings": {"share_reviews": False}})
    assert out["share_reviews"] is False
    assert out["discoverable"] is True


def test_clean_settings_accepts_only_known_booleans():
    assert clean_settings_update({"discoverable": False}) == {"discoverable": False}
    with pytest.raises(HTTPException):
        clean_settings_update({"unknown": True})
    with pytest.raises(HTTPException):
        clean_settings_update({"discoverable": "non"})


def test_hidden_readers_are_excluded_from_search():
    by_name = search_filter("paul", "me")
    by_email = search_filter("paul@mail.fr", "me")
    assert by_name["settings.discoverable"] == {"$ne": False}
    assert by_email["settings.discoverable"] == {"$ne": False}


# ---------- parcours complet (base simulée) ----------

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def world(monkeypatch):
    import bcrypt
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.auth import routes as auth_routes
    from app.friends import routes as friends_routes
    from app.security.jwt import get_current_user

    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr(auth_routes, "users_collection", mock_db["users"])
    monkeypatch.setattr(friends_routes, "users_collection", mock_db["users"])
    monkeypatch.setattr(friends_routes, "friendships", mock_db["friendships"])
    monkeypatch.setattr(friends_routes, "messages", mock_db["friend_messages"])
    monkeypatch.setattr(friends_routes, "books_collection", mock_db["books"])
    monkeypatch.setattr(friends_routes, "_indexes_ready", True)

    hashed = bcrypt.hashpw(b"ancien-mdp", bcrypt.gensalt()).decode()
    mock_db["users"].insert_many(
        [
            {"id": "u1", "email": "alice@mail.fr", "display_name": "Alice", "password_hash": hashed},
            {"id": "u2", "email": "bob@mail.fr", "display_name": "Bob", "password_hash": hashed},
        ]
    )
    mock_db["books"].insert_many(
        [
            {"id": "b1", "user_id": "u2", "title": "Dune", "author": "F. Herbert",
             "is_favorite": True, "rating": 5, "review": "Génial", "status": "reading"},
        ]
    )
    mock_db["friendships"].insert_one(
        {"id": "f1", "requester_id": "u1", "addressee_id": "u2", "status": "accepted"}
    )

    app = FastAPI()
    app.include_router(auth_routes.router)
    app.include_router(friends_routes.router)
    current = {"id": "u1"}
    app.dependency_overrides[get_current_user] = lambda: {"id": current["id"], "email": "x"}
    client = TestClient(app)

    def as_user(user_id):
        current["id"] = user_id
        return client

    return as_user, mock_db


def test_settings_roundtrip_and_privacy_enforced(world):
    as_user, mock_db = world

    me = as_user("u2").get("/api/auth/me").json()
    assert me["settings"] == SETTINGS_DEFAULTS

    # Par défaut, l'ami voit tout
    profile = as_user("u1").get("/api/friends/u2/profile").json()
    assert profile["hidden"] == []
    assert len(profile["favorites"]) == 1 and len(profile["reviews"]) == 1 and len(profile["reading"]) == 1

    # Bob cache ses avis et ses lectures
    res = as_user("u2").put(
        "/api/auth/me/settings", json={"share_reviews": False, "share_reading": False}
    ).json()
    assert res["settings"]["share_reviews"] is False and res["settings"]["share_favorites"] is True

    profile = as_user("u1").get("/api/friends/u2/profile").json()
    assert profile["reviews"] == [] and profile["reading"] == []
    assert len(profile["favorites"]) == 1
    assert set(profile["hidden"]) == {"reviews", "reading"}

    # Lui-même voit toujours tout
    own = as_user("u2").get("/api/friends/u2/profile").json()
    assert own["hidden"] == [] and len(own["reviews"]) == 1

    # Bob se rend introuvable dans la recherche
    assert [u["id"] for u in as_user("u1").get("/api/friends/search", params={"q": "bo"}).json()["users"]] == ["u2"]
    as_user("u2").put("/api/auth/me/settings", json={"discoverable": False})
    assert as_user("u1").get("/api/friends/search", params={"q": "bo"}).json()["users"] == []
    assert as_user("u1").get("/api/friends/search", params={"q": "bob@mail.fr"}).json()["users"] == []

    # Réglage inconnu ou vide refusé
    assert as_user("u2").put("/api/auth/me/settings", json={}).status_code == 400


def test_change_password(world):
    import bcrypt

    as_user, mock_db = world
    client = as_user("u1")

    assert client.post("/api/auth/change-password",
                       json={"current_password": "faux", "new_password": "nouveau-mdp"}).status_code == 401
    assert client.post("/api/auth/change-password",
                       json={"current_password": "ancien-mdp", "new_password": "abc"}).status_code == 400
    assert client.post("/api/auth/change-password",
                       json={"current_password": "ancien-mdp", "new_password": "ancien-mdp"}).status_code == 400

    ok = client.post("/api/auth/change-password",
                     json={"current_password": "ancien-mdp", "new_password": "nouveau-mdp"})
    assert ok.status_code == 200
    stored = mock_db["users"].find_one({"id": "u1"})["password_hash"]
    assert bcrypt.checkpw(b"nouveau-mdp", stored.encode())
    assert not bcrypt.checkpw(b"ancien-mdp", stored.encode())
