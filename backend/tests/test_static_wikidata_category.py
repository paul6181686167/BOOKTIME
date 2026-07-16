"""Tests de l'inférence de catégorie Wikidata statique (type P31 + genres P136)."""

import pytest

from app.static_wikidata.service import infer_series_category, is_real_series


@pytest.mark.parametrize(
    "row,expected",
    [
        ({"type": "manga series"}, "manga"),
        ({"type": "comics series"}, "bd"),
        ({"type": "comic book series"}, "bd"),
        ({"type": "novel series"}, "roman"),
        ({"type": "book series"}, "roman"),
        ({"type": "written work series"}, "roman"),
        # Repli sur les genres P136 des œuvres quand le type est générique.
        ({"type": "book series", "works": [{"genres_en": ["comics", "adventure comic"]}]}, "bd"),
        ({"type": "book series", "works": [{"genres_en": ["light novel"]}]}, "manga"),
        ({"type": "book series", "works": [{"genres_en": ["science fiction"]}]}, "roman"),
        # Repli sur les sujets série.
        ({"type": "book series", "main_subjects_en": ["graphic novel"]}, "bd"),
        # Robustesse.
        ({}, "roman"),
        (None, "roman"),
        ({"type": None, "works": None}, "roman"),
    ],
)
def test_infer_series_category(row, expected):
    assert infer_series_category(row) == expected


@pytest.mark.parametrize(
    "row,expected",
    [
        # Types curés : gardés même sans tome (série réelle, tomes absents de Wikidata).
        ({"type": "manga series", "work_count": 0}, True),
        ({"type": "children's book series", "work_count": 0}, True),
        ({"type": "seed series", "work_count": 0}, True),
        # Hub/franchise de découverte : exige >= 1 tome livre (sinon = série de jeux/films).
        ({"type": "literary series hub", "work_count": 116}, True),
        ({"type": "literary series hub", "work_count": 0}, False),
        ({"type": "literary franchise", "work_count": 0}, False),
        # Générique : exige >= 2 tomes (sinon = livre individuel mal étiqueté).
        ({"type": "book series", "work_count": 0}, False),
        ({"type": "book series", "work_count": 1}, False),
        ({"type": "book series", "work_count": 2}, True),
        ({"type": "written work series", "work_count": 0}, False),
        # Robustesse.
        (None, False),
    ],
)
def test_is_real_series(row, expected):
    assert is_real_series(row) is expected
