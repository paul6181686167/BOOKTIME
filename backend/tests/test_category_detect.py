"""Tests heuristiques prudentes de catégorie."""

from app.utils.category_detect import (
    detect_category_from_subjects,
    detect_category_from_google,
    detect_category_from_text_fallback,
)


def test_ol_comics_with_fiction_stays_roman():
    subjects = ["Fiction", "Fantasy fiction", "Comics adaptations"]
    assert detect_category_from_subjects(subjects, title="The Hobbit") == "roman"


def test_ol_comics_shelf_tags_on_novel_stay_roman():
    """OL ajoute souvent 'Comics & graphic novels' aux romans (adaptations)."""
    subjects = [
        "Fantasy",
        "hobbits",
        "wizards",
        "Fiction",
        "Graphic novels",
        "Comic books, strips",
        "Comics & graphic novels, fantasy",
    ]
    assert detect_category_from_subjects(subjects, title="The Hobbit") == "roman"


def test_ol_orient_express_comics_shelf_stays_roman():
    subjects = [
        "Mystery",
        "Fiction",
        "Literature",
        "Comics & graphic novels, crime & mystery",
    ]
    assert (
        detect_category_from_subjects(subjects, title="Murder on the Orient Express")
        == "roman"
    )


def test_ol_graphic_novel_subject_is_bd():
    subjects = ["Graphic novels", "Superheroes"]
    assert detect_category_from_subjects(subjects, title="Watchmen") == "bd"


def test_ol_manga_subject():
    subjects = ["Manga", "Japanese comics"]
    assert detect_category_from_subjects(subjects, title="Naruto") == "manga"


def test_ol_anime_alone_is_roman():
    subjects = ["Anime", "Fiction"]
    assert detect_category_from_subjects(subjects, title="Some Novel") == "roman"


def test_google_ignores_description_comic_mention():
    assert (
        detect_category_from_google(
            categories=["Fiction"],
            title="A Funny Novel",
            subtitle="",
            description="This comic tale of friendship...",
        )
        == "roman"
    )


def test_google_manga_shelf():
    assert (
        detect_category_from_google(
            categories=["Comics & Graphic Novels / Manga / Action"],
            title="One Piece",
            subtitle="",
        )
        == "manga"
    )


def test_fallback_japan_not_manga():
    assert (
        detect_category_from_text_fallback(
            title="Memoirs of a Geisha",
            description="A story set in Japan",
            subjects=["Fiction"],
        )
        == "roman"
    )


def test_fallback_bande_dessinee_is_bd():
    assert (
        detect_category_from_text_fallback(
            title="Astérix le Gaulois",
            subjects=["Bande dessinée"],
        )
        == "bd"
    )
