"""
Service "Prochaines sorties" — agrège les sorties à venir personnalisées pour un
utilisateur : prochains tomes de ses séries (enrichis via Wikidata), chapitres
manga prédits, et livres qu'il surveille manuellement (watchlist).

Aucune source n'étant exhaustive sur les dates futures, chaque item porte un
niveau de confiance (`date_confidence`) plutôt que de masquer l'incertitude.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any, Optional

import requests

from ..database.connection import books_collection, series_library_collection
from ..static_wikidata import service as wd
from ..google_books import service as gb
from ..chapters.service import ChapterService
from ..series_verification.curated import match_curated
from app.utils.timeutils import utcnow

logger = logging.getLogger(__name__)

# Bornes de fraîcheur pour les sources externes (Google Books).
_TOME_PAST_HORIZON_DAYS = 180   # un tome "récent" non trouvé dans Wikidata
_AUTHOR_PAST_HORIZON_DAYS = 120  # nouveauté récente d'un auteur suivi
_MAX_TOME_ENRICH = 6             # limite d'appels Google Books (perf 1er chargement)
_MAX_FOLLOWED_AUTHORS = 6
_MAX_ITEMS_PER_AUTHOR = 5

# Instance réutilisable (lit le cache partagé series_chapters, indépendant de l'état).
_chapter_service = ChapterService()


def _norm(s: Optional[str]) -> str:
    """Normalisation légère pour comparer/regrouper des noms de séries."""
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def parse_pub_date(raw: Any) -> tuple[Optional[str], str]:
    """
    Parse une date de publication hétérogène (Wikidata/QLever, Google Books...) et
    renvoie (date_iso, confiance) où confiance ∈ {exact, month, year, unknown}.

    Formats gérés : "2024", "2024-03", "2024-03-15", "+2024-03-15T00:00:00Z".
    Heuristique : QLever renvoie souvent une date complète même pour une précision
    à l'année (…-01-01) → on la classe alors "year".
    """
    if not raw:
        return None, "unknown"
    s = str(raw).strip().lstrip("+").split("T")[0]
    m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?$", s)
    if not m:
        return None, "unknown"
    y, mo, d = m.group(1), m.group(2), m.group(3)
    if mo and d:
        if mo == "01" and d == "01":
            return f"{y}-01-01", "year"
        if d == "01":
            return f"{y}-{mo}-01", "month"
        return f"{y}-{mo}-{d}", "exact"
    if mo:
        return f"{y}-{mo}-01", "month"
    return f"{y}-01-01", "year"


def _extract_volumes(works: Any) -> dict[int, dict]:
    """Indexe les œuvres d'une série Wikidata par numéro de tome (P1545)."""
    out: dict[int, dict] = {}
    for w in works or []:
        if not isinstance(w, dict):
            continue
        try:
            vn = int(str(w.get("volume")).strip())
        except (TypeError, ValueError):
            continue
        # Garde la première occurrence (ou la mieux datée) par numéro de tome.
        if vn not in out or (not out[vn].get("publication_date") and w.get("publication_date")):
            out[vn] = w
    return out


def _find_series_doc(series_name: str) -> Optional[dict]:
    """Retrouve la fiche série Wikidata la plus pertinente pour un nom donné."""
    try:
        matches = wd.search_series_by_title(q=series_name, limit=3)
    except Exception as exc:  # pragma: no cover - dépend des données externes
        logger.debug("Wikidata search échouée pour %s : %s", series_name, exc)
        return None
    if not matches:
        return None
    target = _norm(series_name)
    best = next(
        (
            m
            for m in matches
            if any(_norm(n) == target for n in (m.get("name"), m.get("name_fr"), m.get("name_en")) if n)
        ),
        matches[0],
    )
    qid = best.get("qid") or best.get("_id")
    if not qid:
        return None
    try:
        return wd.get_series(qid)
    except Exception as exc:  # pragma: no cover
        logger.debug("Wikidata get_series échouée pour %s : %s", qid, exc)
        return None


def _gb_items(query: str, *, order_by: str = "newest", max_results: int = 20) -> list[dict]:
    """Recherche Google Books tolérante aux erreurs (renvoie [] en cas d'échec)."""
    try:
        res = gb.search_volumes_simplified(query, max_results=max_results, order_by=order_by)
        return res.get("items") or []
    except Exception as exc:  # pragma: no cover - dépend d'une API externe
        logger.debug("Google Books échec (%s) : %s", query, exc)
        return []


