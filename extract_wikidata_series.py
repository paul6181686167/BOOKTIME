"""
Extraction QLever → base statique de séries de livres/manga/BD.
QLever = miroir Wikidata ultra-rapide (0.5-2s par requête vs 60s+ timeout).

Passe 1    : QIDs + labels EN par type P31 (500/page)
Passe 1-extra : children's book series, heptalogy (v1.4)
Passe franchises : Q196600 avec œuvres littéraires P179 (v1.4)
Passe hubs P179  : séries-chapeaux (≥3 œuvres littéraires) (v1.4)
Passe seeds      : QIDs canoniques connus (v1.4)
Passe 1b   : Labels FR pour tous les QIDs (lots de 500)
Passe 2    : Oeuvres (P179 + P527 + P361) + métadonnées volume
Index      : wikidata_series_db.json — noms de série dans title_index (pas les tomes)

Le script est RESUMABLE — relancer = reprend où il s'est arrêté.

Usage :
  python extract_wikidata_series.py              # extraction complète (long)
  python extract_wikidata_series.py --incremental   # nouvelles passes seulement (recommandé)
  python extract_wikidata_series.py --discovery-only
  python extract_wikidata_series.py --reindex   # reconstruire l'index depuis le brut
"""

import json, os, time, re, unicodedata, requests, sys
from pathlib import Path
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────────
QLEVER          = "https://qlever.dev/api/wikidata"
HEADERS_SPARQL  = {
    "User-Agent":   "BooktimeSeriesExtractor/2.0 (educational)",
    "Content-Type": "application/sparql-query",
    "Accept":       "application/sparql-results+json",
}
RAW_FILE        = "wikidata_series_raw.json"
DB_FILE         = "wikidata_series_db.json"
CHECKPOINT      = "wikidata_extract_checkpoint.json"
META_FILE       = "wikidata_export_meta.json"
SCHEMA_FILE     = "wikidata_series_schema.json"
SCHEMA_VERSION  = "1.4.0"
PAGE_SIZE       = 500    # séries par page passe 1
FR_BATCH        = 500    # séries par lot passe 1b
WORKS_BATCH     = 100    # séries par lot passe 2
SLEEP           = 0.5    # pause entre requêtes (QLever est rapide)
SLEEP_ERR       = 5.0    # pause après erreur
TIMEOUT         = 30     # timeout requête

