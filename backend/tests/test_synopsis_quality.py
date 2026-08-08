from app.utils.book_synopsis import (
    is_usable_synopsis,
    _sanitize_synopsis,
    _title_match_score,
)


def test_rejects_wikidata_meta():
    assert not is_usable_synopsis("Wikidata · 0 œuvre(s) · pop. —/100")
    assert not is_usable_synopsis("Wikidata · 9 œuvre(s) · pop. —/100")


def test_rejects_series_counters():
    assert not is_usable_synopsis("Série de 7 tome(s) de Ray Bradbury")
    assert not is_usable_synopsis("Série roman populaire.")


def test_accepts_real_blurb():
    blurb = (
        "Dans une Amérique futuriste, les pompiers brûlent les livres. "
        "Guy Montag commence à douter de sa mission."
    )
    assert is_usable_synopsis(blurb)


def test_strips_also_contained_in_markdown():
    raw = (
        "A Clockwork Orange is a dystopian novel by Anthony Burgess, published in 1962.\n\n"
        "Also contained in:\n"
        "[A Clockwork Orange and Honey for the Bears](https://openlibrary.org/works/OL23787405W)\n"
        "[A Clockwork Orange / The Wanting Seed](https://openlibrary.org/works/OL17306508W)\n"
    )
    cleaned = _sanitize_synopsis(raw)
    assert "dystopian novel" in cleaned
    assert "Also contained" not in cleaned
    assert "openlibrary.org" not in cleaned
    assert is_usable_synopsis(raw)


def test_title_match_rejects_unrelated_same_author():
    # Ne pas confondre « Kilimanjaro » avec n'importe quel Hemingway
    assert _title_match_score("Kilimanjaro", "For Whom the Bell Tolls") < 50
    assert _title_match_score("Kilimanjaro", "The Snows of Kilimanjaro") >= 50
