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
   * Récupère tous les livres "à venir" de l'utilisateur (status = upcoming).
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
   * Ajoute un livre dans "À venir" (status upcoming).
   */
  async addUpcomingBook(bookData) {
    const payload = {
      title: bookData.title,
      author: bookData.author || bookData.authors?.[0] || 'Auteur inconnu',
      category: bookData.category || 'roman',
      cover_url: bookData.cover_url || bookData.cover || '',
      ol_key: bookData.book_id || bookData.ol_key || '',
      status: 'upcoming',
      publish_date: bookData.published_date || bookData.publish_date || null,
      source: bookData.source || 'upcoming',
      metadata: bookData.metadata || {},
    };

    return apiFetch('/api/books', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Migre un livre "à venir" vers "À lire" une fois sorti.
   */
  async migrateToRead(bookId) {
    return apiFetch(`/api/books/${bookId}`, {
      method: 'PUT',
      body: JSON.stringify({ status: 'to_read' }),
    });
  },

  /**
   * Supprime un livre "à venir".
   */
  async removeUpcomingBook(bookId) {
    return apiFetch(`/api/books/${bookId}`, { method: 'DELETE' });
  },

  // ──────────────────────────────────────────────────────────────────────────
  // Calcul des prochains tomes de séries
  // ──────────────────────────────────────────────────────────────────────────

  /**
   * À partir des séries dans la bibliothèque, calcule les "prochains tomes" potentiels.
   * Retourne une liste de suggestions (sans appel API supplémentaire).
   */
  computeNextTomes(userBooks = []) {
    const seriesMap = {};

    userBooks.forEach((book) => {
      const saga = book.saga || book.series_name;
      if (!saga) return;
      const vol = book.volume_number || book.tome || null;
      if (!seriesMap[saga]) {
        seriesMap[saga] = {
          name: saga,
          author: book.author || '',
          category: book.category || 'roman',
          cover_url: book.cover_url || '',
          volumes: [],
        };
      }
      if (vol) seriesMap[saga].volumes.push(parseInt(vol, 10));
    });

    const suggestions = [];
    Object.values(seriesMap).forEach((series) => {
      if (series.volumes.length === 0) return;
      const maxVol = Math.max(...series.volumes);
      suggestions.push({
        type: 'next_tome',
        series_name: series.name,
        title: `${series.name} — Tome ${maxVol + 1}`,
        author: series.author,
        category: series.category,
        cover_url: series.cover_url,
        reason: `Suite de ${series.name}`,
        next_volume: maxVol + 1,
      });
    });

    return suggestions;
  },

  // ──────────────────────────────────────────────────────────────────────────
  // Auteurs suivis (via localStorage)
  // ──────────────────────────────────────────────────────────────────────────

  getFollowedAuthors() {
    try {
      return JSON.parse(localStorage.getItem('booktime_following') || '[]');
    } catch {
      return [];
    }
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
