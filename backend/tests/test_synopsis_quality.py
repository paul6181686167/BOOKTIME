from app.utils.book_synopsis import is_usable_synopsis


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