PREFIXES = """
PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
PREFIX wd:   <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

SERIES_TYPES = [
    ("Q7725634",  "book series"),
    ("Q1667921",  "novel series"),
    ("Q21191270", "manga series"),
    ("Q2368491",  "light novel series"),
    ("Q741470",   "comic book series"),
    ("Q14406742", "comics series"),
    ("Q47461344", "written work series"),
    ("Q27461053", "manhwa series"),
]

# Types P31 manquants dans v1.3 (ex. Harry Potter Q8337 = children's book series).
EXTRA_SERIES_TYPES = [
    ("Q47068459", "children's book series"),
    ("Q614101",   "heptalogy"),
]

# Œuvres littéraires acceptées pour relier une franchise / un hub P179.
LITERARY_WORK_VALUES = "wd:Q571 wd:Q8261 wd:Q47461344 wd:Q3331189"

FRANCHISE_TYPE_QID = "Q196600"
MIN_P179_HUB_WORKS = 3
P179_HUB_PAGE_SIZE = 500
FRANCHISE_PAGE_SIZE = 500

# Séries-chapeaux connues absentes de la passe 1 d'origine (filet de sécurité).
# QID vérifiés via QLever (rdfs:label + P31). Certaines n'ont aucun tome lié dans
# Wikidata (ex. Naruto) : elles apparaissent quand même, les tomes venant d'OL/GB au runtime.
KNOWN_SEED_QIDS = [
    "Q8337",      # Harry Potter
    "Q180736",    # One Piece (manga, série)
    "Q26971382",  # Naruto (manga series)
    "Q464035",    # Le Seigneur des Anneaux
    "Q147810",    # Astérix
]

PASS_FRANCHISES = "__franchises_literary__"
PASS_P179_HUBS = "__p179_literary_hubs__"
PASS_SEEDS = "__seed_qids__"

# ── Normalisation ─────────────────────────────────────────────────────────────
_LIGATURES = {"œ": "oe", "æ": "ae", "ø": "o", "ß": "ss"}
_STOP = re.compile(
    r"\b(le|la|les|l|the|a|an|de|du|des|un|une|of|in|to|for|on|at|by|with|and|et|au|aux|no)\b"
)

def norm(s: str) -> str:
    if not s:
        return ""
    for src, dst in _LIGATURES.items():
        s = s.replace(src, dst).replace(src.upper(), dst)
    s = re.sub(r"'s\b", "s", s, flags=re.IGNORECASE)
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[''`\-]", " ", s.lower())
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = _STOP.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()

# ── SPARQL ────────────────────────────────────────────────────────────────────
def sparql(query: str, retries: int = 3):
    full_query = PREFIXES + "\n" + query
    for attempt in range(retries):
        try:
            r = requests.post(
                QLEVER,
                data=full_query.encode(),
                headers=HEADERS_SPARQL,
                timeout=TIMEOUT,
            )
            if r.status_code == 429:
                print("  [RATE LIMIT] attente 15s ...", flush=True)
                time.sleep(15)
                continue
            r.raise_for_status()
            return r.json().get("results", {}).get("bindings", [])
        except Exception as e:
            wait = SLEEP_ERR * (attempt + 1)
            print(f"  [WARN] tentative {attempt+1}/{retries}: {str(e)[:70]} → {wait:.0f}s", flush=True)
            time.sleep(wait)
    return None

def qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1] if uri else ""


def split_pipe(s: str) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in s.split("|") if p.strip()]


def row_val(row: dict, key: str) -> str:
    return row.get(key, {}).get("value", "") or ""


def parse_enriched_work_row(row: dict, *, link_source: str = "p179") -> dict | None:
    """Construit un enregistrement volume depuis une ligne SPARQL (requête GROUP BY)."""
    work_qid = qid(row.get("work", {}).get("value", ""))
    if not work_qid:
        return None
    t_fr = row_val(row, "title_fr")
    t_en = row_val(row, "title_en")
    if not t_fr and not t_en:
        return None
    return {
        "work_qid": work_qid,
        "link_source": link_source,
        "title_fr": t_fr,
        "title_en": t_en,
        "volume": row_val(row, "volume"),
        "authors_en": split_pipe(row_val(row, "authors_en")),
        "publication_date": row_val(row, "publication_date"),
        "language_qids": split_pipe(row_val(row, "language_qids")),
        "genres_en": split_pipe(row_val(row, "genres_en")),
        "isbns": split_pipe(row_val(row, "isbns")),
        "open_library_id": row_val(row, "open_library_id"),
        "goodreads_work_id": row_val(row, "goodreads_work_id"),
        "goodreads_edition_id": row_val(row, "goodreads_edition_id"),
    }


def fetch_series_main_subjects(series_batch: list[str]) -> dict[str, list[str]]:
    """P921 sur l'entité série : thèmes (libellés EN), une liste par QID série."""
    if not series_batch:
        return {}
    values = " ".join(f"wd:{q}" for q in series_batch)
    query = f"""
SELECT ?series (GROUP_CONCAT(DISTINCT ?sl; separator="|") AS ?subject_labels_en) WHERE {{
  VALUES ?series {{ {values} }}
  OPTIONAL {{
    ?series wdt:P921 ?subj .
    ?subj rdfs:label ?sl .
    FILTER(LANG(?sl) = "en")
  }}
}}
GROUP BY ?series
"""
    rows = sparql(query)
    if not rows:
        return {}
    out: dict[str, list[str]] = {}
    for row in rows:
        sid = qid(row["series"]["value"])
        out[sid] = split_pipe(row_val(row, "subject_labels_en"))
    return out


