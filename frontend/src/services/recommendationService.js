/**
 * PHASE 3.1 - Service de Recommandations Frontend
 * Client pour l'API de recommandations personnalisées
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Configuration axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
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
      // Token expiré ou invalide
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.reload();
    }
    console.error('Recommendation API Error:', error);
    return Promise.reject(error);
  }
);

export const recommendationService = {
  /**
   * Récupère les recommandations personnalisées
   * @param {Object} options - Options de recherche
   * @param {number} options.limit - Nombre de recommandations
   * @param {string} options.category - Catégorie à filtrer
   * @param {boolean} options.refresh - Forcer la régénération
   * @returns {Promise<Object>} Recommandations personnalisées
   */
  async getPersonalized(options = {}) {
    try {
      const { limit = 10, category = null, refresh = false } = options;
      
      const params = { limit, refresh };
      if (category) params.category = category;
      
      const response = await api.get('/api/recommendations/personalized', { params });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations personnalisées:', error);
      throw new Error('Erreur lors de la récupération des recommandations personnalisées');
    }
  },

  /**
   * Récupère les recommandations populaires
   * @param {Object} options - Options de recherche
   * @param {number} options.limit - Nombre de recommandations
   * @param {string} options.category - Catégorie à filtrer
   * @returns {Promise<Object>} Recommandations populaires
   */
  async getPopular(options = {}) {
    try {
      const { limit = 10, category = null } = options;
      
      const params = { limit };
      if (category) params.category = category;
      
      const response = await api.get('/api/recommendations/popular', { params });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations populaires:', error);
      throw new Error('Erreur lors de la récupération des recommandations populaires');
    }
  },

  /**
   * Récupère les recommandations par auteur
   * @param {string} authorName - Nom de l'auteur
   * @param {number} limit - Nombre de recommandations
   * @returns {Promise<Object>} Recommandations par auteur
   */
  async getByAuthor(authorName, limit = 10) {
    try {
      const response = await api.get(`/api/recommendations/by-author/${encodeURIComponent(authorName)}`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations par auteur:', error);
      throw new Error('Erreur lors de la récupération des recommandations par auteur');
    }
  },

  /**
   * Récupère les recommandations par catégorie
   * @param {string} category - Catégorie (roman, bd, manga)
   * @param {number} limit - Nombre de recommandations
   * @returns {Promise<Object>} Recommandations par catégorie
   */
  async getByCategory(category, limit = 10) {
    try {
      const response = await api.get(`/api/recommendations/by-category/${category}`, {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations par catégorie:', error);
      throw new Error('Erreur lors de la récupération des recommandations par catégorie');
    }
  },

  /**
   * Récupère le profil utilisateur pour les recommandations
   * @returns {Promise<Object>} Profil utilisateur
   */
  async getUserProfile() {
    try {
      const response = await api.get('/api/recommendations/user-profile');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération du profil utilisateur:', error);
      throw new Error('Erreur lors de la récupération du profil utilisateur');
    }
  },

  /**
   * Envoie un feedback sur une recommandation
   * @param {string} recommendationId - ID de la recommandation
   * @param {string} feedback - Type de feedback (like, dislike, added_to_library, not_interested)
   * @returns {Promise<Object>} Confirmation du feedback
   */
  async submitFeedback(recommendationId, feedback) {
    try {
      const response = await api.post('/api/recommendations/feedback', {
        recommendation_id: recommendationId,
        feedback: feedback
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'envoi du feedback:', error);
      throw new Error('Erreur lors de l\'envoi du feedback');
    }
  },

  /**
   * Récupère les statistiques des recommandations
   * @returns {Promise<Object>} Statistiques des recommandations
   */
  async getStats() {
    try {
      const response = await api.get('/api/recommendations/stats');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des statistiques:', error);
      throw new Error('Erreur lors de la récupération des statistiques');
    }
  },

  /**
   * Ajoute un livre recommandé à la bibliothèque
   * @param {Object} bookData - Données du livre
   * @returns {Promise<Object>} Livre ajouté
   */
  async addRecommendedBook(bookData) {
    try {
      // Préparer les données pour l'API books
      const formattedBookData = {
        title: bookData.title,
        author: bookData.author,
        category: bookData.category,
        cover_url: bookData.cover_url,
        ol_key: bookData.book_id,
        status: 'to_read',
        source: 'recommendation',
        metadata: bookData.metadata || {}
      };

      const response = await api.post('/api/books', formattedBookData);
      
      // Envoyer un feedback automatique
      if (bookData.book_id) {
        await this.submitFeedback(bookData.book_id, 'added_to_library');
      }
      
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre recommandé:', error);
      throw new Error('Erreur lors de l\'ajout du livre recommandé');
    }
  },

  /**
   * Marque une recommandation comme "pas intéressé"
   * @param {string} recommendationId - ID de la recommandation
   * @returns {Promise<Object>} Confirmation
   */
  async markAsNotInterested(recommendationId) {
    try {
      return await this.submitFeedback(recommendationId, 'not_interested');
    } catch (error) {
      console.error('Erreur lors du marquage "pas intéressé":', error);
      throw new Error('Erreur lors du marquage "pas intéressé"');
    }
  },

  /**
   * Aime une recommandation
   * @param {string} recommendationId - ID de la recommandation
   * @returns {Promise<Object>} Confirmation
   */
  async likeRecommendation(recommendationId) {
    try {
      return await this.submitFeedback(recommendationId, 'like');
    } catch (error) {
      console.error('Erreur lors du like:', error);
      throw new Error('Erreur lors du like');
    }
  },

  /**
   * N'aime pas une recommandation
   * @param {string} recommendationId - ID de la recommandation
   * @returns {Promise<Object>} Confirmation
   */
  async dislikeRecommendation(recommendationId) {
    try {
      return await this.submitFeedback(recommendationId, 'dislike');
    } catch (error) {
      console.error('Erreur lors du dislike:', error);
      throw new Error('Erreur lors du dislike');
    }
  }
};

export default recommendationService;