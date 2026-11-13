from __future__ import annotations

import gzip
import json
from pathlib import Path

from app.catalog import ol_dump_import
from app.catalog.daily_ingest import is_human_label


def _write_gz(path: Path, rows: list[tuple[str, str, dict]]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for typ, key, data in rows:
            fh.write(f"{typ}\t{key}\t1\t2020-01-01T00:00:00.000000\t{json.dumps(data)}\n")


def test_iter_json_records_and_author_keys(tmp_path: Path):
    f = tmp_path / "authors.txt.gz"
    _write_gz(
        f,
        [
            (
                "/type/author",
                "/authors/OL1A",
                {"name": "Alice Test", "personal_name": "Alice Test"},
            ),
            ("/type/author", "/authors/OL2A", {"name": "Q123"}),
        ],
    )
    rows = list(ol_dump_import._iter_json_records(str(f)))
    assert len(rows) == 2
    assert rows[0][1] == "/authors/OL1A"
    assert is_human_label(rows[0][2]["name"])


def test_work_author_keys_and_cover():
    data = {
        "title": "Roman Dump",
        "authors": [{"author": {"key": "/authors/OL9A"}}],
        "covers": [12345],
        "subjects": ["fiction", "manga"],
        "first_publish_date": "1998",
    }
    assert ol_dump_import._work_author_keys(data) == ["OL9A"]
    assert "12345" in ol_dump_import._cover_from_work(data)
    assert ol_dump_import._cat_from_subjects(data["subjects"])[0] == "manga"
    assert ol_dump_import._year_from_work(data) == 1998


def test_edition_keys_and_worker_sharding():
    data = {
        "title": "Edition Dump",
        "authors": [{"key": "/authors/OL8A"}],
        "isbn_13": ["9782070360024"],
        "covers": [9],
        "works": [{"key": "/works/OL1W"}],
        "publish_date": "2001",
    }
    assert ol_dump_import._author_keys_from_record(data) == ["OL8A"]
    assert ol_dump_import._year_from_record(data) == 2001
    assert ol_dump_import._worker_keeps(4, 0, 4) is True
    assert ol_dump_import._worker_keeps(5, 0, 4) is False
    assert ol_dump_import._worker_keeps(5, 1, 4) is True
