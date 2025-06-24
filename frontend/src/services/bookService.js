import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Configuration axios
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour gérer les erreurs
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const bookService = {
  // Récupérer tous les livres
  async getBooks(category = null, status = null) {
    try {
      const params = {};
      if (category) params.category = category;
      if (status) params.status = status;
      
      const response = await api.get('/api/books', { params });
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des livres');
    }
  },

  // Récupérer un livre par ID
  async getBook(bookId) {
    try {
      const response = await api.get(`/api/books/${bookId}`);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération du livre');
    }
  },

  // Créer un nouveau livre
  async createBook(bookData) {
    try {
      const response = await api.post('/api/books', bookData);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la création du livre');
    }
  },

  // Mettre à jour un livre
  async updateBook(bookId, updates) {
    try {
      const response = await api.put(`/api/books/${bookId}`, updates);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la mise à jour du livre');
    }
  },

  // Supprimer un livre
  async deleteBook(bookId) {
    try {
      const response = await api.delete(`/api/books/${bookId}`);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la suppression du livre');
    }
  },

  // Récupérer les statistiques
  async getStats() {
    try {
      const response = await api.get('/api/stats');
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des statistiques');
    }
  },

  // Utilitaires pour les images
  async uploadImage(file) {
    try {
      const formData = new FormData();
      formData.append('image', file);
      
      const response = await api.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      return response.data.url;
    } catch (error) {
      throw new Error('Erreur lors de l\'upload de l\'image');
    }
  },

  // Rechercher des livres (API externe optionnelle)
  async searchBooks(query) {
    try {
      // Ici, vous pourriez intégrer une API comme Google Books
      // Pour l'instant, on retourne un tableau vide
      return [];
    } catch (error) {
      console.error('Erreur lors de la recherche de livres:', error);
      return [];
    }
  }
};

export default bookService;