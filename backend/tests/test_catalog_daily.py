"""Ajout quotidien de fiches complètes au noyau curé."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.catalog import daily_authors, daily_ingest, daily_pending, daily_store, expanded, isbn_resolve
from app.db_config import _mock_storage
from app.series_verification import curated as curated_mod


def _reset_daily():
    isbn_resolve.reset_budget(0)
    daily_ingest._active_window = 0
    store = _mock_storage.setdefault("catalog_daily_series", [])
    store.clear()
    _mock_storage.setdefault("authors", []).clear()
    _mock_storage.setdefault("catalog_daily_pending", []).clear()
    _mock_storage.pop("catalog_ingest_meta", None)
    daily_pending.reset_wd_budget(0)
    expanded.clear_cache()
    curated_mod.clear_cache()
    from app.catalog.seed import reset_seed_flag

    reset_seed_flag()


def test_complete_entry_requires_two_titles_author_and_cover():
    isbn_resolve.reset_budget(0)
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


def test_human_label_rejects_qid_keeps_real_titles():
    assert daily_ingest.is_human_label("Sa Majesté des mouches")
    assert daily_ingest.is_human_label("1984")
    assert daily_ingest.is_human_label("進撃の巨人")
    assert not daily_ingest.is_human_label("Q136831715")
    assert not daily_ingest.is_human_label("Q42")
    assert not daily_ingest.is_human_label("")
    assert not daily_ingest.is_human_label("?")


def test_complete_entry_rejects_qid_as_title_or_author():
    isbn_resolve.reset_budget(0)
    cand = {
        "qid": "Q136831715",
        "name": "Q136831715",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/c.jpg",
    }
    works = [{"title": "Q136831715", "author": "A. Auteur", "published_year": 2020}]
    assert daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True) is None
    cand["name"] = "Vrai Titre"
    works[0]["title"] = "Vrai Titre"
    works[0]["author"] = "Q42"
    assert daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True) is None
    works[0]["author"] = "A. Auteur"
    assert daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True) is not None


def test_complete_author_rejects_qid_as_name():
    cand = {
        "qid": "Q107883",
        "name": "Q107883",
        "photo_url": "https://example.test/a.jpg",
        "birth_date": "1900-01-01",
        "bio": "Bio.",
    }
    assert daily_authors.build_complete_author(cand) is None
    cand["name"] = "Vrai Auteur"
    assert daily_authors.build_complete_author(cand) is not None


def test_purge_qid_named_daily(monkeypatch):
    from app.db_config import MockCollection, _mock_storage

    monkeypatch.setenv("CATALOG_DAILY_PURGE", "1")
    _mock_storage["catalog_daily_series"] = []
    mock = MockCollection("catalog_daily_series")
    monkeypatch.setattr(daily_store, "_coll", lambda: mock)
    daily_store.upsert_series(
        {
            "qid": "Q136831715",
            "name": "Q136831715",
            "authors": ["A. Auteur"],
            "cover_url": "https://example.test/c.jpg",
            "volumes": 1,
            "volume_titles": {"1": "Q136831715"},
            "volume_details": {"1": {"author": "A. Auteur", "cover_url": "https://example.test/c.jpg"}},
            "source": "daily",
        }
    )
    daily_store.upsert_series(
        {
            "qid": "Qok",
            "name": "Officially Dead",
            "authors": ["A. Auteur"],
            "cover_url": "https://example.test/c.jpg",
            "volumes": 1,
            "volume_titles": {"1": "Officially Dead"},
            "volume_details": {"1": {"author": "A. Auteur", "cover_url": "https://example.test/c.jpg"}},
            "source": "daily",
        }
    )
    assert daily_ingest.purge_qid_named_daily() == 1
    names = {s.get("name") for s in daily_store.all_series()}
    assert "Officially Dead" in names
    assert "Q136831715" not in names


def test_standalone_book_one_volume_with_real_isbn():
    isbn_resolve.reset_budget(0)
    cand = {
        "qid": "Qsolo",
        "name": "Le Livre Seul",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/c.jpg",
    }
    works = [
        {"title": "Le Livre Seul", "author": "Solo Auteur", "published_year": 2019, "isbn": "9782070360024"}
    ]
    assert daily_ingest.build_complete_entry(cand, works) is None
    entry = daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True)
    assert entry is not None
    assert entry["volumes"] == 1
    assert entry["type"] == "standalone"
    assert entry["volume_details"]["1"]["isbn"] == "9782070360024"
    assert "est un roman" in entry["volume_details"]["1"]["description"]


def test_pick_isbn_checksum_et_isbn10():
    assert daily_ingest.pick_isbn("9782070123456") == ""
    assert daily_ingest.pick_isbn("978-2-07-036002-4") == "9782070360024"
    assert daily_ingest.pick_isbn("2070360024") == "9782070360024"


def test_build_entry_fills_isbn_from_other_sources(monkeypatch):
    isbn_resolve.reset_budget(5)
    monkeypatch.setattr(isbn_resolve, "resolve_isbn", lambda **kw: "9782070360024")
    cand = {
        "qid": "Qisbn",
        "name": "Sans Isbn Wikidata",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/c.jpg",
    }
    works = [{"title": "Sans Isbn Wikidata", "author": "Auteur X", "published_year": 2018}]
    entry = daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True)
    assert entry is not None
    assert entry["volume_details"]["1"]["isbn"] == "9782070360024"


def test_plafonds_quotidiens_par_defaut(monkeypatch):
    monkeypatch.delenv("CATALOG_DAILY_SERIES", raising=False)
    monkeypatch.delenv("CATALOG_DAILY_BOOKS", raising=False)
    monkeypatch.delenv("CATALOG_DAILY_FICHES", raising=False)
    monkeypatch.delenv("CATALOG_DAILY_AUTHORS", raising=False)
    assert daily_ingest.daily_series_limit() == 400
    assert daily_ingest.daily_books_limit() == 10000
    assert daily_ingest.daily_fiches_target() == 10000
    assert daily_ingest.catalog_goal() == 100000
    assert daily_authors.daily_authors_limit() == 10000


def test_ingest_status_exposes_catalog_goal():
    st = daily_ingest.ingest_status()
    assert st["goal_fiches"] == 100000
    assert "catalog_fiches" in st
    assert "remaining" in st
    assert st["remaining"] == max(0, st["goal_fiches"] - st["catalog_fiches"])
    assert "wd_window" in st


def test_ingest_stops_when_catalog_goal_reached(monkeypatch):
    _reset_daily()
    monkeypatch.setattr(daily_ingest, "catalog_fiche_total", lambda: 100000)
    monkeypatch.setattr(
        daily_ingest,
        "fetch_candidate_series",
        lambda limit: (_ for _ in ()).throw(AssertionError("ne doit pas requêter Wikidata")),
    )
    result = daily_ingest.run_daily_ingest()
    assert result["fiches"] == 0
    assert result["catalog_fiches"] == 100000
    assert result["goal_fiches"] == 100000


def test_ingest_skips_known_qid_and_incomplete(monkeypatch):
    _reset_daily()
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: {"Qknown"})
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(
        daily_ingest,
        "fetch_candidate_series",
        lambda limit: [
            {"qid": "Qknown", "name": "Déjà là", "category": "roman", "genre": "Roman", "cover_url": "https://x/c.jpg"},
            {"qid": "Qnew", "name": "Trop court", "category": "roman", "genre": "Roman", "cover_url": "https://x/c.jpg"},
        ],
    )
    monkeypatch.setattr(daily_ingest, "fetch_works", lambda qid: [{"title": "Seul", "author": ""}])
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
        {"title": "Le Premier", "title_en": "The First", "author": "Ève Test", "published_year": 2022, "isbn": "9782070360024", "work_qid": "Q11"},
        {"title": "Le Second", "author": "Ève Test", "published_year": 2023, "work_qid": "Q12"},
    ]
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [cand])
    monkeypatch.setattr(daily_ingest, "fetch_works", lambda qid: works)
    result = daily_ingest.run_daily_ingest(limit=3)
    assert result["added"] == 1
    assert result["fiches"] == 1
    assert result["tomes"] == 2
    stored = daily_store.all_series()
    assert stored[0]["name"] == "Chroniques de Pytest"
    assert stored[0]["volume_details"]["1"]["isbn"] == "9782070360024"
    expanded.clear_cache()
    assert all(s.get("qid") != "Q999001" for s in expanded.all_series())
    hits = expanded.search_series("Chroniques de Pytest")
    assert hits and hits[0]["name"] == "Chroniques de Pytest"
    assert hits[0]["source"] == "daily"
    entry = curated_mod.match_curated("Chroniques de Pytest")
    assert entry and entry.get("source") == "curated_daily"


def test_ingest_skips_overlay_series_like_one_piece(monkeypatch):
    _reset_daily()
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    cand = {
        "qid": "Q710662",
        "name": "One Piece",
        "category": "manga",
        "genre": "Manga",
        "cover_url": "https://example.test/cover.jpg",
    }
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [cand])
    monkeypatch.setattr(
        daily_ingest,
        "fetch_works",
        lambda qid: [
            {"title": "Romance Dawn", "author": "Eiichiro Oda", "published_year": 1997},
            {"title": "Baggy", "author": "Eiichiro Oda", "published_year": 1998},
        ],
    )
    result = daily_ingest.run_daily_ingest(limit=3)
    assert result["added"] == 0
    assert result["skipped"] >= 1
    assert not any(s.get("qid") == "Q710662" for s in daily_store.all_series())


def test_single_volume_series_kept_as_standalone(monkeypatch):
    _reset_daily()
    cand = {
        "qid": "Qonevol",
        "name": "Roman Unique",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/cover.jpg",
    }
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [cand])
    monkeypatch.setattr(
        daily_ingest,
        "fetch_works",
        lambda qid: [{"title": "Roman Unique", "author": "Solo", "published_year": 2020}],
    )
    result = daily_ingest.run_daily_ingest(limit=3)
    assert result["added"] == 1
    stored = [s for s in daily_store.all_series() if s.get("qid") == "Qonevol"]
    assert stored and stored[0]["type"] == "standalone"
    assert stored[0]["volumes"] == 1


def test_complete_entry_cover_from_real_isbn():
    isbn_resolve.reset_budget(0)
    daily_ingest._wiki_cover_budget = 0
    cand = {"qid": "Qcov", "name": "Sans Jaquette", "category": "roman", "genre": "Roman", "cover_url": ""}
    works = [
        {"title": "Sans Jaquette", "author": "A. Auteur", "published_year": 2018, "isbn": "9782070360024"}
    ]
    entry = daily_ingest.build_complete_entry(cand, works, min_volumes=1, standalone=True)
    assert entry is not None
    assert "9782070360024" in entry["cover_url"]


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
        "isbn": "9782070360024",
        "ol_key": "",
        "year": 2021,
    }
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
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
    body = r.json()
    assert body["target_fiches"] == 10000
    assert body["goal_fiches"] == 100000
    assert "catalog_fiches" in body


def test_fetch_candidate_books_pages_by_year(monkeypatch):
    from datetime import datetime, timezone

    calls: list[str] = []

    def fake_sparql(query, timeout=55):
        calls.append(query)
        return []

    monkeypatch.setattr(daily_ingest, "_sparql", fake_sparql)
    daily_ingest._active_window = 0
    daily_ingest.fetch_candidate_books(900)
    assert len(calls) >= 2
    assert any("YEAR(?date)" in c for c in calls)
    assert any("OPTIONAL { ?work wdt:P18 ?img." in c for c in calls)
    assert all("?author rdfs:label ?authorLabel" not in c for c in calls)
    assert any(str(datetime.now(timezone.utc).year) in c for c in calls)


def test_book_years_starts_with_recent():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).year
    years = daily_ingest._book_years(20, salt=0)
    assert years[0] == now
    assert now - 1 in years
    assert len(years) == 20
    assert len(set(years)) == 20


def test_book_years_rotates_with_window():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).year
    a = daily_ingest._book_years(20, salt=0)
    b = daily_ingest._book_years(20, salt=1)
    c = daily_ingest._book_years(20, salt=12)
    assert a[0] == now
    assert b[0] == now - 1
    assert a != b
    assert a != c
    assert len(set(b)) == 20
    assert set(a[:12]) == set(b[:12])


def test_remaining_quota_fills_with_authors(monkeypatch):
    _reset_daily()
    monkeypatch.setenv("CATALOG_DAILY_FICHES", "200")
    cand = {
        "qid": "Qfill1",
        "name": "Saga Quota",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "https://example.test/cover.jpg",
    }
    works = [
        {"title": "Un", "author": "A. Quota", "published_year": 2020},
        {"title": "Deux", "author": "A. Quota", "published_year": 2021},
    ]
    captured: dict = {}

    def fake_authors(cap, hints=None):
        captured["cap"] = cap
        return ["Auteur A", "Auteur B", "Auteur C", "Auteur D"], 0

    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [cand])
    monkeypatch.setattr(daily_ingest, "fetch_works", lambda qid: works)
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [])
    monkeypatch.setattr("app.catalog.daily_authors.ingest_authors", fake_authors)
    result = daily_ingest.run_daily_ingest()
    assert captured["cap"] == 199
    assert result["added_series"] == 1
    assert result["added_books"] == 0
    assert result["added_authors"] == 4
    assert result["fiches"] == 5
    assert result["target_fiches"] == 200


def test_author_year_slice_spreads_across_centuries():
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).year
    years = daily_authors._year_slice(40, salt=0)
    assert len(years) == 40
    assert len(set(years)) == 40
    assert min(years) >= 1800
    assert max(years) <= now
    assert max(years) - min(years) > 50


def test_author_year_slice_changes_with_window():
    a = daily_authors._year_slice(40, salt=0)
    b = daily_authors._year_slice(40, salt=1)
    assert a[0] != b[0]
    assert a != b


def test_series_and_books_offset_change_with_window(monkeypatch):
    series_q: list[str] = []
    book_q: list[str] = []

    def fake_series_sparql(query, timeout=55):
        series_q.append(query)
        return []

    def fake_book_sparql(query, timeout=55):
        book_q.append(query)
        return []

    monkeypatch.setattr(daily_ingest, "_sparql", fake_series_sparql)
    daily_ingest._active_window = 0
    daily_ingest.fetch_candidate_series(10)
    monkeypatch.setattr(daily_ingest, "_sparql", fake_book_sparql)
    daily_ingest.fetch_candidate_books(200)
    daily_ingest._active_window = 3
    series_q.clear()
    book_q.clear()
    monkeypatch.setattr(daily_ingest, "_sparql", fake_series_sparql)
    daily_ingest.fetch_candidate_series(10)
    monkeypatch.setattr(daily_ingest, "_sparql", fake_book_sparql)
    daily_ingest.fetch_candidate_books(200)
    assert any("OFFSET 240" in q for q in series_q)
    assert any("OFFSET " in q for q in book_q)


def test_begin_ingest_window_advances_each_lot(monkeypatch):
    _reset_daily()
    monkeypatch.delenv("CATALOG_WD_WINDOW", raising=False)
    first = daily_ingest.begin_ingest_window()
    second = daily_ingest.begin_ingest_window()
    assert first != second
    assert daily_ingest.window_salt() == second


def test_fetch_candidate_authors_many_years(monkeypatch):
    calls: list[str] = []

    def fake_sparql(query, timeout=55):
        calls.append(query)
        return []

    monkeypatch.setattr(daily_authors, "_sparql", fake_sparql)
    daily_ingest._active_window = 0
    daily_authors.fetch_candidate_authors(10000)
    assert len(calls) >= 70
    assert any("Q49757" in c for c in calls)


def test_fetch_candidate_authors_offset_rotates(monkeypatch):
    calls: list[str] = []

    def fake_sparql(query, timeout=55):
        calls.append(query)
        return []

    monkeypatch.setattr(daily_authors, "_sparql", fake_sparql)
    daily_ingest._active_window = 0
    daily_authors.fetch_candidate_authors(400)
    assert all("OFFSET" not in c for c in calls)
    calls.clear()
    daily_ingest._active_window = 1
    daily_authors.fetch_candidate_authors(400)
    assert any("OFFSET 80" in c for c in calls)


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


def _isolate_catalog(monkeypatch):
    _reset_daily()
    from app.db_config import MockCollection
    from app.catalog import seed as seed_mod

    monkeypatch.setattr(daily_pending, "_coll", lambda: MockCollection("catalog_daily_pending"))
    monkeypatch.setattr(daily_store, "_coll", lambda: MockCollection("catalog_daily_series"))
    monkeypatch.setattr(daily_authors, "_coll", lambda: MockCollection("authors"))
    monkeypatch.setattr(seed_mod, "ensure_seeded", lambda **k: {"status": "skipped_test", "seeded": False})


def test_incomplete_book_queued_unique_not_counted(monkeypatch):
    _isolate_catalog(monkeypatch)
    book = {
        "qid": "Qpend1",
        "name": "Roman Sans Jaquette",
        "author": "Jane Doe",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "",
        "isbn": "",
        "ol_key": "",
        "year": 2021,
    }
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [])
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [book, dict(book)])
    monkeypatch.setattr(daily_pending, "enrich_work_candidate", lambda cand, works: None)
    result = daily_ingest.run_daily_ingest(limit=0, books_limit=5)
    assert result["added_books"] == 0
    assert result["fiches"] == 0
    pending = _mock_storage.get("catalog_daily_pending") or []
    assert len(pending) == 1
    assert pending[0]["qid"] == "Qpend1"
    assert pending[0]["kind"] == "book"
    assert not any(s.get("qid") == "Qpend1" for s in (_mock_storage.get("catalog_daily_series") or []))
    assert daily_pending.count() == 1


def test_qid_name_and_known_not_queued(monkeypatch):
    _isolate_catalog(monkeypatch)
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: {"Qknown"})
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(
        daily_ingest,
        "fetch_candidate_series",
        lambda limit: [
            {"qid": "Qknown", "name": "Déjà là", "category": "roman", "genre": "Roman", "cover_url": "https://x/c.jpg"},
            {
                "qid": "Q136831715",
                "name": "Q136831715",
                "category": "roman",
                "genre": "Roman",
                "cover_url": "",
            },
        ],
    )
    monkeypatch.setattr(daily_ingest, "fetch_works", lambda qid: [{"title": "Un", "author": "A. Auteur"}])
    monkeypatch.setattr(daily_pending, "enrich_work_candidate", lambda cand, works: None)
    daily_ingest.run_daily_ingest(limit=5)
    assert daily_pending.count() == 0


def test_cover_enrichment_saves_book_instead_of_pending(monkeypatch):
    _isolate_catalog(monkeypatch)
    book = {
        "qid": "Qcover1",
        "name": "Roman Recupere",
        "author": "Jane Doe",
        "category": "roman",
        "genre": "Roman",
        "cover_url": "",
        "isbn": "",
        "year": 2020,
    }

    def fake_enrich(cand, works):
        cand["cover_url"] = "https://covers.openlibrary.org/b/id/99-M.jpg"

    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [])
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [book])
    monkeypatch.setattr(daily_pending, "enrich_work_candidate", fake_enrich)
    result = daily_ingest.run_daily_ingest(limit=0, books_limit=5)
    assert result["added_books"] == 1
    assert result["fiches"] == 1
    assert daily_pending.count() == 0
    stored = [s for s in daily_store.all_series() if s.get("qid") == "Qcover1"]
    assert stored and stored[0]["cover_url"].startswith("https://")


def test_promote_pending_book_once_cover_found(monkeypatch):
    _isolate_catalog(monkeypatch)
    daily_pending.remember(
        "book",
        {
            "qid": "Qlater",
            "name": "Livre En Attente",
            "author": "Paul Test",
            "category": "roman",
            "genre": "Roman",
            "cover_url": "",
        },
        reason="incomplete",
        works=[{"title": "Livre En Attente", "author": "Paul Test", "published_year": 2019}],
        known=set(),
        names=set(),
    )
    assert daily_pending.count() == 1
    assert not any(s.get("qid") == "Qlater" for s in (_mock_storage.get("catalog_daily_series") or []))

    def fake_enrich(cand, works):
        cand["cover_url"] = "https://example.test/recovered.jpg"

    monkeypatch.setattr(daily_pending, "enrich_work_candidate", fake_enrich)
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "existing_names", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [])
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [])
    monkeypatch.setattr(daily_authors, "fetch_candidate_authors", lambda limit: [])
    result = daily_ingest.run_daily_ingest()
    assert result["recovered"] == 1
    assert result["added_books"] == 1
    assert daily_pending.count() == 0
    stored = [s for s in daily_store.all_series() if s.get("qid") == "Qlater"]
    assert stored and stored[0]["authors"] == ["Paul Test"]


def test_promote_pending_author_after_photo(monkeypatch):
    _isolate_catalog(monkeypatch)
    from app.db_config import MockCollection

    mock_authors = MockCollection("authors")
    monkeypatch.setattr(daily_authors, "_coll", lambda: mock_authors)
    monkeypatch.setattr("app.authors.service.authors_collection", mock_authors)
    daily_pending.remember(
        "author",
        {"qid": "Qada2", "name": "Ada Pending", "photo_url": "", "birth_date": ""},
        reason="incomplete",
        known=set(),
        names=set(),
    )
    assert daily_pending.count() == 1

    def fake_enrich(cand):
        cand["photo_url"] = "https://example.test/ada2.jpg"
        cand["birth_date"] = "1815-12-10"

    monkeypatch.setattr(daily_pending, "enrich_author_candidate", fake_enrich)
    monkeypatch.setattr(daily_ingest, "existing_qids", lambda: set())
    monkeypatch.setattr(daily_ingest, "fetch_candidate_series", lambda limit: [])
    monkeypatch.setattr(daily_ingest, "fetch_candidate_books", lambda limit: [])
    monkeypatch.setattr(daily_authors, "fetch_candidate_authors", lambda limit: [])
    monkeypatch.setattr(daily_authors, "known_qids", lambda: set())
    monkeypatch.setattr(daily_authors, "known_names", lambda: set())
    result = daily_ingest.run_daily_ingest()
    assert result["recovered"] == 1
    assert result["added_authors"] == 1
    assert daily_pending.count() == 0
    stored = [a for a in _mock_storage.get("authors", []) if a.get("wikidata_qid") == "Qada2"]
    assert stored and stored[0]["photo_url"].startswith("https://")
