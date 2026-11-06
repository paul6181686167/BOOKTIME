"""Inscription : acceptation obligatoire des conditions générales d'utilisation."""

from datetime import datetime

import pytest

mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def client(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.auth import routes

    mock_db = mongomock.MongoClient().db
    monkeypatch.setattr(routes, "users_collection", mock_db["users"])
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), mock_db


def _body(**extra):
    return {"email": "Nouveau@Mail.fr", "password": "secret123", **extra}


def test_register_without_acceptance_is_refused(client):
    api, db = client
    res = api.post("/api/auth/register", json=_body())
    assert res.status_code == 400
    assert "conditions générales" in res.json()["detail"]
    assert db["users"].count_documents({}) == 0


def test_register_with_explicit_refusal_is_refused(client):
    api, db = client
    assert api.post("/api/auth/register", json=_body(accept_terms=False)).status_code == 400
    assert db["users"].count_documents({}) == 0


def test_register_records_acceptance_date_and_version(client):
    api, db = client
    res = api.post(
        "/api/auth/register", json=_body(accept_terms=True, terms_version="2026-11-06")
    )
    assert res.status_code == 200
    stored = db["users"].find_one({"email": "nouveau@mail.fr"})
    assert stored["terms_version"] == "2026-11-06"
    assert isinstance(stored["terms_accepted_at"], datetime)


def test_login_does_not_require_acceptance(client):
    api, _ = client
    api.post("/api/auth/register", json=_body(accept_terms=True))
    res = api.post("/api/auth/login", json={"email": "nouveau@mail.fr", "password": "secret123"})
    assert res.status_code == 200
