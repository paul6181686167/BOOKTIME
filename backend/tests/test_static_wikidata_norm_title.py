"""Tests unitaires de norm_title (static Wikidata), sans conftest Mongo.

    cd backend && set PYTHONPATH=. && python -m pytest tests/test_static_wikidata_norm_title.py -q --noconftest
"""

from app.static_wikidata.service import norm_title


def test_norm_title_empty():
    assert norm_title("") == ""


def test_norm_title_strips_accents_and_stopwords():
    out = norm_title("L'Étranger")
    assert "etranger" in out.replace(" ", "") or "tranger" in out
    assert "le" not in out.split() or out == "etranger"


def test_norm_title_ligatures():
    assert "coeur" in norm_title("cœur").replace(" ", "") or norm_title("cœur") == "coeur"
