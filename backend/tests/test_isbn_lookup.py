from app.openlibrary.isbn_lookup import (
    _clean_bnf_author,
    _clean_bnf_title,
    clean_isbn,
    is_valid_isbn,
    isbn10_to_13,
    isbn13_to_10,
    isbn_variants,
)


def test_clean_isbn_keeps_digits_and_x():
    assert clean_isbn("978-2-07-036002-4") == "9782070360024"
    assert clean_isbn("2-07-036002-4") == "2070360024"
    assert clean_isbn("0-8044-2957-x") == "080442957X"


def test_valid_and_invalid_checksums():
    assert is_valid_isbn("9782070360024")
    assert is_valid_isbn("2070360024")
    assert is_valid_isbn("080442957X")
    assert not is_valid_isbn("9782070360025")
    assert not is_valid_isbn("9780000000003")
    assert not is_valid_isbn("12345")


def test_isbn_conversions_round_trip():
    assert isbn10_to_13("2070360024") == "9782070360024"
    assert isbn13_to_10("9782070360024") == "2070360024"
    assert isbn13_to_10("9791234567896") == ""
    assert isbn_variants("9782070360024") == ["9782070360024", "2070360024"]
    assert isbn_variants("2070360024") == ["2070360024", "9782070360024"]


def test_bnf_fields_are_cleaned():
    assert _clean_bnf_title("Memory / Arnaud Delalande") == "Memory"
    assert (
        _clean_bnf_author("Delalande, Arnaud (1971-....). Auteur du texte")
        == "Arnaud Delalande"
    )
