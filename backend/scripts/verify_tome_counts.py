"""
Vérification batch du nombre de tomes par série : recoupe Référence + Wikidata
+ Open Library + Google Books et affiche, pour chaque série, l'estimation, la
confiance et le détail par niveau. Diagnostic uniquement (aucune écriture).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.series_verification import sources, consensus, curated  # noqa: E402

# (nom, qid éventuel, attendu connu pour repère humain)
SERIES = [
    ("Harry Potter", "Q8337", 7),
    ("Le Seigneur des anneaux", None, 3),
    ("One Piece", None, 105),
    ("Naruto", None, 72),
    ("Dragon Ball", None, 42),
    ("Astérix", None, 39),
    ("Les Aventures de Tintin", None, 24),
    ("Le Trône de fer", None, None),
    ("Twilight", None, 4),
    ("Hunger Games", None, None),
    ("Percy Jackson", None, 5),
    ("Bleach", None, None),
    ("Death Note", None, 12),
    ("L'Attaque des Titans", None, 34),
    ("Les Chroniques de Narnia", None, 7),
    ("Millénium", None, None),
    ("Le Petit Nicolas", None, None),
    ("Gaston Lagaffe", None, None),
    ("Largo Winch", None, None),
    ("Thorgal", None, None),
]


def main():
    print(f"{'Série':<28}{'est.':>5} {'conf.':<10}{'autorité':<10} niveaux")
    print("-" * 100)
    for name, qid, expected in SERIES:
        entry = curated.match_curated(name)
        src = {}
        if entry:
            src["reference"] = curated.curated_to_source_rows(entry)
        src["wikidata"] = sources.fetch_wikidata_static(qid, name)
        src["openlibrary"] = sources.fetch_openlibrary(name, None)
        src["google_books"] = sources.fetch_google_books(name, None)
        r = consensus.cross_verify(src)
        if entry:
            ref_titles = entry.get("volume_titles") or []
            r["best_estimate_count"] = int(entry.get("volumes") or len(ref_titles))
            r["overall_confidence"] = "officiel"
        su = r["sources_used"]
        lvl = f"ref={su.get('reference','-')} wd={su.get('wikidata',0)} ol={su.get('openlibrary',0)} gb={su.get('google_books',0)}"
        auth = "oui" if entry else "non"
        exp = f" (attendu~{expected})" if expected else ""
        print(f"{name:<28}{r['best_estimate_count']:>5} {r['overall_confidence']:<10}{auth:<10} {lvl}{exp}")


if __name__ == "__main__":
    main()
