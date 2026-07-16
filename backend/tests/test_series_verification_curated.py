"""Tests du niveau "référence/officiel" (référentiel curé) et de son appariement."""

from app.series_verification import curated


def test_curated_matches_harry_potter_exact():
    entry = curated.match_curated("Harry Potter", "J.K. Rowling")
    assert entry is not None
    assert entry["volumes"] == 7
    titles = [t["title"] for t in entry["volume_titles"]]
    assert len(titles) == 7
    assert any("école des sorciers" in t.lower() for t in titles)


def test_curated_matches_with_suffix_variation():
    # "Harry Potter (series)" doit toujours retomber sur l'entrée curée.
    entry = curated.match_curated("Harry Potter (series)")
    assert entry is not None
    assert entry["name"] == "Harry Potter"


def test_curated_respects_exclusions():
    # "cursed child" fait partie des exclusions de Harry Potter.
    entry = curated.match_curated("Harry Potter and the Cursed Child")
    assert entry is None or entry.get("name") != "Harry Potter"


def test_curated_author_mismatch_rejected():
    entry = curated.match_curated("Harry Potter", "Auteur Inconnu XYZ")
    assert entry is None


def test_curated_unknown_series_returns_none():
    assert curated.match_curated("Une Série Totalement Inventée 12345") is None


def test_curated_to_source_rows_uses_titles_when_present():
    entry = curated.match_curated("Harry Potter")
    rows = curated.curated_to_source_rows(entry)
    assert len(rows) == 7
    assert all(r["volume_number"] for r in rows)
    assert rows[0]["title"]
