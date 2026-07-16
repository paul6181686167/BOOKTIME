"""
Relance uniquement l'analyse pipeline + validation Wikidata sur les livres deja collectes.
Evite de refaire la collecte OL (longue).
"""
import json, sys, time, random
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from demo_pipeline_v2 import detect_v2, series_match, check_wikidata_v2

RESULTS_FILE = "demo_large_scale_results.json"

# ── Chargement ────────────────────────────────────────────────────────────────
print("\n" + "="*68)
print("  REANALYSE PIPELINE V2 (sur livres OL deja collectes)")
print("="*68)

if not Path(RESULTS_FILE).exists():
    print(f"\n  [ERREUR] Fichier {RESULTS_FILE!r} introuvable.")
    print("  Lancez d'abord demo_large_scale_test.py pour collecter les livres.")
    sys.exit(1)

with open(RESULTS_FILE, encoding="utf-8") as f:
    books = json.load(f)
print(f"\n  {len(books)} livres charges depuis {RESULTS_FILE!r}")

# ── Analyse pipeline ──────────────────────────────────────────────────────────
print("\n  Analyse pipeline V2 ...")
t0 = time.time()
methods = Counter()
detected_series = Counter()
series_books = []
standalone_books = []

for b in books:
    title = b.get("title", "")
    saga  = b.get("saga", "") or b.get("series", "") or ""
    res = detect_v2(title, saga_ol=saga, use_wikidata=False)
    if res["is_series"]:
        methods[res.get("method", "unknown")] += 1
        detected_series[res["series_name"]] += 1
        series_books.append((title, res["series_name"], res.get("method", "")))
    else:
        standalone_books.append(title)

elapsed = time.time() - t0
n_series = len(series_books)
n_total  = len(books)
print(f"\n  Temps : {elapsed:.1f}s  ({n_total/elapsed:.0f} livres/s)")
print(f"\n  Serie detectee   : {n_series:>6}  ({100*n_series/n_total:.1f}%)")
print(f"  Standalone       : {len(standalone_books):>6}  ({100*len(standalone_books)/n_total:.1f}%)")

print(f"\n  Methodes de detection :")
for method, cnt in sorted(methods.items(), key=lambda x: -x[1]):
    print(f"    {method:<30} {cnt:>5}")

print(f"\n  Top 20 series detectees :")
for name, cnt in detected_series.most_common(20):
    print(f"    {cnt:>4}x  {name}")

# ── Validation Wikidata (echantillon) ─────────────────────────────────────────
print(f"\n  Validation Wikidata (echantillon 60 series + 60 standalone) ...")
sample_series = random.sample(series_books,     min(60, len(series_books)))
sample_standa = random.sample(standalone_books, min(60, len(standalone_books)))

wiki_ok_series = wiki_fp = wiki_ok_standa = wiki_fn = 0
fp_examples = []
fn_examples = []

for title, detected_name, method in sample_series:
    res = check_wikidata_v2(title)
    if res:
        wiki_ok_series += 1
    else:
        wiki_fp += 1
        fp_examples.append(f"  [FP] \"{title}\" → detecte: {detected_name} [{method}]")

for title in sample_standa:
    res = check_wikidata_v2(title)
    if res:
        wiki_fn += 1
        fn_examples.append(f"  [FN] \"{title}\"")
    else:
        wiki_ok_standa += 1

print(f"\n    Serie OK      : {wiki_ok_series}/{len(sample_series)}")
print(f"    Faux positifs : {wiki_fp}/{len(sample_series)}")
print(f"    Standalone OK : {wiki_ok_standa}/{len(sample_standa)}")
print(f"    Faux negatifs : {wiki_fn}/{len(sample_standa)}")

if fp_examples:
    print(f"\n  Faux positifs Wikidata ({len(fp_examples)}) :")
    for x in fp_examples[:10]: print(x)

if fn_examples:
    print(f"\n  Faux negatifs Wikidata ({len(fn_examples)}) :")
    for x in fn_examples[:10]: print(x)

n_s = len(sample_series); n_st = len(sample_standa)
fp_rate = wiki_fp / n_s  if n_s else 0
fn_rate = wiki_fn / n_st if n_st else 0
precision = 1 - fp_rate
recall    = 1 - fn_rate
f1 = 2*precision*recall/(precision+recall) if (precision+recall) else 0

print(f"\n  ── Estimation qualite pipeline ──")
print(f"    Precision estimee : {100*precision:.1f}%")
print(f"    Rappel estime     : {100*recall:.1f}%")
print(f"    F1 estime         : {100*f1:.1f}%")
print("\n" + "="*68)
