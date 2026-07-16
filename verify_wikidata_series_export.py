#!/usr/bin/env python3
"""
Vérifications à grande échelle après reindex (ou avant popularité).

Contrôles :
  - Présence et JSON valide : checkpoint, brut, index
  - Cohérence des tailles (qids / brut / by_qid)
  - Chaque clé title_index → QID présent dans by_qid
  - work_qid : format Q…, unicité approximative (échantillon + comptage global)
  - Échantillon : entrées by_qid avec works ont volume / titres cohérents

Usage :
  python verify_wikidata_series_export.py
  python verify_wikidata_series_export.py --data-dir "D:\\...\\BOOKTIME-main" --sample 500
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

QID_RE = re.compile(r"^Q[1-9]\d*$")


def load_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser(description="Vérifications export Wikidata séries / index.")
    ap.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--sample", type=int, default=400, help="Taille échantillon aléatoire by_qid.")
    ap.add_argument("--work-sample-cap", type=int, default=500_000, help="Max work_qid pour comptage doublons.")
    args = ap.parse_args()
    d: Path = args.data_dir.resolve()

    raw_p = d / "wikidata_series_raw.json"
    db_p = d / "wikidata_series_db.json"
    cp_p = d / "wikidata_extract_checkpoint.json"

    errors: list[str] = []
    warns: list[str] = []

    for p in (raw_p, db_p, cp_p):
        if not p.is_file():
            errors.append(f"Fichier manquant : {p}")
    if errors:
        print("\n".join(errors), flush=True)
        sys.exit(1)

    print("  Chargement JSON (peut prendre une minute) ...", flush=True)
    raw = load_json(raw_p)
    db = load_json(db_p)
    cp = load_json(cp_p)

    if not isinstance(raw, dict):
        errors.append("wikidata_series_raw.json : racine doit être un objet.")
    if not isinstance(db, dict) or "by_qid" not in db:
        errors.append("wikidata_series_db.json : attendu { by_qid, title_index }.")
    if errors:
        print("\n".join(errors), flush=True)
        sys.exit(1)

    by_qid: dict = db["by_qid"]
    title_index: dict = db.get("title_index") or {}

    n_raw = len(raw)
    n_by = len(by_qid)
    n_cp_qids = len(cp.get("qids") or {})
    n_cp_done = len(set(cp.get("works_done") or []))

    print(f"\n  Séries brut (raw)     : {n_raw:,}")
    print(f"  Séries index (by_qid) : {n_by:,}")
    print(f"  Checkpoint qids       : {n_cp_qids:,}")
    print(f"  Checkpoint works_done : {n_cp_done:,}")
    print(f"  Entrées title_index   : {len(title_index):,}")

    if n_cp_qids > 0 and n_cp_done < n_cp_qids:
        errors.append(f"Passe 2 incomplète : works_done {n_cp_done} < qids {n_cp_qids}")
    if n_by > n_raw + 10:
        errors.append(f"by_qid ({n_by}) > raw ({n_raw}) de façon inattendue.")
    if n_by < n_raw * 0.5:
        warns.append(f"by_qid nettement < raw ({n_by} vs {n_raw}) — normal si beaucoup sans libellé FR/EN.")

    bad_ti = 0
    for k, q in title_index.items():
        if q not in by_qid:
            bad_ti += 1
            if bad_ti <= 5:
                errors.append(f"title_index[{k!r}] → {q} absent de by_qid")
    if bad_ti > 5:
        errors.append(f"title_index : {bad_ti} entrées pointent hors by_qid")

    # work_qid : format + doublons (cap mémoire)
    dup_counter: Counter[str] = Counter()
    n_works = 0
    bad_qid = 0
    for e in by_qid.values():
        for w in e.get("works") or []:
            wq = w.get("work_qid")
            if not wq:
                continue
            n_works += 1
            if not isinstance(wq, str) or not QID_RE.match(wq):
                bad_qid += 1
                if bad_qid <= 5:
                    errors.append(f"work_qid invalide : {wq!r}")
            if n_works <= args.work_sample_cap:
                dup_counter[wq] += 1

    multi = sum(1 for c in dup_counter.values() if c > 1)
    print(f"\n  Volumes (lignes works) : {n_works:,}")
    print(f"  work_qid invalides     : {bad_qid}")
    print(
        f"  work_qid repetes (max {args.work_sample_cap:,} premiers) : "
        f"{multi} QIDs apparaissent >1 fois (normal si meme tome cite par plusieurs series)"
    )

    # Échantillon by_qid
    keys = list(by_qid.keys())
    random.shuffle(keys)
    sample = keys[: min(args.sample, len(keys))]
    for q in sample:
        e = by_qid[q]
        if not e.get("name"):
            errors.append(f"[{q}] name vide")
        wc = e.get("work_count", len(e.get("works") or []))
        if wc != len(e.get("works") or []):
            warns.append(f"[{q}] work_count={wc} != len(works)={len(e.get('works') or [])}")

    if warns:
        print("\n  Avertissements :", flush=True)
        for w in warns[:30]:
            print(f"    • {w}", flush=True)
        if len(warns) > 30:
            print(f"    … +{len(warns) - 30} autres", flush=True)

    if errors:
        print("\n  ERREURS :", flush=True)
        for e in errors:
            print(f"    ✗ {e}", flush=True)
        sys.exit(1)

    print("\n  ✓ Vérifications OK.", flush=True)


if __name__ == "__main__":
    main()
