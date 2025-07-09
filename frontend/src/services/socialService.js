/**
 * PHASE 3.3 - Service Social Frontend
 * Service pour les fonctionnalités sociales et communautaires
 */

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class SocialService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Récupération du token d'authentification
  getAuthToken() {
    return localStorage.getItem('token');
  }

  // Headers avec authentification
  getAuthHeaders() {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  // === GESTION DES PROFILS ===

  async createProfile(profileData) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/profile`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(profileData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la création du profil:', error);
      throw error;
    }
  }

  async getProfile(userId) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/profile/${userId}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la récupération du profil:', error);
      throw error;
    }
  }

  async updateProfile(updates) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/profile`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la mise à jour du profil:', error);
      throw error;
    }
  }

  // === GESTION DES FOLLOWS ===

  async followUser(userId) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/follow/${userId}`, {
        method: 'POST',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors du follow:', error);
      throw error;
    }
  }

  async unfollowUser(userId) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/follow/${userId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de l\'unfollow:', error);
      throw error;
    }
  }

  async getFollowers(userId, limit = 20, offset = 0) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/followers/${userId}?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la récupération des followers:', error);
      throw error;
    }
  }

  async getFollowing(userId, limit = 20, offset = 0) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/following/${userId}?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la récupération des following:', error);
      throw error;
    }
  }

  // === GESTION DES ACTIVITÉS ===

  async createActivity(activityData) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/activity`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(activityData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la création de l\'activité:', error);
      throw error;
    }
  }

  async getFeed(limit = 20, offset = 0) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/feed?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la récupération du feed:', error);
      throw error;
    }
  }

  // === GESTION DES NOTIFICATIONS ===

  async getNotifications(limit = 20, unreadOnly = false) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/notifications?limit=${limit}&unread_only=${unreadOnly}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la récupération des notifications:', error);
      throw error;
    }
  }

  async markNotificationRead(notificationId) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors du marquage de la notification:', error);
      throw error;
    }
  }

  async markAllNotificationsRead() {
    try {
      const response = await fetch(`${this.baseURL}/api/social/notifications/read-all`, {
        method: 'PUT',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors du marquage de toutes les notifications:', error);
      throw error;
    }
  }

  // === RECHERCHE SOCIALE ===

  async searchUsers(query, limit = 20) {
    try {
      const response = await fetch(`${this.baseURL}/api/social/search/users?q=${encodeURIComponent(query)}&limit=${limit}`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la recherche d\'utilisateurs:', error);
      throw error;
    }
  }

  // === STATISTIQUES SOCIALES ===

  async getSocialStats() {
    try {
      const response = await fetch(`${this.baseURL}/api/social/stats`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la récupération des stats sociales:', error);
      throw error;
    }
  }

  // === UTILITAIRES ===

  async healthCheck() {
    try {
      const response = await fetch(`${this.baseURL}/api/social/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors du health check social:', error);
      throw error;
    }
  }

  // === HELPERS POUR LES ACTIVITÉS ===

  createBookCompletedActivity(bookData) {
    return {
      activity_type: 'book_completed',
      content: {
        book_id: bookData.id,
        title: bookData.title,
        author: bookData.author,
        cover_url: bookData.cover_url,
        rating: bookData.rating,
        review: bookData.review
      },
      privacy_level: 'public'
    };
  }

  createBookRatedActivity(bookData) {
    return {
      activity_type: 'book_rated',
      content: {
        book_id: bookData.id,
        title: bookData.title,
        author: bookData.author,
        cover_url: bookData.cover_url,
        rating: bookData.rating
      },
      privacy_level: 'public'
    };
  }

  createBookAddedActivity(bookData) {
    return {
      activity_type: 'book_added',
      content: {
        book_id: bookData.id,
        title: bookData.title,
        author: bookData.author,
        cover_url: bookData.cover_url,
        category: bookData.category
      },
      privacy_level: 'public'
    };
  }
}

// Instance globale du service
const socialService = new SocialService();

export default socialService;