def sparql_works_for_series_batch(values: str, link_via: str) -> str:
    """
    Volumes liés à une série : P179 (œuvre → série) et/ou P527 (série → parties).
    P527 récupère beaucoup de tomes jamais reliés par P179 sur l'œuvre.
    """
    if link_via == "p179":
        link = "?work wdt:P179 ?series ."
    elif link_via == "p527":
        link = "?series wdt:P527 ?work ."
    elif link_via == "p361":
        link = "?work wdt:P361 ?series ."
    else:
        raise ValueError(link_via)
    return f"""
SELECT ?series ?work
  (SAMPLE(?labFR) AS ?title_fr)
  (SAMPLE(?labEN) AS ?title_en)
  (SAMPLE(?volRaw) AS ?volume)
  (GROUP_CONCAT(DISTINCT ?authorLabel; separator="|") AS ?authors_en)
  (SAMPLE(?pubAt) AS ?publication_date)
  (GROUP_CONCAT(DISTINCT ?langQ; separator="|") AS ?language_qids)
  (GROUP_CONCAT(DISTINCT ?genreLabel; separator="|") AS ?genres_en)
  (GROUP_CONCAT(DISTINCT ?isbn; separator="|") AS ?isbns)
  (SAMPLE(?olidRaw) AS ?open_library_id)
  (SAMPLE(?grwRaw) AS ?goodreads_work_id)
  (SAMPLE(?greRaw) AS ?goodreads_edition_id)
WHERE {{
  VALUES ?series {{ {values} }}
  {link}
  FILTER( ?work != ?series )
  FILTER NOT EXISTS {{ ?work wdt:P31 wd:Q5 }}
  OPTIONAL {{ ?work rdfs:label ?labFR FILTER(LANG(?labFR) = "fr") }}
  OPTIONAL {{ ?work rdfs:label ?labEN FILTER(LANG(?labEN) = "en") }}
  OPTIONAL {{ ?work wdt:P1545 ?volRaw }}
  OPTIONAL {{
    ?work wdt:P50 ?author .
    ?author rdfs:label ?authorLabel .
    FILTER(LANG(?authorLabel) = "en")
  }}
  OPTIONAL {{ ?work wdt:P577 ?pubAt }}
  OPTIONAL {{
    ?work wdt:P407 ?langEnt .
    BIND(REPLACE(STR(?langEnt), "http://www.wikidata.org/entity/", "") AS ?langQ)
  }}
  OPTIONAL {{
    ?work wdt:P136 ?genre .
    ?genre rdfs:label ?genreLabel .
    FILTER(LANG(?genreLabel) = "en")
  }}
  OPTIONAL {{ ?work wdt:P213 ?isbn }}
  OPTIONAL {{ ?work wdt:P648 ?olidRaw }}
  OPTIONAL {{ ?work wdt:P8383 ?grwRaw }}
  OPTIONAL {{ ?work wdt:P2963 ?greRaw }}
}}
GROUP BY ?series ?work
"""


def write_export_meta(
    *,
    series_count: int | None,
    note: str = "",
    extra: dict | None = None,
    out_path: str | Path | None = None,
):
    """Fichier léger à côté du JSON brut : version, date, pointeur vers le schéma JSON Schema."""
    from datetime import datetime, timezone

    meta = {
        "schema_version": SCHEMA_VERSION,
        "format": "booktime_wikidata_series_raw",
        "json_schema_file": SCHEMA_FILE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_sparql_endpoint": QLEVER,
        "series_entities_count": series_count,
        "wikidata_properties_documented": {
            "series": ["P31", "P921", "rdfs:label"],
            "work": [
                "P179",
                "P527",
                "P1545",
                "rdfs:label",
                "P50",
                "P577",
                "P407",
                "P136",
                "P213",
                "P648",
                "P8383",
                "P2963",
            ],
        },
        "index_policy": {
            "file": DB_FILE,
            "includes_series_without_works": True,
            "indexes_work_titles": False,
            "description": (
                "Toute série avec libellé FR ou EN est dans by_qid ; work_count indique les volumes "
                "liés (P179, P527, P361). title_index = noms de série uniquement (pas les titres de tomes)."
            ),
        },
    }
    if extra:
        meta.update(extra)
    if note:
        meta["note"] = note
    target = Path(out_path) if out_path else Path(META_FILE)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# ── Checkpoint ────────────────────────────────────────────────────────────────
def load_cp() -> dict:
    if Path(CHECKPOINT).exists():
        with open(CHECKPOINT, encoding="utf-8") as f:
            return json.load(f)
    return {"done_types": [], "done_passes": [], "qids": {}, "fr_done": [], "works_done": [], "series_data": {}}

def save_cp(cp: dict):
    """Écriture atomique : évite un JSON tronqué si le process est interrompu pendant l'écriture."""
    path = Path(CHECKPOINT)
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(cp, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)

# ── Passe 1 : QIDs + labels EN ────────────────────────────────────────────────
def _add_qid(qids: dict, q_id: str, label_en: str, type_label: str) -> bool:
    """Ajoute un QID si absent. Retourne True si nouvellement ajouté."""
    if not q_id or not label_en or q_id in qids:
        return False
    qids[q_id] = {
        "name_en": label_en,
        "name_fr": "",
        "name": label_en,
        "type": type_label,
    }
    return True


