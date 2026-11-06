// Service d'authentification multi-environnement
import { API_BASE_URL } from '../config/environment';

class AuthService {
  constructor() {
    this.backendUrl = API_BASE_URL;
    console.log(' AuthService initialized with:', this.backendUrl);
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
        console.log(' Inscription réussie');
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

  /** Profil complet (nom, biographie, photo) depuis le serveur. */
  async fetchProfile() {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/me`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!response.ok) return { success: false };
      const data = await response.json();
      return {
        success: true,
        profile: {
          display_name: data.display_name || '',
          bio: data.bio || '',
          avatar_url: data.avatar_url || '',
        },
      };
    } catch (_) {
      return { success: false };
    }
  }

  /** Réglages de confidentialité (visibilité auprès des amis, recherche de lecteurs). */
  async fetchSettings() {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/me`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!response.ok) return { success: false };
      const data = await response.json();
      return { success: true, settings: data.settings || {} };
    } catch (_) {
      return { success: false };
    }
  }

  async updateSettings(patch) {
    return this._send('PUT', '/api/auth/me/settings', patch);
  }

  async changePassword(currentPassword, newPassword) {
    return this._send('POST', '/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  async _send(method, path, body) {
    try {
      const response = await fetch(`${this.backendUrl}${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(body),
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) return { success: true, ...data };
      const msg =
        typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg || 'Action impossible';
      return { success: false, error: msg };
    } catch (error) {
      return { success: false, error: error.message || 'Serveur inaccessible' };
    }
  }

  /** Enregistre nom, biographie et/ou photo (avatar_url vide = retirer la photo). */
  async updateProfile(patch) {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/me/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(patch),
      });
      if (response.ok) {
        const data = await response.json();
        return { success: true, profile: data.profile };
      }
      const error = await response.json().catch(() => ({}));
      const msg =
        typeof error.detail === 'string'
          ? error.detail
          : error.detail?.[0]?.msg || 'Enregistrement impossible';
      return { success: false, error: msg };
    } catch (error) {
      return { success: false, error: error.message || 'Serveur inaccessible' };
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
