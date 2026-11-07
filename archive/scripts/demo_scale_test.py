"""
TEST A GRANDE ECHELLE -- Pipeline detection serie BOOKTIME
- Recupere ~5000 livres depuis Open Library (categories variees)
- Pour chaque livre : teste le pipeline (base statique + champ OL)
- Mesure precision, rappel, faux positifs, faux negatifs
- Wikidata active uniquement sur un echantillon de 100 cas limites

Lance avec : python demo_scale_test.py
Resultats sauvegardes dans : demo_scale_results.json
"""
import sys, json, time, requests, unicodedata, re
from pathlib import Path
from collections import defaultdict

# ─── Reutilise la base statique et le pipeline de demo_pipeline.py ────────────
sys.path.insert(0, str(Path(__file__).parent))
from demo_pipeline import detect, STATIC_DB, normalize, CACHE, cache_save

OL_SEARCH = "https://openlibrary.org/search.json"
RESULTS_FILE = Path("demo_scale_results.json")

# ─── Categories a interroger (titre OL + nombre cible) ────────────────────────
QUERIES = [
    ("fantasy fiction",              500),
    ("science fiction novel",        500),
    ("thriller mystery",             500),
    ("romance novel",                400),
    ("young adult fiction",          400),
    ("horror fiction",               300),
    ("historical fiction",           300),
    ("manga japanese comics",        400),
    ("graphic novel comics",         300),
    ("detective mystery police",     400),
]
# Total cible : 4000 + quelques centaines de bonus = ~5000

# ─── Recuperation OL ──────────────────────────────────────────────────────────
def fetch_ol_books(subject, target):
    """Recupere des livres OL par sujet, retourne une liste de dicts."""
    books = []
    page = 1
    per_page = 100
    seen = set()
    while len(books) < target:
        try:
            r = requests.get(OL_SEARCH, params={
                "q": subject,
                "fields": "key,title,author_name,series,first_publish_year,subject,edition_count",
                "limit": per_page,
                "offset": (page - 1) * per_page,
                "sort": "editions",
            }, timeout=12)
            if not r.ok:
                break
            docs = r.json().get("docs", [])
            if not docs:
                break
            for doc in docs:
                key = doc.get("key", "")
                if key in seen:
                    continue
                seen.add(key)
                raw_series = doc.get("series", [])
                saga = ""
                if raw_series:
                    s = raw_series[0] if isinstance(raw_series, list) else raw_series
                    if isinstance(s, str):
                        s = re.sub(r'[,\s]*[\(#]?\s*(?:book|tome|vol\.?|#)\s*\d+[\)]?.*$', '', s,
                                   flags=re.IGNORECASE).strip()
                        saga = s
                books.append({
                    "key": key,
                    "title": (doc.get("title") or "").strip(),
                    "author": ", ".join(doc.get("author_name") or []),
                    "saga_ol": saga,
                    "ol_has_series": bool(saga),
                    "edition_count": doc.get("edition_count", 0),
                    "subject": subject,
                })
            page += 1
            time.sleep(0.4)
        except Exception as e:
            print(f"  [OL] Erreur page {page} pour '{subject}': {e}")
            break
    return books[:target]

# ─── Pipeline sans Wikidata (test rapide) ─────────────────────────────────────
def detect_fast(title, saga_ol=""):
    """Pipeline sans appel reseau (base statique + champ OL seulement)."""
    from demo_pipeline import check_static
    static = check_static(title, saga_ol)
    if static:
        return {"is_series": True, "series_name": static["series_name"],
                "volume": static.get("volume"), "method": static["method"]}
    if saga_ol:
        return {"is_series": True, "series_name": saga_ol,
                "volume": None, "method": "ol_saga_field"}
    return {"is_series": False, "series_name": None, "volume": None, "method": "standalone"}

