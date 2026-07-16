#!/usr/bin/env python3
"""
Après extraction QLever complète :

  1) (optionnel) Attente fin passe 2
  2) --reindex
  3) Vérification légère (subprocess verify_wikidata_series_export.py)
  4) Sitelinks QLever : toutes les séries + tous les work_qid (volumes) + top livres hors série
  5) Popularité unifiée **popularity** (entier 0–100) : même plage pour séries, tomes et cache standalone,
     à partir d'un pool global de **log1p(sitelinks)** (winsor 99e puis min–max sur ce pool).
  6) Fichier **popular_standalone_books.json** : les **standalone_top** livres les plus sitelinkés
     (œuvres Q571/Q8261 sans P179), hors série.

Usage :
  python post_extract_to_popularity.py
  python post_extract_to_popularity.py --skip-wait --skip-verify
  python post_extract_to_popularity.py --standalone-top 10000 --sparql-timeout 120
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from extract_wikidata_series import META_FILE, write_export_meta  # noqa: E402

QLEVER = "https://qlever.dev/api/wikidata"
HEADERS_SPARQL = {
    "User-Agent": "BooktimePostExtract/1.1 (educational)",
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}
SLEEP_ERR = 5.0
TIMEOUT_DEFAULT = 45
PREFIXES = """
PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
PREFIX wd:   <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wikibase: <http://wikiba.se/ontology#>
"""


def qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1] if uri else ""


def row_int(row: dict, key: str) -> int:
    raw = row.get(key, {}).get("value", "")
    if raw in ("", None):
        return 0
    try:
        return int(float(raw))
    except ValueError:
        return 0


def row_val(row: dict, key: str) -> str:
    return row.get(key, {}).get("value", "") or ""


def sparql(query: str, *, retries: int = 5, timeout: float = TIMEOUT_DEFAULT) -> list[dict] | None:
    full = PREFIXES + "\n" + query
    for attempt in range(retries):
        try:
            r = requests.post(
                QLEVER,
                data=full.encode(),
                headers=HEADERS_SPARQL,
                timeout=timeout,
            )
            if r.status_code == 429:
                print("  [RATE LIMIT] attente 20s ...", flush=True)
                time.sleep(20)
                continue
            r.raise_for_status()
            return r.json().get("results", {}).get("bindings", [])
        except Exception as e:
            wait = SLEEP_ERR * (attempt + 1)
            print(f"  [WARN] SPARQL {attempt + 1}/{retries}: {str(e)[:80]} → {wait:.0f}s", flush=True)
            time.sleep(wait)
    return None


def sitelinks_batch(qids: list[str]) -> dict[str, int]:
    if not qids:
        return {}
    values = " ".join(f"wd:{q}" for q in qids)
    q = f"""
SELECT ?item ?sc WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item wikibase:sitelinks ?sc . }}
}}
"""
    rows: list[dict] | None = None
    for outer in range(12):
        rows = sparql(q, retries=5, timeout=TIMEOUT_DEFAULT)
        if rows is not None:
            break
        wait = 20 * (outer + 1)
        print(f"  [WARN] Lot sitelinks échoué, nouvelle tentative dans {wait}s ...", flush=True)
        time.sleep(wait)
    out: dict[str, int] = {q: 0 for q in qids}
    if rows is None:
        print("  [ERR] Lot sitelinks : abandon après reprises.", flush=True)
        sys.exit(1)
    if not rows:
        return out
    for row in rows:
        item = qid(row.get("item", {}).get("value", ""))
        if not item:
            continue
        out[item] = row_int(row, "sc")
    return out


def fetch_standalone_labels_batch(work_qids: list[str]) -> dict[str, tuple[str, str]]:
    """work_qid -> (title_en, title_fr) via un seul lot VALUES."""
    if not work_qids:
        return {}
    values = " ".join(f"wd:{q}" for q in work_qids)
    q = f"""
SELECT ?work (SAMPLE(?labEN) AS ?title_en) (SAMPLE(?labFR) AS ?title_fr) WHERE {{
  VALUES ?work {{ {values} }}
  OPTIONAL {{ ?work rdfs:label ?labEN . FILTER(LANG(?labEN) = "en") }}
  OPTIONAL {{ ?work rdfs:label ?labFR . FILTER(LANG(?labFR) = "fr") }}
}}
GROUP BY ?work
"""
    rows = sparql(q, retries=4, timeout=TIMEOUT_DEFAULT)
    out: dict[str, tuple[str, str]] = {}
    if not rows:
        return out
    for row in rows:
        wq = qid(row.get("work", {}).get("value", ""))
        if wq.startswith("Q"):
            out[wq] = (row_val(row, "title_en"), row_val(row, "title_fr"))
    return out


def fetch_standalone_candidates(*, fetch_limit: int, timeout: float) -> list[dict]:
    """
    Livres « hors série » : instance de livre ou roman, sans déclaration P179.
    Phase 1 : tri strict par sitelinks (sans GROUP BY qui casse ORDER BY sur certains moteurs).
    Phase 2 : libellés FR/EN par lots.
    """
    query = f"""