def _collect_user_series(user_id: str) -> tuple[dict[str, dict], set[str]]:
    """
    Agrège les séries de l'utilisateur (livres avec `saga` + `series_library`),
    avec les tomes possédés, pour en déduire les prochains tomes.
    Retourne aussi l'ensemble des titres possédés (normalisés) pour filtrer les
    nouveautés d'auteurs déjà en bibliothèque.
    """
    series_map: dict[str, dict] = {}
    owned_titles: set[str] = set()

    def touch(name, category, author, cover):
        key = _norm(name)
        if not key:
            return None
        entry = series_map.get(key)
        if entry is None:
            entry = {
                "name": name,
                "category": category or "roman",
                "author": author or "",
                "cover": cover or "",
                "owned": set(),
                "series_status": None,
                "library_volume_count": 0,
                "from_series_library": False,
            }
            series_map[key] = entry
        # Complète les métadonnées manquantes si une source les fournit.
        if not entry["author"] and author:
            entry["author"] = author
        if not entry["cover"] and cover:
            entry["cover"] = cover
        return entry

    book_proj = {
        "_id": 0,
        "title": 1,
        "saga": 1,
        "category": 1,
        "author": 1,
        "cover_url": 1,
        "volume_number": 1,
    }
    for b in books_collection.find({"user_id": user_id}, book_proj):
        title_key = _norm(b.get("title"))
        if title_key:
            owned_titles.add(title_key)
        saga = (b.get("saga") or "").strip()
        if not saga:
            continue
        entry = touch(saga, b.get("category"), b.get("author"), b.get("cover_url"))
        if not entry:
            continue
        vn = b.get("volume_number")
        try:
            if vn is not None:
                entry["owned"].add(int(vn))
        except (TypeError, ValueError):
            pass

    series_proj = {
        "_id": 0,
        "series_name": 1,
        "name": 1,
        "authors": 1,
        "category": 1,
        "cover_image_url": 1,
        "series_status": 1,
        "volumes": 1,
        "total_volumes": 1,
    }
    for s in series_library_collection.find({"user_id": user_id}, series_proj):
        name = s.get("series_name") or s.get("name")
        if not name:
            continue
        authors = s.get("authors") or []
        author = authors[0] if isinstance(authors, list) and authors else ""
        entry = touch(name, s.get("category"), author, s.get("cover_image_url"))
        if not entry:
            continue
        entry["from_series_library"] = True
        st = s.get("series_status")
        if st:
            entry["series_status"] = st
        vols = s.get("volumes") or []
        try:
            declared = int(s.get("total_volumes") or 0)
        except (TypeError, ValueError):
            declared = 0
        entry["library_volume_count"] = max(
            entry.get("library_volume_count") or 0,
            len(vols),
            declared,
        )
        for v in vols:
            vn = v.get("volume_number") if isinstance(v, dict) else None
            try:
                if vn is not None:
                    entry["owned"].add(int(vn))
            except (TypeError, ValueError):
                pass

    return series_map, owned_titles


async def _prefetch_wd_docs(series_map: dict[str, dict]) -> dict[str, Optional[dict]]:
    """Wikidata en parallèle pour toutes les séries (évite N+1 séquentiel)."""
    keys = list(series_map.keys())
    if not keys:
        return {}
    docs = await asyncio.gather(
        *(asyncio.to_thread(_find_series_doc, series_map[k]["name"]) for k in keys)
    )
    return dict(zip(keys, docs))


def _curated_volume_titles(entry: dict) -> dict[int, str]:
    titles: dict[int, str] = {}
    raw = entry.get("volume_titles") or []
    if isinstance(raw, dict):
        for k, v in raw.items():
            try:
                titles[int(k)] = str(v or "")
            except (TypeError, ValueError):
                continue
    elif isinstance(raw, list):
        for t in raw:
            if not isinstance(t, dict) or t.get("volume_number") is None:
                continue
            try:
                titles[int(t["volume_number"])] = str(t.get("title") or "")
            except (TypeError, ValueError):
                continue
    return titles


