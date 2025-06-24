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

  // Récupérer les statistiques
  async getStats() {
    try {
      const response = await api.get('/api/stats');
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des statistiques');
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

  // Récupérer les auteurs
  async getAuthors() {
    try {
      const response = await api.get('/api/authors');
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des auteurs');
    }
  },

  // Récupérer les livres d'un auteur
  async getBooksByAuthor(authorName) {
    try {
      const response = await api.get(`/api/authors/${encodeURIComponent(authorName)}/books`);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des livres de l\'auteur');
    }
  },

  // Récupérer les sagas
  async getSagas() {
    try {
      const response = await api.get('/api/sagas');
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des sagas');
    }
  },

  // Récupérer les livres d'une saga
  async getBooksBySaga(sagaName) {
    try {
      const response = await api.get(`/api/sagas/${encodeURIComponent(sagaName)}/books`);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de la récupération des livres de la saga');
    }
  },

  // Ajouter automatiquement le prochain tome d'une saga
  async autoAddNextVolume(sagaName) {
    try {
      const response = await api.post(`/api/sagas/${encodeURIComponent(sagaName)}/auto-add`);
      return response.data;
    } catch (error) {
      throw new Error('Erreur lors de l\'ajout automatique du prochain tome');
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

  // === OPEN LIBRARY INTEGRATION ===
  
  // Rechercher des livres sur Open Library
  async searchOpenLibrary(query, limit = 10) {
    try {
      const response = await api.get('/api/openlibrary/search', {
        params: { q: query, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la recherche Open Library:', error);
      throw new Error('Erreur lors de la recherche sur Open Library');
    }
  },

  // Importer un livre depuis Open Library
  async importFromOpenLibrary(olKey, category = 'roman') {
    try {
      const response = await api.post('/api/openlibrary/import', {
        ol_key: olKey,
        category: category
      });
      return response.data;
    } catch (error) {
      if (error.response?.status === 409) {
        throw new Error('Ce livre existe déjà dans votre collection');
      }
      console.error('Erreur lors de l\'import Open Library:', error);
      throw new Error('Erreur lors de l\'import du livre');
    }
  },

  // Enrichir un livre existant avec les données Open Library
  async enrichBook(bookId) {
    try {
      const response = await api.post(`/api/books/${bookId}/enrich`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        throw new Error('Aucune correspondance trouvée sur Open Library');
      }
      console.error('Erreur lors de l\'enrichissement:', error);
      throw new Error('Erreur lors de l\'enrichissement du livre');
    }
  },

  // === OPEN LIBRARY INTEGRATION ===
  
  // Rechercher des livres sur Open Library
  async searchOpenLibrary(query, limit = 10) {
    try {
      const response = await api.get('/api/openlibrary/search', {
        params: { q: query, limit }
      });
      return response.data;
    } catch (error) {
      console.error('Erreur lors de la recherche Open Library:', error);
      throw new Error('Erreur lors de la recherche sur Open Library');
    }
  },

  // Importer un livre depuis Open Library
  async importFromOpenLibrary(olKey, category = 'roman') {
    try {
      const response = await api.post('/api/openlibrary/import', {
        ol_key: olKey,
        category: category
      });
      return response.data;
    } catch (error) {
      if (error.response?.status === 409) {
        throw new Error('Ce livre existe déjà dans votre collection');
      }
      console.error('Erreur lors de l\'import Open Library:', error);
      throw new Error('Erreur lors de l\'import du livre');
    }
  },

  // Enrichir un livre existant avec les données Open Library
  async enrichBook(bookId) {
    try {
      const response = await api.post(`/api/books/${bookId}/enrich`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 404) {
        throw new Error('Aucune correspondance trouvée sur Open Library');
      }
      console.error('Erreur lors de l\'enrichissement:', error);
      throw new Error('Erreur lors de l\'enrichissement du livre');
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