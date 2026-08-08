"""
PHASE 3.1 - Système de Recommandations
Service principal pour générer des recommendations personnalisées
Algorithme ML basique basé sur la bibliothèque utilisateur
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging
from dataclasses import dataclass
import math
import re
import asyncio

from ..database.connection import client
from ..openlibrary.service import OpenLibraryService
from ..google_books import service as google_books_service

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RecommendationItem:
    """Élément de recommandation structuré"""
    book_id: str
    title: str
    author: str
    category: str
    cover_url: Optional[str]
    confidence_score: float
    reasons: List[str]
    source: str  # 'library', 'openlibrary', 'algorithm'
    metadata: Dict

class RecommendationService:
    """Service de recommandations intelligent"""
    
    def __init__(self):
        self.db = client.booktime
        self.openlibrary_service = OpenLibraryService()
        self.min_confidence_score = 0.3
        self.max_recommendations = 20
        
    async def get_personalized_recommendations(self, user_id: str, limit: int = 10) -> Dict:
        """
        Génère des recommandations personnalisées basées sur la bibliothèque utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            limit: Nombre maximum de recommandations
            
        Returns:
            Dict avec recommendations et métadonnées
        """
        try:
            logger.info(f"Génération de recommandations pour l'utilisateur {user_id}")
            
            # 1. Analyser la bibliothèque utilisateur
            user_profile = await self._analyze_user_library(user_id)
            
            if not user_profile['has_books']:
                return await self._get_popular_recommendations(limit)
            
            # 2. Générer des recommandations par algorithme
            algorithm_recommendations = await self._generate_algorithm_recommendations(user_profile, limit)
            
            # 3. Enrichir avec Open Library
            enriched_recommendations = await self._enrich_with_openlibrary(algorithm_recommendations, user_profile)
            
            # 4. Scorer et trier
            scored_recommendations = await self._score_and_rank(enriched_recommendations, user_profile)
            
            # 5. Prendre les meilleures recommandations
            final_recommendations = scored_recommendations[:limit]
            
            return {
                'recommendations': [self._format_recommendation(rec) for rec in final_recommendations],
                'user_profile': self._strip_internal(user_profile),
                'algorithm_info': {
                    'total_analyzed': len(algorithm_recommendations),
                    'total_enriched': len(enriched_recommendations),
                    'final_count': len(final_recommendations),
                    'min_confidence': self.min_confidence_score
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations: {str(e)}")
            return {
                'recommendations': [],
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }

    def _infer_seed_category(
        self,
        user_id: str,
        *,
        title: str = "",
        series_name: str = "",
        category: str = "",
        subjects: Optional[List[str]] = None,
    ) -> str:
        """Déduit roman / bd / manga pour ancrer les similaires."""
        cat = (category or "").strip().lower()
        if cat in ("roman", "bd", "manga"):
            return cat
        blob = f"{title} {series_name} {' '.join(str(s) for s in (subjects or []))}".lower()
        blob = blob.replace("é", "e").replace("è", "e")
        manga_kw = ("manga", "one piece", "naruto", "dragon ball", "shonen", "shonen")
        bd_kw = (
            "tintin",
            "asterix",
            "asterix",
            "lucky luke",
            "spirou",
            "gaston",
            "blake et mortimer",
            "bande dessinee",
            "bande dessinee",
            "comics",
            "dog man",
            "super chien",
            "graphic novel",
            "comic",
        )
        if any(k in blob for k in manga_kw):
            return "manga"
        if any(k in blob for k in bd_kw):
            return "bd"
        # Catégorie en bibliothèque pour cette série / ce titre
        try:
            target = self._normalize_title(series_name or title)
            if target:
                for book in self.db.books.find(
                    {"user_id": user_id},
                    {"title": 1, "saga": 1, "saga_name": 1, "series_name": 1, "category": 1},
                ):
                    c = (book.get("category") or "").lower()
                    if c not in ("bd", "manga", "roman"):
                        continue
                    saga = book.get("saga") or book.get("saga_name") or book.get("series_name") or ""
                    if saga and self._normalize_title(saga) == target:
                        return c
                    if self._normalize_title(book.get("title") or "") == target:
                        return c
                for series in self.db.series_library.find(
                    {"user_id": user_id},
                    {"series_name": 1, "name": 1, "category": 1},
                ):
                    name = series.get("series_name") or series.get("name") or ""
                    if name and self._normalize_title(name) == target:
                        c = (series.get("category") or "").lower()
                        if c in ("bd", "manga", "roman"):
                            return c
        except Exception as exc:
            logger.debug("infer seed category: %s", exc)
        return "roman"

    async def get_similar_to_seed(
        self,
        user_id: str,
        *,
        title: str = "",
        author: str = "",
        series_name: str = "",
        subjects: Optional[List[str]] = None,
        category: str = "",
        limit: int = 18,
    ) -> Dict:
        """
        Propositions similaires à un livre ou une série choisis par l'utilisateur.
        """
        seed_title = (series_name or title or "").strip()
        seed_author = (author or "").strip()
        if not seed_title:
            return {
                "recommendations": [],
                "seed": None,
                "error": "title_or_series_required",
                "generated_at": datetime.utcnow().isoformat(),
            }

        try:
            # Profil léger (possession + feedback) — évite l'analyse complète trop lente
            user_profile = await self._ownership_profile(user_id)

            # Auteur manquant : le déduire des tomes en bibliothèque
            if not seed_author:
                seed_author = self._author_from_library(
                    user_id, seed_title, series_name=series_name
                )

            seed_subjects = subjects or []
            if isinstance(seed_subjects, str):
                seed_subjects = [seed_subjects]

            seed_category = self._infer_seed_category(
                user_id,
                title=title,
                series_name=series_name,
                category=category,
                subjects=seed_subjects,
            )

            # Sur-fetch OL + Google Books (les deux sources, toujours)
            ol_n = max(limit * 2, 24)
            gb_n = max(limit, 16)

            ol_task = self.openlibrary_service.search_similar_books(
                seed_title,
                seed_author,
                limit=ol_n,
                subjects=seed_subjects if seed_subjects else None,
                category=seed_category,
            )
            gb_task = asyncio.to_thread(
                google_books_service.search_similar_books,
                seed_title,
                seed_author,
                limit=gb_n,
                subjects=seed_subjects if seed_subjects else None,
                category=seed_category,
            )
            ol_books, gb_books = await asyncio.gather(
                ol_task, gb_task, return_exceptions=True
            )
            if isinstance(ol_books, Exception):
                logger.warning("similar OL: %s", ol_books)
                ol_books = []
            if isinstance(gb_books, Exception):
                logger.warning("similar Google Books: %s", gb_books)
                gb_books = []
            ol_books = list(ol_books or [])
            gb_books = list(gb_books or [])

            # Filet dans la MÊME catégorie (Tintin → BD, pas romans fantasy)
            if len(ol_books) < max(6, limit // 2):
                try:
                    popular = await self.openlibrary_service.search_popular_books(
                        seed_category or "roman", limit=max(16, limit)
                    )
                    ol_books.extend(popular or [])
                except Exception as exc:
                    logger.debug("similar popular fallback: %s", exc)

            short = seed_title if len(seed_title) <= 42 else seed_title[:39] + "…"
            kind = "série" if (series_name or "").strip() else "livre"
            reason_ol = f"Proche de {kind} « {short} »"
            reason_gb = f"Proche de {kind} « {short} »"
            reason_pop = f"Dans le même esprit que « {short} »"

            out: List[RecommendationItem] = []
            seen = set()
            seed_norm = self._normalize_title(seed_title)
            series_norm = self._normalize_title(series_name or seed_title)
            author_norm = self._normalize_author(seed_author)
            seed_tokens = [
                w
                for w in seed_norm.split()
                if len(w) >= 4 and w not in {"tome", "book", "volume", "part", "serie", "series"}
            ]

            def _is_seed_universe(book: Dict) -> bool:
                """True si le livre appartient à la même série / même auteur seed."""
                title_b = self._normalize_title(book.get("title") or "")
                saga_b = self._normalize_title(
                    book.get("saga") or book.get("series_name") or ""
                )
                author_b = self._normalize_author(book.get("author") or "")
                subjects_b = " ".join(
                    str(s) for s in (book.get("subjects") or [])[:12]
                ).lower()
                blob = f"{title_b} {saga_b} {subjects_b}"
                if seed_norm and seed_norm in blob:
                    return True
                if series_norm and series_norm in blob:
                    return True
                if seed_tokens and all(t in blob for t in seed_tokens[:3]):
                    return True
                # Même auteur = souvent la même saga (Riordan / Percy Jackson)
                if author_norm and author_norm == author_b:
                    return True
                if author_norm and author_norm in author_b:
                    return True
                return False

            async def _push(
                book: Dict,
                *,
                source: str,
                reason: str,
                confidence: float,
                skip_owned: bool = True,
            ):
                title_b = (
                    book.get("display_title") or book.get("title_fr") or book.get("title") or ""
                ).strip()
                author_b = (book.get("author") or "").strip()
                if not title_b:
                    return
                if self._normalize_title(title_b) == seed_norm:
                    return
                if _is_seed_universe(book):
                    return
                # Ancrage catégorie : Tintin (BD) ≠ Harry Potter (roman)
                book_cat = (book.get("category") or "roman").lower()
                subjects_b = " ".join(
                    str(s) for s in (book.get("subjects") or [])[:12]
                ).lower()
                if seed_category == "bd":
                    if book_cat != "bd" and not any(
                        k in subjects_b
                        for k in ("comic", "bande dessin", "graphic novel", "strip")
                    ):
                        return
                elif seed_category == "manga":
                    if book_cat != "manga" and "manga" not in subjects_b:
                        return
                # Série déjà possédée → pas dans les « similaires »
                saga_b = (
                    book.get("saga")
                    or book.get("series_name")
                    or book.get("saga_name")
                    or ""
                )
                owned_series = set(user_profile.get("owned_series") or [])
                if saga_b and self._normalize_title(saga_b) in owned_series:
                    return
                key = self._book_key(title_b, author_b)
                if key in seen:
                    return
                seen.add(key)
                bid = book.get("ol_key") or book.get("google_books_id") or key
                if skip_owned and await self._should_skip(
                    user_profile,
                    bid,
                    title_b,
                    author_b,
                    ol_key=book.get("ol_key") or book.get("google_books_id"),
                    saga=saga_b,
                    alt_titles=[
                        book.get("original_title"),
                        book.get("display_title"),
                        book.get("title_fr"),
                    ],
                ):
                    return
                out.append(
                    RecommendationItem(
                        book_id=str(bid),
                        title=title_b,
                        author=author_b,
                        category=book.get("category") or seed_category or "roman",
                        cover_url=book.get("cover_url"),
                        confidence_score=confidence,
                        reasons=[reason],
                        source=source,
                        metadata={
                            **book,
                            "seed_title": seed_title,
                            "seed_author": seed_author,
                            "seed_kind": kind,
                            "seed_category": seed_category,
                            "provider": "google_books"
                            if source.endswith("_gb") or book.get("isFromGoogleBooks")
                            else "openlibrary",
                        },
                    )
                )

            # Alterner OL / GB pour diversifier la grille
            ol_i = gb_i = 0
            while len(out) < limit and (ol_i < len(ol_books) or gb_i < len(gb_books)):
                if ol_i < len(ol_books):
                    await _push(
                        ol_books[ol_i],
                        source="seed_similarity",
                        reason=reason_ol,
                        confidence=0.82,
                    )
                    ol_i += 1
                if len(out) >= limit:
                    break
                if gb_i < len(gb_books):
                    await _push(
                        gb_books[gb_i],
                        source="seed_similarity_gb",
                        reason=reason_gb,
                        confidence=0.78,
                    )
                    gb_i += 1

            # 2e passe : toujours hors univers seed ET hors bibliothèque
            if len(out) < 6:
                for book in ol_books + gb_books:
                    if len(out) >= limit:
                        break
                    src = (
                        "seed_similarity_gb"
                        if book.get("google_books_id") or book.get("isFromGoogleBooks")
                        else "seed_similarity"
                    )
                    await _push(
                        book,
                        source=src,
                        reason=reason_pop,
                        confidence=0.65,
                        skip_owned=True,
                    )

            if len(out) < 4:
                try:
                    # Dernier recours : populaires de la même catégorie uniquement
                    popular = await self.openlibrary_service.search_popular_books(
                        seed_category or "roman", limit=max(20, limit)
                    )
                    for book in popular or []:
                        if len(out) >= limit:
                            break
                        await _push(
                            book,
                            source="seed_similarity",
                            reason=reason_pop,
                            confidence=0.55,
                        )
                except Exception as exc:
                    logger.debug("similar last-resort popular: %s", exc)

            # Mémoire tampon catalogue : créer les entrées absentes (vignettes Booktime)
            try:
                self._upsert_similar_into_catalog(out)
            except Exception as exc:
                logger.debug("catalog upsert similaires: %s", exc)

            return {
                "recommendations": [self._format_recommendation(r) for r in out],
                "seed": {
                    "title": seed_title,
                    "author": seed_author,
                    "series_name": (series_name or "").strip() or None,
                    "kind": kind,
                },
                "sources": {
                    "openlibrary": len(ol_books or []),
                    "google_books": len(gb_books or []),
                },
                "count": len(out),
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error("Erreur similarité seed: %s", e)
            return {
                "recommendations": [],
                "seed": {"title": seed_title, "author": seed_author},
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat(),
            }

    def _upsert_similar_into_catalog(self, items: List[RecommendationItem]) -> int:
        """Crée dans books_catalog les livres similaires absents (mémoire tampon)."""
        try:
            catalog = self.db.books_catalog
        except Exception:
            return 0
        created = 0
        for rec in items or []:
            meta = rec.metadata if isinstance(rec.metadata, dict) else {}
            ol_key = (meta.get("ol_key") or rec.book_id or "").strip()
            gb_id = (meta.get("google_books_id") or "").strip()
            if not ol_key and not gb_id:
                continue
            lookup = {"ol_key": ol_key} if ol_key and not str(ol_key).startswith("gbooks_") else None
            if not lookup and gb_id:
                lookup = {"google_books_id": gb_id}
            if not lookup and ol_key:
                lookup = {"ol_key": ol_key}
            if not lookup:
                continue
            try:
                existing = catalog.find_one(lookup, {"_id": 1})
                if existing:
                    continue
                doc = {
                    "ol_key": ol_key or f"gbooks_{gb_id}",
                    "google_books_id": gb_id or None,
                    "title": rec.title,
                    "display_title": meta.get("display_title") or rec.title,
                    "title_fr": meta.get("title_fr"),
                    "original_title": meta.get("original_title"),
                    "author": rec.author,
                    "category": rec.category or "roman",
                    "cover_url": rec.cover_url or meta.get("cover_url") or "",
                    "subjects": (meta.get("subjects") or [])[:8],
                    "saga": meta.get("saga") or "",
                    "first_publish_year": meta.get("publication_year")
                    or meta.get("first_publish_year"),
                    "description": (meta.get("description") or "")[:2000],
                    "source": "similar_reco",
                    "popularity_score": 0,
                    "indexed_at": datetime.utcnow().isoformat(),
                }
                catalog.update_one(lookup, {"$setOnInsert": doc}, upsert=True)
                created += 1
            except Exception as exc:
                logger.debug("upsert catalog skip %s: %s", lookup, exc)
        if created:
            logger.info("Catalogue: %s entrées similaires ajoutées", created)
        return created

    async def _ownership_profile(self, user_id: str) -> Dict:
        """Profil minimal pour exclure livres / séries déjà en bibliothèque."""
        try:
            owned_keys = set()
            owned_titles = set()
            owned_ol_keys = set()
            owned_series = set()

            def _add_title(title: str, author: str = ""):
                t = (title or "").strip()
                if not t:
                    return
                norm = self._normalize_title(t)
                if norm:
                    owned_titles.add(norm)
                    owned_keys.add(self._book_key(t, author))

            def _add_ol(key):
                if not key:
                    return
                k = str(key).strip()
                if not k:
                    return
                owned_ol_keys.add(k)
                owned_ol_keys.add(k.lstrip("/"))
                if not k.startswith("/"):
                    owned_ol_keys.add("/" + k)

            cursor = self.db.books.find(
                {"user_id": user_id},
                {
                    "title": 1,
                    "author": 1,
                    "original_title": 1,
                    "display_title": 1,
                    "title_fr": 1,
                    "ol_key": 1,
                    "saga": 1,
                    "saga_name": 1,
                    "series_name": 1,
                },
            )
            for book in cursor:
                author = (book.get("author") or "").strip()
                for field in ("title", "original_title", "display_title", "title_fr"):
                    _add_title(book.get(field) or "", author)
                _add_ol(book.get("ol_key"))
                for field in ("saga", "saga_name", "series_name"):
                    saga = (book.get(field) or "").strip()
                    if saga:
                        owned_series.add(self._normalize_title(saga))

            try:
                for series in self.db.series_library.find(
                    {"user_id": user_id},
                    {"series_name": 1, "name": 1, "title": 1},
                ):
                    for field in ("series_name", "name", "title"):
                        name = (series.get(field) or "").strip()
                        if name:
                            owned_series.add(self._normalize_title(name))
            except Exception as exc:
                logger.debug("ownership series_library: %s", exc)

            return {
                "has_books": bool(owned_titles or owned_series),
                "owned_keys": owned_keys,
                "owned_titles": owned_titles,
                "owned_ol_keys": owned_ol_keys,
                "owned_series": owned_series,
                "disliked_book_ids": list(self._load_disliked_ids(user_id)),
                "high_rated_books": [],
                "completed_books": [],
            }
        except Exception as e:
            logger.warning("ownership profile: %s", e)
            return {
                "has_books": False,
                "owned_keys": set(),
                "owned_titles": set(),
                "owned_ol_keys": set(),
                "owned_series": set(),
                "disliked_book_ids": [],
                "high_rated_books": [],
                "completed_books": [],
            }

    def _author_from_library(
        self, user_id: str, seed_title: str, *, series_name: str = ""
    ) -> str:
        """Retrouve l'auteur d'un titre / série dans la biblio utilisateur."""
        try:
            target = self._normalize_title(series_name or seed_title)
            if not target:
                return ""
            cursor = self.db.books.find(
                {"user_id": user_id},
                {"author": 1, "saga_name": 1, "series_name": 1, "title": 1},
            )
            for book in cursor:
                if not book.get("author"):
                    continue
                saga = book.get("saga_name") or book.get("series_name") or ""
                if saga and self._normalize_title(saga) == target:
                    return str(book.get("author")).split(",")[0].strip()
                if self._normalize_title(book.get("title") or "") == target:
                    return str(book.get("author")).split(",")[0].strip()
        except Exception as e:
            logger.debug("author_from_library: %s", e)
        return ""
    
    async def _analyze_user_library(self, user_id: str) -> Dict:
        """Analyse la bibliothèque utilisateur pour créer un profil"""
        try:
            # Récupérer tous les livres de l'utilisateur
            books = list(self.db.books.find({"user_id": user_id}))
            
            if not books:
                return {
                    'has_books': False,
                    'total_books': 0,
                    'favorite_authors': [],
                    'favorite_categories': [],
                    'reading_patterns': {}
                }
            
            # Comptages bruts (pour affichage) + affinités pondérées (pour le scoring)
            author_counts = Counter()
            category_counts = Counter()
            author_affinity = defaultdict(float)
            category_affinity = defaultdict(float)
            high_rated_books = []
            completed_books = []

            # Index de toute la bibliothèque pour une déduplication fiable
            owned_keys = set()   # clé titre|auteur normalisée
            owned_titles = set() # titre normalisé seul (repli)
            owned_ol_keys = set()
            owned_series = set()
            
            for book in books:
                author = (book.get('author') or '').strip()
                category = (book.get('category') or '').strip()
                try:
                    rating = float(book.get('rating') or 0)
                except (TypeError, ValueError):
                    rating = 0.0
                status = book.get('status')

                # Poids d'affinité : privilégie ce qui est terminé et bien noté,
                # pénalise ce qui est mal noté.
                weight = 1.0
                if status == 'completed':
                    weight += 1.0
                if rating >= 4:
                    weight += 1.5
                elif rating == 3:
                    weight += 0.3
                elif 1 <= rating <= 2:
                    weight -= 1.0

                if author:
                    author_counts[author] += 1
                    author_affinity[author] += weight
                if category:
                    category_counts[category] += 1
                    category_affinity[category] += weight

                # « Bon score » : 4+ prioritaire ; 3+ accepté pour alimenter l'onglet Aimé
                if rating >= 3:
                    high_rated_books.append(book)
                if status == 'completed':
                    completed_books.append(book)

                # Indexer pour la déduplication (toute la bibliothèque)
                for field in ('title', 'original_title', 'display_title', 'title_fr'):
                    title = book.get(field) or ''
                    norm_title = self._normalize_title(title)
                    if norm_title:
                        owned_titles.add(norm_title)
                        owned_keys.add(self._book_key(title, author))
                ol_key = book.get('ol_key')
                if ol_key:
                    owned_ol_keys.add(str(ol_key))
                    owned_ol_keys.add(str(ol_key).lstrip('/'))
                for field in ('saga', 'saga_name', 'series_name'):
                    saga = (book.get(field) or '').strip()
                    if saga:
                        owned_series.add(self._normalize_title(saga))

            # Séries en library
            try:
                for series in self.db.series_library.find(
                    {"user_id": user_id},
                    {"series_name": 1, "name": 1, "title": 1},
                ):
                    for field in ("series_name", "name", "title"):
                        name = (series.get(field) or "").strip()
                        if name:
                            owned_series.add(self._normalize_title(name))
            except Exception:
                pass

            # Prioriser les meilleurs scores pour les suggestions « aimé »
            high_rated_books.sort(
                key=lambda b: (b.get('rating') or 0, 1 if b.get('status') == 'completed' else 0),
                reverse=True,
            )
            
            # Favoris pondérés par l'affinité (pas juste le nombre de livres)
            favorite_authors = [
                a for a, w in sorted(author_affinity.items(), key=lambda x: x[1], reverse=True)
                if w > 0
            ][:5]
            favorite_categories = [
                c for c, w in sorted(category_affinity.items(), key=lambda x: x[1], reverse=True)
                if w > 0
            ][:3]

            # Normaliser les affinités entre 0 et 1 pour le scoring
            max_author_w = max(author_affinity.values(), default=1.0) or 1.0
            max_cat_w = max(category_affinity.values(), default=1.0) or 1.0
            author_affinity_norm = {
                a: max(0.0, min(1.0, w / max_author_w)) for a, w in author_affinity.items()
            }
            category_affinity_norm = {
                c: max(0.0, min(1.0, w / max_cat_w)) for c, w in category_affinity.items()
            }

            # Feedback négatif : livres à ne plus recommander
            disliked_book_ids = self._load_disliked_ids(user_id)
            
            reading_patterns = {
                'completion_rate': len(completed_books) / len(books) if books else 0,
                'average_rating': sum((b.get('rating') or 0) for b in books) / len(books) if books else 0,
                'high_rated_count': len(high_rated_books),
                'preferred_languages': self._extract_languages(books),
                'series_preference': self._analyze_series_preference(books)
            }
            
            return {
                'has_books': True,
                'total_books': len(books),
                'favorite_authors': favorite_authors,
                'favorite_categories': favorite_categories,
                'reading_patterns': reading_patterns,
                'high_rated_books': high_rated_books[:12],  # Top livres bien notés (≥4)
                'completed_books': completed_books[:10],     # Top 10 livres terminés
                'author_counts': dict(author_counts.most_common(10)),
                'category_counts': dict(category_counts.most_common(5)),
                # Données internes pour un scoring plus pertinent (non affichées)
                'owned_keys': list(owned_keys),
                'owned_titles': list(owned_titles),
                'owned_ol_keys': list(owned_ol_keys),
                'owned_series': list(owned_series),
                'author_affinity': author_affinity_norm,
                'category_affinity': category_affinity_norm,
                'disliked_book_ids': list(disliked_book_ids),
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la bibliothèque: {str(e)}")
            return {'has_books': False, 'error': str(e)}

    def _normalize_title(self, title: str) -> str:
        """Normalise un titre pour la comparaison (casse, accents, ponctuation).

        Conserve les numéros de tome afin de ne pas confondre deux tomes
        différents d'une même série.
        """
        if not title:
            return ''
        import unicodedata
        t = title.lower().strip()
        t = unicodedata.normalize('NFD', t)
        t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn')
        t = re.sub(r'[^a-z0-9 ]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def _normalize_author(self, author: str) -> str:
        """Normalise un nom d'auteur pour la comparaison."""
        if not author:
            return ''
        a = author.lower().strip()
        a = re.sub(r'[^a-z0-9àâäéèêëïîôöùûüç ]', ' ', a)
        a = re.sub(r'\s+', ' ', a).strip()
        return a

    def _book_key(self, title: str, author: str) -> str:
        """Clé unique normalisée titre|auteur."""
        return f"{self._normalize_title(title)}|{self._normalize_author(author)}"

    def _load_disliked_ids(self, user_id: str) -> set:
        """Charge les identifiants de livres à exclure d'après le feedback négatif."""
        try:
            cursor = self.db.recommendation_feedback.find({
                "user_id": user_id,
                "feedback": {"$in": ["dislike", "not_interested"]}
            })
            return {
                doc.get('recommendation_id')
                for doc in cursor
                if doc.get('recommendation_id')
            }
        except Exception as e:
            logger.warning(f"Impossible de charger le feedback négatif: {str(e)}")
            return set()
    
    async def _generate_algorithm_recommendations(self, user_profile: Dict, limit: int) -> List[RecommendationItem]:
        """Génère des recommandations basées sur l'algorithme (sources en parallèle)."""
        try:
            author_n = max(4, limit // 3)
            category_n = max(4, limit // 3)
            series_n = max(4, limit // 3)
            similarity_n = max(12, limit // 2)

            results = await asyncio.gather(
                self._recommend_by_authors(user_profile, author_n),
                self._recommend_by_categories(user_profile, category_n),
                self._recommend_by_series(user_profile, series_n),
                self._recommend_by_similarity(user_profile, similarity_n),
                return_exceptions=True,
            )

            recommendations: List[RecommendationItem] = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Branche recommandations en échec: {result}")
                    continue
                recommendations.extend(result or [])
            return recommendations

        except Exception as e:
            logger.error(f"Erreur lors de la génération algorithme: {str(e)}")
            return []
    
    async def _recommend_by_authors(self, user_profile: Dict, limit: int) -> List[RecommendationItem]:
        """Recommandations basées sur les auteurs favoris"""
        recommendations = []
        
        try:
            favorite_authors = user_profile.get('favorite_authors', [])
            
            for author in favorite_authors[:3]:  # Top 3 auteurs
                # Chercher d'autres livres de cet auteur via Open Library
                author_books = await self.openlibrary_service.search_books_by_author(author, limit=5)
                
                for book in author_books:
                    # Écarter les livres déjà possédés ou rejetés
                    if not await self._should_skip(user_profile, book.get('ol_key', ''), book.get('title', ''), author):
                        rec = RecommendationItem(
                            book_id=book.get('ol_key', ''),
                            title=book.get('title', ''),
                            author=author,
                            category=book.get('category', 'roman'),
                            cover_url=book.get('cover_url'),
                            confidence_score=0.8,  # Haute confiance pour auteurs favoris
                            reasons=[f"Tu as aimé d'autres livres de {author}"],
                            source='algorithm_author',
                            metadata=book
                        )
                        recommendations.append(rec)
                        
                        if len(recommendations) >= limit:
                            break
                
                if len(recommendations) >= limit:
                    break
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recommandations auteurs: {str(e)}")
            return []
    
    async def _recommend_by_categories(self, user_profile: Dict, limit: int) -> List[RecommendationItem]:
        """Recommandations basées sur les catégories favorites"""
        recommendations = []
        
        try:
            favorite_categories = user_profile.get('favorite_categories', [])
            
            for category in favorite_categories:
                # Chercher des livres populaires dans cette catégorie
                popular_books = await self.openlibrary_service.search_popular_books(category, limit=8)
                
                for book in popular_books:
                    # Écarter les livres déjà possédés ou rejetés
                    if not await self._should_skip(user_profile, book.get('ol_key', ''), book.get('title', ''), book.get('author', '')):
                        rec = RecommendationItem(
                            book_id=book.get('ol_key', ''),
                            title=book.get('title', ''),
                            author=book.get('author', ''),
                            category=category,
                            cover_url=book.get('cover_url'),
                            confidence_score=0.6,  # Confiance moyenne pour catégories
                            reasons=[f"Tu lis beaucoup de {category}"],
                            source='algorithm_category',
                            metadata=book
                        )
                        recommendations.append(rec)
                        
                        if len(recommendations) >= limit:
                            break
                
                if len(recommendations) >= limit:
                    break
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recommandations catégories: {str(e)}")
            return []
    
    async def _recommend_by_series(self, user_profile: Dict, limit: int) -> List[RecommendationItem]:
        """Recommandations basées sur les séries"""
        recommendations = []
        
        try:
            # Analyser les séries dans la bibliothèque
            user_series = self._extract_user_series(user_profile)
            
            for series_name, books in user_series.items():
                # Si l'utilisateur a des livres d'une série, recommander le reste
                if len(books) > 0:
                    # Chercher la série complète
                    complete_series = await self.openlibrary_service.search_series(series_name, limit=10)
                    
                    for book in complete_series:
                        # Écarter les livres déjà possédés ou rejetés
                        if not await self._should_skip(user_profile, book.get('ol_key', ''), book.get('title', ''), book.get('author', '')):
                            rec = RecommendationItem(
                                book_id=book.get('ol_key', ''),
                                title=book.get('title', ''),
                                author=book.get('author', ''),
                                category=book.get('category', 'roman'),
                                cover_url=book.get('cover_url'),
                                confidence_score=0.9,  # Très haute confiance pour séries
                                reasons=[f"Prochain tome de la série {series_name}"],
                                source='algorithm_series',
                                metadata=book
                            )
                            recommendations.append(rec)
                            
                            if len(recommendations) >= limit:
                                break
                
                if len(recommendations) >= limit:
                    break
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recommandations séries: {str(e)}")
            return []
    
    async def _recommend_by_similarity(self, user_profile: Dict, limit: int) -> List[RecommendationItem]:
        """Livres similaires aux titres bien notés — Open Library + Google Books."""
        try:
            seeds = list(user_profile.get('high_rated_books') or [])
            # Repli : livres terminés correctement notés si peu de coups de cœur
            if len(seeds) < 2:
                for book in user_profile.get('completed_books') or []:
                    if (book.get('rating') or 0) >= 3:
                        key = self._book_key(book.get('title', ''), book.get('author', ''))
                        if not any(
                            self._book_key(s.get('title', ''), s.get('author', '')) == key
                            for s in seeds
                        ):
                            seeds.append(book)
                    if len(seeds) >= 4:
                        break

            if not seeds:
                seeds = list(user_profile.get('completed_books') or [])[:3]

            # Dernier repli : n'importe quels livres de la biblio (titres connus)
            if not seeds:
                for title_key in (user_profile.get('owned_titles') or [])[:3]:
                    if title_key:
                        seeds.append({'title': title_key, 'author': '', 'rating': 0})

            seeds = [s for s in seeds if (s.get('title') or '').strip()][:3]
            if not seeds:
                return []

            per_seed = max(4, (limit // max(1, len(seeds))) + 1)

            async def _for_seed(seed: Dict) -> List[RecommendationItem]:
                seed_title = (seed.get('title') or '').strip()
                seed_author = (seed.get('author') or '').strip()
                seed_rating = seed.get('rating') or 0
                seed_subjects = seed.get('subjects') or seed.get('genres') or []
                if isinstance(seed_subjects, str):
                    seed_subjects = [seed_subjects]

                ol_task = self.openlibrary_service.search_similar_books(
                    seed_title,
                    seed_author,
                    limit=per_seed,
                    subjects=seed_subjects if isinstance(seed_subjects, list) else None,
                )
                gb_task = asyncio.to_thread(
                    google_books_service.search_similar_books,
                    seed_title,
                    seed_author,
                    limit=max(3, per_seed // 2),
                    subjects=seed_subjects if isinstance(seed_subjects, list) else None,
                )
                ol_books, gb_books = await asyncio.gather(
                    ol_task, gb_task, return_exceptions=True
                )
                if isinstance(ol_books, Exception):
                    ol_books = []
                if isinstance(gb_books, Exception):
                    gb_books = []

                short_title = seed_title if len(seed_title) <= 42 else seed_title[:39] + '…'
                if seed_rating:
                    reason_ol = f"Parce que tu as aimé « {short_title} » ({seed_rating}/5) · Open Library"
                    reason_gb = f"Parce que tu as aimé « {short_title} » ({seed_rating}/5) · Google Books"
                else:
                    reason_ol = f"Parce que tu as aimé « {short_title} » · Open Library"
                    reason_gb = f"Parce que tu as aimé « {short_title} » · Google Books"

                base_confidence = 0.72 + 0.04 * min(5, float(seed_rating or 4))
                out: List[RecommendationItem] = []
                seen_local = set()

                async def _add(book: Dict, *, source: str, reason: str, conf: float):
                    title = book.get('title', '')
                    author = book.get('author', '')
                    key = self._book_key(title, author)
                    if key in seen_local:
                        return
                    seen_local.add(key)
                    bid = book.get('ol_key') or book.get('google_books_id') or ''
                    if await self._should_skip(user_profile, bid, title, author):
                        return
                    if seed_author and self._normalize_author(author) == self._normalize_author(seed_author):
                        return
                    out.append(RecommendationItem(
                        book_id=str(bid or key),
                        title=title,
                        author=author,
                        category=book.get('category', 'roman'),
                        cover_url=book.get('cover_url'),
                        confidence_score=min(0.95, conf),
                        reasons=[reason],
                        source=source,
                        metadata={
                            **book,
                            'seed_title': seed_title,
                            'seed_rating': seed_rating,
                            'provider': 'google_books' if source.endswith('_gb') else 'openlibrary',
                        },
                    ))

                for book in ol_books or []:
                    await _add(
                        book,
                        source='algorithm_similarity',
                        reason=reason_ol,
                        conf=base_confidence,
                    )
                for book in gb_books or []:
                    await _add(
                        book,
                        source='algorithm_similarity_gb',
                        reason=reason_gb,
                        conf=base_confidence - 0.04,
                    )
                return out

            batches = await asyncio.gather(
                *[_for_seed(s) for s in seeds],
                return_exceptions=True,
            )

            recommendations: List[RecommendationItem] = []
            for batch in batches:
                if isinstance(batch, Exception):
                    logger.warning(f"Similarité seed en échec: {batch}")
                    continue
                recommendations.extend(batch or [])

            return recommendations[:limit]

        except Exception as e:
            logger.error(f"Erreur recommandations similarité: {str(e)}")
            return []
    
    async def _enrich_with_openlibrary(self, recommendations: List[RecommendationItem], user_profile: Dict) -> List[RecommendationItem]:
        """Enrichit légèrement (sans N+1 Open Library — trop lent en prod)."""
        # Les sources algorithm_* viennent déjà d'Open Library avec couverture.
        # On ne fait plus de get_book_details par item (timeout fréquent).
        return recommendations
    
    async def _score_and_rank(self, recommendations: List[RecommendationItem], user_profile: Dict) -> List[RecommendationItem]:
        """Score, déduplique et classe les recommandations.

        Le score combine la confiance de la source avec l'affinité réelle de
        l'utilisateur (pondérée par ses notes et ses lectures terminées), ce qui
        remonte les suggestions les plus pertinentes.
        """
        author_affinity = user_profile.get('author_affinity', {}) or {}
        category_affinity = user_profile.get('category_affinity', {}) or {}

        # Déduplication inter-sources : on garde la meilleure occurrence par livre
        best_by_key: Dict[str, RecommendationItem] = {}

        for rec in recommendations:
            try:
                base_score = rec.confidence_score

                # Bonus proportionnel à l'affinité auteur (0 → 0.30)
                aff_author = author_affinity.get(rec.author, 0.0)
                base_score += 0.30 * aff_author
                # Repli : léger bonus si l'auteur est dans les favoris
                if aff_author == 0.0 and rec.author in user_profile.get('favorite_authors', []):
                    base_score += 0.1

                # Bonus proportionnel à l'affinité catégorie (0 → 0.15)
                aff_cat = category_affinity.get(rec.category, 0.0)
                base_score += 0.15 * aff_cat

                # Bonus pour les séries (fort signal de pertinence)
                if rec.source == 'algorithm_series':
                    base_score += 0.15

                # Bonus pour les similaires aux coups de cœur
                if rec.source == 'algorithm_similarity':
                    seed_rating = (rec.metadata or {}).get('seed_rating') or 0
                    base_score += 0.12 + 0.02 * min(5, float(seed_rating or 0))

                # Bonus léger pour les livres bien enrichis (description présente)
                if rec.metadata and rec.metadata.get('description'):
                    base_score += 0.05

                if base_score < self.min_confidence_score:
                    continue

                rec.confidence_score = min(base_score, 1.0)

                # Clé de déduplication
                key = self._book_key(rec.title, rec.author)
                existing = best_by_key.get(key)
                if existing is None or rec.confidence_score > existing.confidence_score:
                    best_by_key[key] = rec

            except Exception as e:
                logger.warning(f"Erreur scoring {rec.title}: {str(e)}")

        scored = list(best_by_key.values())
        scored.sort(key=lambda x: x.confidence_score, reverse=True)

        return scored
    
    async def _get_popular_recommendations(self, limit: int) -> Dict:
        """Recommandations populaires pour nouveaux utilisateurs"""
        try:
            # Récupérer les livres les plus populaires
            popular_books = await self.openlibrary_service.get_popular_books(limit=limit)
            
            recommendations = []
            for book in popular_books:
                rec = RecommendationItem(
                    book_id=book.get('ol_key', ''),
                    title=book.get('title', ''),
                    author=book.get('author', ''),
                    category=book.get('category', 'roman'),
                    cover_url=book.get('cover_url'),
                    confidence_score=0.7,
                    reasons=["Livre populaire pour commencer"],
                    source='popular',
                    metadata=book
                )
                recommendations.append(self._format_recommendation(rec))
            
            return {
                'recommendations': recommendations,
                'user_profile': {
                    'has_books': False,
                    'message': 'Recommandations populaires pour nouveaux utilisateurs'
                },
                'algorithm_info': {
                    'type': 'popular',
                    'count': len(recommendations)
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur recommandations populaires: {str(e)}")
            return {
                'recommendations': [],
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    # Clés internes de scoring à ne pas exposer au client
    _INTERNAL_PROFILE_KEYS = (
        'owned_keys', 'owned_titles', 'author_affinity',
        'category_affinity', 'disliked_book_ids',
        # Docs Mongo bruts (ObjectId / datetime) → cassent la sérialisation JSON
        'high_rated_books', 'completed_books',
    )

    def _public_book_summary(self, book: Dict) -> Dict:
        """Résumé JSON-safe d'un livre pour l'API profil."""
        if not isinstance(book, dict):
            return {}
        return {
            'title': book.get('title') or '',
            'author': book.get('author') or '',
            'rating': book.get('rating'),
            'status': book.get('status'),
            'category': book.get('category') or 'roman',
            'cover_url': book.get('cover_url'),
        }

    def _strip_internal(self, profile: Dict) -> Dict:
        """Retire les données internes / non sérialisables avant exposition API."""
        if not isinstance(profile, dict):
            return profile
        out = {k: v for k, v in profile.items() if k not in self._INTERNAL_PROFILE_KEYS}
        # Versions publiques (sans ObjectId Mongo)
        if 'high_rated_books' in profile:
            out['high_rated_books'] = [
                self._public_book_summary(b) for b in (profile.get('high_rated_books') or [])[:12]
            ]
        if 'completed_books' in profile:
            out['completed_books'] = [
                self._public_book_summary(b) for b in (profile.get('completed_books') or [])[:10]
            ]
        return out

    def _json_safe(self, value):
        """Convertit récursivement ObjectId / datetime en types JSON-safe."""
        try:
            from bson import ObjectId
        except ImportError:
            ObjectId = type(None)  # noqa: N806

        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if ObjectId is not type(None) and isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, dict):
            return {str(k): self._json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(v) for v in value]
        return str(value)

    def _format_recommendation(self, rec: RecommendationItem) -> Dict:
        """Formate une recommandation pour l'API (shape Booktime + métadonnées)."""
        meta = self._json_safe(rec.metadata or {}) if isinstance(rec.metadata, dict) else {}
        title_fr = meta.get("title_fr") or meta.get("display_title")
        display_title = meta.get("display_title") or title_fr or rec.title
        ol_key = meta.get("ol_key") or (
            rec.book_id if isinstance(rec.book_id, str) and "/works/" in str(rec.book_id) else None
        )
        return {
            "book_id": rec.book_id,
            "title": display_title or rec.title,
            "original_title": meta.get("original_title") or rec.title,
            "title_fr": title_fr,
            "display_title": display_title or rec.title,
            "author": rec.author,
            "category": rec.category,
            "cover_url": rec.cover_url or meta.get("cover_url"),
            "ol_key": ol_key or meta.get("ol_key") or "",
            "saga": meta.get("saga") or "",
            "subjects": meta.get("subjects") or [],
            "publication_year": meta.get("publication_year") or meta.get("first_publish_year"),
            "isFromOpenLibrary": True,
            "confidence_score": round(rec.confidence_score, 2),
            "reasons": rec.reasons,
            "source": rec.source,
            "metadata": meta,
        }
    
    async def _should_skip(
        self,
        user_profile: Dict,
        book_id: str,
        title: str,
        author: str,
        *,
        ol_key: str = None,
        saga: str = None,
        alt_titles: list = None,
    ) -> bool:
        """Détermine si un livre doit être écarté des recommandations.

        Un livre est écarté s'il est déjà dans la bibliothèque (comparaison sur
        l'ensemble de la bibliothèque, normalisée) ou s'il a fait l'objet d'un
        feedback négatif (dislike / pas intéressé).
        """
        # 1. Feedback négatif
        if book_id and book_id in set(user_profile.get('disliked_book_ids', [])):
            return True

        # 2. Déjà possédé — comparaison sur toute la bibliothèque
        owned_keys = set(user_profile.get('owned_keys', []))
        owned_titles = set(user_profile.get('owned_titles', []))
        owned_ol_keys = set(user_profile.get('owned_ol_keys', []))

        candidates = [title] + list(alt_titles or [])
        for cand in candidates:
            norm_title = self._normalize_title(cand or '')
            if norm_title and norm_title in owned_titles:
                return True
            if cand and self._book_key(cand, author) in owned_keys:
                return True

        # Clé OL / Google Books
        for key in (ol_key, book_id):
            if not key:
                continue
            k = str(key).strip()
            if k in owned_ol_keys or k.lstrip('/') in owned_ol_keys:
                return True

        # Note: on n'exclut PAS toute une série ici — `_recommend_by_series`
        # doit pouvoir proposer les tomes manquants d'une série déjà commencée.
        # L'exclusion de cartes série se fait côté similaires / frontend.

        # 3. Repli pour les profils factices (by-author / by-category)
        norm_title = self._normalize_title(title)
        for book in user_profile.get('high_rated_books', []) + user_profile.get('completed_books', []):
            if (self._normalize_title(book.get('title', '')) == norm_title and
                    self._normalize_author(book.get('author', '')) == self._normalize_author(author)):
                return True
        return False

    async def _user_has_book(self, user_profile: Dict, title: str, author: str) -> bool:
        """Compatibilité : vérifie si l'utilisateur possède déjà ce livre."""
        return await self._should_skip(user_profile, '', title, author)
    
    def _extract_languages(self, books: List[Dict]) -> List[str]:
        """Extrait les langues préférées"""
        languages = Counter()
        for book in books:
            lang = book.get('original_language', 'français')
            languages[lang] += 1
        return [lang for lang, count in languages.most_common(3)]
    
    def _analyze_series_preference(self, books: List[Dict]) -> Dict:
        """Analyse la préférence pour les séries"""
        series_books = []
        for book in books:
            if book.get('saga_name'):
                series_books.append(book)
        
        return {
            'total_series_books': len(series_books),
            'series_ratio': len(series_books) / len(books) if books else 0,
            'prefers_series': len(series_books) > len(books) * 0.3  # 30% seuil
        }
    
    def _extract_user_series(self, user_profile: Dict) -> Dict:
        """Extrait les séries de l'utilisateur"""
        series = defaultdict(list)
        
        for book in user_profile.get('high_rated_books', []) + user_profile.get('completed_books', []):
            saga_name = book.get('saga_name')
            if saga_name:
                series[saga_name].append(book)
        
        return dict(series)
    
    async def _find_similar_users(self, user_profile: Dict) -> List[Dict]:
        """Trouve des utilisateurs similaires"""
        try:
            # Algorithme simple basé sur les auteurs communs
            favorite_authors = user_profile.get('favorite_authors', [])
            
            if not favorite_authors:
                return []
            
            # Rechercher des utilisateurs qui ont des livres des mêmes auteurs
            similar_users = []
            
            for author in favorite_authors:
                users_with_author = self.db.books.distinct("user_id", {
                    "author": author,
                    "rating": {"$gte": 4}
                })
                
                for user_id in users_with_author:
                    if user_id not in [u.get('user_id') for u in similar_users]:
                        similar_users.append({
                            'user_id': user_id,
                            'common_author': author,
                            'similarity_score': 0.7
                        })
            
            return similar_users[:5]  # Top 5 utilisateurs similaires
            
        except Exception as e:
            logger.error(f"Erreur recherche utilisateurs similaires: {str(e)}")
            return []