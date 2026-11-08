"""Ajout quotidien de fiches complètes au noyau curé."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.catalog import daily_ingest, daily_store, expanded
from app.db_config import _mock_storage
from app.series_verification import curated as curated_mod


def _reset_daily():
    _mock_storage["catalog_daily_series"] = []
    expanded.clear_cache()
    curated_mod.clear_cache()


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
    stored = daily_store.all_series()
    assert stored[0]["name"] == "Chroniques de Pytest"
    assert stored[0]["volume_details"]["1"]["isbn"] == "9782070123456"
    expanded.clear_cache()
    hits = expanded.search_series("Chroniques de Pytest")
    assert hits and hits[0]["name"] == "Chroniques de Pytest"
    assert hits[0]["source"] == "daily"
    entry = curated_mod.match_curated("Chroniques de Pytest")
    assert entry and entry.get("source") == "curated_daily"


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