# ─── Test Wikidata sur echantillon ────────────────────────────────────────────
def wikidata_sample_test(disagreements, n=80):
    """
    Sur les n premiers cas ou notre pipeline dit 'standalone' mais OL dit 'serie',
    verifie avec Wikidata si c'est vraiment une serie.
    """
    from demo_pipeline import check_wikidata
    sample = disagreements[:n]
    wikidata_catches = 0
    print(f"\n  [Wikidata] Test sur {len(sample)} cas limites...")
    for book in sample:
        try:
            wd = check_wikidata(book["title"])
            if wd["series_name"]:
                wikidata_catches += 1
            time.sleep(0.3)
        except Exception:
            pass
    cache_save(CACHE)
    return wikidata_catches

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 72)
    print("  TEST ECHELLE -- Pipeline detection serie BOOKTIME")
    print("=" * 72)

    # 1. Collecte des livres OL
    all_books = []
    seen_keys = set()
    for subject, target in QUERIES:
        print(f"  [OL] '{subject}' => {target} livres...")
        batch = fetch_ol_books(subject, target)
        for b in batch:
            if b["key"] not in seen_keys:
                seen_keys.add(b["key"])
                all_books.append(b)
        print(f"       {len(batch)} recus | total: {len(all_books)}")

    total = len(all_books)
    print(f"\n  Total livres collectes : {total}")

    # 2. Pipeline sur tous les livres
    print(f"\n  Analyse en cours...")
    results = []
    method_counts = defaultdict(int)
    ol_series_total = 0
    our_series_total = 0
    true_positive = 0   # OL dit serie, on dit serie
    false_negative = 0  # OL dit serie, on dit standalone
    true_negative = 0   # OL dit standalone, on dit standalone
    false_positive = 0  # OL dit standalone, on dit serie
    fn_books = []       # livres rates (faux negatifs)
    fp_books = []       # faux positifs

    for i, book in enumerate(all_books):
        if (i + 1) % 500 == 0:
            print(f"    {i+1}/{total}...")

        res = detect_fast(book["title"], book["saga_ol"])
        method_counts[res["method"]] += 1

        ol_is_series = book["ol_has_series"]
        our_is_series = res["is_series"]

        if ol_is_series:
            ol_series_total += 1
        if our_is_series:
            our_series_total += 1

        if ol_is_series and our_is_series:
            true_positive += 1
        elif ol_is_series and not our_is_series:
            false_negative += 1
            fn_books.append(book)
        elif not ol_is_series and our_is_series:
            false_positive += 1
            fp_books.append({**book, "our_series": res["series_name"]})
        else:
            true_negative += 1

        results.append({**book, "our_series": res["series_name"],
                        "our_volume": res["volume"], "our_method": res["method"]})

    # 3. Wikidata sur les faux negatifs (echantillon)
    wd_extra = 0
    if fn_books:
        wd_extra = wikidata_sample_test(fn_books, n=min(80, len(fn_books)))

    # 4. Statistiques
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0
    recall    = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    accuracy  = (true_positive + true_negative) / total if total else 0

    print()
    print("=" * 72)
    print("  RESULTATS")
    print("=" * 72)
    print(f"  Livres testes        : {total}")
    print(f"  OL avec serie        : {ol_series_total} ({100*ol_series_total/total:.1f}%)")
    print(f"  Notre pipeline serie : {our_series_total} ({100*our_series_total/total:.1f}%)")
    print()
    print(f"  Vrais positifs (TP)  : {true_positive}  -- serie detectee correctement")
    print(f"  Faux negatifs (FN)   : {false_negative} -- serie OL ratee par notre pipeline")
    print(f"  Vrais negatifs (TN)  : {true_negative}  -- standalone correct")
    print(f"  Faux positifs (FP)   : {false_positive} -- serie inventee (pas dans OL)")
    print()
    print(f"  Precision  : {100*precision:.1f}%  (pas de fausse serie)")
    print(f"  Rappel     : {100*recall:.1f}%  (series OL detectees)")
    print(f"  F1-score   : {100*f1:.1f}%")
    print(f"  Exactitude : {100*accuracy:.1f}%")
    print()
    print(f"  Methodes utilisees :")
    for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
        print(f"    {method:<30} : {count}")
    print()
    if wd_extra:
        print(f"  Wikidata aurait recupere {wd_extra}/{min(80,len(fn_books))} series supplementaires")
        print(f"  => Rappel estime avec Wikidata : ~{100*(true_positive+wd_extra*(false_negative/max(1,min(80,len(fn_books)))))/ol_series_total:.1f}%")
    print()

    # 5. Exemples de faux negatifs (series ratees)
    print("  Top 20 series ratees (FN) -- OL les connait mais pas notre pipeline :")
    fn_by_series = defaultdict(int)
    for b in fn_books:
        fn_by_series[b["saga_ol"]] += 1
    for series, count in sorted(fn_by_series.items(), key=lambda x: -x[1])[:20]:
        print(f"    {count:3d}x  {series}")

    # 6. Exemples de faux positifs (series inventees)
    print()
    print("  Top 10 faux positifs (FP) -- notre pipeline invente une serie :")
    fp_seen = set()
    fp_shown = 0
    for b in fp_books:
        if b["our_series"] not in fp_seen:
            fp_seen.add(b["our_series"])
            print(f"    \"{b['title']}\" -> serie detectee: \"{b['our_series']}\"")
            fp_shown += 1
            if fp_shown >= 10:
                break

    # 7. Sauvegarde
    summary = {
        "total": total, "ol_series": ol_series_total, "our_series": our_series_total,
        "TP": true_positive, "FN": false_negative, "TN": true_negative, "FP": false_positive,
        "precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy,
        "wikidata_extra_on_sample": wd_extra,
        "fn_series": dict(sorted(fn_by_series.items(), key=lambda x: -x[1])[:50]),
        "fp_examples": [{"title": b["title"], "our_series": b["our_series"]} for b in fp_books[:30]],
        "methods": dict(method_counts),
    }
    RESULTS_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Resultats complets sauvegardes dans {RESULTS_FILE}")
    print("=" * 72)
    print()

if __name__ == "__main__":
    main()
