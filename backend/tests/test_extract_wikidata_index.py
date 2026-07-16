"""Tests pour build_index (extract_wikidata_series)."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "extract_wikidata_series",
    ROOT / "extract_wikidata_series.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules["extract_wikidata_series"] = mod
spec.loader.exec_module(mod)


def test_build_index_does_not_index_work_titles():
    series_data = {
        "Q8337": {
            "name_en": "Harry Potter",
            "name_fr": "",
            "name": "Harry Potter",
            "type": "literary series hub",
            "works": [
                {
                    "work_qid": "Q43361",
                    "title_en": "Harry Potter and the Philosopher's Stone",
                    "title_fr": "",
                }
            ],
        },
        "Q43361": {
            "name_en": "Harry Potter and the Philosopher's Stone",
            "name_fr": "",
            "name": "Harry Potter and the Philosopher's Stone",
            "type": "book series",
            "works": [],
        },
    }
    db = mod.build_index(series_data)
    ti = db["title_index"]
    assert ti[mod.norm("Harry Potter")] == "Q8337"
    # Ancien bug : le titre d'un tome dans works[] était indexé sous le QID parent.
    assert ti.get(mod.norm("Harry Potter and the Philosopher's Stone")) != "Q8337"


def test_build_index_dedupes_work_editions():
    series_data = {
        "Q8337": {
            "name_en": "Harry Potter",
            "name_fr": "",
            "name": "Harry Potter",
            "type": "children's book series",
            "works": [
                {"work_qid": "Q1", "title_en": "Philosopher's Stone", "title_fr": ""},
                {"work_qid": "Q2", "title_en": "Philosopher's Stone", "title_fr": ""},
                {"work_qid": "Q3", "title_en": "Chamber of Secrets", "title_fr": ""},
            ],
        }
    }
    db = mod.build_index(series_data)
    # 3 entrées brutes -> 2 tomes uniques (Philosopher's Stone dédoublonné).
    assert db["by_qid"]["Q8337"]["work_count"] == 2


def test_build_index_type_priority_beats_work_count():
    series_data = {
        "Q_hub": {
            "name_en": "Harry Potter",
            "name_fr": "",
            "name": "Harry Potter",
            "type": "literary series hub",
            "works": [{"work_qid": f"W{i}", "title_en": f"t{i}"} for i in range(19)],
        },
        "Q8337": {
            "name_en": "Harry Potter",
            "name_fr": "",
            "name": "Harry Potter",
            "type": "children's book series",
            "works": [{"work_qid": f"B{i}", "title_en": f"b{i}"} for i in range(7)],
        },
    }
    db = mod.build_index(series_data)
    # La série de livres curée gagne malgré moins de tomes que le hub.
    assert db["title_index"][mod.norm("Harry Potter")] == "Q8337"


def test_build_index_prefers_higher_work_count_on_collision():
    series_data = {
        "Q1": {
            "name_en": "Astérix",
            "name_fr": "Astérix",
            "name": "Astérix",
            "type": "comics series",
            "works": [{"work_qid": "W1"}, {"work_qid": "W2"}],
        },
        "Q2": {
            "name_en": "Astérix",
            "name_fr": "",
            "name": "Astérix",
            "type": "book series",
            "works": [],
        },
    }
    db = mod.build_index(series_data)
    assert db["title_index"][mod.norm("Astérix")] == "Q1"
