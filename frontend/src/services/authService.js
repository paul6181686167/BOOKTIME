// Service d'authentification multi-environnement
import { API_BASE_URL } from '../config/environment';
import { TERMS_VERSION } from '../legal/terms';
import { clearUserCaches } from '../utils/offlineCaches';
import logger from '../utils/logger';
import { getToken } from './apiClient';

class AuthService {
  constructor() {
    this.backendUrl = API_BASE_URL;
    logger.debug(' AuthService initialized with:', this.backendUrl);
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

  async register(email, password, acceptTerms = false) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      const response = await fetch(`${this.backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          accept_terms: !!acceptTerms,
          terms_version: TERMS_VERSION,
        }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        logger.debug(' Inscription réussie');
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
      const token = getToken();
      
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
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!response.ok) return { success: false };
      const data = await response.json();
      return {
        success: true,
        profile: {
          display_name: data.display_name || '',
          bio: data.bio || '',
          avatar_url: data.avatar_url || '',
          username: data.username || '',
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
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!response.ok) return { success: false };
      const data = await response.json();
      return { success: true, settings: data.settings || {}, isAdmin: data.is_admin === true };
    } catch (_) {
      return { success: false };
    }
  }

  async updateSettings(patch) {
    return this._send('PUT', '/api/auth/me/settings', patch);
  }

  async changePassword(currentPassword, newPassword) {
    const res = await this._send('POST', '/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    // Les autres sessions sont révoquées par le serveur : on garde celle-ci avec le nouveau jeton
    if (res.success && res.access_token) {
      try {
        localStorage.setItem('token', res.access_token);
      } catch (_) {
        /* stockage indisponible */
      }
    }
    return res;
  }

  async _send(method, path, body) {
    try {
      const response = await fetch(`${this.backendUrl}${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
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
  async updateProfile(patch, { attempts = 3, timeoutMs = 30000, retryDelayMs = 2000 } = {}) {
    // Le serveur gratuit peut dormir (premier appel de 30 à 60 s) : on relance plutôt
    // que d'abandonner. Seules les pannes réseau, délais dépassés et erreurs 5xx sont relancés.
    let lastError = 'Serveur inaccessible';
    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const response = await fetch(`${this.backendUrl}/api/auth/me/profile`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`,
          },
          body: JSON.stringify(patch),
          signal: controller.signal,
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
        if (response.status < 500) return { success: false, error: msg };
        lastError = msg;
      } catch (error) {
        lastError =
          error.name === 'AbortError'
            ? 'Le serveur met du temps à répondre'
            : error.message || 'Serveur inaccessible';
      } finally {
        clearTimeout(timer);
      }
      if (attempt < attempts) await new Promise((r) => setTimeout(r, retryDelayMs));
    }
    return { success: false, error: lastError };
  }

  async deleteAccount(password) {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/me`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
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
    // Bibliothèque et fiches gardées pour le hors ligne : propres au compte
    clearUserCaches();
    // Supprime le cookie de session httpOnly s'il est utilisé (sans effet sinon)
    try {
      fetch(`${this.backendUrl}/api/auth/logout`, { method: 'POST', credentials: 'include', keepalive: true }).catch(() => {});
    } catch {
      /* hors ligne ou fetch indisponible : le cookie expirera de lui-même */
    }
  }
}

export default AuthService;
