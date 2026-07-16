"""Modèle bibliothèque séries (sans Mongo)."""

from app.models.series import SeriesLibraryCreate, VolumeData


def test_series_library_create_dump_uses_series_name():
    doc = SeriesLibraryCreate(
        series_name="Ma saga",
        authors=["Auteur"],
        category="roman",
        volumes=[VolumeData(volume_number=1, volume_title="Tome 1", is_read=False)],
    )
    d = doc.model_dump()
    assert d["series_name"] == "Ma saga"
    assert d.get("name") is None