def _pass1_types(cp: dict, type_list: list[tuple[str, str]], *, pass_label: str) -> int:
    """Collecte paginée par type P31 (réutilisée pour types série et extra)."""
    done = set(cp.get("done_types", []))
    qids = cp.get("qids", {})
    added = 0

    for type_qid, label in type_list:
        if type_qid in done:
            n = sum(1 for v in qids.values() if v.get("type") == label)
            print(f"  [SKIP] {label:<30} ({n} séries déjà collectées)", flush=True)
            continue

        print(f"\n  {pass_label} — {label} ({type_qid})", flush=True)
        offset = 0
        n_type = 0

        while True:
            q = f"""
SELECT ?series ?label WHERE {{
  ?series wdt:P31 wd:{type_qid} ;
          rdfs:label ?label .
  FILTER(LANG(?label) = "en")
}}
ORDER BY ?series
LIMIT {PAGE_SIZE} OFFSET {offset}
"""
            rows = sparql(q)
            if rows is None:
                print(f"  [ERR] Abandon après échecs — {n_type} collectées", flush=True)
                break
            if not rows:
                break

            for row in rows:
                q_id = qid(row["series"]["value"])
                lbl = row.get("label", {}).get("value", "")
                if _add_qid(qids, q_id, lbl, label):
                    n_type += 1
                    added += 1

            print(
                f"    offset {offset:>7}  +{len(rows):>4}  ({n_type} ce type  /  {len(qids)} total)",
                flush=True,
            )
            time.sleep(SLEEP)
            if len(rows) < PAGE_SIZE:
                break
            offset += PAGE_SIZE

        done.add(type_qid)
        cp["done_types"] = list(done)
        cp["qids"] = qids
        save_cp(cp)
        print(f"  → {n_type} pour '{label}'   Total global : {len(qids)}", flush=True)

    return added


def pass1(cp: dict) -> dict:
    _pass1_types(cp, SERIES_TYPES, pass_label="Passe 1")
    print(f"\n  ✓ Passe 1 terminée : {len(cp.get('qids', {}))} séries", flush=True)
    return cp.get("qids", {})


def pass1_extra(cp: dict) -> int:
    """Types P31 complémentaires (children's book series, heptalogy, …)."""
    print("\n  Passe 1-extra — types P31 complémentaires", flush=True)
    n = _pass1_types(cp, EXTRA_SERIES_TYPES, pass_label="Passe 1-extra")
    print(f"  ✓ Passe 1-extra : +{n} nouvelles séries", flush=True)
    return n


def pass1_franchises(cp: dict) -> int:
    """Franchises multimédia (Q196600) ayant au moins une œuvre littéraire liée par P179."""
    done_passes = set(cp.get("done_passes", []))
    if PASS_FRANCHISES in done_passes:
        print("\n  [SKIP] Passe franchises littéraires", flush=True)
        return 0

    qids = cp.get("qids", {})
    added = 0
    offset = 0
    print("\n  Passe franchises — Q196600 avec œuvres littéraires (P179)", flush=True)

    while True:
        q = f"""
SELECT ?franchise ?label WHERE {{
  ?franchise wdt:P31 wd:{FRANCHISE_TYPE_QID} ;
             rdfs:label ?label .
  FILTER(LANG(?label) = "en")
  FILTER EXISTS {{
    ?work wdt:P179 ?franchise .
    ?work wdt:P31/wdt:P279* ?lit .
    VALUES ?lit {{ {LITERARY_WORK_VALUES} }}
  }}
}}
ORDER BY ?franchise
LIMIT {FRANCHISE_PAGE_SIZE} OFFSET {offset}
"""
        rows = sparql(q)
        if rows is None:
            print("  [ERR] franchises — abandon partiel", flush=True)
            break
        if not rows:
            break

        for row in rows:
            q_id = qid(row["franchise"]["value"])
            lbl = row.get("label", {}).get("value", "")
            if _add_qid(qids, q_id, lbl, "literary franchise"):
                added += 1

        print(f"    offset {offset:>7}  +{len(rows):>4}  ({added} nouvelles franchises)", flush=True)
        time.sleep(SLEEP)
        if len(rows) < FRANCHISE_PAGE_SIZE:
            break
        offset += FRANCHISE_PAGE_SIZE

    done_passes.add(PASS_FRANCHISES)
    cp["done_passes"] = list(done_passes)
    cp["qids"] = qids
    save_cp(cp)
    print(f"  ✓ Passe franchises : +{added} franchises", flush=True)
    return added


