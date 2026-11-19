"""Jaquette + résumé catalogue."""
from __future__ import annotations

from app.catalog import catalog_media, daily_ingest, isbn_resolve


def test_template_blurb_detection():
    assert catalog_media.is_template_blurb(
        "« Dune » est le tome 1 de la série Dune, par Frank Herbert (Science-fiction, français, 1965)."
    )
    assert catalog_media.is_template_blurb(
        "« 1984 » est un roman de George Orwell (Roman, français, 1949)."
    )
    assert not catalog_media.is_template_blurb(
        "Dans un Londres futuriste, Winston Smith travaille au Ministère de la Vérité "
        "et commence à remettre en cause le régime totalitaire de Big Brother. "
        "Surveillance, novlangue et réécriture de l'histoire structurent sa révolte intérieure."
    )


def test_apply_synopsis_sets_series_and_tome1():
    doc = {
        "qid": "Q1",
        "name": "Test",
        "volume_details": {
            "1": {"description": "« Test » est un roman de A."},
            "2": {"description": "« Suite » est le tome 2 de la série Test, par A."},
        },
    }
    text = (
        "Une enquête commence dans une ville portuaire où les secrets familiaux "
        "remontent à la surface au fil des témoignages contradictoires."
    )
    assert catalog_media.apply_synopsis(doc, text, "openlibrary")
    assert doc["description"] == text
    assert doc["needs_summary"] is False
    assert doc["summary_source"] == "openlibrary"
    assert doc["volume_details"]["1"]["description"] == text


def test_build_entry_flags_needs_summary_without_budget():
    isbn_resolve.reset_budget(0)
    catalog_media.reset_budgets(synopsis=0, covers=0)
    cand = {
        "qid": "Q99",
        "name": "Saga Media",
        "category": "roman",
        "genre": "Fantasy",
        "cover_url": "https://example.test/c.jpg",
    }
    works = [
        {"title": "Un", "author": "A. Auteur", "published_year": 2020},
        {"title": "Deux", "author": "A. Auteur", "published_year": 2021},
    ]
    entry = daily_ingest.build_complete_entry(cand, works)
    assert entry is not None
    assert entry.get("needs_summary") is True
    assert catalog_media.is_template_blurb(entry["volume_details"]["1"]["description"])


def test_build_entry_uses_synopsis_when_budget(monkeypatch):
    isbn_resolve.reset_budget(0)
    catalog_media.reset_budgets(synopsis=5, covers=0)
    monkeypatch.setattr(
        catalog_media,
        "fetch_synopsis",
        lambda **kwargs: (
            "Sur une planète désertique, les Fremen protègent l'épice la plus "
            "convoité de l'univers tandis qu'une dynastie bascule.",
            "google_books",
        ),
    )
    cand = {
        "qid": "Q100",
        "name": "Saga Media",
        "category": "roman",
        "genre": "Fantasy",
        "cover_url": "https://example.test/c.jpg",
    }
    works = [
        {"title": "Un", "author": "A. Auteur", "published_year": 2020},
        {"title": "Deux", "author": "A. Auteur", "published_year": 2021},
    ]
    entry = daily_ingest.build_complete_entry(cand, works)
    assert entry is not None
    assert entry.get("needs_summary") is False
    assert entry.get("description", "").startswith("Sur une planète")
    assert entry["volume_details"]["1"]["description"].startswith("Sur une planète")
