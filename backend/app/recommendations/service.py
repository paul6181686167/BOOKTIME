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
                'user_profile': user_profile,
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
            
            # Analyser les auteurs préférés
            author_counts = Counter()
            category_counts = Counter()
            high_rated_books = []
            completed_books = []
            
            for book in books:
                # Compter les auteurs
                author = book.get('author', '').strip()
                if author:
                    author_counts[author] += 1
                
                # Compter les catégories
                category = book.get('category', '').strip()
                if category:
                    category_counts[category] += 1
                
                # Livres bien notés (rating >= 4)
                rating = book.get('rating', 0)
                if rating >= 4:
                    high_rated_books.append(book)
                
                # Livres terminés
                if book.get('status') == 'completed':
                    completed_books.append(book)
            
            # Extraire les favoris
            favorite_authors = [author for author, count in author_counts.most_common(5)]
            favorite_categories = [cat for cat, count in category_counts.most_common(3)]
            
            # Analyser les patterns de lecture
            reading_patterns = {
                'completion_rate': len(completed_books) / len(books) if books else 0,
                'average_rating': sum(book.get('rating', 0) for book in books) / len(books) if books else 0,
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
                'high_rated_books': high_rated_books[:10],  # Top 10 livres bien notés
                'completed_books': completed_books[:10],     # Top 10 livres terminés
                'author_counts': dict(author_counts.most_common(10)),
                'category_counts': dict(category_counts.most_common(5))
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la bibliothèque: {str(e)}")
            return {'has_books': False, 'error': str(e)}
    
    async def _generate_algorithm_recommendations(self, user_profile: Dict, limit: int) -> List[RecommendationItem]:
        """Génère des recommandations basées sur l'algorithme"""
        recommendations = []
        
        try:
            # 1. Recommandations basées sur les auteurs favoris
            author_recommendations = await self._recommend_by_authors(user_profile, limit // 3)
            recommendations.extend(author_recommendations)
            
            # 2. Recommandations basées sur les catégories favorites
            category_recommendations = await self._recommend_by_categories(user_profile, limit // 3)
            recommendations.extend(category_recommendations)
            
            # 3. Recommandations basées sur les séries
            series_recommendations = await self._recommend_by_series(user_profile, limit // 3)
            recommendations.extend(series_recommendations)
            
            # 4. Recommandations basées sur la similarité
            similarity_recommendations = await self._recommend_by_similarity(user_profile, limit // 4)
            recommendations.extend(similarity_recommendations)
            
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
                    # Vérifier si l'utilisateur n'a pas déjà ce livre
                    if not await self._user_has_book(user_profile, book.get('title', ''), author):
                        rec = RecommendationItem(
                            book_id=book.get('ol_key', ''),
                            title=book.get('title', ''),
                            author=author,
                            category=book.get('category', 'roman'),
                            cover_url=book.get('cover_url'),
                            confidence_score=0.8,  # Haute confiance pour auteurs favoris
                            reasons=[f"Vous avez apprécié d'autres livres de {author}"],
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
                    # Vérifier si l'utilisateur n'a pas déjà ce livre
                    if not await self._user_has_book(user_profile, book.get('title', ''), book.get('author', '')):
                        rec = RecommendationItem(
                            book_id=book.get('ol_key', ''),
                            title=book.get('title', ''),
                            author=book.get('author', ''),
                            category=category,
                            cover_url=book.get('cover_url'),
                            confidence_score=0.6,  # Confiance moyenne pour catégories
                            reasons=[f"Vous lisez beaucoup de {category}"],
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
                        # Vérifier si l'utilisateur n'a pas déjà ce livre
                        if not await self._user_has_book(user_profile, book.get('title', ''), book.get('author', '')):
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
        """Recommandations basées sur la similarité avec d'autres utilisateurs"""
        recommendations = []
        
        try:
            # Trouver des utilisateurs similaires
            similar_users = await self._find_similar_users(user_profile)
            
            for similar_user in similar_users[:3]:  # Top 3 utilisateurs similaires
                # Récupérer leurs livres bien notés
                similar_books = list(self.db.books.find({
                    "user_id": similar_user['user_id'],
                    "rating": {"$gte": 4}
                }))
                
                for book in similar_books:
                    # Vérifier si l'utilisateur n'a pas déjà ce livre
                    if not await self._user_has_book(user_profile, book.get('title', ''), book.get('author', '')):
                        rec = RecommendationItem(
                            book_id=book.get('_id', ''),
                            title=book.get('title', ''),
                            author=book.get('author', ''),
                            category=book.get('category', 'roman'),
                            cover_url=book.get('cover_url'),
                            confidence_score=0.5,  # Confiance moyenne pour similarité
                            reasons=[f"Apprécié par des lecteurs similaires"],
                            source='algorithm_similarity',
                            metadata=book
                        )
                        recommendations.append(rec)
                        
                        if len(recommendations) >= limit:
                            break
                
                if len(recommendations) >= limit:
                    break
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recommandations similarité: {str(e)}")
            return []
    
    async def _enrich_with_openlibrary(self, recommendations: List[RecommendationItem], user_profile: Dict) -> List[RecommendationItem]:
        """Enrichit les recommandations avec des données Open Library"""
        enriched = []
        
        for rec in recommendations:
            try:
                # Enrichir avec des métadonnées supplémentaires
                if rec.source.startswith('algorithm'):
                    # Rechercher des informations complémentaires
                    enhanced_info = await self.openlibrary_service.get_book_details(rec.book_id)
                    
                    if enhanced_info:
                        # Mettre à jour les métadonnées
                        rec.metadata.update(enhanced_info)
                        
                        # Ajuster le score de confiance
                        if 'description' in enhanced_info:
                            rec.confidence_score += 0.1
                        
                        if 'publication_year' in enhanced_info:
                            # Bonus pour les livres récents
                            year = enhanced_info.get('publication_year', 0)
                            if year > 2020:
                                rec.confidence_score += 0.05
                
                enriched.append(rec)
                
            except Exception as e:
                logger.warning(f"Erreur enrichissement {rec.title}: {str(e)}")
                enriched.append(rec)  # Garder même sans enrichissement
        
        return enriched
    
    async def _score_and_rank(self, recommendations: List[RecommendationItem], user_profile: Dict) -> List[RecommendationItem]:
        """Score et classe les recommandations"""
        scored = []
        
        for rec in recommendations:
            try:
                # Score de base
                base_score = rec.confidence_score
                
                # Bonus pour les auteurs très appréciés
                if rec.author in user_profile.get('favorite_authors', []):
                    base_score += 0.2
                
                # Bonus pour les catégories préférées
                if rec.category in user_profile.get('favorite_categories', []):
                    base_score += 0.15
                
                # Bonus pour les séries
                if rec.source == 'algorithm_series':
                    base_score += 0.1
                
                # Penalty pour les scores trop bas
                if base_score < self.min_confidence_score:
                    continue
                
                # Limiter le score max
                rec.confidence_score = min(base_score, 1.0)
                scored.append(rec)
                
            except Exception as e:
                logger.warning(f"Erreur scoring {rec.title}: {str(e)}")
        
        # Trier par score décroissant
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
            'metadata': rec.metadata
        }
    
    async def _user_has_book(self, user_profile: Dict, title: str, author: str) -> bool:
        """Vérifie si l'utilisateur a déjà ce livre"""
        # Recherche simple par titre et auteur
        # TODO: Améliorer avec recherche fuzzy
        for book in user_profile.get('high_rated_books', []) + user_profile.get('completed_books', []):
            if (book.get('title', '').lower().strip() == title.lower().strip() and
                book.get('author', '').lower().strip() == author.lower().strip()):
                return True
        return False
    
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