def pass1_p179_hubs(cp: dict) -> int:
    """
    Découverte des séries-chapeaux via P179 inverse : entités ciblées par ≥N œuvres littéraires.
    Rattrape Harry Potter (Q8337) et autres ombrelles mal typées ou absentes de la pagination P31.
    """
    done_passes = set(cp.get("done_passes", []))
    if PASS_P179_HUBS in done_passes:
        print("\n  [SKIP] Passe hubs P179 littéraires", flush=True)
        return 0

    qids = cp.get("qids", {})
    added = 0
    offset = 0
    print(f"\n  Passe hubs P179 — ≥{MIN_P179_HUB_WORKS} œuvres littéraires", flush=True)

    while True:
        q = f"""
SELECT ?series ?label (COUNT(DISTINCT ?work) AS ?wc) WHERE {{
  ?work wdt:P179 ?series .
  ?work wdt:P31/wdt:P279* ?lit .
  VALUES ?lit {{ {LITERARY_WORK_VALUES} }}
  ?series rdfs:label ?label .
  FILTER(LANG(?label) = "en")
  FILTER NOT EXISTS {{ ?series wdt:P31 wd:Q5 }}
}}
GROUP BY ?series ?label
HAVING(COUNT(DISTINCT ?work) >= {MIN_P179_HUB_WORKS})
ORDER BY DESC(?wc)
LIMIT {P179_HUB_PAGE_SIZE} OFFSET {offset}
"""
        rows = sparql(q)
        if rows is None:
            print("  [ERR] hubs P179 — abandon partiel", flush=True)
            break
        if not rows:
            break

        for row in rows:
            q_id = qid(row["series"]["value"])
            lbl = row.get("label", {}).get("value", "")
            if _add_qid(qids, q_id, lbl, "literary series hub"):
                added += 1

        print(f"    offset {offset:>7}  +{len(rows):>4}  ({added} nouveaux hubs)", flush=True)
        time.sleep(SLEEP)
        if len(rows) < P179_HUB_PAGE_SIZE:
            break
        offset += P179_HUB_PAGE_SIZE

    done_passes.add(PASS_P179_HUBS)
    cp["done_passes"] = list(done_passes)
    cp["qids"] = qids
    save_cp(cp)
    print(f"  ✓ Passe hubs P179 : +{added} séries-chapeaux", flush=True)
    return added


def pass1_seeds(cp: dict) -> int:
    """Filet de sécurité : QIDs canoniques connus (Harry Potter, One Piece, …)."""
    done_passes = set(cp.get("done_passes", []))
    if PASS_SEEDS in done_passes:
        print("\n  [SKIP] Passe seeds connus", flush=True)
        return 0

    qids = cp.get("qids", {})
    missing = [q for q in KNOWN_SEED_QIDS if q not in qids]
    if not missing:
        done_passes.add(PASS_SEEDS)
        cp["done_passes"] = list(done_passes)
        save_cp(cp)
        print("\n  Passe seeds — tous déjà présents", flush=True)
        return 0

    values = " ".join(f"wd:{q}" for q in missing)
    q = f"""
SELECT ?series ?label WHERE {{
  VALUES ?series {{ {values} }}
  ?series rdfs:label ?label .
  FILTER(LANG(?label) IN ("en", "fr"))
}}
"""
    rows = sparql(q) or []
    labels_by_qid: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        q_id = qid(row["series"]["value"])
        lang = row.get("label", {}).get("xml:lang", "") or row.get("label", {}).get("lang", "")
        lbl = row.get("label", {}).get("value", "")
        if q_id and lbl and lang in ("en", "fr"):
            labels_by_qid[q_id][lang] = lbl

    added = 0
    for q_id, langs in labels_by_qid.items():
        lbl_en = langs.get("en", "")
        lbl_fr = langs.get("fr", "")
        lbl = lbl_en or lbl_fr
        if _add_qid(qids, q_id, lbl, "seed series"):
            if lbl_fr:
                qids[q_id]["name_fr"] = lbl_fr
                qids[q_id]["name"] = lbl_fr
            added += 1

    done_passes.add(PASS_SEEDS)
    cp["done_passes"] = list(done_passes)
    cp["qids"] = qids
    save_cp(cp)
    print(f"\n  ✓ Passe seeds : +{added} séries canoniques", flush=True)
    return added

# ── Passe 1b : Labels FR ──────────────────────────────────────────────────────
def pass1b(cp: dict):
    qids     = cp.get("qids", {})
    fr_done  = set(cp.get("fr_done", []))
    todo     = [q for q in qids if q not in fr_done]
    total    = len(todo)

    print(f"\n  Passe 1b — Labels FR : {total} séries à enrichir", flush=True)

    for i in range(0, total, FR_BATCH):
        batch  = todo[i : i + FR_BATCH]
        values = " ".join(f"wd:{q}" for q in batch)
        q = f"""
SELECT ?series ?label WHERE {{
  VALUES ?series {{ {values} }}
  ?series rdfs:label ?label .
  FILTER(LANG(?label) = "fr")
}}
"""
        rows = sparql(q)
        if rows:
            for row in rows:
                q_id = qid(row["series"]["value"])
                lbl_fr = row.get("label", {}).get("value", "")
                if q_id in qids and lbl_fr:
                    qids[q_id]["name_fr"] = lbl_fr
                    qids[q_id]["name"]    = lbl_fr   # FR prioritaire

        fr_done.update(batch)
        if i % (FR_BATCH * 20) == 0 or i + FR_BATCH >= total:
            pct = 100 * (i + len(batch)) / total
            print(f"    {i+len(batch):>7}/{total}  ({pct:.1f}%)", flush=True)
            cp["fr_done"] = list(fr_done)
            cp["qids"]    = qids
            save_cp(cp)
        time.sleep(SLEEP)

    print("  ✓ Passe 1b terminée", flush=True)

