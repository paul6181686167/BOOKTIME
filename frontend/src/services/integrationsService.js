/**
 * PHASE 3.5 - Service d'Intégrations Externes Frontend
 * Client pour l'API d'intégrations tierces
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Configuration axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Timeout élevé pour uploads
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
    console.error('Integrations API Error:', error);
    return Promise.reject(error);
  }
);

export const integrationsService = {
  // === GOODREADS INTEGRATION ===

  /**
   * Importe un fichier CSV d'export Goodreads
   * @param {File} file - Fichier CSV Goodreads
   * @returns {Promise<Object>} Résultat d'import
   */
  async importGoodreadsCSV(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/integrations/goodreads/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data;
    } catch (error) {
      console.error('Erreur lors de l\'import Goodreads:', error);
      throw new Error('Erreur lors de l\'import Goodreads');
    }
  },

  // === GOOGLE BOOKS INTEGRATION ===

  /**
   * Recherche des livres sur Google Books
   * @param {string} query - Terme de recherche
   * @param {number} maxResults - Nombre maximum de résultats
   * @returns {Promise<Object>} Résultats de recherche
   */
  async searchGoogleBooks(query, maxResults = 20) {
    try {
      const response = await api.get('/api/integrations/google-books/search', {
        params: {
          query: query,
          max_results: maxResults
        }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la recherche Google Books:', error);
      throw new Error('Erreur lors de la recherche Google Books');
    }
  },

  /**
   * Récupère les détails d'un livre Google Books
   * @param {string} volumeId - ID du volume Google Books
   * @returns {Promise<Object>} Détails du livre
   */
  async getGoogleBookDetails(volumeId) {
    try {
      const response = await api.get(`/api/integrations/google-books/details/${volumeId}`);
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des détails Google Books:', error);
      throw new Error('Erreur lors de la récupération des détails Google Books');
    }
  },

  // === LIBRARYTHING INTEGRATION ===

  /**
   * Récupère les recommandations LibraryThing pour un livre
   * @param {string} isbn - ISBN du livre
   * @returns {Promise<Object>} Recommandations
   */
  async getLibraryThingRecommendations(isbn) {
    try {
      const response = await api.get('/api/integrations/librarything/recommendations', {
        params: { isbn: isbn }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des recommandations LibraryThing:', error);
      throw new Error('Erreur lors de la récupération des recommandations LibraryThing');
    }
  },

  /**
   * Récupère les tags LibraryThing pour un livre
   * @param {string} isbn - ISBN du livre
   * @returns {Promise<Object>} Tags
   */
  async getLibraryThingTags(isbn) {
    try {
      const response = await api.get('/api/integrations/librarything/tags', {
        params: { isbn: isbn }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des tags LibraryThing:', error);
      throw new Error('Erreur lors de la récupération des tags LibraryThing');
    }
  },

  // === RECHERCHE COMBINÉE ===

  /**
   * Effectue une recherche combinée sur plusieurs sources
   * @param {string} query - Terme de recherche
   * @param {Array} sources - Sources à utiliser
   * @param {number} maxResultsPerSource - Résultats max par source
   * @returns {Promise<Object>} Résultats combinés
   */
  async combinedSearch(query, sources = ['google_books'], maxResultsPerSource = 10) {
    try {
      const response = await api.get('/api/integrations/combined-search', {
        params: {
          query: query,
          sources: sources.join(','),
          max_results_per_source: maxResultsPerSource
        }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la recherche combinée:', error);
      throw new Error('Erreur lors de la recherche combinée');
    }
  },

  // === STATISTIQUES ===

  /**
   * Récupère les statistiques des intégrations
   * @returns {Promise<Object>} Statistiques
   */
  async getIntegrationsStats() {
    try {
      const response = await api.get('/api/integrations/stats');
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la récupération des statistiques:', error);
      throw new Error('Erreur lors de la récupération des statistiques');
    }
  },

  // === UTILITAIRES ===

  /**
   * Valide un fichier CSV Goodreads
   * @param {File} file - Fichier à valider
   * @returns {boolean} True si valide
   */
  validateGoodreadsCSV(file) {
    if (!file) return false;
    if (!file.name.toLowerCase().endsWith('.csv')) return false;
    if (file.size > 50 * 1024 * 1024) return false; // Max 50MB
    return true;
  },

  /**
   * Parse le nom d'un fichier pour extraire des informations
   * @param {string} filename - Nom du fichier
   * @returns {Object} Informations extraites
   */
  parseFilename(filename) {
    const info = {
      source: 'unknown',
      date: null,
      type: 'unknown'
    };

    if (filename.toLowerCase().includes('goodreads')) {
      info.source = 'goodreads';
    }

    if (filename.toLowerCase().includes('export')) {
      info.type = 'export';
    }

    // Extraire date si possible (format YYYY-MM-DD)
    const dateMatch = filename.match(/(\d{4}-\d{2}-\d{2})/);
    if (dateMatch) {
      info.date = dateMatch[1];
    }

    return info;
  },

  /**
   * Formate les statistiques d'import pour affichage
   * @param {Object} stats - Statistiques brutes
   * @returns {Object} Statistiques formatées
   */
  formatImportStats(stats) {
    return {
      totalBooks: stats.total_books || 0,
      convertedBooks: stats.converted_books || 0,
      conversionRate: stats.total_books > 0 ? 
        Math.round((stats.converted_books / stats.total_books) * 100) : 0,
      categories: stats.categories || {},
      statuses: stats.statuses || {},
      hasErrors: (stats.total_books || 0) > (stats.converted_books || 0)
    };
  },

  /**
   * Génère une clé de cache pour les recherches
   * @param {string} query - Requête de recherche
   * @param {Array} sources - Sources utilisées
   * @returns {string} Clé de cache
   */
  generateCacheKey(query, sources = []) {
    const normalizedQuery = query.toLowerCase().trim().replace(/\s+/g, '-');
    const sourcesStr = sources.sort().join('-');
    return `search-${normalizedQuery}-${sourcesStr}`;
  }
};

export default integrationsService;