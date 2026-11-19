from pathlib import Path

from app.catalog import local_catalog_sqlite as local_cat


def test_local_catalog_upsert_and_known(tmp_path: Path, monkeypatch):
    db = tmp_path / "local.sqlite"
    monkeypatch.setenv("CATALOG_LOCAL_SQLITE", str(db))
    monkeypatch.setenv("CATALOG_DUMP_LOCAL", "1")
    local_cat._conn = None  # type: ignore[attr-defined]

    n = local_cat.upsert_series(
        [
            {
                "qid": "OL1W",
                "name": "Livre Test",
                "name_norm": "livre test",
                "source": "test",
                "added_at": "now",
            }
        ]
    )
    assert n == 1
    assert "OL1W" in local_cat.known_qids()
    assert local_cat.count_series() == 1
    assert local_cat.count_unsynced() == 1

    local_cat.upsert_authors([("OL1A", "Alice Test", "alice test")])
    assert local_cat.resolve_authors(["OL1A"])["OL1A"] == "Alice Test"

    local_cat.mark_synced(["OL1W"])
    assert local_cat.count_unsynced() == 0
