"""Catalogue étendu de 50 000 fiches (Wikidata, hors overlay curé)."""
from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from app.catalog import expanded


def _tiny_catalog():
    return {
        "meta": {"book_count": 3, "series_count": 1, "categories": {"roman": 1}},
        "series": [
            {
                "key": "shannara",
                "qid": "Q123",
                "name": "Shannara",
                "name_en": "Shannara",
                "authors": ["Terry Brooks"],
                "category": "roman",
                "volumes": 3,
                "volume_titles": {"1": "Les Épées de Shannara", "2": "Les Pierres de Shannara"},
                "wikidata_qid": "Q123",
                "cover_url": "https://covers.openlibrary.org/b/olid/OL1W-L.jpg",
            }
        ],
    }


def _isolate_catalog_mongo(monkeypatch):
    from app.db_config import MockCollection, _mock_storage

    _mock_storage.setdefault("catalog_daily_series", []).clear()
    monkeypatch.setattr("app.catalog.daily_store._coll", lambda: MockCollection("catalog_daily_series"))


def test_search_prefers_exact_series_name(tmp_path, monkeypatch):
    _isolate_catalog_mongo(monkeypatch)
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(json.dumps(_tiny_catalog()), encoding="utf-8")
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    hits = expanded.search_series("Shannara")
    assert hits
    assert hits[0]["name"] == "Shannara"
    assert hits[0]["volumes"] == 3


def test_search_matches_volume_title(tmp_path, monkeypatch):
    _isolate_catalog_mongo(monkeypatch)
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(json.dumps(_tiny_catalog()), encoding="utf-8")
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    hits = expanded.search_series("épées de shannara")
    assert hits
    assert hits[0]["name"] == "Shannara"


def test_generated_catalog_has_50000_books():
    from app.catalog.seed import read_json_catalog

    data = read_json_catalog()
    meta = data.get("meta") or {}
    if int(meta.get("book_count") or 0) <= 0 and not data.get("series"):
        return
    assert int(meta.get("book_count") or 0) >= 50_000
    assert int(meta.get("series_count") or 0) >= 2000


def test_generated_catalog_volumes_are_complete():
    series = expanded.all_series()
    if not series:
        return
    n = 0
    missing = {k: 0 for k in ("author", "year", "genre", "language", "cover", "description", "pages")}
    for s in series:
        details = s.get("volume_details") or {}
        for vn, title in (s.get("volume_titles") or {}).items():
            n += 1
            d = details.get(str(vn)) or details.get(vn) or {}
            if not (d.get("author") or "").strip():
                missing["author"] += 1
            if not d.get("published_year"):
                missing["year"] += 1
            if not d.get("genre"):
                missing["genre"] += 1
            if not d.get("language"):
                missing["language"] += 1
            cover = (d.get("cover_url") or "").strip()
            if not cover or cover.startswith("data:"):
                missing["cover"] += 1
            if not (d.get("description") or "").strip():
                missing["description"] += 1
            if not d.get("pages"):
                missing["pages"] += 1
    assert n >= 50_000
    assert missing == {k: 0 for k in missing}, missing


@pytest.mark.asyncio
async def test_expanded_endpoint_requires_auth(test_client: AsyncClient):
    r = await test_client.get("/api/catalog/expanded")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_expanded_search_endpoint(test_client: AsyncClient, auth_headers: dict, tmp_path, monkeypatch):
    _isolate_catalog_mongo(monkeypatch)
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(json.dumps(_tiny_catalog()), encoding="utf-8")
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    r = await test_client.get("/api/catalog/expanded/search?q=shannara", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["results"][0]["name"] == "Shannara"