def _curated_volume_details(entry: dict) -> dict[int, dict]:
    out: dict[int, dict] = {}
    raw = entry.get("volume_details") or {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        try:
            out[int(k)] = v if isinstance(v, dict) else {}
        except (TypeError, ValueError):
            continue
    return out


def _is_unreleased_volume(detail: dict | None, today_year: int) -> bool:
    """True si le référentiel indique un tome pas encore paru."""
    if not detail:
        return False
    if detail.get("released") is False:
        return True
    if detail.get("released") is True:
        return False
    if "published_year" in detail:
        y = detail.get("published_year")
        if y is None or y == "":
            return True
        try:
            if int(y) > today_year:
                return True
        except (TypeError, ValueError):
            return True
    pub = detail.get("publish_date")
    if pub:
        iso = str(pub)[:10]
        if len(iso) == 10 and iso > date.today().isoformat():
            return True
    return False


def _curated_has_unreleased(details: dict[int, dict], today_year: int) -> bool:
    return any(_is_unreleased_volume(d, today_year) for d in details.values())


def _curated_status_complete(curated: dict | None, details: dict[int, dict], today_year: int) -> bool:
    """Série considérée terminée (plus de suite attendue hors tomes explicitement non sortis)."""
    if not curated:
        return False
    status = str(curated.get("status") or "").lower().strip()
    if status in ("completed", "finished", "ended", "complete"):
        return not _curated_has_unreleased(details, today_year)
    if status in ("ongoing", "hiatus", "announced"):
        return False
    # Sans statut : terminée si tous les tomes curatés sont parus
    total = int(curated.get("volumes") or 0)
    if total > 0 and details and len(details) >= total:
        return not _curated_has_unreleased(details, today_year)
    return False


def _is_standalone_series(entry: dict, curated: dict | None, curated_total: int) -> bool:
    """Livre individuel / fausse série à 1 tome — pas de « prochain tome » à inventer."""
    lib_count = int(entry.get("library_volume_count") or 0)
    owned_n = len(entry.get("owned") or [])
    slots = max(lib_count, owned_n)
    if curated_total > 1:
        return False
    if curated_total == 1:
        return True
    # Pas de référentiel multi-tomes : 0–1 slot en bibliothèque = standalone
    return slots <= 1


def _build_next_tomes(
    series_map: dict[str, dict],
    today_iso: str,
    manga_info: dict[str, dict] | None = None,
    wd_docs: dict[str, Optional[dict]] | None = None,
) -> list[dict]:
    """
    Prochains tomes **à paraître** uniquement :
    - pas de suites inventées pour livres individuels ;
    - pas de tomes déjà sortis (trous de collection) ;
    - pas de séries terminées sans tome annoncé non sorti.
    """
    manga_info = manga_info or {}
    wd_docs = wd_docs or {}
    items: list[dict] = []
    today_year = date.fromisoformat(today_iso).year

    for key, entry in series_map.items():
        owned = set(entry["owned"] or [])
        curated = match_curated(entry["name"], entry.get("author"))
        details = _curated_volume_details(curated) if curated else {}
        titles = _curated_volume_titles(curated) if curated else {}
        curated_total = int(curated.get("volumes") or 0) if curated else 0

        # Livre unique ajouté comme « série » → ignorer
        if _is_standalone_series(entry, curated, curated_total):
            continue

        # Les slots catalogue non sortis (ex. Red God) ne comptent pas comme « possédés »
        released_owned = {
            vn
            for vn in owned
            if not _is_unreleased_volume(details.get(vn), today_year)
        }
        owned_max = max(released_owned) if released_owned else 0

        info = manga_info.get(key)
        is_manga = (entry.get("category") or "").lower() == "manga"
        if is_manga and info:
            base = max(owned_max, info.get("max_tagged_vol", 0), info.get("max_released_vol", 0))
        else:
            base = owned_max
        next_vol = base + 1
        vol_title = titles.get(next_vol) or ""
        curated_unreleased = False

        # Premier tome curaté non sorti (prioritaire sur owned_max+1)
        if curated and details:
            for n in range(1, (curated_total or max(details) or 0) + 1):
                if n in released_owned:
                    continue
                if _is_unreleased_volume(details.get(n), today_year):
                    next_vol = n
                    vol_title = titles.get(n) or vol_title
                    curated_unreleased = True
                    break

        # Série marquée terminée (biblio ou référentiel) sans tome annoncé
        lib_completed = (entry.get("series_status") or "").lower() == "completed"
        if (
            (lib_completed or _curated_status_complete(curated, details, today_year))
            and not curated_unreleased
        ):
            continue

        if curated_total and next_vol > curated_total and not curated_unreleased:
            continue

        wd_doc = wd_docs.get(key) if key in wd_docs else _find_series_doc(entry["name"])
        vol_works = _extract_volumes(wd_doc.get("works")) if wd_doc else {}

        work = vol_works.get(next_vol)
        iso, conf = parse_pub_date(work.get("publication_date")) if work else (None, "unknown")
        detail = details.get(next_vol) or {}
        if not iso and detail.get("publish_date"):
            iso, conf = parse_pub_date(detail.get("publish_date"))
        if not iso and detail.get("published_year"):
            try:
                y = int(detail["published_year"])
                iso = f"{y:04d}-01-01"
                conf = "year"
            except (TypeError, ValueError):
                pass

        available = bool(iso) and iso <= today_iso
        is_future = bool(iso) and iso > today_iso

        # À venir = annoncé non sorti, ou date future. Pas les tomes déjà parus.
        if curated_unreleased:
            available = False
        elif is_future:
            pass
        elif is_manga and info and next_vol > owned_max:
            # Manga en cours : garder le prochain tome même sans date si MU/WD le connaît
            max_known = max(info.get("max_tagged_vol", 0), info.get("max_released_vol", 0))
            if next_vol > max_known + 1 and not work:
                continue
            if available:
                continue
        else:
            # Speculatif (Tome N+1 sans preuve de non-sortie) → ignorer
            continue

        source = "curated" if curated_unreleased else ("wikidata" if work else "library")
        if is_manga and info and not curated_unreleased:
            source = "mangaupdates+wikidata" if wd_doc else "mangaupdates"

        display_title = (
            f"{entry['name']} — {vol_title}"
            if vol_title
            else f"{entry['name']} — Tome {next_vol}"
        )

        items.append(
            {
                "id": f"tome:{key}:{next_vol}",
                "type": "next_tome",
                "title": display_title,
                "author": entry["author"],
                "cover_url": entry["cover"],
                "category": entry["category"],
                "series_name": entry["name"],
                "volume": next_vol,
                "date": iso,
                "date_confidence": conf if iso else "unknown",
                "source": source,
                "available": False,
                "confirmed": True,
                "reason": (
                    f"À paraître — suite de {entry['name']}"
                    if curated_unreleased
                    else f"Suite de {entry['name']}"
                ),
            }
        )
    return items


def _enrich_next_tome_date(item: dict, today_iso: str) -> None:
    """
    Complète (en place) la date d'un prochain tome sans date, via Google Books.
    Règles prudentes pour éviter d'accrocher la date d'un ancien tome :
    - une sortie **future** de la série est très probablement le prochain tome ;
    - une sortie **récente** (< 180 j) n'est retenue que si son titre mentionne le
      numéro de tome recherché.
    """
    series = item.get("series_name") or ""
    author = item.get("author") or ""
    next_vol = item.get("volume")
    if not series:
        return

    query = f'intitle:"{series}"'
    if author:
        query += f' inauthor:"{author}"'
    results = _gb_items(query, order_by="newest", max_results=20)
    if not results:
        return

    past_horizon = (date.fromisoformat(today_iso) - timedelta(days=_TOME_PAST_HORIZON_DAYS)).isoformat()
    future: list[tuple[str, str, bool]] = []
    recent_matches: list[tuple[str, str]] = []

    for it in results:
        iso, conf = parse_pub_date(it.get("published_date"))
        if not iso:
            continue
        blob = f"{it.get('title', '')} {it.get('subtitle', '')}"
        matches_vol = bool(next_vol) and re.search(rf"(?<!\d){next_vol}(?!\d)", blob) is not None
        if iso >= today_iso:
            future.append((iso, conf, matches_vol))
        elif matches_vol and iso >= past_horizon:
            recent_matches.append((iso, conf))

    if future:
        future.sort(key=lambda x: (not x[2], x[0]))  # tome correspondant d'abord, puis date la plus proche
        iso, conf, _ = future[0]
        item.update(date=iso, date_confidence=conf, available=False, source="google_books", confirmed=True)
    elif recent_matches:
        recent_matches.sort(key=lambda x: x[0], reverse=True)
        iso, conf = recent_matches[0]
        item.update(date=iso, date_confidence=conf, available=True, source="google_books", confirmed=True)


def _build_author_releases(author: str, owned_titles: set[str], today_iso: str, today: date) -> list[dict]:
    """Nouveautés (récentes ou à venir) d'un auteur suivi, via Google Books."""
    past_horizon = (today - timedelta(days=_AUTHOR_PAST_HORIZON_DAYS)).isoformat()
    results = _gb_items(f'inauthor:"{author}"', order_by="newest", max_results=20)

    out: list[dict] = []
    seen: set[str] = set()
    for it in results:
        iso, conf = parse_pub_date(it.get("published_date"))
        if not iso or iso < past_horizon:
            continue
        title = it.get("title") or ""
        key = _norm(title)
        if not key or key in seen or key in owned_titles:
            continue
        seen.add(key)
        cover = (it.get("thumbnail") or "").replace("http://", "https://")
        out.append(
            {
                "id": f"author:{_norm(author)}:{key}",
                "type": "author_release",
                "title": title,
                "author": author,
                "cover_url": cover,
                "category": gb.infer_book_category_from_google_item(it),
                "series_name": None,
                "volume": None,
                "date": iso,
                "date_confidence": conf,
                "source": "google_books",
                "available": iso <= today_iso,
                "confirmed": True,
                "reason": f"Nouveauté de {author}",
                "isbn": it.get("isbn_13") or it.get("isbn_10") or "",
                "google_books_id": it.get("google_books_id") or "",
            }
        )
        if len(out) >= _MAX_ITEMS_PER_AUTHOR:
            break
    return out


def _build_watchlist(user_id: str, today_iso: str) -> list[dict]:
    items: list[dict] = []
    query = {"user_id": user_id, "$or": [{"watchlist": True}, {"status": "upcoming"}]}
    for b in books_collection.find(query, {"_id": 0}):
        iso, conf = parse_pub_date(b.get("publish_date") or b.get("published_date"))
        if not conf or conf == "unknown":
            conf = b.get("date_confidence") or "unknown"
        available = bool(iso) and iso <= today_iso
        items.append(
            {
                "id": f"watch:{b.get('id')}",
                "book_id": b.get("id"),
                "type": "watchlist",
                "title": b.get("title", ""),
                "author": b.get("author", ""),
                "cover_url": b.get("cover_url", ""),
                "category": b.get("category", "roman"),
                "series_name": b.get("saga") or None,
                "volume": b.get("volume_number"),
                "date": iso,
                "date_confidence": conf,
                "source": "library",
                "available": available,
                "confirmed": True,
                "reason": "Livre surveillé",
            }
        )
    return items


async def _fetch_manga_chapters_map(series_map: dict[str, dict]) -> dict[str, Any]:
    """Récupère (en parallèle) les données de chapitres MangaUpdates des séries manga."""
    manga_keys = [
        k for k, e in series_map.items() if (e.get("category") or "").lower() == "manga"
    ]
    out: dict[str, Any] = {}
    if not manga_keys:
        return out

    async def _one(key: str, name: str) -> None:
        try:
            sc = await _chapter_service.get_series_chapters(name)
            if sc:
                out[key] = sc
        except Exception as exc:  # pragma: no cover - dépend de sources externes
            logger.debug("Chapitres indisponibles pour %s : %s", name, exc)

    await asyncio.gather(*(_one(k, series_map[k]["name"]) for k in manga_keys))
    return out


def _manga_tome_info(
    series_name: str,
    series_chapters: Any,
    today_iso: str,
    wd_doc: Optional[dict] = None,
) -> dict:
    """
    Analyse les tomes d'un manga pour déterminer :
    - ``released_chapters`` : chapitres appartenant à un tome CONFIRMÉ déjà sorti
      (date officielle Wikidata passée) — ils ne doivent plus s'afficher chapitre
      par chapitre ;
    - ``max_released_vol`` : plus haut tome confirmé sorti ;
    - ``max_tagged_vol`` : plus haut tome étiqueté par MangaUpdates.
    """
    tagged_vols: set[int] = set()
    volumes = getattr(series_chapters, "volumes", None) or []
    for vol in volumes:
        tagged_vols.add(vol.volume_number)

    if wd_doc is None:
        wd_doc = _find_series_doc(series_name)
    vol_works = _extract_volumes(wd_doc.get("works")) if wd_doc else {}

    released_chapters: set[float] = set()
    max_released_vol = 0
    for vol in volumes:
        work = vol_works.get(vol.volume_number)
        iso, conf = parse_pub_date(work.get("publication_date")) if work else (None, "unknown")
        if iso and conf != "unknown" and iso <= today_iso:
            released_chapters.update(vol.chapters_included)
            max_released_vol = max(max_released_vol, vol.volume_number)

    return {
        "released_chapters": released_chapters,
        "max_released_vol": max_released_vol,
        "max_tagged_vol": max(tagged_vols) if tagged_vols else 0,
    }


async def _build_manga_chapters(
    series_map: dict[str, dict],
    today_iso: str,
    manga_info: dict[str, dict] | None = None,
) -> list[dict]:
    """
    Sorties de chapitres manga prédites, filtrées sur les séries de l'utilisateur.

    Les chapitres déjà regroupés dans un tome confirmé sorti sont masqués : ils
    n'apparaissent plus individuellement (ils « vivent » désormais dans le tome).
    """
    manga_info = manga_info or {}
    user_series_names = [e.get("name") for e in series_map.values() if e.get("name")]
    try:
        releases = await _chapter_service.get_upcoming_releases(
            series_names=user_series_names or None
        )
    except Exception as exc:  # pragma: no cover
        logger.debug("Chapters upcoming indisponible : %s", exc)
        return []

    items: list[dict] = []
    for bucket in ("this_week", "next_week", "this_month"):
        for rel in releases.get(bucket, []) or []:
            name = rel.get("series_name") or ""
            key = _norm(name)
            if key not in series_map:
                continue

            chapter = rel.get("chapter_number")
            # Masquage : chapitre déjà collecté dans un tome confirmé sorti.
            released = manga_info.get(key, {}).get("released_chapters") or set()
            if chapter is not None and float(chapter) in released:
                continue

            entry = series_map[key]
            iso, conf = parse_pub_date(rel.get("estimated_date"))
            if iso and conf == "exact":
                conf = "estimated"  # c'est une prédiction, pas une date officielle
            items.append(
                {
                    "id": f"chapter:{key}:{chapter}",
                    "type": "manga_chapter",
                    "title": f"{name} — Chapitre {chapter}" if chapter else f"{name} — Nouveau chapitre",
                    "author": entry.get("author", ""),
                    "cover_url": entry.get("cover", ""),
                    "category": "manga",
                    "series_name": name,
                    "volume": None,
                    "date": iso,
                    "date_confidence": conf or "estimated",
                    "source": "chapters",
                    "available": bool(iso) and iso <= today_iso,
                    "confirmed": False,
                    "reason": "Prochain chapitre estimé",
                }
            )
    return items


# Genres proposés dans « À venir », du plus spécifique au plus large.
_TASTE_GENRES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("fantasy", 'subject:"Fantasy"', ("fantasy", "fantastique")),
    ("science-fiction", 'subject:"Science fiction"', ("science fiction", "science-fiction")),
    ("polar", 'subject:"Detective and mystery stories"', ("polar", "detective", "mystery", "crime")),
    ("thriller", 'subject:"Thriller"', ("thriller", "suspense")),
    ("romance", 'subject:"Romance"', ("romance", "amour")),
    ("jeunesse", 'subject:"Young adult fiction"', ("jeunesse", "young adult")),
    ("historique", 'subject:"Historical fiction"', ("historique", "historical")),
    ("horreur", 'subject:"Horror"', ("horreur", "horror", "epouvante")),
)
_MAX_TASTE_QUERIES = 4
_MAX_SUGGESTIONS = 8
_SUGGESTION_PAST_DAYS = 75


