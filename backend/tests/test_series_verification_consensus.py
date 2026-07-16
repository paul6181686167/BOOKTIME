"""Tests de la vérification croisée multi-sources (logique pure)."""

from app.series_verification.consensus import (
    cross_verify,
    normalize_isbn,
    normalize_title_key,
    parse_volume_number,
)


def test_parse_volume_number_from_fields_and_titles():
    assert parse_volume_number(3) == 3
    assert parse_volume_number("03") == 3
    assert parse_volume_number(None, "One Piece, Tome 12") == 12
    assert parse_volume_number(None, "Naruto #7") == 7
    assert parse_volume_number(None, "Vol. 5: Something") == 5
    assert parse_volume_number(None, "Sans numéro") is None
    assert parse_volume_number(0, 99999) is None  # hors plage


def test_normalize_isbn_strips_non_digits():
    assert normalize_isbn("978-2-07-054127-0") == "9782070541270"
    assert normalize_isbn(None) == ""


def test_normalize_title_key_handles_accents_and_volume_words():
    # Accents/casse normalisés, mot "Tome" retiré, numéro conservé (l'appariement
    # par numéro s'occupe des tomes ; le titre seul reste discriminant).
    assert normalize_title_key("Astérix") == "asterix"
    assert normalize_title_key("Astérix, Tome 1") == "asterix 1"
    assert normalize_title_key("LE Hobbit") == normalize_title_key("le hobbit")


def test_confirmed_when_two_sources_agree_on_volume_number():
    report = cross_verify(
        {
            "wikidata": [{"title": "T1", "volume": "1"}, {"title": "T2", "volume": "2"}],
            "openlibrary": [{"title": "Tome 1", "volume": "Serie #1"}, {"title": "Tome 2", "volume": "Serie #2"}],
        }
    )
    assert report["confirmed_count"] == 2
    assert report["candidate_count"] == 2
    assert report["numbering"]["contiguous"] is True
    assert report["best_estimate_count"] == 2
    assert report["overall_confidence"] in ("eleve", "moyen")


def test_isbn_matches_across_sources_without_number():
    report = cross_verify(
        {
            "wikidata": [{"title": "Un livre", "isbns": ["978-2-07-054127-0"]}],
            "google_books": [{"title": "A Book", "isbn_13": "9782070541270"}],
        }
    )
    # Même ISBN -> 1 seul tome confirmé (2 sources).
    assert report["candidate_count"] == 1
    assert report["confirmed_count"] == 1


def test_single_source_with_number_is_probable():
    report = cross_verify({"wikidata": [{"title": "Solo", "volume": "1"}]})
    assert report["probable_count"] == 1
    assert report["confirmed_count"] == 0


def test_single_source_titleonly_is_uncertain():
    report = cross_verify({"openlibrary": [{"title": "Mystery Book"}]})
    assert report["uncertain_count"] == 1


def test_gaps_detected_in_numbering():
    report = cross_verify(
        {
            "wikidata": [
                {"title": "T1", "volume": "1"},
                {"title": "T2", "volume": "2"},
                {"title": "T5", "volume": "5"},
            ]
        }
    )
    assert report["numbering"]["gaps"] == [3, 4]
    assert report["numbering"]["contiguous"] is False


def test_intra_source_dedup_does_not_double_count():
    report = cross_verify(
        {
            "wikidata": [
                {"title": "Tome 1 (éd. 2001)", "volume": "1"},
                {"title": "Tome 1 (éd. 2010)", "volume": "1"},
            ]
        }
    )
    assert report["candidate_count"] == 1


def test_empty_sources_low_confidence():
    report = cross_verify({})
    assert report["candidate_count"] == 0
    assert report["best_estimate_count"] == 0
    assert report["overall_confidence"] == "faible"


def test_title_match_when_no_number():
    report = cross_verify(
        {
            "wikidata": [{"title": "Le Hobbit"}],
            "openlibrary": [{"title": "le hobbit"}],
        }
    )
    assert report["candidate_count"] == 1
    assert report["confirmed_count"] == 1


def test_reference_source_alone_is_confirmed():
    # Le niveau référence fait autorité : un tome présent y est "confirmé" même seul.
    report = cross_verify({"reference": [{"title": "Tome 1", "volume_number": 1}]})
    assert report["confirmed_count"] == 1
    assert report["volumes"][0]["confidence"] == "confirme"


def test_by_source_breakdown_present():
    report = cross_verify(
        {
            "wikidata": [{"title": "A", "volume": "1"}],
            "openlibrary": [{"title": "B", "volume": "Serie #2"}],
        }
    )
    assert "wikidata" in report["by_source"]
    assert "openlibrary" in report["by_source"]
    assert report["by_source"]["wikidata"][0]["volume_number"] == 1
