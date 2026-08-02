"""Priorité édition poche française pour le nombre de pages."""

from app.utils.book_synopsis import (
    _french_title_candidates,
    _is_secondary_literature,
    _score_fr_poche_text,
    _title_match_score,
)


def test_score_prefers_livre_de_poche():
    poche = _score_fr_poche_text(
        language="fre",
        format_text="paperback",
        publisher="Le Livre de Poche",
        title="Les Misérables",
    )
    hardcover = _score_fr_poche_text(
        language="fre",
        format_text="hardcover",
        publisher="Gallimard",
        title="Les Misérables",
    )
    assert poche > hardcover
    assert poche >= 145


def test_score_rejects_english_hardcover():
    score = _score_fr_poche_text(
        language="eng",
        format_text="hardcover",
        publisher="Penguin",
        title="The Hobbit",
    )
    assert score < 0


def test_score_accepts_pocket_publisher_without_lang():
    score = _score_fr_poche_text(
        language="",
        format_text="",
        publisher="Pocket",
        title="Une vie",
    )
    assert score >= 100


def test_rejects_etudes_as_title_match():
    assert _is_secondary_literature("Dix études sur les raisins de la colère de John Steinbeck")
    assert _title_match_score(
        "Les raisins de la colère",
        "Dix études sur les raisins de la colère de John Steinbeck",
    ) == 0


def test_exact_french_title_matches():
    assert (
        _title_match_score("Les raisins de la colère", "Les raisins de la colère")
        == 100
    )


def test_english_title_has_french_alias():
    cands = _french_title_candidates("Percy Jackson's Greek Gods")
    assert any("dieux grecs" in c.lower() for c in cands)
