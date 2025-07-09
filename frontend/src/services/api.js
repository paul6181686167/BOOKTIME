// Client API central pour BOOKTIME
// Gestion centralisée des requêtes HTTP avec gestion d'erreurs

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Méthode utilitaire pour construire l'URL complète
  buildURL(endpoint) {
    return `${this.baseURL}${endpoint}`;
  }

  // Méthode utilitaire pour obtenir les headers par défaut
  getDefaultHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    };
  }

  // Méthode utilitaire pour gérer les erreurs
  async handleResponse(response) {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  // GET request
  async get(endpoint, options = {}) {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'GET',
      headers: {
        ...this.getDefaultHeaders(),
        ...options.headers
      },
      ...options
    });
    return this.handleResponse(response);
  }

  // POST request
  async post(endpoint, data = null, options = {}) {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'POST',
      headers: {
        ...this.getDefaultHeaders(),
        ...options.headers
      },
      ...(data && { body: JSON.stringify(data) }),
      ...options
    });
    return this.handleResponse(response);
  }

  // PUT request
  async put(endpoint, data = null, options = {}) {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'PUT',
      headers: {
        ...this.getDefaultHeaders(),
        ...options.headers
      },
      ...(data && { body: JSON.stringify(data) }),
      ...options
    });
    return this.handleResponse(response);
  }

  // DELETE request
  async delete(endpoint, options = {}) {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'DELETE',
      headers: {
        ...this.getDefaultHeaders(),
        ...options.headers
      },
      ...options
    });
    return this.handleResponse(response);
  }

  // PATCH request
  async patch(endpoint, data = null, options = {}) {
    const response = await fetch(this.buildURL(endpoint), {
      method: 'PATCH',
      headers: {
        ...this.getDefaultHeaders(),
        ...options.headers
      },
      ...(data && { body: JSON.stringify(data) }),
      ...options
    });
    return this.handleResponse(response);
  }
}

// Instance singleton du client API
const apiClient = new ApiClient();

export default apiClient;