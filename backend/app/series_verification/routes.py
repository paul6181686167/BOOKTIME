"""Endpoint de vérification croisée multi-sources du nombre de tomes et des titres."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..security.jwt import get_current_user
from . import consensus, curated, sources

router = APIRouter(prefix="/api/series", tags=["series-verification"])

# Libellés/ordre des niveaux de vérification (du plus fiable au moins fiable).
_LEVEL_LABELS = {
    "reference": "Référence (curé)",
    "wikidata": "Wikidata",
    "openlibrary": "Open Library",
    "google_books": "Google Books",
}


@router.get("/verify-volumes")
async def verify_volumes(
    name: str = Query(..., min_length=1, max_length=200),
    author: str | None = Query(None, max_length=200),
    qid: str | None = Query(None, max_length=20),
    use_google: bool = Query(True, description="Inclure Google Books (3e niveau)."),
    _user: dict = Depends(get_current_user),
):
    """
    Croise plusieurs niveaux de vérification pour fiabiliser le nombre de tomes
    et les titres d'une série :
      - Niveau 0 : référentiel curé/officiel (fait autorité, sans fluctuation) ;
      - Niveau 1 : Wikidata (index statique) ;
      - Niveau 2 : Open Library ;
      - Niveau 3 : Google Books.

    Chaque tome reçoit un niveau de confiance ; le résultat expose le détail par
    niveau (`levels`) pour pouvoir afficher les divergences.
    """
    curated_entry = curated.match_curated(name, author)

    src: dict[str, list] = {}
    if curated_entry:
        src["reference"] = curated.curated_to_source_rows(curated_entry)
    src["wikidata"] = sources.fetch_wikidata_static(qid, name)
    src["openlibrary"] = sources.fetch_openlibrary(name, author)
    if use_google:
        src["google_books"] = sources.fetch_google_books(name, author)

    report = consensus.cross_verify(src)

    # Niveau "référence" : il fait autorité sur le compte et (si dispo) les titres.
    if curated_entry:
        ref_titles = curated_entry.get("volume_titles") or []
        report["best_estimate_count"] = int(curated_entry.get("volumes") or len(ref_titles))
        report["overall_confidence"] = "officiel"
        report["authority"] = {
            "source": "curated_reference",
            "name": curated_entry.get("name"),
            "authors": curated_entry.get("authors") or [],
            "volumes": int(curated_entry.get("volumes") or len(ref_titles)),
            "has_titles": bool(ref_titles),
        }

    report["levels"] = _build_levels(report.get("sources_used") or {}, report.get("by_source") or {})
    report["query"] = {"name": name, "author": author, "qid": qid}
    return report


def _build_levels(sources_used: dict, by_source: dict) -> list[dict]:
    levels = []
    for key, label in _LEVEL_LABELS.items():
        count = int(sources_used.get(key) or 0)
        levels.append(
            {
                "key": key,
                "label": label,
                "available": key in sources_used,
                "count": count,
                "sample": (by_source.get(key) or [])[:60],
            }
        )
    return levels
