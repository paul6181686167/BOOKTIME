/**
 * Cache local de la bibliothèque pour consultation hors ligne.
 * Stockage : localStorage (simple, suffisant pour ~1000 livres).
 */

const CACHE_KEY = 'booktime_offline_library_v1';
const META_KEY = 'booktime_offline_library_meta_v1';
const SERIES_CACHE_KEY = 'booktime_offline_series_v1';
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 jours

function safeParse(raw, fallback) {
  try {
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function saveLibraryCache(books, filters = {}) {
  if (typeof window === 'undefined' || !Array.isArray(books)) return;
  try {
    const payload = {
      books,
      filters: {
        category: filters.category || null,
        status: filters.status || null,
      },
      savedAt: Date.now(),
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(payload));
    localStorage.setItem(
      META_KEY,
      JSON.stringify({ savedAt: payload.savedAt, count: books.length })
    );
  } catch {
    // Quota / mode privé : ignorer
  }
}

export function loadLibraryCache(filters = {}) {
  if (typeof window === 'undefined') return null;
  try {
    const payload = safeParse(localStorage.getItem(CACHE_KEY), null);
    if (!payload || !Array.isArray(payload.books)) return null;

    const age = Date.now() - (payload.savedAt || 0);
    if (age > MAX_AGE_MS) return null;

    const wantCategory = filters.category || null;
    const wantStatus = filters.status || null;
    const cachedCategory = payload.filters?.category || null;
    const cachedStatus = payload.filters?.status || null;

    // Si le cache est un dump complet (sans filtre), on peut filtrer côté client
    if (!cachedCategory && !cachedStatus) {
      let books = payload.books;
      if (wantCategory) {
        books = books.filter(
          (b) => (b.category || b.genre || '').toLowerCase() === wantCategory.toLowerCase()
        );
      }
      if (wantStatus) {
        books = books.filter(
          (b) => (b.status || '').toLowerCase() === wantStatus.toLowerCase()
        );
      }
      return {
        books,
        fromCache: true,
        savedAt: payload.savedAt,
        offline: true,
      };
    }

    // Cache filtré : ne servir que si les filtres correspondent
    if (cachedCategory === wantCategory && cachedStatus === wantStatus) {
      return {
        books: payload.books,
        fromCache: true,
        savedAt: payload.savedAt,
        offline: true,
      };
    }

    return null;
  } catch {
    return null;
  }
}

export function getLibraryCacheMeta() {
  if (typeof window === 'undefined') return null;
  return safeParse(localStorage.getItem(META_KEY), null);
}

export function clearLibraryCache() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(CACHE_KEY);
  localStorage.removeItem(META_KEY);
  localStorage.removeItem(SERIES_CACHE_KEY);
}

export function saveSeriesCache(series) {
  if (typeof window === 'undefined' || !Array.isArray(series)) return;
  try {
    localStorage.setItem(
      SERIES_CACHE_KEY,
      JSON.stringify({ series, savedAt: Date.now() })
    );
  } catch {
    /* quota */
  }
}

export function loadSeriesCache() {
  if (typeof window === 'undefined') return null;
  try {
    const payload = safeParse(localStorage.getItem(SERIES_CACHE_KEY), null);
    if (!payload || !Array.isArray(payload.series)) return null;
    if (Date.now() - (payload.savedAt || 0) > MAX_AGE_MS) return null;
    return { series: payload.series, savedAt: payload.savedAt, fromCache: true };
  } catch {
    return null;
  }
}

export function isLikelyOffline() {
  return typeof navigator !== 'undefined' && navigator.onLine === false;
}