SELECT ?work ?sc WHERE {{
  ?work wikibase:sitelinks ?sc .
  FILTER (
    EXISTS {{ ?work wdt:P31 ?c1 . ?c1 wdt:P279* wd:Q571 . }} ||
    EXISTS {{ ?work wdt:P31 ?c2 . ?c2 wdt:P279* wd:Q8261 . }}
  )
  FILTER NOT EXISTS {{ ?work wdt:P179 ?any }}
  FILTER NOT EXISTS {{ ?work wdt:P31 wd:Q5 }}
}}
ORDER BY DESC(?sc)
LIMIT {fetch_limit}
"""
    rows: list[dict] | None = None
    for outer in range(8):
        rows = sparql(query, retries=4, timeout=timeout)
        if rows is not None:
            break
        print(f"  [WARN] Requête standalone, retry {outer + 1}/8 ...", flush=True)
        time.sleep(30 * (outer + 1))
    if not rows:
        print("  [ERR] Aucun résultat standalone — cache vide.", flush=True)
        return []
    ordered: list[tuple[str, int]] = []
    for row in rows:
        wq = qid(row.get("work", {}).get("value", ""))
        if not wq.startswith("Q"):
            continue
        ordered.append((wq, row_int(row, "sc")))
    if not ordered:
        return []

    labels: dict[str, tuple[str, str]] = {}
    batch = 400
    for i in range(0, len(ordered), batch):
        chunk = [q for q, _ in ordered[i : i + batch]]
        labels.update(fetch_standalone_labels_batch(chunk))
        time.sleep(0.15)

    out: list[dict] = []
    for wq, sc in ordered:
        en, fr = labels.get(wq, ("", ""))
        out.append(
            {
                "work_qid": wq,
                "wikidata_sitelinks": sc,
                "title_en": en,
                "title_fr": fr,
            }
        )
    return out


def build_log1p_pool(
    *,
    series_sl: dict[str, int],
    series_ids: list[str],
    work_sl: dict[str, int],
    work_ids: set[str],
) -> list[float]:
    pool: list[float] = []
    for sid in series_ids:
        pool.append(math.log1p(float(series_sl.get(sid, 0))))
    for wq in work_ids:
        pool.append(math.log1p(float(work_sl.get(wq, 0))))
    return pool


def mapper_to_0_100(pool: list[float], *, high_q: float = 0.99):
    """Retourne une fonction float -> int 0..100 (winsor haute + min-max sur le pool)."""
    if not pool:
        return lambda _: 0

    arr = sorted(pool)
    n = len(arr)
    cap = float(arr[min(max(int(high_q * (n - 1)), 0), n - 1)])
    clipped = [min(x, cap) for x in pool]
    lo = float(min(clipped))
    hi = float(max(clipped))

    def to100(x: float) -> int:
        xc = min(float(x), cap)
        if hi <= lo:
            return 50
        v = 100.0 * (xc - lo) / (hi - lo)
        return int(max(0, min(100, round(v))))

    return to100


def save_json_atomic(path: Path, obj: object) -> None:
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def wait_extraction_complete(cp_path: Path, interval: int) -> None:
    print(f"\n  Attente fin passe 2 ({cp_path.name}) ...", flush=True)
    while True:
        with open(cp_path, encoding="utf-8") as f:
            cp = json.load(f)
        qids = cp.get("qids") or {}
        done = cp.get("works_done") or []
        n_q = len(qids) if isinstance(qids, dict) else 0
        n_d = len(set(done)) if isinstance(done, list) else 0
        if n_q > 0 and n_d >= n_q:
            print(f"  ✓ Passe 2 complète ({n_d:,} / {n_q:,}).", flush=True)
            return
        print(f"  … {n_d:,} / {n_q:,} — prochaine vérif. dans {interval}s", flush=True)
        time.sleep(interval)


def run_reindex(data_dir: Path, py: str) -> None:
    script = data_dir / "extract_wikidata_series.py"
    if not script.is_file():
        print(f"[ERR] Introuvable : {script}", flush=True)
        sys.exit(1)
    print("\n  Re-indexation (--reindex) ...", flush=True)
    r = subprocess.run([py, str(script), "--reindex"], cwd=str(data_dir), check=False)
    if r.returncode != 0:
        print(f"[ERR] --reindex code {r.returncode}.", flush=True)
        sys.exit(r.returncode)
    print("  ✓ Re-indexation terminée.", flush=True)


def run_verify(data_dir: Path, py: str) -> None:
    script = data_dir / "verify_wikidata_series_export.py"
    if not script.is_file():
        print("  [SKIP] verify_wikidata_series_export.py absent.", flush=True)
        return
    print("\n  Vérification export (verify_wikidata_series_export.py) ...", flush=True)
    r = subprocess.run([py, str(script), "--data-dir", str(data_dir)], cwd=str(data_dir), check=False)
    if r.returncode != 0:
        print("[ERR] Vérification export échouée.", flush=True)
        sys.exit(r.returncode)


def load_db(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def enrich(
    db: dict,
    *,
    batch_size: int,
    sleep_between: float,
    standalone_top: int,
    standalone_fetch_margin: int,
    sparql_timeout: float,
) -> tuple[dict, list[dict]]:
    by_qid = db.get("by_qid") or {}
    series_ids = list(by_qid.keys())

    print(f"\n  Sitelinks séries ({len(series_ids):,} QIDs) ...", flush=True)
    series_sl: dict[str, int] = {}
    for i in range(0, len(series_ids), batch_size):
        chunk = series_ids[i : i + batch_size]
        series_sl.update(sitelinks_batch(chunk))
        if (i // batch_size) % 25 == 0:
            j = min(i + batch_size, len(series_ids))
            print(f"    {j:,}/{len(series_ids):,} séries", flush=True)
        time.sleep(sleep_between)

    work_ids: set[str] = set()
    for entry in by_qid.values():
        for w in entry.get("works") or []:
            wq = w.get("work_qid")
            if isinstance(wq, str) and wq.startswith("Q"):
                work_ids.add(wq)

    fetch_n = standalone_top + standalone_fetch_margin
    print(f"\n  Livres hors série (SPARQL, jusqu'à {fetch_n:,} candidats) ...", flush=True)
    standalone_rows = fetch_standalone_candidates(fetch_limit=min(fetch_n, 50_000), timeout=sparql_timeout)
    standalone_rows.sort(key=lambda r: r["wikidata_sitelinks"], reverse=True)
    standalone_top_rows = standalone_rows[:standalone_top]
    for r in standalone_top_rows:
        work_ids.add(r["work_qid"])

    work_list = sorted(work_ids)
    print(f"\n  Sitelinks œuvres ({len(work_list):,} QIDs uniques, volumes + standalone) ...", flush=True)
    work_sl: dict[str, int] = {}
    for i in range(0, len(work_list), batch_size):
        chunk = work_list[i : i + batch_size]
        work_sl.update(sitelinks_batch(chunk))
        if (i // batch_size) % 60 == 0:
            j = min(i + batch_size, len(work_list))
            print(f"    {j:,}/{len(work_list):,} œuvres", flush=True)
        time.sleep(sleep_between)

    # Raffraîchir les sitelinks des standalone avec les lots (plus fiable que le GROUP BY initial)
    for r in standalone_top_rows:
        wq = r["work_qid"]
        r["wikidata_sitelinks"] = int(work_sl.get(wq, r["wikidata_sitelinks"]))

    pool = build_log1p_pool(
        series_sl=series_sl,
        series_ids=series_ids,
        work_sl=work_sl,
        work_ids=work_ids,
    )
    to100 = mapper_to_0_100(pool, high_q=0.99)
    print(f"\n  Pool popularité (log1p sitelinks) : {len(pool):,} valeurs → scores 0–100.", flush=True)

    out_by_qid: dict = {}
    for sid, entry in by_qid.items():
        sl = int(series_sl.get(sid, 0))
        ne = {k: v for k, v in entry.items() if k not in ("popularity_series", "popularity_work")}
        ne["wikidata_sitelinks"] = sl
        ne["popularity"] = to100(math.log1p(float(sl)))
        new_works = []
        for w in entry.get("works") or []:
            wq = w.get("work_qid")
            ww = {k: v for k, v in w.items() if k not in ("popularity_series", "popularity_work")}
            if isinstance(wq, str) and wq.startswith("Q"):
                wsl = int(work_sl.get(wq, 0))
                ww["wikidata_sitelinks"] = wsl
                ww["popularity"] = to100(math.log1p(float(wsl)))
            new_works.append(ww)
        ne["works"] = new_works
        out_by_qid[sid] = ne

    cache_books = []
    for r in standalone_top_rows:
        wq = r["work_qid"]
        sl = int(work_sl.get(wq, r["wikidata_sitelinks"]))
        cache_books.append(
            {
                "work_qid": wq,
                "wikidata_sitelinks": sl,
                "popularity": to100(math.log1p(float(sl))),
                "title_en": r.get("title_en") or "",
                "title_fr": r.get("title_fr") or "",
            }
        )

    return (
        {"by_qid": out_by_qid, "title_index": db.get("title_index") or {}},
        cache_books,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Reindex + popularité 0–100 + cache livres hors série.")
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--skip-wait", action="store_true")
    ap.add_argument("--wait-interval", type=int, default=120)
    ap.add_argument("--skip-reindex", action="store_true")
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--batch-size", type=int, default=200)
    ap.add_argument("--sleep-between", type=float, default=0.35)
    ap.add_argument("--standalone-top", type=int, default=10_000)
    ap.add_argument("--standalone-margin", type=int, default=2_000)
    ap.add_argument("--sparql-timeout", type=float, default=180.0)
    ap.add_argument("--output", type=Path, default=None)
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--python", type=str, default=sys.executable)
    args = ap.parse_args()

    data_dir: Path = args.data_dir.resolve()
    cp_path = data_dir / "wikidata_extract_checkpoint.json"
    db_path = data_dir / "wikidata_series_db.json"
    cache_path = data_dir / "popular_standalone_books.json"
    out_path = (args.output or db_path).resolve()

    if not args.skip_wait:
        if not cp_path.is_file():
            print(f"[ERR] Checkpoint absent : {cp_path}", flush=True)
            sys.exit(1)
        wait_extraction_complete(cp_path, args.wait_interval)

    if not args.skip_reindex:
        run_reindex(data_dir, args.python)

    if not args.skip_verify:
        run_verify(data_dir, args.python)

    if not db_path.is_file():
        print(f"[ERR] Index absent : {db_path}", flush=True)
        sys.exit(1)

    print(f"\n  Chargement {db_path.name} ...", flush=True)
    db = load_db(db_path)
    enriched, cache_books = enrich(
        db,
        batch_size=args.batch_size,
        sleep_between=args.sleep_between,
        standalone_top=args.standalone_top,
        standalone_fetch_margin=args.standalone_margin,
        sparql_timeout=args.sparql_timeout,
    )

    if out_path == db_path and db_path.is_file() and not args.no_backup:
        bak = db_path.with_suffix(".json.bak")
        print(f"\n  Copie sécurité → {bak.name}", flush=True)
        shutil.copy2(db_path, bak)

    print(f"\n  Écriture atomique {out_path.name} ...", flush=True)
    save_json_atomic(out_path, enriched)

    from datetime import datetime, timezone

    cache_doc = {
        "format": "booktime_popular_standalone_books",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_n": len(cache_books),
        "standalone_top_requested": args.standalone_top,
        "popularity_note": "Entier 0–100 : même loi que les séries/volumes (pool global log1p(sitelinks), winsor 0.99, min-max).",
        "books": cache_books,
    }
    print(f"\n  Écriture {cache_path.name} ({len(cache_books):,} livres) ...", flush=True)
    save_json_atomic(cache_path, cache_doc)

    n_series = len(enriched.get("by_qid") or {})
    write_export_meta(
        series_count=n_series,
        note="Index enrichi : popularity 0–100 (sitelinks) + cache popular_standalone_books.json.",
        extra={
            "index_enriched": True,
            "popular_standalone_file": cache_path.name,
            "popularity": {
                "field": "popularity",
                "range": "0-100 integer",
                "raw_axis": "log1p(wikidata_sitelinks)",
                "pool": "all series entities + all volume work_qids + standalone candidate work_qids",
                "normalization": "winsor_high_0.99_then_min_max_on_pool",
                "source_endpoint": QLEVER,
            },
        },
        out_path=data_dir / META_FILE,
    )
    print(f"  Métadonnées → {data_dir / META_FILE}", flush=True)
    print(f"\n  ✓ Terminé. Index : {out_path.name} | Cache standalone : {cache_path.name}", flush=True)


if __name__ == "__main__":
    main()