# ── Passe 2 : Oeuvres ─────────────────────────────────────────────────────────
def pass2(cp: dict) -> dict:
    qids        = cp.get("qids", {})
    works_done  = set(cp.get("works_done", []))
    series_data = cp.get("series_data", {})
    todo        = [q for q in qids if q not in works_done]
    total       = len(todo)

    print(f"\n  Passe 2 — Oeuvres (P179 + P527) : {total} séries à traiter ({len(works_done)} déjà faites)", flush=True)

    t_start = time.time()
    for i in range(0, total, WORKS_BATCH):
        batch  = todo[i : i + WORKS_BATCH]
        values = " ".join(f"wd:{q}" for q in batch)

        works_by_series: dict[str, list[dict]] = defaultdict(list)
        seen_work: dict[str, set[str]] = defaultdict(set)

        def ingest_rows(rows, via: str) -> int:
            n = 0
            if not rows:
                return 0
            for row in rows:
                wrec = parse_enriched_work_row(row, link_source=via)
                if not wrec:
                    continue
                sid = qid(row["series"]["value"])
                wq = wrec["work_qid"]
                if wq in seen_work[sid]:
                    continue
                seen_work[sid].add(wq)
                works_by_series[sid].append(wrec)
                n += 1
            return n

        n_p179 = ingest_rows(sparql(sparql_works_for_series_batch(values, "p179")), "p179")
        time.sleep(SLEEP)
        n_p527 = ingest_rows(sparql(sparql_works_for_series_batch(values, "p527")), "p527")
        time.sleep(SLEEP)
        n_p361 = ingest_rows(sparql(sparql_works_for_series_batch(values, "p361")), "p361")

        subjects_map = fetch_series_main_subjects(batch)

        for q_id in batch:
            raw  = works_by_series.get(q_id, [])
            uniq = sorted(
                raw,
                key=lambda w: (
                    0 if w.get("link_source") == "p179" else 1,
                    w.get("volume") or "",
                    w.get("title_en") or w.get("title_fr") or "",
                ),
            )
            base = {**qids.get(q_id, {}), "works": uniq}
            subs = subjects_map.get(q_id)
            if subs:
                base["main_subjects_en"] = subs
            series_data[q_id] = base
            works_done.add(q_id)

        # Progression + ETA
        done_n   = i + len(batch)
        pct      = 100 * done_n / total
        elapsed  = time.time() - t_start
        eta_s    = (elapsed / done_n) * (total - done_n) if done_n else 0
        eta_min  = eta_s / 60
        n_works  = n_p179 + n_p527 + n_p361
        print(f"  {done_n:>7}/{total}  {pct:>5.1f}%  +{n_works:>4} oeuvres (P179:{n_p179} P527:{n_p527} P361:{n_p361})  ETA {eta_min:.0f}min", flush=True)

        if i % (WORKS_BATCH * 50) == 0 or done_n >= total:
            cp["works_done"]  = list(works_done)
            cp["series_data"] = series_data
            save_cp(cp)
        time.sleep(SLEEP)

    save_cp(cp)
    print(f"  ✓ Passe 2 terminée : {len(series_data)} séries", flush=True)
    return series_data

# ── Index ─────────────────────────────────────────────────────────────────────
# Priorité de type sur collision de titre : une série de livres *curée* (typée
# explicitement chez Wikidata) prime sur un hub/franchise (agrégat bruité mêlant
# films, jeux, doublons d'éditions). Plus le score est haut, plus c'est prioritaire.
_TYPE_PRIORITY = {
    "novel series": 5,
    "manga series": 5,
    "light novel series": 5,
    "manhwa series": 5,
    "comic book series": 5,
    "comics series": 5,
    "children's book series": 4,
    "book series": 4,
    "written work series": 3,
    "heptalogy": 3,
    "seed series": 2,
    "literary franchise": 1,
    "literary series hub": 0,
}


def _type_rank(type_label: str) -> int:
    return _TYPE_PRIORITY.get((type_label or "").strip().lower(), 2)


WORK_FORMATS_FILE = "wikidata_work_formats.json"
_work_formats: dict[str, int] | None = None


