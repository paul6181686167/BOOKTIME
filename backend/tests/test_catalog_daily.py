"""Ajout quotidien de fiches complètes au noyau curé."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.catalog import daily_authors, daily_ingest, daily_store, expanded
from app.db_config import _mock_storage
from app.series_verification import curated as curated_mod


def _reset_daily():
    store = _mock_storage.setdefault("catalog_daily_series", [])
    store.clear()
    _mock_storage.setdefault("authors", []).clear()
    expanded.clear_cache()
    curated_mod.clear_cache()
    from app.catalog.seed import reset_seed_flag

    reset_seed_flag()


def test_complete_entry_requires_two_titles_author_and_cover():
    cand = {"qid": "Q1", "name": "Saga Test", "category": "roman", "genre": "Fantasy", "cover_url": ""}
    assert daily_ingest.build_complete_entry(cand, [{"title": "Un"}]) is None
    works = [
        {"title": "Un", "author": "", "published_year": 2020},
        {"title": "Deux", "author": "", "published_year": 2021},
    ]
    assert daily_ingest.build_complete_entry(cand, works) is None
    works[0]["author"] = "A. Auteur"
    assert daily_ingest.build_complete_entry(cand, works) is None
    cand["cover_url"] = "https://example.test/c.jpg"
    entry = daily_ingest.build_complete_entry(cand, works)
    assert entry is not None
    assert entry["authors"] == ["A. Auteur"]
    assert entry["volumes"] == 2
    d1 = entry["volume_details"]["1"]
    assert d1["author"] and d1["genre"] and d1["language"] and d1["description"] and d1["pages"]
    assert d1["cover_url"].startswith("https://")
    assert d1["published_year"] == 2020


def test_standalone_book_one_volume_with_real_isbn():
    cand = {
        "qid": "Qsolo",
        "name": "Le Livre Seul",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/c.jpg",
    }
    works = [
        {"title": "Le Livre Seul", "author": "Solo Auteur", "published_year": 2019, "isbn": "9782070123456"}
    ]
    assert daily_ingest.build_complete_entry(cand, works) is None
    entry = daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True)
    assert entry is not None
    assert entry["volumes"] == 1
    assert entry["type"] == "standalone"
    assert entry["volume_details"]["1"]["isbn"] == "9782070123456"
    assert "est un roman" in entry["volume_details"]["1"]["description"]


def test_plafonds_quotidiens_par_defaut(monkeypatch):
    monkeypatch.delenv("CATALOG_DAILY_SERIES", raising=False)
    monkeypatch.delenv("CATALOG_DAILY_BOOKS", raising=False)
    monkeypatch.delenv("CATALOG_DAILY_FICHES", raising=False)
    monkeypatch.delenv("CATALOG_DAILY_AUTHORS", raising=False)
    assert daily_ingest.daily_series_limit() == 80
    assert daily_ingest.daily_books_limit() == 10000
    assert daily_ingest.daily_fiches_target() == 10000
    assert daily_authors.daily_authors_limit() == 2000


def test_ingest_skips_known_qid_and_incomplete(monkeypatch):
    _reset_daily()
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: {"Qknown"})
    monkeypatch.setattr(
        daily_ingest,
        "fetch_candidate_series",
        lambda limit: [
            {"qid": "Qknown", "name": "Déjà là", "category": "roman", "genre": "Roman", "cover_url": "https://x/c.jpg"},
            {"qid": "Qnew", "name": "Trop court", "category": "roman", "genre": "Roman", "cover_url": "https://x/c.jpg"},
        ],
    )
    monkeypatch.setattr(daily_ingest, "fetch_works", lambda qid: [{"title": "Seul", "author": "Moi"}])
    result = daily_ingest.run_daily_ingest(limit=5)
    assert result["added"] == 0
    assert result["skipped"] >= 2


def test_ingest_persists_complete_series(monkeypatch):
    _reset_daily()
    cand = {
        "qid": "Q999001",
        "name": "Chroniques de Pytest",
        "name_en": "Pytest Chronicles",
        "category": "roman",
        "genre": "Fantasy",
        "cover_url": "https://example.test/cover.jpg",
    }
    works = [
        {"title": "Le Premier", "title_en": "The First", "author": "Ève Test", "published_year": 2022, "isbn": "9782070123456", "work_qid": "Q11"},
        {"title": "Le Second", "author": "Ève Test", "published_year": 2023, "work_qid": "Q12"},
    ]
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [cand])
    monkeypatch.setattr(daily_ingest, "fetch_works", lambda qid: works)
    result = daily_ingest.run_daily_ingest(limit=3)
    assert result["added"] == 1
    assert result["fiches"] == 2
    stored = daily_store.all_series()
    assert stored[0]["name"] == "Chroniques de Pytest"
    assert stored[0]["volume_details"]["1"]["isbn"] == "9782070123456"
    expanded.clear_cache()
    assert all(s.get("qid") != "Q999001" for s in expanded.all_series())
    hits = expanded.search_series("Chroniques de Pytest")
    assert hits and hits[0]["name"] == "Chroniques de Pytest"
    assert hits[0]["source"] == "daily"
    entry = curated_mod.match_curated("Chroniques de Pytest")
    assert entry and entry.get("source") == "curated_daily"


def test_ingest_adds_standalone_books(monkeypatch):
    _reset_daily()
    book = {
        "qid": "Qsolo1",
        "name": "Roman Independant XYZ",
        "name_en": "Independent Novel XYZ",
        "author": "Jane Doe",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/cover.jpg",
        "isbn": "9782070123456",
        "ol_key": "",
        "year": 2021,
    }
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [])
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [book])
    result = daily_ingest.run_daily_ingest(limit=0, books_limit=5)
    assert result["added_books"] == 1
    assert result["added_series"] == 0
    assert result["fiches"] == 1
    stored = [s for s in daily_store.all_series() if s.get("qid") == "Qsolo1"]
    assert len(stored) == 1
    assert stored[0]["volumes"] == 1
    assert stored[0]["type"] == "standalone"
    expanded.clear_cache()
    hits = expanded.search_series("Roman Independant XYZ")
    assert hits and hits[0]["name"] == "Roman Independant XYZ"


@pytest.mark.asyncio
async def test_daily_run_endpoint_requires_secret(test_client: AsyncClient, monkeypatch):
    monkeypatch.setenv("CATALOG_DAILY_SECRET", "s3cret-daily")
    r = await test_client.post("/api/catalog/daily/run")
    assert r.status_code == 403
    called = []

    def fake_run(**kwargs):
        called.append(True)
        return {"added": 0, "skipped": 0, "names": []}

    monkeypatch.setattr("app.catalog.daily_ingest.run_daily_ingest", fake_run)
    r = await test_client.post(
        "/api/catalog/daily/run",
        headers={"X-Catalog-Daily-Secret": "s3cret-daily"},
    )
    assert r.status_code == 200
    assert called
    r = await test_client.get(
        "/api/catalog/daily/status",
        headers={"X-Catalog-Daily-Secret": "s3cret-daily"},
    )
    assert r.status_code == 200
    assert r.json()["target_fiches"] == 10000


def test_fetch_candidate_books_pages_by_year(monkeypatch):
    calls: list[str] = []

    def fake_sparql(query, timeout=55):
        calls.append(query)
        return []

    monkeypatch.setattr(daily_ingest, "_sparql", fake_sparql)
    daily_ingest.fetch_candidate_books(900)
    assert len(calls) >= 2
    assert any("YEAR(?date)" in c for c in calls)


def test_complete_author_needs_photo_and_birth_or_bio():
    cand = {"qid": "Q42", "name": "Ada Test", "photo_url": ""}
    assert daily_authors.build_complete_author(cand) is None
    cand["photo_url"] = "https://example.test/ada.jpg"
    assert daily_authors.build_complete_author(cand) is None
    cand["birth_date"] = "1815-12-10"
    cand["bio"] = "Mathématicienne et pionnière de l'informatique."
    entry = daily_authors.build_complete_author(cand)
    assert entry is not None
    assert entry["wikidata_qid"] == "Q42"
    assert entry["photo_url"].startswith("https://")
    assert entry["source"] == "daily"


def test_ingest_adds_author_fiches(monkeypatch):
    _reset_daily()
    from app.db_config import MockCollection

    mock_authors = MockCollection("authors")
    monkeypatch.setattr(daily_authors, "_coll", lambda: mock_authors)
    monkeypatch.setattr("app.authors.service.authors_collection", mock_authors)
    author = {
        "qid": "Q42",
        "name": "Ada Lovelace",
        "name_en": "Ada Lovelace",
        "photo_url": "https://example.test/ada.jpg",
        "birth_date": "1815-12-10",
        "nationality": "britannique",
        "bio": "Mathématicienne britannique, pionnière de la programmation.",
        "wikipedia_url": "https://fr.wikipedia.org/wiki/Ada_Lovelace",
    }
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [])
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [])
    monkeypatch.setattr(daily_authors, "fetch_candidate_authors", lambda limit: [author])
    monkeypatch.setattr(daily_authors, "wiki_bio", lambda *a, **k: (author["bio"], author["wikipedia_url"]))
    monkeypatch.setattr(daily_authors, "known_qids", lambda: set())
    monkeypatch.setattr(daily_authors, "known_names", lambda: set())
    result = daily_ingest.run_daily_ingest(limit=0, books_limit=0, authors_limit=5)
    assert result["added_authors"] == 1
    stored = [a for a in _mock_storage.get("authors", []) if a.get("wikidata_qid") == "Q42"]
    assert len(stored) == 1
    assert stored[0]["name"] == "Ada Lovelace"
    from app.authors.service import get_cached_author

    cached = get_cached_author("Ada Lovelace")
    assert cached and cached.get("photo_url")
    hits = expanded.search_authors("Ada Lovelace")
    assert hits and hits[0]["type"] == "author"
    assert hits[0]["name"] == "Ada Lovelace"