def taste_queries(books: list[dict], followed_authors: list[str] | None = None) -> list[tuple[str, str]]:
    """Requêtes Google Books (query, raison) selon les lectures en cours et les genres."""
    followed = {_norm(a) for a in (followed_authors or []) if a}
    genre_weight: dict[str, float] = {}
    author_weight: dict[str, float] = {}
    category_weight: dict[str, float] = {}

    for book in books or []:
        status = (book.get("status") or "").strip()
        if status == "upcoming":
            continue
        weight = 1.0
        if status == "reading":
            weight = 5.0
        elif status == "completed":
            weight = 2.5
        elif status == "to_reread":
            weight = 2.0
        try:
            rating = float(book.get("rating") or 0)
        except (TypeError, ValueError):
            rating = 0.0
        if rating >= 4:
            weight += 1.5

        author = (book.get("author") or "").split(",")[0].strip()
        if author and _norm(author) not in followed:
            author_weight[author] = author_weight.get(author, 0.0) + weight

        blob = _norm(f"{book.get('genre') or ''} {book.get('category') or ''}")
        for label, _query, keywords in _TASTE_GENRES:
            if any(_norm(k) in blob for k in keywords):
                genre_weight[label] = genre_weight.get(label, 0.0) + weight

        category = (book.get("category") or "").strip().lower()
        if category in ("manga", "bd", "roman"):
            category_weight[category] = category_weight.get(category, 0.0) + weight

    queries: list[tuple[str, str]] = []
    # D'abord ce qui est en cours de lecture (auteurs), puis les genres dominants.
    reading_authors = []
    for book in books or []:
        if (book.get("status") or "") != "reading":
            continue
        author = (book.get("author") or "").split(",")[0].strip()
        if author and _norm(author) not in followed and author not in reading_authors:
            reading_authors.append(author)
    for author in reading_authors[:2]:
        queries.append((f'inauthor:"{author}"', f"Parce que tu lis {author}"))

    if not reading_authors:
        for author, _w in sorted(author_weight.items(), key=lambda x: x[1], reverse=True)[:1]:
            queries.append((f'inauthor:"{author}"', f"Proche de {author}"))

    for label, query, _keywords in _TASTE_GENRES:
        if genre_weight.get(label, 0) <= 0:
            continue
        queries.append((query, f"Dans tes genres : {label}"))

    if category_weight.get("manga", 0) >= 3 and "manga" not in genre_weight:
        queries.append(('subject:"Manga"', "Dans tes genres : manga"))
    if category_weight.get("bd", 0) >= 3:
        queries.append(('subject:"Comics & Graphic Novels"', "Dans tes genres : bande dessinée"))

    # Les genres les plus lus d'abord, en gardant les requêtes auteur en tête.
    author_part = [q for q in queries if q[0].startswith("inauthor:")]
    genre_part = [q for q in queries if not q[0].startswith("inauthor:")]
    genre_part.sort(key=lambda q: genre_weight.get(q[1].split(" : ")[-1], 0), reverse=True)
    return (author_part + genre_part)[:_MAX_TASTE_QUERIES]