def _load_work_formats() -> dict[str, int]:
    """Charge wikidata_work_formats.json (work_qid -> 1 livre / 0 non-livre) si présent."""
    global _work_formats
    if _work_formats is None:
        path = Path(WORK_FORMATS_FILE)
        if path.exists():
            try:
                _work_formats = json.loads(path.read_text(encoding="utf-8"))
                print(f"  Formats d'œuvres chargés : {len(_work_formats):,}", flush=True)
            except Exception as e:  # noqa: BLE001
                print(f"  [WARN] formats illisibles ({e}); filtre désactivé", flush=True)
                _work_formats = {}
        else:
            _work_formats = {}
    return _work_formats


def _dedupe_works(works: list[dict]) -> list[dict]:
    """
    1) Exclut les œuvres non-livre (pièces, films, jeux) si wikidata_work_formats.json est présent.
    2) Dédoublonne les tomes par titre normalisé (FR puis EN). Wikidata stocke souvent
       plusieurs éditions/traductions d'un même tome : sans ça, work_count est gonflé.
    """
    formats = _load_work_formats()
    seen: set[str] = set()
    out: list[dict] = []
    for w in works:
        if not isinstance(w, dict):
            continue
        # Filtre format : on ne garde que les vrais tomes (livre). Défaut = garder si inconnu.
        wq = w.get("work_qid")
        if formats and wq in formats and formats[wq] == 0:
            continue
        title = w.get("title_fr") or w.get("title_en") or ""
        key = norm(title)
        if not key:
            out.append(w)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(w)
    return out


def _register_title_key(
    title_index: dict[str, str],
    key: str,
    qid_val: str,
    ranks: dict[str, tuple[int, int]],
) -> None:
    """
    Collision de titre : on garde la meilleure série selon (priorité de type, work_count).
    Le type prime — une série de livres curée (même avec moins d'entrées) bat un hub pollué.
    """
    if not key:
        return
    prev = title_index.get(key)
    if prev is None or ranks.get(qid_val, (0, 0)) > ranks.get(prev, (0, 0)):
        title_index[key] = qid_val


def build_index(series_data: dict) -> dict:
    """
    Index : toute entité série avec au moins un libellé (FR ou EN).
    title_index = noms de série uniquement (pas les titres de tomes individuels).
    """
    title_index: dict[str, str] = {}
    by_qid: dict[str, dict] = {}
    # (priorité de type, nombre de volumes) sert d'arbitrage sur collision.
    ranks: dict[str, tuple[int, int]] = {}

    deduped: dict[str, list[dict]] = {}
    for q_id, info in series_data.items():
        works = _dedupe_works(info.get("works", []))
        deduped[q_id] = works
        ranks[q_id] = (_type_rank(info.get("type", "")), len(works))

    for q_id, info in series_data.items():
        name = info.get("name_fr") or info.get("name_en") or ""
        works = deduped.get(q_id, [])
        if not name:
            continue

        entry = {
            "qid": q_id,
            "name": name,
            "name_fr": info.get("name_fr", ""),
            "name_en": info.get("name_en", ""),
            "type": info.get("type", ""),
            "works": works,
            "work_count": len(works),
        }
        if info.get("main_subjects_en"):
            entry["main_subjects_en"] = info["main_subjects_en"]
        by_qid[q_id] = entry

        for n in {info.get("name_fr", ""), info.get("name_en", "")} - {""}:
            k = norm(n)
            _register_title_key(title_index, k, q_id, ranks)

    return {"by_qid": by_qid, "title_index": title_index}


def print_index_summary(db: dict) -> None:
    """Statistiques après build_index (séries avec / sans volumes P179)."""
    by_qid = db["by_qid"]
    with_w = sum(1 for e in by_qid.values() if e.get("work_count", 0) > 0)
    no_w   = len(by_qid) - with_w
    print(f"    … dont avec volumes (work_count>0) : {with_w:,}", flush=True)
    print(f"    … dont sans volume lié (work_count=0) : {no_w:,}", flush=True)


