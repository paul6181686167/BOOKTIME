// Phase 2.2 - Service de pagination pour BOOKTIME
import { bookService } from './bookService';

class PaginationService {
  constructor() {
    this.baseUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  }

  // Récupérer les headers avec authentification
  getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  // Récupérer les livres avec pagination
  async getPaginatedBooks(params = {}) {
    const {
      limit = 20,
      offset = 0,
      category,
      status,
      author,
      saga,
      sort_by = 'date_added',
      sort_order = 'desc',
      exclude_series = false
    } = params;

    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', offset.toString());
    queryParams.append('sort_by', sort_by);
    queryParams.append('sort_order', sort_order);
    
    if (category) queryParams.append('category', category);
    if (status) queryParams.append('status', status);
    if (author) queryParams.append('author', author);
    if (saga) queryParams.append('saga', saga);
    if (exclude_series) queryParams.append('exclude_series', 'true');

    const response = await fetch(`${this.baseUrl}/api/books?${queryParams.toString()}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Récupérer TOUS les livres avec pagination (incluant séries)
  async getAllPaginatedBooks(params = {}) {
    const {
      limit = 20,
      offset = 0,
      category,
      status,
      author,
      saga,
      sort_by = 'date_added',
      sort_order = 'desc'
    } = params;

    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', offset.toString());
    queryParams.append('sort_by', sort_by);
    queryParams.append('sort_order', sort_order);
    
    if (category) queryParams.append('category', category);
    if (status) queryParams.append('status', status);
    if (author) queryParams.append('author', author);
    if (saga) queryParams.append('saga', saga);

    const response = await fetch(`${this.baseUrl}/api/books/all?${queryParams.toString()}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Récupérer les séries avec pagination
  async getPaginatedSeries(params = {}) {
    const {
      limit = 20,
      offset = 0,
      category,
      status,
      sort_by = 'date_added',
      sort_order = 'desc'
    } = params;

    const queryParams = new URLSearchParams();
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', offset.toString());
    queryParams.append('sort_by', sort_by);
    queryParams.append('sort_order', sort_order);
    
    if (category) queryParams.append('category', category);
    if (status) queryParams.append('status', status);

    const response = await fetch(`${this.baseUrl}/api/series/paginated?${queryParams.toString()}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Recherche paginée dans Open Library
  async searchOpenLibraryPaginated(params = {}) {
    const {
      query,
      limit = 20,
      offset = 0,
      category,
      year_start,
      year_end,
      language,
      author_filter
    } = params;

    const queryParams = new URLSearchParams();
    queryParams.append('q', query);
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', offset.toString());
    
    if (category) queryParams.append('category', category);
    if (year_start) queryParams.append('year_start', year_start);
    if (year_end) queryParams.append('year_end', year_end);
    if (language) queryParams.append('language', language);
    if (author_filter) queryParams.append('author_filter', author_filter);

    const response = await fetch(`${this.baseUrl}/api/openlibrary/search?${queryParams.toString()}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Recherche groupée paginée
  async searchGroupedPaginated(params = {}) {
    const {
      query,
      limit = 20,
      offset = 0,
      category
    } = params;

    const queryParams = new URLSearchParams();
    queryParams.append('q', query);
    queryParams.append('limit', limit.toString());
    queryParams.append('offset', offset.toString());
    
    if (category) queryParams.append('category', category);

    const response = await fetch(`${this.baseUrl}/api/books/search-grouped?${queryParams.toString()}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Récupérer les suggestions de recherche
  async getSearchSuggestions(query, limit = 5) {
    const queryParams = new URLSearchParams();
    queryParams.append('q', query);
    queryParams.append('limit', limit.toString());

    const response = await fetch(`${this.baseUrl}/api/suggestions/search?${queryParams.toString()}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Invalider le cache utilisateur
  async invalidateUserCache() {
    const response = await fetch(`${this.baseUrl}/api/cache/invalidate`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }

  // Récupérer les statistiques de cache
  async getCacheStats() {
    const response = await fetch(`${this.baseUrl}/api/cache/stats`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Erreur HTTP: ${response.status}`);
    }

    return await response.json();
  }
}

export const paginationService = new PaginationService();
export default paginationService;