def _gb_newest_fr(query: str, max_results: int = 8) -> list[dict]:
    if not gb.is_enabled():
        return []
    try:
        raw = gb.search_volumes(
            query,
            max_results=max_results,
            order_by="newest",
            lang_restrict="fr",
            print_type="books",
        )
        return [gb.simplify_item(it) for it in (raw.get("items") or []) if isinstance(it, dict)]
    except Exception as exc:  # pragma: no cover - API externe
        logger.debug("Suggestions GB échouées (%s) : %s", query, exc)
        return []


def _ol_newest(query: str, max_results: int = 8) -> list[dict]:
    """Repli Open Library : éditions récentes en français."""
    year = date.today().year
    q = query
    q = re.sub(r'^subject:"([^"]+)"$', r"\1", q)
    q = re.sub(r'^inauthor:"([^"]+)"$', r"\1", q)
    try:
        resp = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "q": q,
                "language": "fre",
                "sort": "new",
                "limit": max_results,
                "fields": "title,author_name,cover_i,first_publish_year,key,isbn",
            },
            timeout=8,
            headers={"User-Agent": "Booktime/1.0 (upcoming)"},
        )
        if not resp.ok:
            return []
        out = []
        for doc in (resp.json() or {}).get("docs") or []:
            pub_year = doc.get("first_publish_year")
            try:
                pub_year = int(pub_year)
            except (TypeError, ValueError):
                continue
            if pub_year < year:
                continue
            authors = doc.get("author_name") or []
            cover_i = doc.get("cover_i")
            isbn = (doc.get("isbn") or [""])[0]
            out.append(
                {
                    "title": doc.get("title") or "",
                    "authors": authors[:1],
                    "published_date": str(pub_year),
                    "thumbnail": (
                        f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg" if cover_i else ""
                    ),
                    "isbn_13": isbn if len(str(isbn)) == 13 else "",
                    "isbn_10": isbn if len(str(isbn)) == 10 else "",
                    "categories": [],
                    "subtitle": "",
                }
            )
        return out
    except Exception as exc:  # pragma: no cover
        logger.debug("Suggestions OL échouées (%s) : %s", query, exc)
        return []


