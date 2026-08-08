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

    async def get_similar_to_seed(
        self,
        user_id: str,
        *,
        title: str = "",
        author: str = "",
        series_name: str = "",
        subjects: Optional[List[str]] = None,
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
            user_profile = await self._analyze_user_library(user_id)
            if not user_profile.get("has_books"):
                user_profile = {
                    "has_books": False,
                    "owned_keys": set(),
                    "owned_titles": set(),
                    "disliked_book_ids": [],
                    "high_rated_books": [],
                    "completed_books": [],
                }

            seed_subjects = subjects or []
            if isinstance(seed_subjects, str):
                seed_subjects = [seed_subjects]

            similar_books = await self.openlibrary_service.search_similar_books(
                seed_title,
                seed_author,
                limit=max(limit * 2, 24),
                subjects=seed_subjects if seed_subjects else None,
            )

            # Série : compléter avec d'autres volumes / œuvres liées au nom
            if (series_name or "").strip() and len(similar_books) < limit:
                try:
                    extra = await self.openlibrary_service.search_series(
                        seed_title, limit=max(8, limit // 2)
                    )
                    for book in extra or []:
                        similar_books.append(book)
                except Exception as exc:
                    logger.debug("similar series fallback: %s", exc)

            short = seed_title if len(seed_title) <= 42 else seed_title[:39] + "…"
            kind = "série" if (series_name or "").strip() else "livre"
            reason = f"Similaire à {kind} « {short} »"

            out: List[RecommendationItem] = []
            seen = set()
            seed_norm = self._normalize_title(seed_title)

            for book in similar_books:
                title_b = (book.get("title") or "").strip()
                author_b = (book.get("author") or "").strip()
                if not title_b:
                    continue
                if self._normalize_title(title_b) == seed_norm:
                    continue
                key = self._book_key(title_b, author_b)
                if key in seen:
                    continue
                seen.add(key)
                if await self._should_skip(
                    user_profile, book.get("ol_key", ""), title_b, author_b
                ):
                    continue

                out.append(
                    RecommendationItem(
                        book_id=book.get("ol_key", "") or key,
                        title=title_b,
                        author=author_b,
                        category=book.get("category", "roman"),
                        cover_url=book.get("cover_url"),
                        confidence_score=0.8,
                        reasons=[reason],
                        source="seed_similarity",
                        metadata={
                            **book,
                            "seed_title": seed_title,
                            "seed_author": seed_author,
                            "seed_kind": kind,
                        },
                    )
                )
                if len(out) >= limit:
                    break

            return {
                "recommendations": [self._format_recommendation(r) for r in out],
                "seed": {
                    "title": seed_title,
                    "author": seed_author,
                    "series_name": (series_name or "").strip() or None,
                    "kind": kind,
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
                title = book.get('title') or ''
                norm_title = self._normalize_title(title)
                if norm_title:
                    owned_titles.add(norm_title)
                    owned_keys.add(self._book_key(title, author))

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
                'author_affinity': author_affinity_norm,
                'category_affinity': category_affinity_norm,
                'disliked_book_ids': list(disliked_book_ids),
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la bibliothèque: {str(e)}")
            return {'has_books': False, 'error': str(e)}

    def _normalize_title(self, title: str) -> str:
        """Normalise un titre pour la comparaison (casse, ponctuation, espaces).

        Conserve les numéros de tome afin de ne pas confondre deux tomes
        différents d'une même série.
        """
        if not title:
            return ''
        t = title.lower().strip()
        t = re.sub(r'[^a-z0-9àâäéèêëïîôöùûüç ]', ' ', t)
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
        """Livres similaires aux titres bien notés (≥ 4) de l'utilisateur via Open Library."""
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

                similar_books = await self.openlibrary_service.search_similar_books(
                    seed_title,
                    seed_author,
                    limit=per_seed,
                    subjects=seed_subjects if isinstance(seed_subjects, list) else None,
                )

                short_title = seed_title if len(seed_title) <= 42 else seed_title[:39] + '…'
                if seed_rating:
                    reason = f"Parce que tu as aimé « {short_title} » ({seed_rating}/5)"
                else:
                    reason = f"Parce que tu as aimé « {short_title} »"

                base_confidence = 0.72 + 0.04 * min(5, float(seed_rating or 4))
                out: List[RecommendationItem] = []

                for book in similar_books:
                    title = book.get('title', '')
                    author = book.get('author', '')
                    if await self._should_skip(
                        user_profile, book.get('ol_key', ''), title, author
                    ):
                        continue
                    if seed_author and self._normalize_author(author) == self._normalize_author(seed_author):
                        continue

                    out.append(RecommendationItem(
                        book_id=book.get('ol_key', ''),
                        title=title,
                        author=author,
                        category=book.get('category', 'roman'),
                        cover_url=book.get('cover_url'),
                        confidence_score=min(0.95, base_confidence),
                        reasons=[reason],
                        source='algorithm_similarity',
                        metadata={
                            **book,
                            'seed_title': seed_title,
                            'seed_rating': seed_rating,
                        },
                    ))
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
        """Formate une recommandation pour l'API"""
        return {
            'book_id': rec.book_id,
            'title': rec.title,
            'author': rec.author,
            'category': rec.category,
            'cover_url': rec.cover_url,
            'confidence_score': round(rec.confidence_score, 2),
            'reasons': rec.reasons,
            'source': rec.source,
            'metadata': self._json_safe(rec.metadata or {}),
        }
    
    async def _should_skip(self, user_profile: Dict, book_id: str, title: str, author: str) -> bool:
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
        norm_title = self._normalize_title(title)

        if norm_title and norm_title in owned_titles:
            return True
        if self._book_key(title, author) in owned_keys:
            return True

        # 3. Repli pour les profils factices (by-author / by-category)
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