def reindex_only():
    """Reconstruit wikidata_series_db.json depuis wikidata_series_raw.json (sans appeler QLever)."""
    if not Path(RAW_FILE).exists():
        print(f"[ERR] Fichier manquant : {RAW_FILE!r}", flush=True)
        sys.exit(1)
    print(f"\n  Re-indexation depuis {RAW_FILE!r} ...", flush=True)
    with open(RAW_FILE, encoding="utf-8") as f:
        series_data = json.load(f)
    db = build_index(series_data)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)
    ns = len(db["by_qid"])
    ni = len(db["title_index"])
    sz = Path(DB_FILE).stat().st_size / 1e6
    print(f"  ✓ Index → {DB_FILE!r}", flush=True)
    print(f"    Séries indexées      : {ns:,}", flush=True)
    print_index_summary(db)
    print(f"    Entrées titre→série  : {ni:,}", flush=True)
    print(f"    Taille               : {sz:.1f} Mo", flush=True)
    write_export_meta(
        series_count=len(series_data),
        note="Reconstruction index uniquement ; champs volume dépendent du contenu du brut.",
    )
    print(f"  Métadonnées export → {META_FILE!r}", flush=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def run_discovery(cp: dict) -> None:
    """Passes de découverte v1.4 : types extra, franchises, hubs P179, seeds."""
    pass1_extra(cp)
    pass1_franchises(cp)
    pass1_p179_hubs(cp)
    pass1_seeds(cp)


def main(*, incremental: bool = False, discovery_only: bool = False):
    print("\n" + "=" * 68, flush=True)
    mode = "INCRÉMENTAL" if incremental else "COMPLÈTE"
    if discovery_only:
        mode = "DÉCOUVERTE UNIQUEMENT"
    print(f"  EXTRACTION QLever → BASE STATIQUE SÉRIES ({mode})", flush=True)
    print("=" * 68, flush=True)

    cp = load_cp()

    if incremental:
        print("\n  [INCRÉMENTAL] Passe 1 standard ignorée (déjà complète).", flush=True)
    else:
        pass1(cp)

    run_discovery(cp)

    if discovery_only:
        n = len(cp.get("qids", {}))
        print(f"\n  Découverte terminée — {n:,} QIDs au total. Relancez sans --discovery-only pour pass 1b/2.", flush=True)
        return

    pass1b(cp)
    series_data = pass2(cp)

    # Sauvegarde brute
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        json.dump(series_data, f, ensure_ascii=False)
    print(f"\n  Données brutes → {RAW_FILE!r}  ({Path(RAW_FILE).stat().st_size/1e6:.1f} Mo)", flush=True)

    # Index
    print("  Construction de l'index ...", flush=True)
    db = build_index(series_data)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

    ns = len(db["by_qid"])
    ni = len(db["title_index"])
    sz = Path(DB_FILE).stat().st_size / 1e6
    print(f"\n  ✓ Index → {DB_FILE!r}", flush=True)
    print(f"    Séries indexées      : {ns:,}", flush=True)
    print_index_summary(db)
    print(f"    Entrées titre→série  : {ni:,}", flush=True)
    print(f"    Taille               : {sz:.1f} Mo", flush=True)

    write_export_meta(series_count=len(series_data))
    print(f"  Métadonnées export → {META_FILE!r}", flush=True)

    print("\n  Top 10 séries (≥5 tomes) :", flush=True)
    shown = 0
    for info in sorted(
        db["by_qid"].values(),
        key=lambda e: e.get("work_count", 0),
        reverse=True,
    ):
        if info.get("work_count", 0) >= 5:
            print(f"    [{info['qid']}] {info['name']}  ({info['work_count']} tomes)", flush=True)
            shown += 1
            if shown >= 10:
                break

    print("\n" + "=" * 68, flush=True)
    print("  Extraction terminée.", flush=True)
    print("=" * 68 + "\n", flush=True)


def reset_discovery(cp: dict | None = None) -> None:
    """Réinitialise les passes de découverte v1.4 (types extra, franchises, hubs, seeds)."""
    cp = cp or load_cp()
    done_types = set(cp.get("done_types", []))
    for tq, _ in EXTRA_SERIES_TYPES:
        done_types.discard(tq)
    cp["done_types"] = list(done_types)
    cp["done_passes"] = []
    save_cp(cp)
    print(
        "Checkpoint : done_passes vidé ; types extra retirés de done_types.\n"
        "Relancez : python extract_wikidata_series.py --incremental",
        flush=True,
    )

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reindex":
        reindex_only()
    elif len(sys.argv) > 1 and sys.argv[1] == "--incremental":
        main(incremental=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "--discovery-only":
        main(discovery_only=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "--reset-discovery":
        reset_discovery()
    elif len(sys.argv) > 1 and sys.argv[1] == "--reset-pass2":
        cp = load_cp()
        cp["works_done"] = []
        cp["series_data"] = {}
        save_cp(cp)
        print(
            "Checkpoint : works_done et series_data vidés.\n"
            "Relancez : python extract_wikidata_series.py --incremental\n"
            "(passe 1 ignorée si déjà complète ; passe 2 repartira de zéro).",
            flush=True,
        )
    else:
        main()
