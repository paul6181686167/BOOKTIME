from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.security import cookies
from app.security import jwt as security
from app.security.jwt import create_access_token, get_current_user

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def users(monkeypatch):
    coll = mongomock.MongoClient().db.users
    coll.insert_one({"id": "u1", "email": "a@b.fr"})
    monkeypatch.setattr(security, "users_collection", coll)
    return coll


@pytest.fixture
def client(users):
    app = FastAPI()

    @app.get("/who")
    def who(user=Depends(get_current_user)):
        return {"id": user["id"]}

    @app.post("/change")
    def change(user=Depends(get_current_user)):
        return {"changed": user["id"]}

    return TestClient(app)


def token(minutes=5):
    return create_access_token({"sub": "u1"}, timedelta(minutes=minutes))


# ---------- compatibilité : l'en-tête Bearer marche toujours, cookie désactivé ----------

def test_bearer_header_still_works(client):
    r = client.get("/who", headers={"Authorization": f"Bearer {token()}"})
    assert r.status_code == 200 and r.json() == {"id": "u1"}


def test_no_credentials_is_401(client):
    assert client.get("/who").status_code == 401


def test_cookie_ignored_when_feature_disabled(client, monkeypatch):
    monkeypatch.delenv("AUTH_COOKIE_ENABLED", raising=False)
    client.cookies.set(cookies.cookie_name(), token())
    assert client.get("/who").status_code == 401


# ---------- cookie httpOnly activé ----------

@pytest.fixture
def cookie_on(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_ENABLED", "true")


def test_cookie_authenticates_safe_requests(client, cookie_on):
    client.cookies.set(cookies.cookie_name(), token())
    assert client.get("/who").json() == {"id": "u1"}


def test_cookie_write_requires_csrf_header(client, cookie_on):
    client.cookies.set(cookies.cookie_name(), token())
    assert client.post("/change").status_code == 403
    ok = client.post("/change", headers={"X-Requested-With": "BookTime"})
    assert ok.status_code == 200 and ok.json() == {"changed": "u1"}
    assert client.post("/change", headers={"X-Requested-With": "autre"}).status_code == 403


def test_bearer_write_needs_no_csrf_header(client, cookie_on):
    r = client.post("/change", headers={"Authorization": f"Bearer {token()}"})
    assert r.status_code == 200


def test_invalid_cookie_is_rejected(client, cookie_on):
    client.cookies.set(cookies.cookie_name(), "pas-un-jwt")
    assert client.get("/who").status_code == 401


# ---------- login / logout ----------

@pytest.fixture
def api(monkeypatch, users):
    from app.auth import routes as auth_routes
    from app.main import app

    users.update_one(
        {"id": "u1"}, {"$set": {"password_hash": auth_routes._hash_password("secret123")}}
    )
    monkeypatch.setattr(auth_routes, "users_collection", users)
    return TestClient(app)


def test_login_sets_httponly_cookie_when_enabled(api, cookie_on):
    r = api.post("/api/auth/login", json={"email": "a@b.fr", "password": "secret123"})
    assert r.status_code == 200
    assert r.json()["access_token"]  # toujours renvoyé : appli Android et anciennes versions
    header = r.headers["set-cookie"].lower()
    assert f"{cookies.cookie_name()}=" in header
    assert "httponly" in header and "secure" in header and "samesite=none" in header


def test_login_sets_no_cookie_by_default(api, monkeypatch):
    monkeypatch.delenv("AUTH_COOKIE_ENABLED", raising=False)
    r = api.post("/api/auth/login", json={"email": "a@b.fr", "password": "secret123"})
    assert r.status_code == 200
    assert "set-cookie" not in r.headers


def test_logout_clears_cookie(api):
    r = api.post("/api/auth/logout")
    assert r.status_code == 200
    header = r.headers["set-cookie"].lower()
    assert f"{cookies.cookie_name()}=" in header and "max-age=0" in header
