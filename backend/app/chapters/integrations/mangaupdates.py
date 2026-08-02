"""
Service d'intégration MangaUpdates
=================================

Intégration avec l'API publique v1 de MangaUpdates (Baka-Updates) pour :
- Recherche de séries manga
- Récupération des métadonnées de série (dernier chapitre, statut...)
- Récupération des sorties (scanlations) au niveau chapitre

⚠️ Rappel important sur la nature des données MangaUpdates :
MangaUpdates traque les **sorties de scanlation au niveau chapitre**. Le champ
`release_date` d'une sortie est la date de **scanlation du chapitre**, PAS la date
de publication officielle du tome (tankōbon). Le champ `volume` n'est renseigné
que lorsqu'un tome a été explicitement étiqueté (souvent tardivement, voire jamais
pour les chapitres récents). Les dates de sortie *officielles de tomes* doivent
donc venir d'une autre source (Wikidata / Google Books).

API sans clé, mais avec rate limiting : un cache mémoire fronte les appels.
"""

import re
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class MangaUpdatesService:
    """
    Client de l'API v1 MangaUpdates.

    Interface publique (consommée par ``ChapterService``) :
    - ``search_series(name, limit)``
    - ``get_series(series_id)``
    - ``get_series_releases(series_id, days_back)``
    - ``get_recent_releases_by_name(name, days_back)``
    - ``predict_next_release(name)``
    - ``health_check()``
    """

    BASE_URL = "https://www.mangaupdates.com"
    API_BASE = "https://api.mangaupdates.com/v1"

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 1.0  # Délai respectueux entre requêtes
        self.last_request_time = datetime.min
        self.cache: Dict[str, tuple] = {}
        self.cache_duration = timedelta(hours=4)

        # Patterns d'extraction depuis les champs texte MangaUpdates.
        self._chapter_num_re = re.compile(r"(\d+(?:\.\d+)?)")
        self._volume_total_re = re.compile(r"(\d+)\s*volume", re.IGNORECASE)

    # ── Session / HTTP ────────────────────────────────────────────────────────

    async def _ensure_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "BOOKTIME-Chapters/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )

    async def _rate_limit(self):
        now = datetime.now()
        elapsed = (now - self.last_request_time).total_seconds()
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = datetime.now()

    async def _request(
        self, method: str, path: str, json_body: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Effectue une requête vers l'API v1 MangaUpdates et renvoie le JSON décodé
        (ou None en cas d'échec). Gère le rate limit (429) avec un backoff simple.
        """
        await self._ensure_session()
        await self._rate_limit()

        url = path if path.startswith("http") else f"{self.API_BASE}{path}"

        try:
            async with self.session.request(method, url, json=json_body) as response:
                if response.status == 200:
                    return await response.json()
                if response.status == 429:
                    logger.warning("Rate limit MangaUpdates atteint, attente 30s...")
                    await asyncio.sleep(30)
                    return await self._request(method, path, json_body)
                logger.error("Erreur HTTP MangaUpdates %s sur %s", response.status, url)
                return None
        except aiohttp.ClientError as exc:
            logger.error("Erreur connexion MangaUpdates: %s", exc)
            return None
        except Exception as exc:  # pragma: no cover - robustesse réseau
            logger.error("Erreur inattendue MangaUpdates: %s", exc)
            return None

    # ── Recherche de séries ───────────────────────────────────────────────────

    async def search_series(self, series_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche une série via ``POST /v1/series/search``.

        Retourne une liste normalisée de dicts : ``id``, ``title``,
        ``latest_chapter``, ``total_volumes`` (si connu), ``year``, ``mu_url``,
        ``confidence``.
        """
        if not series_name or not isinstance(series_name, str):
            return []

        cache_key = f"search_{series_name.lower()}_{limit}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._request(
            "POST",
            "/series/search",
            {"search": series_name, "perpage": max(1, min(limit, 50))},
        )
        if not data:
            return []

        results: List[Dict[str, Any]] = []
        for item in data.get("results", []) or []:
            record = item.get("record") or {}
            series_id = record.get("series_id")
            title = record.get("title") or ""
            if not series_id or not title:
                continue

            results.append(
                {
                    "id": series_id,
                    "title": title,
                    "latest_chapter": self._parse_chapter_number(record.get("latest_chapter")),
                    "total_volumes": self._parse_total_volumes(record),
                    "year": record.get("year"),
                    "type": (record.get("type") or "").lower(),
                    "mu_url": record.get("url") or f"{self.BASE_URL}/series/{series_id}",
                    "confidence": self._search_confidence(series_name, record, item),
                }
            )

        results.sort(key=lambda r: r["confidence"], reverse=True)
        results = results[:limit]
        self._save_to_cache(cache_key, results)
        logger.info("MangaUpdates: %d résultats pour '%s'", len(results), series_name)
        return results

    async def get_series(self, series_id: int) -> Optional[Dict[str, Any]]:
        """Récupère le profil d'une série via ``GET /v1/series/{id}``."""
        cache_key = f"series_{series_id}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        record = await self._request("GET", f"/series/{series_id}")
        if not record:
            return None

        result = {
            "id": record.get("series_id", series_id),
            "title": record.get("title") or "",
            "latest_chapter": self._parse_chapter_number(record.get("latest_chapter")),
            "total_volumes": self._parse_total_volumes(record),
            "year": record.get("year"),
            "status_text": record.get("status") or "",
            "mu_url": record.get("url") or f"{self.BASE_URL}/series/{series_id}",
        }
        self._save_to_cache(cache_key, result, duration=timedelta(hours=12))
        return result

    # ── Sorties (chapitres) ───────────────────────────────────────────────────

    async def get_series_releases(
        self, series_id: int, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Récupère les sorties (scanlations) récentes d'une série.

        MangaUpdates ne propose pas de recherche de sorties par ``series_id`` :
        on recherche par titre puis on filtre sur l'``id`` de série présent dans
        les métadonnées de chaque sortie.
        """
        cache_key = f"releases_{series_id}_{days_back}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        series = await self.get_series(series_id)
        if not series or not series.get("title"):
            return []

        releases = await self._search_releases(series["title"], series_id, days_back)
        self._save_to_cache(cache_key, releases, duration=timedelta(hours=1))
        logger.info("MangaUpdates: %d sorties pour série %s", len(releases), series_id)
        return releases

    async def _search_releases(
        self, title: str, series_id: Optional[int], days_back: int
    ) -> List[Dict[str, Any]]:
        """Appelle ``POST /v1/releases/search`` et normalise/filtre le résultat."""
        data = await self._request(
            "POST",
            "/releases/search",
            {"search": title, "perpage": 50},
        )
        if not data:
            return []

        cutoff = datetime.now() - timedelta(days=days_back) if days_back else None
        out: List[Dict[str, Any]] = []

        for item in data.get("results", []) or []:
            record = item.get("record") or {}

            # Filtrage sur la série cible via les métadonnées de la sortie.
            if series_id is not None and not self._release_matches_series(item, series_id):
                continue

            chapter_number = self._parse_chapter_number(record.get("chapter"))
            if chapter_number is None:
                continue

            release_iso = self._parse_release_date(record.get("release_date"))
            if cutoff and release_iso:
                try:
                    if datetime.strptime(release_iso, "%Y-%m-%d") < cutoff:
                        continue
                except ValueError:
                    pass

            groups = [
                g.get("name")
                for g in (record.get("groups") or [])
                if isinstance(g, dict) and g.get("name")
            ]

            out.append(
                {
                    "chapter_number": chapter_number,
                    "title": record.get("title") or f"Chapter {chapter_number}",
                    "release_date": release_iso,
                    "volume": self._parse_volume(record.get("volume")),
                    "groups": groups,
                    "raw_text": f"{record.get('title', '')} v{record.get('volume', '')} c{record.get('chapter', '')}",
                }
            )

        out.sort(key=lambda r: r["chapter_number"], reverse=True)
        return out

    async def get_recent_releases_by_name(
        self, series_name: str, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Récupère les sorties récentes à partir d'un nom de série."""
        cache_key = f"releases_name_{series_name.lower()}_{days_back}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        matches = await self.search_series(series_name, limit=1)
        if not matches:
            return []

        series = matches[0]
        releases = await self.get_series_releases(series["id"], days_back)
        for release in releases:
            release["series_info"] = {
                "name": series.get("title"),
                "id": series.get("id"),
                "mu_url": series.get("mu_url"),
            }

        self._save_to_cache(cache_key, releases, duration=timedelta(hours=1))
        return releases

    async def predict_next_release(self, series_name: str) -> Optional[Dict[str, Any]]:
        """Prédit la prochaine sortie à partir de l'historique des intervalles."""
        try:
            recent = await self.get_recent_releases_by_name(series_name, days_back=120)
            dates: List[datetime] = []
            for release in recent:
                iso = release.get("release_date")
                if not iso:
                    continue
                try:
                    dates.append(datetime.strptime(iso, "%Y-%m-%d"))
                except ValueError:
                    continue

            if len(dates) < 2:
                return None

            dates.sort()
            intervals = [
                (dates[i] - dates[i - 1]).days
                for i in range(1, len(dates))
                if (dates[i] - dates[i - 1]).days > 0
            ]
            if not intervals:
                return None

            avg_interval = sum(intervals) / len(intervals)
            last_release = max(dates)
            predicted_date = last_release + timedelta(days=avg_interval)

            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            confidence = max(0.1, min(0.9, 1.0 - (variance / (avg_interval * avg_interval)))) if avg_interval else 0.1

            return {
                "predicted_date": predicted_date.strftime("%Y-%m-%d"),
                "confidence": confidence,
                "average_interval_days": avg_interval,
                "last_release_date": last_release.strftime("%Y-%m-%d"),
                "pattern": "weekly" if 6 <= avg_interval <= 8 else "irregular",
                "data_points": len(dates),
            }
        except Exception as exc:  # pragma: no cover
            logger.error("Erreur prédiction release '%s': %s", series_name, exc)
            return None

    async def health_check(self) -> bool:
        """Vérifie l'accessibilité de l'API (série One Piece, id 15090100540)."""
        try:
            data = await self._request("GET", "/series/15090100540")
            return bool(data and data.get("title"))
        except Exception:
            return False

    # ── Parsing / helpers ─────────────────────────────────────────────────────

    def _parse_chapter_number(self, raw: Any) -> Optional[float]:
        """Extrait un numéro de chapitre depuis un champ hétérogène (str/int)."""
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None
        match = self._chapter_num_re.search(str(raw))
        if not match:
            return None
        try:
            return float(match.group(1))
        except ValueError:
            return None

    def _parse_volume(self, raw: Any) -> Optional[int]:
        """Extrait un numéro de tome depuis le champ ``volume`` (souvent vide)."""
        if raw is None:
            return None
        if isinstance(raw, int):
            return raw
        match = re.search(r"\d+", str(raw))
        return int(match.group(0)) if match else None

    def _parse_total_volumes(self, record: Dict[str, Any]) -> Optional[int]:
        """Devine le nombre total de tomes depuis le texte de statut, si présent."""
        status = record.get("status") or ""
        match = self._volume_total_re.search(str(status))
        return int(match.group(1)) if match else None

    def _parse_release_date(self, raw: Any) -> Optional[str]:
        """Normalise une date de sortie MangaUpdates en 'YYYY-MM-DD'."""
        if not raw:
            return None
        s = str(raw).strip()
        # Formats courants renvoyés par l'API.
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(s.split("T")[0] if "T" in s else s, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _release_matches_series(self, release_item: Dict[str, Any], series_id: int) -> bool:
        """Vrai si la sortie appartient à la série ciblée (via métadonnées)."""
        metadata = release_item.get("metadata") or {}
        series_meta = metadata.get("series")
        if series_meta is None:
            # Pas de métadonnées de série : on ne peut pas garantir → on exclut.
            return False
        if isinstance(series_meta, dict):
            return series_meta.get("series_id") == series_id
        # Certains variantes renvoient directement l'id.
        try:
            return int(series_meta) == int(series_id)
        except (TypeError, ValueError):
            return False

    def _search_confidence(
        self, query: str, record: Dict[str, Any], item: Dict[str, Any]
    ) -> float:
        """Score de confiance basique par similarité de titre."""
        q = (query or "").lower().strip()
        title = (record.get("title") or "").lower().strip()
        hit_title = (item.get("hit_title") or "").lower().strip()

        if q and (q == title or q == hit_title):
            return 1.0
        if q and (q in title or title in q or (hit_title and q in hit_title)):
            return 0.85
        return 0.4

    def _get_from_cache(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_duration:
                return value
            del self.cache[key]
        return None

    def _save_to_cache(self, key: str, value: Any, duration: timedelta = None) -> None:
        self.cache[key] = (value, datetime.now())
        if len(self.cache) > 500:
            oldest = sorted(self.cache.items(), key=lambda kv: kv[1][1])
            for old_key, _ in oldest[:50]:
                del self.cache[old_key]

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
