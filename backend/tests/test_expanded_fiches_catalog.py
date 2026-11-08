"""Catalogue étendu de 10 000 fiches (Wikidata, hors overlay curé)."""
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


def test_search_prefers_exact_series_name(tmp_path, monkeypatch):
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(json.dumps(_tiny_catalog()), encoding="utf-8")
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    hits = expanded.search_series("Shannara")
    assert hits
    assert hits[0]["name"] == "Shannara"
    assert hits[0]["volumes"] == 3


def test_search_matches_volume_title(tmp_path, monkeypatch):
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(json.dumps(_tiny_catalog()), encoding="utf-8")
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    hits = expanded.search_series("épées de shannara")
    assert hits
    assert hits[0]["name"] == "Shannara"


def test_generated_catalog_has_10000_books():
    expanded.clear_cache()
    st = expanded.stats()
    if not st.get("ready"):
        return
    assert st["books"] == 10_000
    assert st["series"] >= 1000
    assert st["series"] + st["books"] >= 10_000


@pytest.mark.asyncio
async def test_expanded_endpoint_requires_auth(test_client: AsyncClient):
    r = await test_client.get("/api/catalog/expanded")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_expanded_search_endpoint(test_client: AsyncClient, auth_headers: dict, tmp_path, monkeypatch):
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(json.dumps(_tiny_catalog()), encoding="utf-8")
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    r = await test_client.get("/api/catalog/expanded/search?q=shannara", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["results"][0]["name"] == "Shannara"
