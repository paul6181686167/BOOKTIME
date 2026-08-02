/**
 * Service "À venir" — gestion des livres à paraître et des sorties attendues
 */
import { API_BASE_URL } from '../config/environment';

function authHeaders() {
  const token = localStorage.getItem('token');
  return token
    ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
    : { 'Content-Type': 'application/json' };
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ──────────────────────────────────────────────────────────────────────────────
// Upcoming books (status === 'upcoming' in the books collection)
// ──────────────────────────────────────────────────────────────────────────────

export const upcomingService = {
  /**
   * Agrégat unifié des prochaines sorties (prochains tomes, chapitres manga,
   * livres surveillés), groupé par échéance. Source de vérité du panneau.
   * @param {boolean} refresh - ignore le cache serveur et recalcule.
   */
  async getUpcoming(refresh = false) {
    try {
      return await apiFetch(`/api/upcoming${refresh ? '?refresh=true' : ''}`);
    } catch (err) {
      console.warn('upcomingService.getUpcoming error:', err);
      return {
        items: [],
        groups: { available: [], this_week: [], this_month: [], later: [], unknown: [] },
        counts: { total: 0 },
      };
    }
  },

  // ──────────────────────────────────────────────────────────────────────────
  // Réglages de notification
  // ──────────────────────────────────────────────────────────────────────────

  async getNotificationSettings() {
    try {
      return await apiFetch('/api/settings/notifications');
    } catch {
      return { notif_upcoming: 'in_app' };
    }
  },

  async setNotificationMode(mode) {
    return apiFetch('/api/settings/notifications', {
      method: 'PUT',
      body: JSON.stringify({ notif_upcoming: mode }),
    });
  },

  // ──────────────────────────────────────────────────────────────────────────
  // Notifications in-app
  // ──────────────────────────────────────────────────────────────────────────

  async getNotifications(limit = 50) {
    try {
      return await apiFetch(`/api/notifications?limit=${limit}`);
    } catch {
      return { notifications: [], unread: 0 };
    }
  },

  async markNotificationRead(id) {
    return apiFetch(`/api/notifications/${id}/read`, { method: 'POST' });
  },

  async markAllNotificationsRead() {
    return apiFetch('/api/notifications/read-all', { method: 'POST' });
  },

  /**
   * Récupère les livres surveillés de l'utilisateur (watchlist).
   */
  async getUpcomingBooks() {
    try {
      const data = await apiFetch('/api/books/all?status=upcoming&limit=100');
      const books = data.items || data.books || (Array.isArray(data) ? data : []);
      return books;
    } catch (err) {
      console.warn('upcomingService.getUpcomingBooks error:', err);
      return [];
    }
  },

  /**
   * Ajoute un livre dans la liste de surveillance (watchlist).
   */
  async addUpcomingBook(bookData) {
    const payload = {
      title: bookData.title,
      author: bookData.author || bookData.authors?.[0] || 'Auteur inconnu',
      category: bookData.category || 'roman',
      cover_url: bookData.cover_url || bookData.cover || '',
      saga: bookData.series_name || bookData.saga || '',
      volume_number: bookData.next_volume || bookData.volume || null,
      ol_key: bookData.book_id || bookData.ol_key || '',
      status: 'upcoming',
      watchlist: true,
      publish_date: bookData.date || bookData.published_date || bookData.publish_date || null,
      date_confidence: bookData.date_confidence || null,
    };

    return apiFetch('/api/books', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Migre un livre surveillé vers "À lire" une fois sorti.
   */
  async migrateToRead(bookId) {
    return apiFetch(`/api/books/${bookId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'to_read', watchlist: false }),
    });
  },

  /**
   * Supprime un livre "à venir".
   */
  async removeUpcomingBook(bookId) {
    return apiFetch(`/api/books/${bookId}`, { method: 'DELETE' });
  },

  // ──────────────────────────────────────────────────────────────────────────
  // Auto-migration des livres "à venir" devenus disponibles
  // ──────────────────────────────────────────────────────────────────────────

  /**
   * Vérifie parmi les livres "upcoming" lesquels sont maintenant sortis,
   * et les migre vers "to_read".
   * Retourne le nombre de migrations effectuées.
   */
  async autoMigrateReleasedBooks() {
    try {
      const upcoming = await this.getUpcomingBooks();
      const today = new Date().toISOString().substring(0, 10);
      let migrated = 0;

      for (const book of upcoming) {
        const pubDate = book.publish_date || book.published_date;
        if (!pubDate) continue;
        const bookDate = pubDate.substring(0, 10);
        if (bookDate <= today) {
          await this.migrateToRead(book.id);
          migrated++;
        }
      }

      return migrated;
    } catch (err) {
      console.warn('autoMigrateReleasedBooks error:', err);
      return 0;
    }
  },

  // ──────────────────────────────────────────────────────────────────────────
  // Recherche de livres à paraître via Open Library
  // ──────────────────────────────────────────────────────────────────────────

  async searchUpcoming(query) {
    if (!query || query.length < 2) return [];
    try {
      const url = `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=8&fields=title,author_name,cover_i,first_publish_year,key,isbn`;
      const res = await fetch(url);
      const data = await res.json();
      return (data.docs || []).map((doc) => ({
        title: doc.title,
        author: doc.author_name?.[0] || 'Auteur inconnu',
        cover_url: doc.cover_i
          ? `https://covers.openlibrary.org/b/id/${doc.cover_i}-M.jpg`
          : null,
        ol_key: doc.key,
        category: 'roman',
        source: 'openlibrary_search',
      }));
    } catch {
      return [];
    }
  },
};

export default upcomingService;
