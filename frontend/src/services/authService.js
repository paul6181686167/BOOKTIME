// Service d'authentification multi-environnement
import { API_BASE_URL } from '../config/environment';

class AuthService {
  constructor() {
    this.backendUrl = API_BASE_URL;
    console.log('🔗 AuthService initialized with:', this.backendUrl);
  }

  async login(email, password, rememberMe = true) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      const response = await fetch(`${this.backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, remember_me: !!rememberMe }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } else {
        const error = await response.json().catch(() => ({}));
        const msg = typeof error.detail === 'string' ? error.detail : (error.detail?.[0]?.msg || 'Erreur de connexion');
        return { success: false, error: msg };
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        return { success: false, error: 'Serveur inaccessible. Verifiez que le backend est demarre sur ' + this.backendUrl };
      }
      return { success: false, error: 'Erreur : ' + (error.message || 'Serveur inaccessible') };
    }
  }

  async register(email, password) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      const response = await fetch(`${this.backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        console.log('✅ Inscription réussie');
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } else {
        const error = await response.json().catch(() => ({}));
        let errorMessage = typeof error.detail === 'string' ? error.detail : (error.detail?.[0]?.msg || 'Erreur inscription');
        if (errorMessage && errorMessage.includes('existe déjà')) {
          errorMessage = `Un compte existe déjà avec cet email. Utilisez l'onglet Connexion.`;
        }
        return { success: false, error: errorMessage };
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        return { success: false, error: 'Serveur inaccessible. Verifiez que le backend tourne sur ' + this.backendUrl };
      }
      return { success: false, error: 'Erreur : ' + (error.message || 'Serveur inaccessible') };
    }
  }

  getCurrentUser() {
    try {
      const userString = localStorage.getItem('user');
      const token = localStorage.getItem('token');
      
      if (userString && token) {
        return JSON.parse(userString);
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  async deleteAccount(password) {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/me`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ password }),
      });

      if (response.ok) {
        this.logout();
        return { success: true };
      }
      const error = await response.json().catch(() => ({}));
      const msg =
        typeof error.detail === 'string'
          ? error.detail
          : error.detail?.[0]?.msg || 'Suppression impossible';
      return { success: false, error: msg };
    } catch (error) {
      return { success: false, error: error.message || 'Serveur inaccessible' };
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
}

export default AuthService;
