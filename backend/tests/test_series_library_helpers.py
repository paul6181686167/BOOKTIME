"""Helpers bibliothèque séries (sans Mongo)."""

from app.library.series_library_helpers import (
    normalize_series_library_doc,
    series_library_duplicate_query,
)


def test_duplicate_query_series_name_and_legacy_name():
    q = series_library_duplicate_query("user-1", "  Saga X  ")
    assert q["user_id"] == "user-1"
    assert q["$or"] == [{"series_name": "Saga X"}, {"name": "Saga X"}]


def test_normalize_fills_name_from_series_name():
    doc = {"id": "1", "series_name": "Titre canon", "volumes": []}
    out = normalize_series_library_doc(doc)
    assert out["name"] == "Titre canon"
    assert out["series_name"] == "Titre canon"


def test_normalize_keeps_existing_name():
    doc = {"series_name": "A", "name": "B"}
    assert normalize_series_library_doc(doc)["name"] == "B"
