from app.catalog.catalog_titles_fr import (
    apply_french_title,
    alias_french_title,
    looks_french,
    needs_french_title,
)


def test_looks_french():
    assert looks_french("Le Hobbit")
    assert looks_french("L'Étranger")
    assert not looks_french("The Hobbit")
    assert not looks_french("Dune")


def test_alias_hobbit():
    fr = alias_french_title("The Hobbit")
    assert fr
    assert looks_french(fr)


def test_apply_keeps_english():
    doc = {"qid": "OL1W", "name": "The Hobbit", "language": "anglais"}
    assert needs_french_title(doc)
    assert apply_french_title(doc, "Le Hobbit", "alias")
    assert doc["name"] == "Le Hobbit"
    assert doc["name_en"] == "The Hobbit"
    assert doc["title_fr"] == "Le Hobbit"


def test_needs_false_when_already_fr():
    doc = {"name": "L'Étranger", "language": "français"}
    assert not needs_french_title(doc)
