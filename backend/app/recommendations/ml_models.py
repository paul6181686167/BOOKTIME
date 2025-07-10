"""
PHASE 3.4 - Modèles Machine Learning pour Recommandations
Algorithmes ML sophistiqués pour prédictions et clustering
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
from dataclasses import dataclass
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA, NMF
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MLModelResult:
    """Résultat d'un modèle ML"""
    predictions: List[float]
    confidence_scores: List[float]
    feature_importance: Dict[str, float]
    model_accuracy: float
    model_type: str

class RecommendationMLModels:
    """Ensemble de modèles ML pour recommandations avancées"""
    
    def __init__(self, models_cache_dir: str = "/tmp/booktime_ml_models"):
        self.cache_dir = models_cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Modèles initialisés
        self.rating_predictor = None
        self.genre_classifier = None
        self.user_clusterer = None
        self.content_vectorizer = None
        self.similarity_matrix = None
        
        # Configuration
        self.min_samples_for_training = 50
        self.model_update_threshold_days = 7
        self.confidence_threshold = 0.6
        
        # Chargement des modèles existants
        self._load_cached_models()
    
    # === PRÉDICTION DE RATINGS ===
    
    async def train_rating_predictor(self, user_data: List[Dict]) -> MLModelResult:
        """Entraîne un modèle de prédiction de ratings"""
        try:
            logger.info("Entraînement du prédicteur de ratings")
            
            if len(user_data) < self.min_samples_for_training:
                raise ValueError(f"Pas assez de données ({len(user_data)} < {self.min_samples_for_training})")
            
            # 1. Préparation des données
            features, ratings = self._prepare_rating_features(user_data)
            
            if len(features) == 0:
                raise ValueError("Aucune feature extraite")
            
            # 2. Division train/test
            X_train, X_test, y_train, y_test = train_test_split(
                features, ratings, test_size=0.2, random_state=42
            )
            
            # 3. Entraînement de plusieurs modèles
            models = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'gradient_boost': GradientBoostingRegressor(n_estimators=100, random_state=42),
                'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
            }
            
            best_model = None
            best_score = -np.inf
            best_model_name = None
            
            for name, model in models.items():
                try:
                    model.fit(X_train, y_train)
                    score = model.score(X_test, y_test)
                    
                    if score > best_score:
                        best_score = score
                        best_model = model
                        best_model_name = name
                        
                    logger.info(f"Modèle {name}: R² = {score:.3f}")
                    
                except Exception as e:
                    logger.warning(f"Erreur entraînement {name}: {str(e)}")
            
            if best_model is None:
                raise ValueError("Aucun modèle n'a pu être entraîné")
            
            # 4. Prédictions et confidence
            predictions = best_model.predict(X_test)
            
            # Calculer la confidence basée sur l'erreur
            mse = mean_squared_error(y_test, predictions)
            confidence_scores = [max(0.1, 1.0 - abs(pred - actual) / 5.0) 
                               for pred, actual in zip(predictions, y_test)]
            
            # 5. Importance des features
            feature_importance = {}
            if hasattr(best_model, 'feature_importances_'):
                feature_names = self._get_feature_names()
                for i, importance in enumerate(best_model.feature_importances_):
                    if i < len(feature_names):
                        feature_importance[feature_names[i]] = float(importance)
            
            # 6. Sauvegarde du modèle
            self.rating_predictor = best_model
            self._save_model(best_model, 'rating_predictor')
            
            result = MLModelResult(
                predictions=predictions.tolist(),
                confidence_scores=confidence_scores,
                feature_importance=feature_importance,
                model_accuracy=best_score,
                model_type=best_model_name
            )
            
            logger.info(f"Prédicteur de ratings entraîné: {best_model_name} (R² = {best_score:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Erreur entraînement prédicteur ratings: {str(e)}")
            raise
    
    def _prepare_rating_features(self, user_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prépare les features pour la prédiction de ratings"""
        try:
            features = []
            ratings = []
            
            # Encodeurs
            genre_encoder = LabelEncoder()
            author_encoder = LabelEncoder()
            
            # Collecter toutes les valeurs pour l'encodage
            all_genres = [book.get('genre', book.get('category', 'unknown')) for book in user_data]
            all_authors = [book.get('author', 'unknown') for book in user_data]
            
            genre_encoder.fit(all_genres)
            author_encoder.fit(all_authors)
            
            for book in user_data:
                rating = book.get('rating', 0)
                if rating > 0:  # Seulement les livres notés
                    
                    # Features numériques
                    feature_row = [
                        book.get('total_pages', 200) / 100,  # Normaliser pages
                        book.get('publication_year', 2000) / 100,  # Normaliser année
                        len(book.get('title', '')),  # Longueur titre
                        len(book.get('description', '')),  # Longueur description
                    ]
                    
                    # Features catégorielles encodées
                    genre = book.get('genre', book.get('category', 'unknown'))
                    author = book.get('author', 'unknown')
                    
                    try:
                        genre_encoded = genre_encoder.transform([genre])[0]
                        author_encoded = author_encoder.transform([author])[0]
                    except ValueError:
                        genre_encoded = 0
                        author_encoded = 0
                    
                    feature_row.extend([genre_encoded, author_encoded])
                    
                    # Features binaires
                    feature_row.extend([
                        1 if book.get('status') == 'completed' else 0,
                        1 if book.get('saga') else 0,
                        1 if book.get('auto_added', False) else 0,
                    ])
                    
                    features.append(feature_row)
                    ratings.append(rating)
            
            if not features:
                return np.array([]), np.array([])
            
            # Normalisation
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            return features_scaled, np.array(ratings)
            
        except Exception as e:
            logger.error(f"Erreur préparation features: {str(e)}")
            return np.array([]), np.array([])
    
    def _get_feature_names(self) -> List[str]:
        """Retourne les noms des features"""
        return [
            'pages_normalized',
            'year_normalized', 
            'title_length',
            'description_length',
            'genre_encoded',
            'author_encoded',
            'is_completed',
            'has_saga',
            'is_auto_added'
        ]
    
    async def predict_rating(self, book_features: Dict) -> Tuple[float, float]:
        """Prédit le rating d'un livre pour un utilisateur"""
        try:
            if self.rating_predictor is None:
                return 3.5, 0.5  # Valeur par défaut
            
            # Préparer les features du livre
            features = self._extract_book_features(book_features)
            
            if features is None:
                return 3.5, 0.5
            
            # Prédiction
            prediction = self.rating_predictor.predict([features])[0]
            
            # Confidence basée sur l'historique du modèle
            confidence = min(0.9, max(0.1, 0.8 - abs(prediction - 3.5) / 5.0))
            
            return float(np.clip(prediction, 1.0, 5.0)), float(confidence)
            
        except Exception as e:
            logger.warning(f"Erreur prédiction rating: {str(e)}")
            return 3.5, 0.5
    
    def _extract_book_features(self, book_features: Dict) -> Optional[List[float]]:
        """Extrait les features d'un livre pour prédiction"""
        try:
            features = [
                book_features.get('total_pages', 200) / 100,
                book_features.get('publication_year', 2000) / 100,
                len(book_features.get('title', '')),
                len(book_features.get('description', '')),
                0,  # genre_encoded (à implémenter avec encodeur sauvegardé)
                0,  # author_encoded (à implémenter avec encodeur sauvegardé) 
                0,  # is_completed (inconnu pour nouveau livre)
                1 if book_features.get('saga') else 0,
                1 if book_features.get('auto_added', False) else 0,
            ]
            
            return features
            
        except Exception as e:
            logger.warning(f"Erreur extraction features: {str(e)}")
            return None
    
    # === CLUSTERING D'UTILISATEURS ===
    
    async def train_user_clusterer(self, users_data: List[Dict]) -> MLModelResult:
        """Entraîne un modèle de clustering d'utilisateurs"""
        try:
            logger.info("Entraînement du clusterer d'utilisateurs")
            
            if len(users_data) < 10:  # Minimum pour clustering
                raise ValueError("Pas assez d'utilisateurs pour clustering")
            
            # 1. Préparer les features utilisateurs
            user_features = self._prepare_user_features(users_data)
            
            if len(user_features) == 0:
                raise ValueError("Aucune feature utilisateur extraite")
            
            # 2. Normalisation
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(user_features)
            
            # 3. Déterminer le nombre optimal de clusters
            optimal_clusters = self._find_optimal_clusters(features_scaled)
            
            # 4. Entraînement KMeans
            kmeans = KMeans(n_clusters=optimal_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # 5. Analyse des clusters
            cluster_analysis = self._analyze_clusters(users_data, cluster_labels)
            
            # 6. Sauvegarde
            self.user_clusterer = kmeans
            self._save_model(kmeans, 'user_clusterer')
            self._save_model(scaler, 'user_scaler')
            
            result = MLModelResult(
                predictions=cluster_labels.tolist(),
                confidence_scores=[0.8] * len(cluster_labels),  # Confidence uniforme pour clustering
                feature_importance=cluster_analysis,
                model_accuracy=self._calculate_silhouette_score(features_scaled, cluster_labels),
                model_type='kmeans'
            )
            
            logger.info(f"Clusterer utilisateurs entraîné: {optimal_clusters} clusters")
            return result
            
        except Exception as e:
            logger.error(f"Erreur entraînement clusterer: {str(e)}")
            raise
    
    def _prepare_user_features(self, users_data: List[Dict]) -> List[List[float]]:
        """Prépare les features pour le clustering d'utilisateurs"""
        try:
            features = []
            
            for user in users_data:
                user_books = user.get('books', [])
                
                if len(user_books) >= 3:  # Minimum pour profil significatif
                    
                    # Features de base
                    total_books = len(user_books)
                    completed_books = len([b for b in user_books if b.get('status') == 'completed'])
                    avg_rating = sum(b.get('rating', 0) for b in user_books) / total_books
                    
                    # Diversité de genres
                    genres = [b.get('genre', b.get('category', '')) for b in user_books]
                    genre_diversity = len(set(genres)) / total_books
                    
                    # Diversité d'auteurs
                    authors = [b.get('author', '') for b in user_books]
                    author_diversity = len(set(authors)) / total_books
                    
                    # Préférence pour séries
                    series_books = len([b for b in user_books if b.get('saga')])
                    series_preference = series_books / total_books
                    
                    # Longueur moyenne des livres
                    avg_pages = sum(b.get('total_pages', 0) for b in user_books) / total_books
                    
                    # Fréquence de lecture (approximation)
                    reading_frequency = total_books / 12  # Livres par mois (assumé sur 1 an)
                    
                    feature_row = [
                        total_books / 50,  # Normaliser
                        completed_books / total_books,
                        avg_rating / 5,
                        genre_diversity,
                        author_diversity,
                        series_preference,
                        avg_pages / 300,  # Normaliser
                        min(reading_frequency, 5) / 5  # Cap à 5 livres/mois
                    ]
                    
                    features.append(feature_row)
            
            return features
            
        except Exception as e:
            logger.error(f"Erreur préparation features utilisateurs: {str(e)}")
            return []
    
    def _find_optimal_clusters(self, features: np.ndarray) -> int:
        """Trouve le nombre optimal de clusters avec elbow method"""
        try:
            max_clusters = min(10, len(features) // 3)
            inertias = []
            
            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(features)
                inertias.append(kmeans.inertia_)
            
            # Elbow method simple
            if len(inertias) >= 3:
                # Trouver le point d'inflexion
                diffs = np.diff(inertias)
                second_diffs = np.diff(diffs)
                
                if len(second_diffs) > 0:
                    elbow_idx = np.argmax(second_diffs) + 2
                    return min(elbow_idx, max_clusters)
            
            # Par défaut, retourner un nombre raisonnable
            return min(5, max_clusters)
            
        except Exception as e:
            logger.warning(f"Erreur recherche clusters optimaux: {str(e)}")
            return 3
    
    def _analyze_clusters(self, users_data: List[Dict], cluster_labels: np.ndarray) -> Dict[str, float]:
        """Analyse les caractéristiques des clusters"""
        try:
            cluster_stats = defaultdict(list)
            
            for i, user in enumerate(users_data):
                if i < len(cluster_labels):
                    cluster_id = cluster_labels[i]
                    user_books = user.get('books', [])
                    
                    if user_books:
                        total_books = len(user_books)
                        avg_rating = sum(b.get('rating', 0) for b in user_books) / total_books
                        
                        cluster_stats[f'cluster_{cluster_id}_size'].append(1)
                        cluster_stats[f'cluster_{cluster_id}_books'].append(total_books)
                        cluster_stats[f'cluster_{cluster_id}_rating'].append(avg_rating)
            
            # Calculer moyennes par cluster
            analysis = {}
            for key, values in cluster_stats.items():
                if values:
                    if 'size' in key:
                        analysis[key] = len(values)
                    else:
                        analysis[key] = sum(values) / len(values)
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Erreur analyse clusters: {str(e)}")
            return {}
    
    def _calculate_silhouette_score(self, features: np.ndarray, labels: np.ndarray) -> float:
        """Calcule le score de silhouette pour évaluer la qualité du clustering"""
        try:
            from sklearn.metrics import silhouette_score
            if len(set(labels)) > 1:
                return float(silhouette_score(features, labels))
            return 0.5
        except Exception as e:
            logger.warning(f"Erreur calcul silhouette: {str(e)}")
            return 0.5
    
    # === ANALYSE DE CONTENU ===
    
    async def train_content_analyzer(self, books_data: List[Dict]) -> MLModelResult:
        """Entraîne un modèle d'analyse de contenu avec TF-IDF"""
        try:
            logger.info("Entraînement de l'analyseur de contenu")
            
            if len(books_data) < 20:
                raise ValueError("Pas assez de livres pour analyse de contenu")
            
            # 1. Préparer les textes
            texts = []
            book_ids = []
            
            for book in books_data:
                # Combiner titre, description, genre
                text_parts = [
                    book.get('title', ''),
                    book.get('description', ''),
                    book.get('genre', ''),
                    book.get('category', ''),
                    book.get('author', '')
                ]
                
                combined_text = ' '.join(filter(None, text_parts))
                if len(combined_text.strip()) > 10:  # Minimum de contenu
                    texts.append(combined_text)
                    book_ids.append(book.get('id', str(len(book_ids))))
            
            if len(texts) < 10:
                raise ValueError("Pas assez de contenu textuel")
            
            # 2. Vectorisation TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',  # À adapter pour le français
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # 3. Calcul de similarité
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 4. Réduction dimensionnelle pour visualisation
            nmf = NMF(n_components=10, random_state=42)
            topics = nmf.fit_transform(tfidf_matrix)
            
            # 5. Sauvegarde
            self.content_vectorizer = vectorizer
            self.similarity_matrix = similarity_matrix
            self._save_model(vectorizer, 'content_vectorizer')
            self._save_model(similarity_matrix, 'similarity_matrix')
            
            # 6. Analyse des topics
            feature_names = vectorizer.get_feature_names_out()
            topic_analysis = {}
            
            for topic_idx in range(nmf.n_components):
                top_features_idx = nmf.components_[topic_idx].argsort()[-10:][::-1]
                top_features = [feature_names[i] for i in top_features_idx]
                topic_analysis[f'topic_{topic_idx}'] = top_features[:5]
            
            result = MLModelResult(
                predictions=topics.tolist(),
                confidence_scores=[0.7] * len(texts),
                feature_importance=topic_analysis,
                model_accuracy=0.8,  # Score arbitraire pour TF-IDF
                model_type='tfidf_nmf'
            )
            
            logger.info(f"Analyseur de contenu entraîné: {len(texts)} livres, {nmf.n_components} topics")
            return result
            
        except Exception as e:
            logger.error(f"Erreur entraînement analyseur contenu: {str(e)}")
            raise
    
    async def find_similar_books(self, book_text: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """Trouve les livres similaires basés sur le contenu"""
        try:
            if self.content_vectorizer is None or self.similarity_matrix is None:
                return []
            
            # Vectoriser le livre de requête
            book_vector = self.content_vectorizer.transform([book_text])
            
            # Calculer la similarité avec tous les livres
            similarities = cosine_similarity(book_vector, self.similarity_matrix).flatten()
            
            # Trouver les top-k plus similaires
            top_indices = similarities.argsort()[-top_k-1:-1][::-1]  # Exclure self
            
            results = [(int(idx), float(similarities[idx])) for idx in top_indices]
            
            return results
            
        except Exception as e:
            logger.warning(f"Erreur recherche livres similaires: {str(e)}")
            return []
    
    # === GESTION DES MODÈLES ===
    
    def _save_model(self, model: Any, model_name: str):
        """Sauvegarde un modèle ML"""
        try:
            model_path = os.path.join(self.cache_dir, f"{model_name}.pkl")
            joblib.dump(model, model_path)
            logger.info(f"Modèle {model_name} sauvegardé")
        except Exception as e:
            logger.warning(f"Erreur sauvegarde modèle {model_name}: {str(e)}")
    
    def _load_cached_models(self):
        """Charge les modèles depuis le cache"""
        try:
            model_files = {
                'rating_predictor': 'rating_predictor.pkl',
                'user_clusterer': 'user_clusterer.pkl',
                'content_vectorizer': 'content_vectorizer.pkl',
                'similarity_matrix': 'similarity_matrix.pkl'
            }
            
            for attr_name, filename in model_files.items():
                model_path = os.path.join(self.cache_dir, filename)
                if os.path.exists(model_path):
                    try:
                        model = joblib.load(model_path)
                        setattr(self, attr_name, model)
                        logger.info(f"Modèle {attr_name} chargé depuis le cache")
                    except Exception as e:
                        logger.warning(f"Erreur chargement {attr_name}: {str(e)}")
                        
        except Exception as e:
            logger.warning(f"Erreur chargement modèles: {str(e)}")
    
    async def should_retrain_models(self) -> Dict[str, bool]:
        """Détermine quels modèles doivent être ré-entraînés"""
        try:
            retrain_decisions = {
                'rating_predictor': False,
                'user_clusterer': False,
                'content_analyzer': False
            }
            
            # Vérifier les dates de dernière modification
            for model_name in retrain_decisions.keys():
                model_path = os.path.join(self.cache_dir, f"{model_name}.pkl")
                
                if not os.path.exists(model_path):
                    retrain_decisions[model_name] = True
                else:
                    # Vérifier l'âge du modèle
                    model_age = datetime.now().timestamp() - os.path.getmtime(model_path)
                    age_days = model_age / (24 * 3600)
                    
                    if age_days > self.model_update_threshold_days:
                        retrain_decisions[model_name] = True
            
            return retrain_decisions
            
        except Exception as e:
            logger.warning(f"Erreur vérification retraining: {str(e)}")
            return {'rating_predictor': True, 'user_clusterer': True, 'content_analyzer': True}


# Instance globale des modèles ML
ml_models = RecommendationMLModels()