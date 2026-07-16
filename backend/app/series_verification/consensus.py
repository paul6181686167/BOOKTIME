"""
Cœur de la vérification croisée (logique pure, sans réseau — testable).

Principe : on reçoit les tomes proposés par chaque source (Wikidata, Open Library,
Google Books), on les regroupe en "clusters" représentant un même tome, puis on
attribue un niveau de confiance selon le nombre de sources qui concordent.

Niveaux de confiance par tome :
  - "confirme"  : au moins 2 sources concordent (ou n° de tome + ISBN).
  - "probable"  : une seule source mais tome structuré (numéro présent).
  - "incertain" : une seule source, titre seul, aucun numéro.

Appariement multi-niveaux (du plus fort au plus faible) :
  1. numéro de tome
  2. ISBN (13 ou 10, normalisé)
  3. titre normalisé (égalité, puis inclusion forte)
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

# Ordre de priorité des sources : la 1re sert d'ancre, les autres confirment.
# "reference" = niveau curé/officiel (le plus fiable), toujours prioritaire.
SOURCE_PRIORITY = ("reference", "wikidata", "openlibrary", "google_books")

_LIGATURES = {"œ": "oe", "æ": "ae", "ø": "o", "ß": "ss"}
_STOP = re.compile(
    r"\b(le|la|les|l|the|a|an|de|du|des|un|une|of|in|to|for|on|at|by|with|and|et|au|aux|no|tome|vol|volume|book|tome|t)\b"
)
# Motifs « numéro de tome » fiables : seulement précédés d'un mot-clé ou d'un '#'.
# On n'accepte JAMAIS un nombre nu dans un titre libre : ce serait souvent une année
# (« ... 2008 »), une édition ou un nombre de pages, ce qui polluerait la numérotation.
_TITLE_VOLUME_PATTERNS = [
    re.compile(r"\b(?:tome|tomes|vol\.?|volume|volumes|book|livre|n[o°]?)\s*#?\s*(\d{1,4})\b", re.I),
    re.compile(r"#\s*(\d{1,4})\b"),
]


def normalize_title_key(s: str) -> str:
    """Clé de titre normalisée (alignée sur l'esprit de static_wikidata.norm_title)."""
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


def normalize_isbn(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"[^0-9Xx]", "", str(s)).upper()


def _in_range(n: int) -> bool:
    return 1 <= n <= 9999


def _number_from_explicit(explicit: Any) -> int | None:
    """Champ explicite (ex. 'volume' Wikidata, 'series' Open Library) — on fait confiance."""
    if explicit is None:
        return None
    if isinstance(explicit, (int, float)):
        n = int(explicit)
        return n if _in_range(n) else None
    text = str(explicit).strip()
    if not text:
        return None
    if text.isdigit():  # "3" / "03"
        n = int(text)
        return n if _in_range(n) else None
    for pat in _TITLE_VOLUME_PATTERNS:  # ex. "Harry Potter #3", "Volume 3"
        m = pat.search(text)
        if m and _in_range(int(m.group(1))):
            return int(m.group(1))
    return None


def _number_from_title(title: Any) -> int | None:
    """Titre libre — uniquement les numéros explicitement marqués (Tome/Vol/#)."""
    if not title:
        return None
    text = str(title)
    for pat in _TITLE_VOLUME_PATTERNS:
        m = pat.search(text)
        if m and _in_range(int(m.group(1))):
            return int(m.group(1))
    return None


def parse_volume_number(explicit: Any = None, title: Any = None) -> int | None:
    """
    Numéro de tome : on privilégie le champ explicite, sinon un marqueur dans le titre.
    Un nombre nu dans un titre n'est PAS retenu (probable année/édition).
    """
    return _number_from_explicit(explicit) or _number_from_title(title)


def normalize_source_volume(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Met une entrée brute (quelle que soit la source) au format commun :
      { title, title_key, volume_number, isbn, year }
    """
    title = (
        raw.get("title")
        or raw.get("title_fr")
        or raw.get("title_en")
        or raw.get("display_title")
        or ""
    ).strip()
    explicit_vol = raw.get("volume_number", raw.get("volume"))
    volume_number = parse_volume_number(explicit_vol, title)

    isbn = ""
    for key in ("isbn_13", "isbn13", "isbn_10", "isbn", "isbns"):
        v = raw.get(key)
        if isinstance(v, list):
            v = v[0] if v else ""
        isbn = normalize_isbn(v)
        if isbn:
            break

    year = None
    for key in ("first_publish_year", "publication_year", "year", "publication_date", "published_date"):
        v = raw.get(key)
        if v:
            m = re.search(r"\d{4}", str(v))
            if m:
                year = int(m.group(0))
                break

    return {
        "title": title,
        "title_key": normalize_title_key(title),
        "volume_number": volume_number,
        "isbn": isbn,
        "year": year,
    }


class _Cluster:
    """Un tome candidat, agrégé depuis une ou plusieurs sources."""

    __slots__ = ("sources", "titles", "numbers", "isbns", "years")

    def __init__(self) -> None:
        self.sources: set[str] = set()
        self.titles: dict[str, str] = {}  # source -> titre
        self.numbers: set[int] = set()
        self.isbns: set[str] = set()
        self.years: list[int] = []

    def add(self, source: str, vol: dict[str, Any]) -> None:
        self.sources.add(source)
        if vol["title"] and source not in self.titles:
            self.titles[source] = vol["title"]
        if vol["volume_number"] is not None:
            self.numbers.add(vol["volume_number"])
        if vol["isbn"]:
            self.isbns.add(vol["isbn"])
        if vol["year"]:
            self.years.append(vol["year"])

    @property
    def volume_number(self) -> int | None:
        return min(self.numbers) if self.numbers else None


def _pick_title(cluster: _Cluster) -> str:
    """Titre affiché : priorité Wikidata > Open Library > Google Books."""
    for src in SOURCE_PRIORITY:
        if src in cluster.titles:
            return cluster.titles[src]
    return next(iter(cluster.titles.values()), "")


def _confidence(cluster: _Cluster) -> str:
    # Présent dans le référentiel curé => fiable (confirmé), même seul.
    if "reference" in cluster.sources:
        return "confirme"
    n = len(cluster.sources)
    if n >= 2:
        return "confirme"
    if cluster.volume_number is not None:
        return "probable"
    return "incertain"


def cross_verify(sources: dict[str, Iterable[dict[str, Any]]]) -> dict[str, Any]:
    """
    Croise les tomes des différentes sources et renvoie un rapport de vérification.

    sources: { "wikidata": [...], "openlibrary": [...], "google_books": [...] }
             (chaque entrée brute ; les clés/sources absentes sont ignorées).
    """
    clusters: list[_Cluster] = []
    by_number: dict[int, _Cluster] = {}
    by_isbn: dict[str, _Cluster] = {}
    by_title: dict[str, _Cluster] = {}

    def find_cluster(vol: dict[str, Any]) -> _Cluster | None:
        if vol["volume_number"] is not None and vol["volume_number"] in by_number:
            return by_number[vol["volume_number"]]
        if vol["isbn"] and vol["isbn"] in by_isbn:
            return by_isbn[vol["isbn"]]
        if vol["title_key"] and vol["title_key"] in by_title:
            return by_title[vol["title_key"]]
        return None

    def index(cluster: _Cluster, vol: dict[str, Any]) -> None:
        if vol["volume_number"] is not None:
            by_number.setdefault(vol["volume_number"], cluster)
        if vol["isbn"]:
            by_isbn.setdefault(vol["isbn"], cluster)
        if vol["title_key"]:
            by_title.setdefault(vol["title_key"], cluster)

    ordered = [s for s in SOURCE_PRIORITY if s in sources]
    ordered += [s for s in sources if s not in SOURCE_PRIORITY]

    source_counts: dict[str, int] = {}
    by_source: dict[str, list[dict[str, Any]]] = {}
    for source in ordered:
        seen_keys: set[str] = set()
        kept: list[dict[str, Any]] = []
        for raw in sources.get(source) or []:
            if not isinstance(raw, dict):
                continue
            vol = normalize_source_volume(raw)
            if not vol["title"] and vol["volume_number"] is None:
                continue
            # Dédup intra-source : un même tome ne compte qu'une fois pour cette source.
            dedup_key = (
                f"n{vol['volume_number']}" if vol["volume_number"] is not None
                else (f"i{vol['isbn']}" if vol["isbn"] else f"t{vol['title_key']}")
            )
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            kept.append(vol)

            cluster = find_cluster(vol)
            if cluster is None:
                cluster = _Cluster()
                clusters.append(cluster)
            cluster.add(source, vol)
            index(cluster, vol)
        source_counts[source] = len(kept)
        by_source[source] = [
            {"volume_number": v["volume_number"], "title": v["title"]}
            for v in sorted(kept, key=lambda v: (v["volume_number"] is None, v["volume_number"] or 0, v["title"]))
        ]

    return _build_report(clusters, source_counts, by_source)


def _build_report(
    clusters: list[_Cluster],
    source_counts: dict[str, int],
    by_source: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    volumes: list[dict[str, Any]] = []
    for c in clusters:
        volumes.append(
            {
                "volume_number": c.volume_number,
                "title": _pick_title(c),
                "titles_by_source": dict(c.titles),
                "sources": sorted(c.sources),
                "source_count": len(c.sources),
                "isbn": next(iter(sorted(c.isbns)), ""),
                "year": min(c.years) if c.years else None,
                "confidence": _confidence(c),
            }
        )

    # Tri : par numéro de tome (les sans-numéro à la fin), puis par titre.
    volumes.sort(key=lambda v: (v["volume_number"] is None, v["volume_number"] or 0, v["title"]))

    confirmed = [v for v in volumes if v["confidence"] == "confirme"]
    probable = [v for v in volumes if v["confidence"] == "probable"]
    uncertain = [v for v in volumes if v["confidence"] == "incertain"]

    numbers = sorted({v["volume_number"] for v in volumes if v["volume_number"] is not None})
    gaps: list[int] = []
    contiguous = True
    if numbers:
        expected = set(range(1, numbers[-1] + 1))
        gaps = sorted(expected - set(numbers))
        contiguous = not gaps and numbers[0] == 1

    # Meilleure estimation du nombre de tomes :
    #  - si la numérotation est contiguë depuis 1 ET couvre l'essentiel des tomes
    #    structurés (confirmés + probables), on fait confiance au plus grand numéro ;
    #  - sinon (numéros épars, séries sans numérotation comme Harry Potter), on compte
    #    les tomes confirmés + probables (distincts).
    structured = len(confirmed) + len(probable)
    numbered_count = len(numbers)
    if numbers and contiguous and numbered_count >= max(3, structured * 0.5):
        best_estimate = numbers[-1]
    else:
        # En dernier recours (rien de confirmé/numéroté), on expose le nombre de
        # candidats distincts plutôt qu'un 0 trompeur.
        best_estimate = max(structured, numbered_count) or len(volumes)

    overall = _overall_confidence(
        n_confirmed=len(confirmed),
        n_total=len(volumes),
        contiguous=contiguous,
        n_sources=sum(1 for c in source_counts.values() if c > 0),
    )

    return {
        "best_estimate_count": best_estimate,
        "confirmed_count": len(confirmed),
        "probable_count": len(probable),
        "uncertain_count": len(uncertain),
        "candidate_count": len(volumes),
        "overall_confidence": overall,
        "numbering": {
            "min": numbers[0] if numbers else None,
            "max": numbers[-1] if numbers else None,
            "contiguous": contiguous,
            "gaps": gaps,
        },
        "sources_used": source_counts,
        "by_source": by_source or {},
        "volumes": volumes,
    }


def _overall_confidence(*, n_confirmed: int, n_total: int, contiguous: bool, n_sources: int) -> str:
    """
    eleve | moyen | faible — fondé sur le NOMBRE de tomes confirmés par plusieurs
    sources et la cohérence de numérotation, plutôt que sur un ratio (les sources
    externes renvoient beaucoup de bruit qui fausserait un ratio).
    """
    if n_total == 0:
        return "faible"
    if n_sources >= 2 and n_confirmed >= 3 and contiguous:
        return "eleve"
    if n_sources >= 2 and n_confirmed >= 2:
        return "moyen"
    if n_confirmed >= 1 or contiguous:
        return "moyen"
    return "faible"
