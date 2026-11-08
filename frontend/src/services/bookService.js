import axios from 'axios';
import { API_BASE_URL } from '../config/environment';
import {
  saveLibraryCache,
  loadLibraryCache,
} from '../utils/offlineLibraryCache';
import {
  enqueueCreateBook,
  enqueueUpdateBook,
  enqueueDeleteBook,
  shouldEnqueueWrite,
  mergePendingBooks,
} from '../utils/offlineWriteQueue';
import logger from '../utils/logger';
import { getToken, notifyUnauthorized } from './apiClient';

// Configuration axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token d'authentification
api.interceptors.request.use(
  (config) => {
    const token = getToken();
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
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Session expirée : l'application déconnecte l'utilisateur (voir AuthProvider)
      notifyUnauthorized();
    }
    logger.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const bookService = {
  getCachedBooks(filters = {}) {
    return loadLibraryCache(filters)?.books || null;
  },

  // Récupérer tous les livres (incluant les séries)
  async getBooks(category = null, status = null) {
    const filters = { category, status };
    try {
      const params = {};
      if (category) params.category = category;
      if (status) params.status = status;
      
      // Charger tous les livres (limit max backend = 1000)
      params.limit = 1000;
      const response = await api.get('/api/books/all', { params });
      const data = response.data;
      const books = Array.isArray(data) ? data : data?.books || data?.items || [];
      const merged = mergePendingBooks(books);
      // Cache complet sans filtre pour permettre le filtrage offline
      if (!category && !status && Array.isArray(merged) && merged.length > 0) {
        saveLibraryCache(merged, {});
      } else if (Array.isArray(merged) && merged.length > 0) {
        saveLibraryCache(merged, filters);
      }
      if (Array.isArray(data)) return merged;
      if (data && Array.isArray(data.books)) return { ...data, books: merged };
      if (data && Array.isArray(data.items)) return { ...data, items: merged };
      return merged;
    } catch (error) {
      const cached = loadLibraryCache(filters);
      if (cached?.books) {
        logger.warn('Bibliothèque servie depuis le cache offline');
        return cached.books;
      }
      logger.error('Erreur lors de la récupération des livres:', error);
      throw new Error('Erreur lors de la récupération des livres');
    }
  },

  // Récupérer un livre par ID
  async getBookById(id) {
    try {
      const response = await api.get(`/api/books/${id}`);
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la récupération du livre:', error);
      throw new Error('Erreur lors de la récupération du livre');
    }
  },

  // Créer un nouveau livre
  async createBook(bookData) {
    if (shouldEnqueueWrite()) {
      return enqueueCreateBook(bookData);
    }
    try {
      const response = await api.post('/api/books', bookData);
      return response.data;
    } catch (error) {
      if (shouldEnqueueWrite(error)) return enqueueCreateBook(bookData);
      logger.error('Erreur lors de la création du livre:', error);
      throw new Error('Erreur lors de la création du livre');
    }
  },

  // Mettre à jour un livre
  async updateBook(id, updateData) {
    if (shouldEnqueueWrite()) {
      return enqueueUpdateBook(id, updateData);
    }
    try {
      const response = await api.put(`/api/books/${id}`, updateData);
      return response.data;
    } catch (error) {
      if (shouldEnqueueWrite(error)) return enqueueUpdateBook(id, updateData);
      logger.error('Erreur lors de la mise à jour du livre:', error);
      throw new Error('Erreur lors de la mise à jour du livre');
    }
  },

  // Supprimer un livre
  async deleteBook(id) {
    if (shouldEnqueueWrite()) {
      return enqueueDeleteBook(id);
    }
    try {
      const response = await api.delete(`/api/books/${id}`);
      return response.data;
    } catch (error) {
      if (shouldEnqueueWrite(error)) return enqueueDeleteBook(id);
      logger.error('Erreur lors de la suppression du livre:', error);
      throw new Error('Erreur lors de la suppression du livre');
    }
  },

  // Récupérer les statistiques
  async getStats() {
    try {
      const response = await api.get('/api/stats');
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la récupération des statistiques:', error);
      throw new Error('Erreur lors de la récupération des statistiques');
    }
  },

  // Récupérer les auteurs
  async getAuthors() {
    try {
      const response = await api.get('/api/authors');
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la récupération des auteurs:', error);
      throw new Error('Erreur lors de la récupération des auteurs');
    }
  },

  // Récupérer les livres d'un auteur
  async getBooksByAuthor(authorName) {
    try {
      const response = await api.get(`/api/authors/${encodeURIComponent(authorName)}/books`);
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la récupération des livres de l\'auteur:', error);
      throw new Error('Erreur lors de la récupération des livres de l\'auteur');
    }
  },

  // Récupérer les sagas
  async getSagas() {
    try {
      const response = await api.get('/api/sagas');
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la récupération des sagas:', error);
      throw new Error('Erreur lors de la récupération des sagas');
    }
  },

  // Récupérer les livres d'une saga (timeout court : endpoint Mongo local)
  async getBooksBySaga(sagaName) {
    try {
      const response = await api.get(`/api/sagas/${encodeURIComponent(sagaName)}/books`, {
        timeout: 8000,
      });
      return response.data;
    } catch (error) {
      logger.warn('Erreur lors de la récupération des livres de la saga:', error?.message || error);
      throw new Error('Erreur lors de la récupération des livres de la saga');
    }
  },

  // Ajouter automatiquement le prochain tome d'une saga
  async autoAddNextVolume(sagaName) {
    try {
      const response = await api.post(`/api/sagas/${encodeURIComponent(sagaName)}/auto-add`);
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de l\'ajout automatique:', error);
      throw new Error('Erreur lors de l\'ajout automatique du prochain tome');
    }
  },

  // Recherche groupée avec sagas
  async searchBooksGrouped(query, category = null) {
    try {
      const params = { q: query };
      if (category) params.category = category;
      
      const response = await api.get('/api/books/search-grouped', { params });
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la recherche groupée:', error);
      throw new Error('Erreur lors de la recherche groupée');
    }
  },

  // === NOUVELLES MÉTHODES POUR LA GESTION DES SÉRIES ===

  // Mise à jour en lot des statuts d'une série
  async updateSagaBulkStatus(sagaName, updateData) {
    try {
      const response = await api.put(`/api/sagas/${encodeURIComponent(sagaName)}/bulk-status`, updateData);
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la mise à jour en lot:', error);
      throw new Error('Erreur lors de la mise à jour en lot');
    }
  },

  // Toggle Lu/Non Lu pour un tome spécifique
  async toggleTomeStatus(sagaName, volumeNumber, isRead) {
    try {
      const response = await api.post(`/api/sagas/${encodeURIComponent(sagaName)}/toggle-tome-status`, {
        volume_number: volumeNumber,
        is_read: isRead
      });
      return response.data;
    } catch (error) {
      logger.error('Erreur lors du toggle du statut:', error);
      throw new Error('Erreur lors de la mise à jour du statut du tome');
    }
  },

  // Auto-complétion intelligente d'une saga
  async autoCompleteSaga(sagaName, targetVolume, source = 'manual') {
    try {
      const response = await api.post(`/api/sagas/${encodeURIComponent(sagaName)}/auto-complete`, {
        target_volume: targetVolume,
        source: source
      });
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de l\'auto-complétion:', error);
      throw new Error('Erreur lors de l\'auto-complétion de la saga');
    }
  },

  // Analyse des tomes manquants
  async analyzeMissingVolumes(sagaName) {
    try {
      const response = await api.get(`/api/sagas/${encodeURIComponent(sagaName)}/missing-analysis`);
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de l\'analyse des tomes manquants:', error);
      throw new Error('Erreur lors de l\'analyse des tomes manquants');
    }
  },

  // Rechercher des séries
  async searchSeries(query) {
    try {
      const response = await api.get('/api/series/search', { params: { q: query } });
      return response.data;
    } catch (error) {
      logger.error('Erreur lors de la recherche de séries:', error);
      throw new Error('Erreur lors de la recherche de séries');
    }
  }
};

export default bookService;
