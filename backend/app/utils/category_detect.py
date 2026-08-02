"""
Détection de catégorie (roman | bd | manga) — heuristiques prudentes.

Règle générale : en cas de doute → roman.
On n'assigne bd/manga que sur des marqueurs forts, pas sur des mentions
secondaires (adaptations, « comics » dans un sujet fiction, description, etc.).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Optional

VALID = frozenset({"roman", "bd", "manga"})

_MANGA_STRONG = re.compile(
    r"\b(manga|manhwa|manhua|webtoon|sh[ōo]nen|shounen|seinen|josei|kodomo|sh[ōo]jo|shojo)\b",
    re.I,
)
# Light novel = prose → roman (pas dans l'onglet Romans graphiques)
_BD_STRONG = re.compile(
    r"\b(comic books?|comic strips?|graphic novels?|roman graphique|"
    r"bande dessin[ée]e|fumetti|franco-?belgian comics?)\b",
    re.I,
)
_BD_WEAK_COMICS = re.compile(r"\bcomics?\b", re.I)
# Attention: ne pas matcher "novels" dans "graphic novels"
_ROMAN_STRONG = re.compile(
    r"\b(fiction|literature|literary|fantasy|thriller|mystery|romance|"
    r"science[\s-]?fiction|young adult|children'?s fiction|historical fiction|"
    r"roman|litt[ée]rature|fantastique|policier|horreur|"
    r"(?<!graphic )novels?)\b",
    re.I,
)
_BD_MARKER_SUBJECT = re.compile(
    r"\b(bande dessin[ée]e|comic strips?|comic books?|graphic novels?|"
    r"cartoons and comics|fumetti|franco-?belgian|pictorial .* humor)\b",
    re.I,
)
# Rayon OL souvent collé aux romans adaptés (pas une vraie BD)
_COMICS_SHELF_ONLY = re.compile(
    r"^comics?\s*&\s*graphic\s*novels?\b",
    re.I,
)
_FICTION_SUBJECT = re.compile(
    r"\b(fiction|literature|fantasy|mystery|thriller|romance|"
    r"science fiction|juvenile fiction|children'?s fiction)\b",
    re.I,
)
_ADAPTATION_NOISE = re.compile(
    r"\b(adaptation|adapted|based on|d'apr[eè]s|tir[eé] de|novelization|novelisation)\b",
    re.I,
)


def normalize_category_key(title: str = "", author: str = "") -> str:
    """Clé stable pour la mémoire tampon (titre + auteur)."""

    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFD", (s or "").strip().lower())
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        s = re.sub(r"[^a-z0-9]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    return f"{_norm(title)}|{_norm(author)}"


def _join_subjects(subjects: Optional[Iterable]) -> str:
    if not subjects:
        return ""
    parts = []
    for s in subjects:
        if isinstance(s, dict):
            parts.append(str(s.get("name") or s.get("title") or ""))
        elif s:
            parts.append(str(s))
    return " ".join(parts)


def detect_category_from_subjects(subjects=None, *, title: str = "") -> str:
    """
    Catégorie depuis sujets Open Library / listes de tags.

    - manga si marqueur manga explicite
    - bd si titre BD, ou assez de sujets BD primaires
    - roman si Fiction/Fantasy + seulement des tags shelf comics secondaires
      (fréquent sur OL pour les adaptations)
    """
    subject_list = []
    if subjects:
        for s in subjects:
            if isinstance(s, dict):
                subject_list.append(str(s.get("name") or s.get("title") or ""))
            elif s:
                subject_list.append(str(s))
    blob = " ".join(subject_list).lower()
    title_l = (title or "").lower()
    if not blob and not title_l:
        return "roman"

    # Manga : marqueur explicite (même si Fiction est aussi présent)
    if _MANGA_STRONG.search(title_l) or _MANGA_STRONG.search(blob):
        return "manga"

    if _BD_STRONG.search(title_l):
        return "bd"

    bd_markers = 0
    shelf_only = 0
    fiction_markers = 0
    for s in subject_list:
        if _COMICS_SHELF_ONLY.search(s.strip()):
            shelf_only += 1
            continue
        if _BD_MARKER_SUBJECT.search(s):
            bd_markers += 1
        if _FICTION_SUBJECT.search(s):
            fiction_markers += 1

    has_adaptation = bool(_ADAPTATION_NOISE.search(blob))

    # Vraie BD (Tintin, Watchmen…) : marqueurs comics strictement dominants
    if bd_markers >= 2 and bd_markers > fiction_markers:
        return "bd"
    if bd_markers >= 1 and fiction_markers == 0:
        return "bd"

    # Roman avec tags comics secondaires / adaptations (Hobbit, Alchimiste…)
    if fiction_markers >= 1 and (
        shelf_only or has_adaptation or bd_markers <= fiction_markers
    ):
        return "roman"

    if bd_markers >= 1:
        return "bd"

    if _BD_WEAK_COMICS.search(blob) and fiction_markers == 0:
        return "bd"

    return "roman"


def detect_category_from_google(
    *,
    categories=None,
    title: str = "",
    subtitle: str = "",
    description: str = "",
) -> str:
    """
    Inférence Google Books — ne scanne PAS la description (trop de faux positifs).
    Light novel → roman.
    """
    cat_parts: list[str] = []
    if isinstance(categories, list):
        cat_parts.extend(str(c) for c in categories if c)
    elif categories:
        cat_parts.append(str(categories))
    cats_blob = " ".join(cat_parts).lower()
    title_blob = f"{title or ''} {subtitle or ''}".lower()

    # Manga explicite dans taxonomie / titre
    if _MANGA_STRONG.search(cats_blob) or _MANGA_STRONG.search(title_blob):
        return "manga"

    # Catégorie Google du type "Comics & Graphic Novels / ..."
    is_comics_shelf = bool(
        re.search(r"comics?\s*&\s*graphic\s*novels?|graphic\s*novels?", cats_blob)
    )
    if is_comics_shelf and not _ROMAN_STRONG.search(cats_blob):
        return "bd"

    if _BD_STRONG.search(title_blob):
        return "bd"

    # Ne pas utiliser la description pour classer en bd/manga
    return "roman"


def detect_category_from_text_fallback(
    *,
    title: str = "",
    description: str = "",
    subjects=None,
) -> str:
    """Fallback front/back — sans `japan`/`bd` en sous-chaîne."""
    subjects_blob = _join_subjects(subjects)
    # Description limitée pour éviter les digressions
    blob = f"{title or ''} {subjects_blob} {(description or '')[:200]}".lower()
    if not blob.strip():
        return "roman"
    if _MANGA_STRONG.search(blob):
        return "manga"
    if _BD_STRONG.search(blob):
        return "bd"
    return "roman"


def detect_category_from_wikidata_type_and_genres(
    *,
    type_label: str = "",
    genres_blob: str = "",
) -> str:
    """Type P31 + genres — light novel → roman (prose)."""
    t = (type_label or "").lower()
    g = (genres_blob or "").lower()

    if "manga" in t or re.search(r"\b(manhwa|manhua|webtoon)\b", t):
        return "manga"
    if "light novel" in t:
        return "roman"
    if re.search(r"\b(comics? series|comic book series|comic book)\b", t):
        return "bd"
    if "novel series" in t:
        return "roman"

    if _MANGA_STRONG.search(g):
        return "manga"
    if "light novel" in g:
        return "roman"
    if _BD_STRONG.search(g) or (
        _BD_WEAK_COMICS.search(g) and not _ROMAN_STRONG.search(g)
    ):
        return "bd"
    return "roman"


def coerce_category(value: Optional[str], default: str = "roman") -> str:
    v = (value or default or "roman").strip().lower()
    return v if v in VALID else default
