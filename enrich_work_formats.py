"""
Enrichissement : format réel (P31) de chaque œuvre liée à une série.

But : distinguer un vrai TOME (roman, manga, BD, recueil...) d'une pièce de théâtre,
d'un film, d'un jeu vidéo, etc. Wikidata mélange tout sous P179/P527/P361 ; sans le
type de l'œuvre, work_count est faussé (ex. Harry Potter compte "L'Enfant maudit"
[pièce] et des jeux vidéo comme des tomes).

Sortie : wikidata_work_formats.json = { work_qid: 0|1 }  (1 = format livre).
Resumable : relancer reprend où le checkpoint s'est arrêté.

Usage : python enrich_work_formats.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests

QLEVER = "https://qlever.dev/api/wikidata"
HEADERS = {
    "User-Agent": "BooktimeFormatEnricher/1.0",
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}
PREFIXES = """
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""
RAW_FILE = "wikidata_series_raw.json"
OUT_FILE = "wikidata_work_formats.json"
BATCH = 400
SLEEP = 0.4
SLEEP_ERR = 5.0
TIMEOUT = 30

# Formats considérés comme un "tome" (livre). Recherche par sous-chaîne sur le libellé EN du type P31.
_BOOK = re.compile(
    r"\b(novel|book|novella|short story|manga|manhwa|manhua|comic|comics|graphic novel|"
    r"light novel|picture book|poetry collection|poem|anthology|essay|fairy tale|"
    r"literary work|written work|monograph|textbook|tankobon|trade paperback|omnibus)\b",
    re.I,
)
# Formats explicitement NON-livre (priment quand aucun format livre n'est présent).
_NON_BOOK = re.compile(
    r"\b(film|movie|video game|board game|card game|role-playing game|television|"
    r"tv series|anime|ova|theatrical|stage play|play|musical|opera|song|single|"
    r"album|podcast|web series|episode|franchise|toy|attraction|theme park)\b",
    re.I,
)


def sparql(query: str, retries: int = 3):
    for attempt in range(retries):
        try:
            r = requests.post(QLEVER, data=(PREFIXES + query).encode(), headers=HEADERS, timeout=TIMEOUT)
            if r.status_code == 429:
                time.sleep(15)
                continue
            r.raise_for_status()
            return r.json().get("results", {}).get("bindings", [])
        except Exception as e:  # noqa: BLE001
            wait = SLEEP_ERR * (attempt + 1)
            print(f"  [WARN] {attempt+1}/{retries}: {str(e)[:70]} -> {wait:.0f}s", flush=True)
            time.sleep(wait)
    return None


def classify(type_labels: list[str]) -> int:
    """1 = livre ; 0 = non-livre. Défaut prudent = livre si aucun type connu."""
    blob = " ".join(type_labels)
    has_book = bool(_BOOK.search(blob))
    has_non_book = bool(_NON_BOOK.search(blob))
    if has_book:
        return 1
    if has_non_book:
        return 0
    return 1  # type inconnu : on ne jette pas un possible livre


def collect_work_qids() -> list[str]:
    raw = json.loads(Path(RAW_FILE).read_text(encoding="utf-8"))
    uniq: set[str] = set()
    for info in raw.values():
        for w in info.get("works") or []:
            wq = w.get("work_qid")
            if wq:
                uniq.add(wq)
    return sorted(uniq)


def main():
    out: dict[str, int] = {}
    if Path(OUT_FILE).exists():
        out = json.loads(Path(OUT_FILE).read_text(encoding="utf-8"))
        print(f"  Reprise : {len(out):,} formats déjà connus", flush=True)

    work_qids = collect_work_qids()
    todo = [q for q in work_qids if q not in out]
    total = len(todo)
    print(f"  Œuvres à enrichir : {total:,} (sur {len(work_qids):,})", flush=True)

    t0 = time.time()
    for i in range(0, total, BATCH):
        batch = todo[i : i + BATCH]
        values = " ".join(f"wd:{q}" for q in batch)
        query = f"""
SELECT ?work (GROUP_CONCAT(DISTINCT ?tl; separator="|") AS ?types) WHERE {{
  VALUES ?work {{ {values} }}
  OPTIONAL {{ ?work wdt:P31 ?t . ?t rdfs:label ?tl . FILTER(LANG(?tl) = "en") }}
}}
GROUP BY ?work
"""
        rows = sparql(query)
        if rows is None:
            print(f"  [ERR] lot {i} abandonné", flush=True)
            continue
        got = {r["work"]["value"].rsplit("/", 1)[-1] for r in rows}
        for r in rows:
            wq = r["work"]["value"].rsplit("/", 1)[-1]
            types = [t for t in (r.get("types", {}).get("value", "") or "").split("|") if t]
            out[wq] = classify(types)
        # Œuvres sans aucune ligne (type inconnu) : marquées livre par défaut.
        for wq in batch:
            if wq not in got:
                out[wq] = 1

        done = i + len(batch)
        if i % (BATCH * 20) == 0 or done >= total:
            Path(OUT_FILE).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
            eta = (time.time() - t0) / done * (total - done) / 60 if done else 0
            print(f"  {done:,}/{total:,}  ({100*done/total:.1f}%)  ETA {eta:.0f}min", flush=True)
        time.sleep(SLEEP)

    Path(OUT_FILE).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    books = sum(1 for v in out.values() if v)
    print(f"\n  ✓ {OUT_FILE} : {len(out):,} œuvres ({books:,} livres, {len(out)-books:,} non-livres)", flush=True)


if __name__ == "__main__":
    main()