def _suggestions_for_query(
    query: str,
    reason: str,
    *,
    owned_titles: set[str],
    seen: set[str],
    today: date,
    today_iso: str,
) -> list[dict]:
    past = (today - timedelta(days=_SUGGESTION_PAST_DAYS)).isoformat()
    hits = _gb_newest_fr(query)
    if not hits:
        hits = _ol_newest(query)
    out: list[dict] = []
    for it in hits:
        title = (it.get("title") or "").strip()
        key = _norm(title)
        if not key or key in seen or key in owned_titles:
            continue
        iso, conf = parse_pub_date(it.get("published_date"))
        if not iso or iso < past:
            continue
        authors = it.get("authors") or []
        author = authors[0] if authors else (it.get("author") or "")
        if isinstance(author, list):
            author = author[0] if author else ""
        seen.add(key)
        cover = (it.get("thumbnail") or "").replace("http://", "https://")
        out.append(
            {
                "id": f"suggest:{key}",
                "type": "suggestion",
                "title": title,
                "author": author,
                "cover_url": cover,
                "category": gb.infer_book_category_from_google_item(it) if it.get("categories") is not None else "roman",
                "series_name": None,
                "volume": None,
                "date": iso,
                "date_confidence": conf,
                "source": "suggestion",
                "available": iso <= today_iso,
                "confirmed": False,
                "reason": reason,
                "isbn": it.get("isbn_13") or it.get("isbn_10") or "",
                "google_books_id": it.get("google_books_id") or "",
            }
        )
        if len(out) >= 3:
            break
    return out


