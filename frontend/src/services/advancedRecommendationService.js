/**
 * PHASE 3.4 - Service de Recommandations Avancées Frontend
 * Client pour l'API de recommandations IA et ML
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Configuration axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Plus de timeout pour IA
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    console.error('Advanced Recommendation API Error:', error);
    return Promise.reject(error);
  }
);

export const advancedRecommendationService = {
  /**
   * Récupère les recommandations contextuelles avec IA
   * @param {Object} context - Contexte utilisateur
   * @param {number} limit - Nombre de recommandations
   * @returns {Promise<Object>} Recommandations contextuelles
   */
  async getContextualRecommendations(context = {}, limit = 10) {
    try {
      const defaultContext = {
        time_of_day: this._getTimeOfDay(),
        mood: 'neutral',
        available_time: 60,
        location: 'home',
        purpose: 'leisure'
      };

      const fullContext = { ...defaultContext, ...context };

      const response = await api.post('/api/recommendations/advanced/contextual', {
        context: fullContext,
        limit: limit
      });
      
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations contextuelles:', error);
      throw new Error('Erreur lors de la récupération des recommandations contextuelles');
    }
  },

  /**
   * Récupère les recommandations sociales intelligentes
   * @param {number} limit - Nombre de recommandations
   * @returns {Promise<Object>} Recommandations sociales
   */
  async getSocialRecommendations(limit = 10) {
    try {
      const response = await api.get('/api/recommendations/advanced/social', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations sociales:', error);
      throw new Error('Erreur lors de la récupération des recommandations sociales');
    }
  },

  /**
   * Récupère le profil utilisateur avancé avec IA
   * @returns {Promise<Object>} Profil utilisateur enrichi
   */
  async getAdvancedUserProfile() {
    try {
      const response = await api.get('/api/recommendations/advanced/user-profile/advanced');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération du profil avancé:', error);
      throw new Error('Erreur lors de la récupération du profil avancé');
    }
  },

  /**
   * Prédit le rating qu'un utilisateur donnerait à un livre
   * @param {string} bookId - ID du livre
   * @returns {Promise<Object>} Prédiction de rating
   */
  async predictRating(bookId) {
    try {
      const response = await api.get('/api/recommendations/advanced/ml/predict-rating', {
        params: { book_id: bookId }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la prédiction de rating:', error);
      throw new Error('Erreur lors de la prédiction de rating');
    }
  },

  /**
   * Entraîne les modèles ML
   * @param {string} modelType - Type de modèle à entraîner
   * @returns {Promise<Object>} Résultat d'entraînement
   */
  async trainModel(modelType) {
    try {
      const response = await api.post('/api/recommendations/advanced/ml/train', {
        model_type: modelType
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'entraînement du modèle:', error);
      throw new Error('Erreur lors de l\'entraînement du modèle');
    }
  },

  /**
   * Envoie un feedback avancé sur une recommandation
   * @param {string} recommendationId - ID de la recommandation
   * @param {string} feedbackType - Type de feedback
   * @param {Object} context - Contexte additionnel
   * @returns {Promise<Object>} Confirmation
   */
  async submitAdvancedFeedback(recommendationId, feedbackType, context = {}) {
    try {
      const response = await api.post('/api/recommendations/advanced/feedback', {
        recommendation_id: recommendationId,
        feedback_type: feedbackType,
        context: context,
        rating: context.rating || null
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'envoi du feedback avancé:', error);
      throw new Error('Erreur lors de l\'envoi du feedback avancé');
    }
  },

  /**
   * Récupère les statistiques ML
   * @returns {Promise<Object>} Statistiques des modèles
   */
  async getMLStats() {
    try {
      const response = await api.get('/api/recommendations/advanced/stats/ml');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des stats ML:', error);
      throw new Error('Erreur lors de la récupération des stats ML');
    }
  },

  /**
   * Détermine automatiquement l'heure de la journée
   * @returns {string} Moment de la journée
   */
  _getTimeOfDay() {
    const hour = new Date().getHours();
    
    if (hour >= 6 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 17) return 'afternoon';
    if (hour >= 17 && hour < 22) return 'evening';
    return 'night';
  },

  /**
   * Analyse le comportement utilisateur pour le contexte
   * @returns {Object} Contexte intelligent
   */
  getSmartContext() {
    const timeOfDay = this._getTimeOfDay();
    const isWeekend = new Date().getDay() >= 5;
    
    // Logique basée sur l'heure et le jour
    let suggestedMood = 'neutral';
    let suggestedPurpose = 'leisure';
    let availableTime = 60;

    if (timeOfDay === 'morning') {
      suggestedMood = 'energetic';
      suggestedPurpose = 'learning';
      availableTime = 30;
    } else if (timeOfDay === 'evening') {
      suggestedMood = 'relaxed';
      suggestedPurpose = 'entertainment';
      availableTime = 90;
    } else if (isWeekend) {
      availableTime = 120;
      suggestedPurpose = 'exploration';
    }

    return {
      time_of_day: timeOfDay,
      mood: suggestedMood,
      purpose: suggestedPurpose,
      available_time: availableTime,
      is_weekend: isWeekend,
      location: 'home'
    };
  }
};

export default advancedRecommendationService;