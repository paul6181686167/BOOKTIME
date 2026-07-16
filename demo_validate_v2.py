"""
Collecte rapide (~2000 livres OL) + analyse complete pipeline V2 affine.
Valide la non-regression sur du vrai trafic OL.
"""
import json, sys, time, random, requests
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from demo_pipeline_v2 import detect_v2, series_match, check_wikidata_v2

CACHE_FILE  = "demo_validate_v2_books.json"
TARGET      = 2000
SUBJECTS    = [
    "fantasy", "science fiction", "mystery", "thriller",
    "young adult fiction", "romance", "manga", "comics",
    "historical fiction", "horror", "adventure",
]

# ── Collecte OL ───────────────────────────────────────────────────────────────
def fetch_ol(subject, target=200):
    out = {}
    offset = 0
    while len(out) < target:
        try:
            r = requests.get(
                "https://openlibrary.org/search.json",
                params={
                    "q": f"subject:{subject}",
                    "fields": "title,author_name,first_publish_year,edition_count",
                    "limit": 100,
                    "offset": offset,
                },
                timeout=15,
            )
            docs = r.json().get("docs", [])
            if not docs:
                break
            for d in docs:
                t = (d.get("title") or "").strip()
                if t:
                    out[t] = {"title": t, "subject": subject}
            offset += 100
            time.sleep(0.3)
        except Exception as e:
            print(f"  [WARN] {subject}: {e}")
            time.sleep(2)
            break
    return out

def collect():
    if Path(CACHE_FILE).exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            books = json.load(f)
        print(f"  Cache charge : {len(books)} livres depuis {CACHE_FILE!r}")
        return books
    books = {}
    per_subject = max(TARGET // len(SUBJECTS), 100)
    for s in SUBJECTS:
        print(f"  Collecte '{s}' ...", end=" ", flush=True)
        chunk = fetch_ol(s, per_subject)
        books.update(chunk)
        print(f"{len(chunk)} → total {len(books)}")
        if len(books) >= TARGET * 1.5:
            break
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(books.values()), f, ensure_ascii=False)
    print(f"  Sauvegarde : {len(books)} livres → {CACHE_FILE!r}")
    return list(books.values())

# ── Analyse ───────────────────────────────────────────────────────────────────
def analyze(books):
    methods   = Counter()
    detected  = Counter()
    s_books   = []
    st_books  = []
    t0 = time.time()
    for b in books:
        title = b.get("title", "")
        saga  = b.get("saga", "")
        res = detect_v2(title, saga_ol=saga, use_wikidata=False)
        if res["is_series"]:
            methods[res.get("method", "??")] += 1
            detected[res["series_name"]] += 1
            s_books.append((title, res["series_name"], res.get("method", "")))
        else:
            st_books.append(title)
    elapsed = time.time() - t0
    n = len(books)
    print(f"\n  Temps : {elapsed:.1f}s  ({n/elapsed:.0f} livres/s)")
    print(f"  Serie detectee : {len(s_books):>5}  ({100*len(s_books)/n:.1f}%)")
    print(f"  Standalone     : {len(st_books):>5}  ({100*len(st_books)/n:.1f}%)")
    print(f"\n  Methodes :")
    for m, c in sorted(methods.items(), key=lambda x: -x[1]):
        print(f"    {m:<35} {c:>5}")
    print(f"\n  Top 20 series :")
    for name, cnt in detected.most_common(20):
        print(f"    {cnt:>4}x  {name}")
    return s_books, st_books

# ── Validation Wikidata ───────────────────────────────────────────────────────
def validate_wikidata(s_books, st_books):
    print(f"\n  Validation Wikidata (50 series + 50 standalone) ...")
    sample_s  = random.sample(s_books,  min(50, len(s_books)))
    sample_st = random.sample(st_books, min(50, len(st_books)))

    ok_s = fp = ok_st = fn = 0
    fp_ex = []; fn_ex = []

    for title, name, method in sample_s:
        res = check_wikidata_v2(title)
        if res and res.get("series_name"):
            ok_s += 1
        else:
            fp += 1
            fp_ex.append(f"  [FP] \"{title}\" → {name} [{method}]")

    for title in sample_st:
        res = check_wikidata_v2(title)
        if res and res.get("series_name"):
            fn += 1
            fn_ex.append(f"  [FN] \"{title}\"")
        else:
            ok_st += 1

    ns = len(sample_s); nst = len(sample_st)
    precision = (ok_s / ns)  if ns else 0
    recall    = (ok_st/ nst) if nst else 0
    f1 = 2*precision*recall/(precision+recall) if (precision+recall) else 0

    print(f"\n    Series OK / echantillon : {ok_s}/{ns}")
    print(f"    Faux positifs           : {fp}/{ns}")
    print(f"    Standalone OK           : {ok_st}/{nst}")
    print(f"    Faux negatifs (FN)      : {fn}/{nst}")
    print(f"\n    Precision estimee : {100*precision:.1f}%")
    print(f"    Rappel estime     : {100*recall:.1f}%")
    print(f"    F1 estime         : {100*f1:.1f}%")

    if fp_ex:
        print(f"\n  Faux positifs ({len(fp_ex)}) :")
        for x in fp_ex[:10]: print(x)
    if fn_ex:
        print(f"\n  Faux negatifs ({len(fn_ex)}) :")
        for x in fn_ex[:10]: print(x)

# ── Main ──────────────────────────────────────────────────────────────────────
print("\n" + "="*68)
print("  VALIDATION PIPELINE V2 AFFINE")
print("="*68)
books = collect()
if isinstance(books, dict):
    books = list(books.values())
s_books, st_books = analyze(books)
validate_wikidata(s_books, st_books)
print("\n" + "="*68)