def _build_taste_suggestions(
    user_id: str,
    followed_authors: list[str],
    owned_titles: set[str],
    already: set[str],
    today: date,
    today_iso: str,
) -> list[dict]:
    proj = {"_id": 0, "title": 1, "author": 1, "genre": 1, "category": 1, "status": 1, "rating": 1}
    try:
        books = list(books_collection.find({"user_id": user_id}, proj))
    except Exception as exc:  # pragma: no cover
        logger.debug("Profil de lecture indisponible : %s", exc)
        return []
    queries = taste_queries(books, followed_authors)
    if not queries:
        return []
    seen = set(already)
    suggestions: list[dict] = []
    for query, reason in queries:
        if len(suggestions) >= _MAX_SUGGESTIONS:
            break
        batch = _suggestions_for_query(
            query,
            reason,
            owned_titles=owned_titles,
            seen=seen,
            today=today,
            today_iso=today_iso,
        )
        suggestions.extend(batch)
    return suggestions[:_MAX_SUGGESTIONS]


def _group_items(items: list[dict], today: date) -> dict[str, list[dict]]:
    end_of_week = (today + timedelta(days=(6 - today.weekday()))).isoformat()
    # Fin de mois : 28 + 4 jours puis retour au 1er, moins 1 jour.
    first_next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_of_month = (first_next_month - timedelta(days=1)).isoformat()
    today_iso = today.isoformat()

    groups = {"available": [], "this_week": [], "this_month": [], "later": [], "unknown": []}
    for it in items:
        d = it.get("date")
        if it.get("available"):
            groups["available"].append(it)
        elif not d:
            groups["unknown"].append(it)
        elif d <= end_of_week:
            groups["this_week"].append(it)
        elif d <= end_of_month:
            groups["this_month"].append(it)
        else:
            groups["later"].append(it)

    for key, lst in groups.items():
        if key == "unknown":
            lst.sort(key=lambda x: (x.get("series_name") or x.get("title") or ""))
        else:
            lst.sort(key=lambda x: x.get("date") or "9999")
    return groups


