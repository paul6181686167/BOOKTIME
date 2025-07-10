"""
PHASE 3.4 - Service de Recommandations Avancées
Intelligence Artificielle et Machine Learning pour recommandations sophistiquées
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging
from dataclasses import dataclass, field
import math
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import re

from ..database.connection import client
from ..openlibrary.service import OpenLibraryService
from .service import RecommendationService, RecommendationItem

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AdvancedUserProfile:
    """Profil utilisateur enrichi pour IA"""
    user_id: str
    reading_velocity: float  # Livres par mois
    genre_preferences: Dict[str, float]  # Scores par genre
    mood_patterns: Dict[str, List[str]]  # Genres par humeur/contexte
    temporal_patterns: Dict[str, float]  # Patterns temporels (matin/soir/weekend)
    completion_patterns: Dict[str, float]  # Patterns de completion par type
    rating_bias: float  # Tendance notation (sévère/généreux)
    exploration_vs_exploitation: float  # Goût pour nouveauté vs sûr
    social_influence_factor: float  # Sensibilité aux recommendations sociales
    learning_trajectory: List[Dict]  # Évolution des goûts dans le temps
    behavioral_clusters: List[str]  # Clusters comportementaux
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ContextualRecommendation:
    """Recommandation contextuelle enrichie"""
    base_recommendation: RecommendationItem
    context_score: float
    context_reasons: List[str]
    mood_match: Optional[str]
    time_appropriateness: float
    social_proof: Dict[str, any]
    learning_potential: float
    novelty_score: float
    confidence_interval: Tuple[float, float]

class AdvancedRecommendationService:
    """Service de recommandations avec IA avancée"""
    
    def __init__(self):
        self.db = client.booktime
        self.basic_service = RecommendationService()
        self.openlibrary_service = OpenLibraryService()
        
        # Configuration IA
        self.min_books_for_ml = 5  # Minimum livres pour ML
        self.max_clusters = 10
        self.context_weight = 0.3
        self.social_weight = 0.2
        self.novelty_weight = 0.15
        
        # Cache pour les modèles ML
        self._user_profiles_cache = {}
        self._similarity_matrix_cache = {}
        self._genre_embeddings_cache = {}
        
    # === ANALYSE COMPORTEMENTALE AVANCÉE ===
    
    async def analyze_advanced_user_profile(self, user_id: str) -> AdvancedUserProfile:
        """Analyse comportementale avancée du profil utilisateur"""
        try:
            logger.info(f"Analyse avancée du profil utilisateur {user_id}")
            
            # Vérifier le cache
            if user_id in self._user_profiles_cache:
                cached_profile = self._user_profiles_cache[user_id]
                if (datetime.utcnow() - cached_profile.created_at).total_seconds() < 3600:  # Cache 1h
                    return cached_profile
            
            # Récupérer les données utilisateur
            books = list(self.db.books.find({"user_id": user_id}).sort("date_added", 1))
            social_activities = list(self.db.social_activities.find({"user_id": user_id}).sort("created_at", 1))
            social_follows = list(self.db.follows.find({"follower_id": user_id}))
            
            if len(books) < 3:
                # Profil par défaut pour nouveaux utilisateurs
                return AdvancedUserProfile(
                    user_id=user_id,
                    reading_velocity=2.0,
                    genre_preferences={},
                    mood_patterns={},
                    temporal_patterns={},
                    completion_patterns={},
                    rating_bias=0.0,
                    exploration_vs_exploitation=0.5,
                    social_influence_factor=0.5,
                    learning_trajectory=[],
                    behavioral_clusters=["novice"]
                )
            
            # 1. Analyser la vélocité de lecture
            reading_velocity = await self._calculate_reading_velocity(books)
            
            # 2. Analyser les préférences de genres
            genre_preferences = await self._analyze_genre_preferences(books)
            
            # 3. Analyser les patterns d'humeur
            mood_patterns = await self._analyze_mood_patterns(books, social_activities)
            
            # 4. Analyser les patterns temporels
            temporal_patterns = await self._analyze_temporal_patterns(books, social_activities)
            
            # 5. Analyser les patterns de completion
            completion_patterns = await self._analyze_completion_patterns(books)
            
            # 6. Analyser le biais de notation
            rating_bias = await self._calculate_rating_bias(books)
            
            # 7. Analyser exploration vs exploitation
            exploration_vs_exploitation = await self._analyze_exploration_tendency(books)
            
            # 8. Analyser l'influence sociale
            social_influence_factor = await self._analyze_social_influence(user_id, social_follows)
            
            # 9. Analyser la trajectoire d'apprentissage
            learning_trajectory = await self._analyze_learning_trajectory(books)
            
            # 10. Déterminer les clusters comportementaux
            behavioral_clusters = await self._determine_behavioral_clusters(books, social_activities)
            
            # Créer le profil avancé
            advanced_profile = AdvancedUserProfile(
                user_id=user_id,
                reading_velocity=reading_velocity,
                genre_preferences=genre_preferences,
                mood_patterns=mood_patterns,
                temporal_patterns=temporal_patterns,
                completion_patterns=completion_patterns,
                rating_bias=rating_bias,
                exploration_vs_exploitation=exploration_vs_exploitation,
                social_influence_factor=social_influence_factor,
                learning_trajectory=learning_trajectory,
                behavioral_clusters=behavioral_clusters
            )
            
            # Mettre en cache
            self._user_profiles_cache[user_id] = advanced_profile
            
            return advanced_profile
            
        except Exception as e:
            logger.error(f"Erreur analyse profil avancé: {str(e)}")
            raise Exception(f"Erreur analyse profil avancé: {str(e)}")
    
    async def _calculate_reading_velocity(self, books: List[Dict]) -> float:
        """Calcule la vélocité de lecture (livres/mois)"""
        try:
            completed_books = [b for b in books if b.get('status') == 'completed' and b.get('date_completed')]
            
            if len(completed_books) < 2:
                return 2.0  # Valeur par défaut
            
            # Calculer sur les 6 derniers mois
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            recent_books = [b for b in completed_books 
                          if b.get('date_completed') and b['date_completed'] >= six_months_ago]
            
            if not recent_books:
                return 1.0
            
            # Calculer la vitesse moyenne
            months_span = max(1, len(set(b['date_completed'].month for b in recent_books)))
            velocity = len(recent_books) / months_span
            
            return round(velocity, 2)
            
        except Exception as e:
            logger.warning(f"Erreur calcul vélocité: {str(e)}")
            return 2.0
    
    async def _analyze_genre_preferences(self, books: List[Dict]) -> Dict[str, float]:
        """Analyse les préférences de genres avec scoring ML"""
        try:
            genre_scores = defaultdict(list)
            
            for book in books:
                genre = book.get('genre', book.get('category', 'unknown'))
                rating = book.get('rating', 0)
                status = book.get('status', '')
                
                # Score basé sur rating et completion
                base_score = rating / 5.0 if rating > 0 else 0.5
                
                # Bonus pour completion
                if status == 'completed':
                    base_score += 0.2
                elif status == 'reading':
                    base_score += 0.1
                
                genre_scores[genre].append(base_score)
            
            # Calculer scores moyens avec pondération
            genre_preferences = {}
            for genre, scores in genre_scores.items():
                if scores:
                    # Score moyen pondéré par le nombre d'occurrences
                    avg_score = sum(scores) / len(scores)
                    frequency_weight = min(1.0, len(scores) / 5.0)  # Max weight à 5 livres
                    genre_preferences[genre] = round(avg_score * frequency_weight, 3)
            
            return genre_preferences
            
        except Exception as e:
            logger.warning(f"Erreur analyse genres: {str(e)}")
            return {}
    
    async def _analyze_mood_patterns(self, books: List[Dict], activities: List[Dict]) -> Dict[str, List[str]]:
        """Analyse les patterns d'humeur basés sur les choix de lecture"""
        try:
            mood_patterns = {
                "stress_relief": [],
                "learning": [],
                "entertainment": [],
                "exploration": [],
                "comfort": []
            }
            
            # Analyser les patterns basés sur les métadonnées
            for book in books:
                genre = book.get('genre', book.get('category', ''))
                rating = book.get('rating', 0)
                pages = book.get('total_pages', 0)
                
                # Catégoriser selon les caractéristiques
                if rating >= 4:
                    if pages < 200:
                        mood_patterns["stress_relief"].append(genre)
                    elif 'science' in genre.lower() or 'history' in genre.lower():
                        mood_patterns["learning"].append(genre)
                    else:
                        mood_patterns["entertainment"].append(genre)
                
                # Pattern exploration basé sur nouveauté
                if book.get('auto_added', False):
                    mood_patterns["exploration"].append(genre)
                
                # Pattern comfort basé sur re-lecture d'auteurs
                if len([b for b in books if b.get('author') == book.get('author')]) > 1:
                    mood_patterns["comfort"].append(genre)
            
            # Nettoyer et déduire les patterns dominants
            for mood, genres in mood_patterns.items():
                genre_counts = Counter(genres)
                mood_patterns[mood] = [genre for genre, count in genre_counts.most_common(3)]
            
            return mood_patterns
            
        except Exception as e:
            logger.warning(f"Erreur analyse mood: {str(e)}")
            return {}
    
    async def _analyze_temporal_patterns(self, books: List[Dict], activities: List[Dict]) -> Dict[str, float]:
        """Analyse les patterns temporels de lecture"""
        try:
            temporal_data = {
                "morning_reader": 0.0,
                "evening_reader": 0.0,
                "weekend_reader": 0.0,
                "binge_reader": 0.0,
                "consistent_reader": 0.0
            }
            
            # Analyser les timestamps des activités
            activity_hours = []
            activity_days = []
            
            for activity in activities:
                if activity.get('created_at'):
                    dt = activity['created_at']
                    activity_hours.append(dt.hour)
                    activity_days.append(dt.weekday())
            
            if activity_hours:
                # Pattern matin/soir
                morning_count = len([h for h in activity_hours if 6 <= h <= 12])
                evening_count = len([h for h in activity_hours if 18 <= h <= 23])
                total_activities = len(activity_hours)
                
                temporal_data["morning_reader"] = morning_count / total_activities if total_activities > 0 else 0
                temporal_data["evening_reader"] = evening_count / total_activities if total_activities > 0 else 0
                
                # Pattern weekend
                weekend_count = len([d for d in activity_days if d >= 5])
                temporal_data["weekend_reader"] = weekend_count / len(activity_days) if activity_days else 0
            
            # Analyser la régularité de lecture
            completion_dates = [b.get('date_completed') for b in books 
                             if b.get('status') == 'completed' and b.get('date_completed')]
            
            if len(completion_dates) > 3:
                # Calculer la variance entre les dates
                intervals = []
                sorted_dates = sorted(completion_dates)
                for i in range(1, len(sorted_dates)):
                    interval = (sorted_dates[i] - sorted_dates[i-1]).days
                    intervals.append(interval)
                
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
                    
                    # Pattern binge vs consistent
                    if variance > avg_interval * 2:
                        temporal_data["binge_reader"] = 0.8
                        temporal_data["consistent_reader"] = 0.2
                    else:
                        temporal_data["binge_reader"] = 0.2
                        temporal_data["consistent_reader"] = 0.8
            
            return temporal_data
            
        except Exception as e:
            logger.warning(f"Erreur analyse temporelle: {str(e)}")
            return {}
    
    async def _analyze_completion_patterns(self, books: List[Dict]) -> Dict[str, float]:
        """Analyse les patterns de completion par type de livre"""
        try:
            completion_data = defaultdict(list)
            
            for book in books:
                category = book.get('category', 'unknown')
                pages = book.get('total_pages', 0)
                status = book.get('status', '')
                
                # Score de completion
                if status == 'completed':
                    completion_score = 1.0
                elif status == 'reading':
                    current_page = book.get('current_page', 0)
                    completion_score = (current_page / pages) if pages > 0 else 0.5
                else:
                    completion_score = 0.0
                
                completion_data[category].append(completion_score)
                
                # Analyser par longueur
                if pages > 0:
                    if pages < 200:
                        completion_data['short_books'].append(completion_score)
                    elif pages > 500:
                        completion_data['long_books'].append(completion_score)
                    else:
                        completion_data['medium_books'].append(completion_score)
            
            # Calculer moyennes
            completion_patterns = {}
            for pattern_type, scores in completion_data.items():
                if scores:
                    completion_patterns[pattern_type] = round(sum(scores) / len(scores), 3)
            
            return completion_patterns
            
        except Exception as e:
            logger.warning(f"Erreur analyse completion: {str(e)}")
            return {}
    
    async def _calculate_rating_bias(self, books: List[Dict]) -> float:
        """Calcule le biais de notation de l'utilisateur"""
        try:
            ratings = [book.get('rating', 0) for book in books if book.get('rating', 0) > 0]
            
            if len(ratings) < 3:
                return 0.0  # Pas de biais détectable
            
            avg_rating = sum(ratings) / len(ratings)
            global_avg = 3.5  # Moyenne globale assumée
            
            # Biais = écart à la moyenne globale
            bias = avg_rating - global_avg
            
            return round(bias, 3)
            
        except Exception as e:
            logger.warning(f"Erreur calcul biais: {str(e)}")
            return 0.0
    
    async def _analyze_exploration_tendency(self, books: List[Dict]) -> float:
        """Analyse la tendance exploration vs exploitation"""
        try:
            total_books = len(books)
            if total_books < 5:
                return 0.5  # Neutre
            
            # Compter les explorations
            unique_authors = len(set(book.get('author', '') for book in books))
            unique_genres = len(set(book.get('genre', book.get('category', '')) for book in books))
            auto_added_count = len([b for b in books if b.get('auto_added', False)])
            
            # Score d'exploration basé sur diversité
            author_diversity = unique_authors / total_books
            genre_diversity = unique_genres / total_books
            exploration_ratio = auto_added_count / total_books
            
            exploration_score = (author_diversity + genre_diversity + exploration_ratio) / 3
            
            return round(min(1.0, exploration_score), 3)
            
        except Exception as e:
            logger.warning(f"Erreur analyse exploration: {str(e)}")
            return 0.5
    
    async def _analyze_social_influence(self, user_id: str, follows: List[Dict]) -> float:
        """Analyse la sensibilité à l'influence sociale"""
        try:
            # Facteurs d'influence sociale
            follow_count = len(follows)
            
            # Analyser les livres ajoutés après des activités sociales
            user_books = list(self.db.books.find({"user_id": user_id}).sort("date_added", 1))
            social_influenced_books = 0
            
            for book in user_books:
                book_date = book.get('date_added', datetime.utcnow())
                
                # Chercher des activités sociales similaires dans les 7 jours précédents
                week_before = book_date - timedelta(days=7)
                similar_activities = list(self.db.social_activities.find({
                    "user_id": {"$in": [f['following_id'] for f in follows]},
                    "created_at": {"$gte": week_before, "$lte": book_date},
                    "activity_type": "book_completed",
                    "content.title": {"$regex": book.get('title', ''), "$options": "i"}
                }))
                
                if similar_activities:
                    social_influenced_books += 1
            
            # Score d'influence sociale
            base_social_score = min(1.0, follow_count / 20.0)  # Normaliser sur 20 follows
            influence_score = social_influenced_books / len(user_books) if user_books else 0
            
            social_influence_factor = (base_social_score + influence_score) / 2
            
            return round(social_influence_factor, 3)
            
        except Exception as e:
            logger.warning(f"Erreur analyse sociale: {str(e)}")
            return 0.5
    
    async def _analyze_learning_trajectory(self, books: List[Dict]) -> List[Dict]:
        """Analyse l'évolution des goûts dans le temps"""
        try:
            trajectory = []
            
            # Grouper les livres par trimestre
            quarterly_data = defaultdict(list)
            
            for book in books:
                date_added = book.get('date_added', datetime.utcnow())
                quarter_key = f"{date_added.year}-Q{(date_added.month-1)//3 + 1}"
                quarterly_data[quarter_key].append(book)
            
            # Analyser l'évolution par trimestre
            for quarter, quarter_books in sorted(quarterly_data.items()):
                if len(quarter_books) >= 2:  # Minimum pour analyse
                    genres = [b.get('genre', b.get('category', '')) for b in quarter_books]
                    avg_rating = sum(b.get('rating', 0) for b in quarter_books) / len(quarter_books)
                    avg_pages = sum(b.get('total_pages', 0) for b in quarter_books) / len(quarter_books)
                    
                    trajectory.append({
                        'period': quarter,
                        'book_count': len(quarter_books),
                        'dominant_genres': Counter(genres).most_common(3),
                        'avg_rating': round(avg_rating, 2),
                        'avg_pages': round(avg_pages),
                        'exploration_level': len(set(genres)) / len(quarter_books)
                    })
            
            return trajectory[-8:]  # Garder 2 dernières années max
            
        except Exception as e:
            logger.warning(f"Erreur analyse trajectoire: {str(e)}")
            return []
    
    async def _determine_behavioral_clusters(self, books: List[Dict], activities: List[Dict]) -> List[str]:
        """Détermine les clusters comportementaux avec ML"""
        try:
            clusters = []
            
            # Analyser les patterns comportementaux
            total_books = len(books)
            completed_rate = len([b for b in books if b.get('status') == 'completed']) / total_books if total_books > 0 else 0
            avg_rating = sum(b.get('rating', 0) for b in books) / total_books if total_books > 0 else 0
            activity_frequency = len(activities) / max(1, total_books)
            
            # Déterminer les clusters basés sur seuils
            if completed_rate > 0.8:
                clusters.append("completionist")
            elif completed_rate < 0.3:
                clusters.append("sampler")
            
            if avg_rating > 4.0:
                clusters.append("enthusiast")
            elif avg_rating < 3.0:
                clusters.append("critic")
            
            if activity_frequency > 2.0:
                clusters.append("social_reader")
            elif activity_frequency < 0.5:
                clusters.append("private_reader")
            
            if total_books > 50:
                clusters.append("power_reader")
            elif total_books < 10:
                clusters.append("casual_reader")
            
            # Clusters par défaut
            if not clusters:
                clusters = ["balanced_reader"]
            
            return clusters
            
        except Exception as e:
            logger.warning(f"Erreur clustering: {str(e)}")
            return ["unknown"]
    
    # === RECOMMANDATIONS CONTEXTUELLES ===
    
    async def get_contextual_recommendations(self, user_id: str, context: Dict, limit: int = 10) -> List[ContextualRecommendation]:
        """Génère des recommandations contextuelles intelligentes"""
        try:
            logger.info(f"Génération recommandations contextuelles pour {user_id}")
            
            # 1. Analyser le profil utilisateur avancé
            user_profile = await self.analyze_advanced_user_profile(user_id)
            
            # 2. Générer des recommandations de base
            basic_recommendations = await self.basic_service.get_personalized_recommendations(user_id, limit * 2)
            
            if not basic_recommendations.get('recommendations'):
                return []
            
            # 3. Enrichir avec le contexte
            contextual_recs = []
            
            for base_rec in basic_recommendations['recommendations']:
                # Créer l'objet RecommendationItem
                rec_item = RecommendationItem(
                    book_id=base_rec['book_id'],
                    title=base_rec['title'],
                    author=base_rec['author'],
                    category=base_rec['category'],
                    cover_url=base_rec.get('cover_url'),
                    confidence_score=base_rec['confidence_score'],
                    reasons=base_rec['reasons'],
                    source=base_rec['source'],
                    metadata=base_rec.get('metadata', {})
                )
                
                # Analyser le contexte
                context_analysis = await self._analyze_context_fit(rec_item, user_profile, context)
                
                contextual_rec = ContextualRecommendation(
                    base_recommendation=rec_item,
                    context_score=context_analysis['context_score'],
                    context_reasons=context_analysis['context_reasons'],
                    mood_match=context_analysis.get('mood_match'),
                    time_appropriateness=context_analysis['time_appropriateness'],
                    social_proof=context_analysis.get('social_proof', {}),
                    learning_potential=context_analysis['learning_potential'],
                    novelty_score=context_analysis['novelty_score'],
                    confidence_interval=context_analysis['confidence_interval']
                )
                
                contextual_recs.append(contextual_rec)
            
            # 4. Trier par score contextuel global
            contextual_recs.sort(key=lambda x: self._calculate_global_score(x), reverse=True)
            
            return contextual_recs[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recommandations contextuelles: {str(e)}")
            raise Exception(f"Erreur recommandations contextuelles: {str(e)}")
    
    async def _analyze_context_fit(self, recommendation: RecommendationItem, 
                                 user_profile: AdvancedUserProfile, context: Dict) -> Dict:
        """Analyse l'adéquation contextuelle d'une recommandation"""
        try:
            analysis = {
                'context_score': 0.5,
                'context_reasons': [],
                'time_appropriateness': 0.5,
                'learning_potential': 0.5,
                'novelty_score': 0.5,
                'confidence_interval': (0.3, 0.7)
            }
            
            # Analyser le contexte temporel
            current_time = context.get('time_of_day', 'unknown')
            if current_time in user_profile.temporal_patterns:
                time_score = user_profile.temporal_patterns[current_time]
                analysis['time_appropriateness'] = time_score
                if time_score > 0.6:
                    analysis['context_reasons'].append(f"Adapté à vos habitudes de lecture {current_time}")
            
            # Analyser l'humeur
            user_mood = context.get('mood', 'neutral')
            if user_mood in user_profile.mood_patterns:
                mood_genres = user_profile.mood_patterns[user_mood]
                if recommendation.category in mood_genres:
                    analysis['context_score'] += 0.2
                    analysis['context_reasons'].append(f"Parfait pour votre humeur {user_mood}")
                    analysis['mood_match'] = user_mood
            
            # Analyser le potentiel d'apprentissage
            user_genres = set(user_profile.genre_preferences.keys())
            if recommendation.metadata.get('genre') not in user_genres:
                analysis['learning_potential'] = 0.8
                analysis['context_reasons'].append("Nouveau genre à explorer")
            
            # Analyser la nouveauté
            user_authors = [item['book']['author'] for item in user_profile.learning_trajectory 
                          if 'book' in item]
            if recommendation.author not in user_authors:
                analysis['novelty_score'] = 0.7
                analysis['context_reasons'].append("Nouvel auteur à découvrir")
            
            # Calculer l'intervalle de confiance
            base_confidence = recommendation.confidence_score
            context_uncertainty = 0.1 * (1 - analysis['context_score'])
            
            analysis['confidence_interval'] = (
                max(0.0, base_confidence - context_uncertainty),
                min(1.0, base_confidence + context_uncertainty)
            )
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Erreur analyse contexte: {str(e)}")
            return {
                'context_score': 0.5,
                'context_reasons': [],
                'time_appropriateness': 0.5,
                'learning_potential': 0.5,
                'novelty_score': 0.5,
                'confidence_interval': (0.3, 0.7)
            }
    
    def _calculate_global_score(self, contextual_rec: ContextualRecommendation) -> float:
        """Calcule le score global d'une recommandation contextuelle"""
        base_score = contextual_rec.base_recommendation.confidence_score
        context_score = contextual_rec.context_score
        novelty_score = contextual_rec.novelty_score
        learning_score = contextual_rec.learning_potential
        
        # Pondération intelligente
        global_score = (
            base_score * 0.4 +
            context_score * self.context_weight +
            novelty_score * self.novelty_weight +
            learning_score * 0.15
        )
        
        return round(global_score, 3)
    
    # === RECOMMANDATIONS SOCIALES INTELLIGENTES ===
    
    async def get_social_recommendations(self, user_id: str, limit: int = 10) -> List[ContextualRecommendation]:
        """Génère des recommandations basées sur l'intelligence sociale"""
        try:
            logger.info(f"Génération recommandations sociales pour {user_id}")
            
            # 1. Récupérer le réseau social
            follows = list(self.db.follows.find({"follower_id": user_id}))
            following_ids = [f['following_id'] for f in follows]
            
            if not following_ids:
                return []  # Pas de réseau social
            
            # 2. Analyser les activités du réseau
            recent_activities = list(self.db.social_activities.find({
                "user_id": {"$in": following_ids},
                "activity_type": {"$in": ["book_completed", "book_rated"]},
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }).sort("created_at", -1).limit(50))
            
            # 3. Extraire les livres populaires dans le réseau
            social_books = defaultdict(list)
            
            for activity in recent_activities:
                if activity.get('content', {}).get('book_id'):
                    book_info = activity['content']
                    social_books[book_info['book_id']].append({
                        'user_id': activity['user_id'],
                        'rating': book_info.get('rating', 0),
                        'activity_type': activity['activity_type'],
                        'timestamp': activity['created_at']
                    })
            
            # 4. Scorer et filtrer
            social_recommendations = []
            
            for book_id, social_data in social_books.items():
                if len(social_data) >= 2:  # Au moins 2 personnes du réseau
                    # Vérifier que l'utilisateur n'a pas déjà ce livre
                    existing_book = self.db.books.find_one({
                        "user_id": user_id,
                        "$or": [
                            {"id": book_id},
                            {"title": social_data[0].get('title', '')}
                        ]
                    })
                    
                    if not existing_book:
                        # Créer la recommandation sociale
                        social_rec = await self._create_social_recommendation(book_id, social_data, user_id)
                        if social_rec:
                            social_recommendations.append(social_rec)
            
            # 5. Trier par score social
            social_recommendations.sort(key=lambda x: x.social_proof.get('social_score', 0), reverse=True)
            
            return social_recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Erreur recommandations sociales: {str(e)}")
            return []
    
    async def _create_social_recommendation(self, book_id: str, social_data: List[Dict], user_id: str) -> Optional[ContextualRecommendation]:
        """Crée une recommandation basée sur les données sociales"""
        try:
            # Calculer le score social
            ratings = [d['rating'] for d in social_data if d.get('rating', 0) > 0]
            avg_rating = sum(ratings) / len(ratings) if ratings else 3.5
            social_popularity = len(social_data)
            
            # Score social basé sur popularité et qualité
            social_score = min(1.0, (social_popularity / 5.0) * (avg_rating / 5.0))
            
            # Récupérer les infos du livre
            first_mention = social_data[0]
            book_title = first_mention.get('title', 'Livre recommandé')
            book_author = first_mention.get('author', 'Auteur inconnu')
            
            # Créer la recommandation de base
            base_rec = RecommendationItem(
                book_id=book_id,
                title=book_title,
                author=book_author,
                category=first_mention.get('category', 'roman'),
                cover_url=first_mention.get('cover_url'),
                confidence_score=0.6 + (social_score * 0.3),
                reasons=[f"Apprécié par {social_popularity} personnes que vous suivez"],
                source='social_network',
                metadata=first_mention
            )
            
            # Données de preuve sociale
            social_proof = {
                'social_score': social_score,
                'recommendation_count': social_popularity,
                'average_rating': avg_rating,
                'recent_activity': len([d for d in social_data 
                                     if (datetime.utcnow() - d['timestamp']).days <= 7]),
                'recommenders': [d['user_id'] for d in social_data[:3]]  # Top 3
            }
            
            # Créer la recommandation contextuelle
            contextual_rec = ContextualRecommendation(
                base_recommendation=base_rec,
                context_score=social_score,
                context_reasons=[f"Populaire dans votre réseau ({social_popularity} recommandations)"],
                mood_match=None,
                time_appropriateness=0.7,  # Les recommandations sociales sont généralement appropriées
                social_proof=social_proof,
                learning_potential=0.6,
                novelty_score=0.8,  # Recommandations sociales souvent nouvelles
                confidence_interval=(0.5, 0.9)
            )
            
            return contextual_rec
            
        except Exception as e:
            logger.warning(f"Erreur création recommandation sociale: {str(e)}")
            return None


# Instance globale du service avancé
advanced_recommendation_service = AdvancedRecommendationService()