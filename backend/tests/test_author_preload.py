import asyncio
from datetime import datetime, timedelta

import pytest

from app.authors import service

mongomock = pytest.importorskip("mongomock")


def _doc(**extra):
    return {"name": "X", "name_normalized": "x", "enriched_at": datetime.utcnow(), **extra}


# ---------- règles de fraîcheur ----------


def test_empty_fiche_is_not_ready():
    assert not service.author_fiche_ready(_doc())  # enrichie mais vide
    assert service.author_fiche_ready(_doc(bio="Une biographie."))
    assert service.author_fiche_ready(_doc(wikidata_qid="Q1"))


def test_needs_enrichment_rules():
    assert service.needs_enrichment(None)
    assert not service.needs_enrichment(_doc(bio="Bio"))
    old = datetime.utcnow() - timedelta(days=40)
    assert service.needs_enrichment(_doc(bio="Bio", enriched_at=old))
    # fiche vide : retentée seulement après un jour
    assert not service.needs_enrichment(_doc())
    assert service.needs_enrichment(_doc(enriched_at=datetime.utcnow() - timedelta(days=2)))


# ---------- préchargement par lots ----------


@pytest.fixture
def env(monkeypatch):
    db = mongomock.MongoClient().db
    monkeypatch.setattr(service, "authors_collection", db["authors"])
    monkeypatch.setattr(service, "books_collection", db["books"])
    monkeypatch.setattr(service, "series_library_collection", db["series_library"])
    for i, name in enumerate(["Camus", "Hugo", "Zola", "Sand", "Verne"]):
        for j in range(5 - i):  # Camus a le plus de livres
            db["books"].insert_one({"user_id": "u1", "author": name, "title": f"{name}{j}"})
    db["books"].insert_one({"user_id": "u1", "author": "Duo, Autre", "title": "Livre à deux"})
    calls = []

    async def fake_enrich(name, *, force=False):
        calls.append(name)
        if name == "Sand":  # aucune source n'a répondu
            doc = {"name": name, "name_normalized": name.lower(), "enriched_at": datetime.utcnow()}
        else:
            doc = {
                "name": name, "name_normalized": name.lower(), "bio": f"Bio de {name}",
                "enriched_at": datetime.utcnow(),
            }
        db["authors"].update_one({"name_normalized": name.lower()}, {"$set": doc}, upsert=True)
        return {**doc, "found": service.author_fiche_ready(doc)}

    monkeypatch.setattr(service, "enrich_author_fiche", fake_enrich)
    return calls


def test_ensure_processes_in_batches_and_reports_remaining(env):
    first = asyncio.run(service.ensure_authors_from_library("u1", limit=2))
    assert first["ensured_count"] == 2
    assert first["remaining"] == 4  # 6 auteurs - 2 traités
    assert set(first["ensured"]) == {"Camus", "Hugo"}

    second = asyncio.run(service.ensure_authors_from_library("u1", limit=10))
    assert second["remaining"] == 0
    assert second["ensured_count"] == 3  # Sand reste vide : non comptée
    assert len(env) == 6

    # Tout est traité (la fiche vide de Sand n'est retentée que le lendemain)
    third = asyncio.run(service.ensure_authors_from_library("u1", limit=10))
    assert third["remaining"] == 0 and third["ensured_count"] == 0
    assert len(env) == 6


def test_ensure_uses_first_author_of_a_list(env):
    asyncio.run(service.ensure_authors_from_library("u1", limit=20))
    assert "Duo" in env and "Duo, Autre" not in env


# ---------- endpoints ----------


def test_profile_falls_back_to_first_author_and_ensure_endpoint(env, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.authors import routes
    from app.security.jwt import get_current_user

    asyncio.run(service.ensure_authors_from_library("u1", limit=20))
    monkeypatch.setattr(routes, "get_cached_author", service.get_cached_author)
    monkeypatch.setattr(routes, "enrich_author_fiche", service.enrich_author_fiche)  # faux, sans réseau
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_current_user] = lambda: {"id": "u1"}
    client = TestClient(app)

    data = client.get("/api/authors/Duo, Autre/profile").json()
    assert data["found"] is True and data["author"]["bio"] == "Bio de Duo"

    missing = client.get("/api/authors/Inconnu/profile").json()
    assert missing["found"] is False and missing["message"] == "not_ready"

    ensured = client.post("/api/authors/Nouveau, Coauteur/ensure").json()
    assert ensured["found"] is True
    assert ensured["author"]["name"] == "Nouveau"
    assert "Nouveau, Coauteur" not in env