async def get_upcoming_for_user(current_user: dict) -> dict[str, Any]:
    """Point d'entrée : construit la charge utile complète des prochaines sorties.

    Les appels bloquants (Mongo, fichier Wikidata, HTTP Google Books) sont déportés
    dans des threads pour ne pas figer la boucle asyncio, et les requêtes Google
    Books sont parallélisées.
    """
    user_id = current_user["id"]
    today = date.today()
    today_iso = today.isoformat()

    series_map, owned_titles = await asyncio.to_thread(_collect_user_series, user_id)

    # MangaUpdates + Wikidata en parallèle (évite N+1 Wikidata séquentiel)
    manga_chapters_map, wd_docs = await asyncio.gather(
        _fetch_manga_chapters_map(series_map),
        _prefetch_wd_docs(series_map),
    )

    manga_info: dict[str, dict] = {}
    if manga_chapters_map:
        keys = list(manga_chapters_map.keys())
        infos = await asyncio.gather(
            *(
                asyncio.to_thread(
                    _manga_tome_info,
                    series_map[k]["name"],
                    manga_chapters_map[k],
                    today_iso,
                    wd_docs.get(k),
                )
                for k in keys
            )
        )
        manga_info = dict(zip(keys, infos))

    next_tomes = await asyncio.to_thread(
        _build_next_tomes, series_map, today_iso, manga_info, wd_docs
    )

    gb_on = gb.is_enabled()

    # Enrichissement GB borné + auteurs suivis + watchlist + chapitres — en parallèle
    async def _enrich_tomes() -> list[dict]:
        tomes = list(next_tomes)
        if not gb_on:
            return tomes
        to_enrich = [
            it
            for it in tomes
            if not it.get("date") and it.get("source") != "curated"
        ][:_MAX_TOME_ENRICH]
        if to_enrich:
            await asyncio.gather(
                *(asyncio.to_thread(_enrich_next_tome_date, it, today_iso) for it in to_enrich)
            )
            tomes = [
                it
                for it in tomes
                if it.get("source") == "curated"
                or (it.get("date") and it["date"] > today_iso)
                or (
                    (it.get("category") or "").lower() == "manga"
                    and not it.get("available")
                )
            ]
        return tomes

    async def _author_releases() -> list[dict]:
        followed = current_user.get("followed_authors") or []
        if not (gb_on and isinstance(followed, list) and followed):
            return []
        results = await asyncio.gather(
            *(
                asyncio.to_thread(_build_author_releases, a, owned_titles, today_iso, today)
                for a in followed[:_MAX_FOLLOWED_AUTHORS]
            )
        )
        out: list[dict] = []
        for r in results:
            out.extend(r)
        return out

    followed = current_user.get("followed_authors") or []
    if not isinstance(followed, list):
        followed = []

    next_tomes, author_items, watchlist, manga = await asyncio.gather(
        _enrich_tomes(),
        _author_releases(),
        asyncio.to_thread(_build_watchlist, user_id, today_iso),
        _build_manga_chapters(series_map, today_iso, manga_info),
    )

    items = next_tomes + author_items + manga + watchlist
    already = {_norm(it.get("title")) for it in items if it.get("title")}
    suggestions = await asyncio.to_thread(
        _build_taste_suggestions,
        user_id,
        followed,
        owned_titles,
        already,
        today,
        today_iso,
    )
    groups = _group_items(items, today)

    counts = {k: len(v) for k, v in groups.items()}
    counts["suggestions"] = len(suggestions)
    counts["total"] = len(items) + len(suggestions)

    return {
        "items": items,
        "groups": groups,
        "suggestions": suggestions,
        "counts": counts,
        "generated_at": utcnow().isoformat(),
    }
