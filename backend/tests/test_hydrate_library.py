"""Une fiche ajoutée en bibliothèque est hydratée depuis le noyau curé."""
from app.catalog.hydrate import hydrate_book_dict, hydrate_series_dict


def test_hydrate_series_shannara_from_core():
    out = hydrate_series_dict(
        {
            "series_name": "Shannara",
            "authors": [],
            "category": "roman",
            "volumes": [
                {"volume_number": 1, "volume_title": "Shannara - Tome 1", "is_read": False},
            ],
            "total_volumes": 1,
            "description_fr": "Série de roman par Terry Brooks. Comprend 1 tome.",
        }
    )
    assert out["series_name"] == "Shannara"
    assert int(out["total_volumes"]) >= 3
    assert len(out["volumes"]) >= 3
    generic = [v for v in out["volumes"] if " - Tome " in (v.get("volume_title") or "")]
    assert len(generic) < len(out["volumes"]) / 2
    assert out.get("curated_source") == "curated_core"
    assert out.get("genre")
    titled = [v["volume_title"] for v in out["volumes"][:3]]
    assert all(titled)


def test_hydrate_preserves_read_flag():
    out = hydrate_series_dict(
        {
            "series_name": "Shannara",
            "volumes": [{"volume_number": 1, "volume_title": "X", "is_read": True}],
        }
    )
    assert out["volumes"][0]["is_read"] is True


def test_hydrate_book_attaches_saga():
    book = hydrate_book_dict(
        {
            "title": "Les Épées de Shannara",
            "author": "Terry Brooks",
            "saga": "",
            "cover_url": "",
        }
    )
    assert book.get("saga") == "Shannara"
    assert book.get("curated_source") == "curated_core"
    assert book.get("cover_url")
    assert book.get("genre")


def test_unknown_series_unchanged():
    raw = {"series_name": "Série Inventée XYZ 999", "volumes": [], "authors": ["Moi"]}
    out = hydrate_series_dict(raw)
    assert out["series_name"] == "Série Inventée XYZ 999"
    assert not out.get("curated_source")
