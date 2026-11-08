"""Tests du niveau "référence/officiel" (référentiel curé) et de son appariement."""

import json

from app.catalog import expanded
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


def test_noyau_cure_inclut_le_catalogue_50000():
    entry = curated.match_curated("Shannara")
    assert entry is not None
    assert int(entry["volumes"]) >= 3
    assert entry.get("source") == "curated_core"


def test_overlay_riche_reste_prioritaire_sur_le_noyau():
    entry = curated.match_curated("Harry Potter")
    assert entry is not None
    assert entry.get("source") == "curated_overlay"
    assert entry["volumes"] == 7


def test_curated_reutilise_le_json_expanded_sans_le_relire(tmp_path, monkeypatch):
    path = tmp_path / "expanded_fiches_catalog.json"
    path.write_text(
        json.dumps(
            {
                "meta": {},
                "series": [
                    {
                        "name": "Serie Unique Test XYZ",
                        "authors": ["Auteur"],
                        "volumes": 2,
                        "volume_titles": {"1": "Tome un"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(expanded, "_PATH", path)
    expanded.clear_cache()
    curated.clear_cache()

    opens = {"n": 0}
    builtin_open = open

    def counting_open(file, *args, **kwargs):
        if str(file) == str(path):
            opens["n"] += 1
        return builtin_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", counting_open)
    try:
        entry = curated.match_curated("Serie Unique Test XYZ")
        assert entry is not None
        assert entry.get("source") == "curated_core"
        assert opens["n"] == 1

        curated.clear_cache()
        again = curated.match_curated("Serie Unique Test XYZ")
        assert again is not None
        assert opens["n"] == 1
    finally:
        expanded.clear_cache()
        curated.clear_cache()
