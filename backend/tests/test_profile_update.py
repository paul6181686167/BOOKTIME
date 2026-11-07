import base64

import pytest
from fastapi import HTTPException

from app.auth.routes import (
    MAX_BIO,
    MAX_DISPLAY_NAME,
    clean_profile_update,
    public_profile,
)

PIXEL = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode()


def test_public_profile_returns_empty_strings_when_missing():
    empty = {"display_name": "", "bio": "", "avatar_url": "", "username": ""}
    assert public_profile({}) == empty
    assert public_profile(None) == empty


def test_name_and_bio_are_trimmed():
    out = clean_profile_update({"display_name": "  Paul   B  ", "bio": "  Lecteur\r\nde SF  "})
    assert out == {"display_name": "Paul B", "bio": "Lecteur\nde SF"}


def test_only_sent_fields_are_returned():
    assert clean_profile_update({"bio": "Salut"}) == {"bio": "Salut"}


def test_too_long_name_or_bio_is_rejected():
    with pytest.raises(HTTPException) as e1:
        clean_profile_update({"display_name": "a" * (MAX_DISPLAY_NAME + 1)})
    assert e1.value.status_code == 400
    with pytest.raises(HTTPException) as e2:
        clean_profile_update({"bio": "a" * (MAX_BIO + 1)})
    assert e2.value.status_code == 400


def test_valid_avatar_is_kept_and_empty_removes_it():
    assert clean_profile_update({"avatar_url": PIXEL}) == {"avatar_url": PIXEL}
    assert clean_profile_update({"avatar_url": ""}) == {"avatar_url": ""}
    assert clean_profile_update({"avatar_url": None}) == {"avatar_url": ""}


@pytest.mark.parametrize(
    "bad",
    [
        "https://example.com/a.png",
        "data:text/html;base64,PGgxPg==",
        "data:image/svg+xml;base64,PHN2Zz4=",
        "data:image/png;base64,@@@@",
        "javascript:alert(1)",
    ],
)
def test_invalid_avatar_is_rejected(bad):
    with pytest.raises(HTTPException) as e:
        clean_profile_update({"avatar_url": bad})
    assert e.value.status_code == 400


def test_huge_avatar_is_rejected():
    huge = "data:image/jpeg;base64," + "A" * 200_000
    with pytest.raises(HTTPException):
        clean_profile_update({"avatar_url": huge})
