/**
 * Pré-crée les fiches auteurs des livres de la bibliothèque (arrière-plan).
 * Même esprit que libraryMetaEnrichment pour les livres.
 */
import { API_BASE_URL } from '../config/environment';
import { isMobileClient } from '../utils/device';

let running = false;
let lastRunAt = 0;
const MIN_GAP_MS = 5 * 60 * 1000;

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * @returns {() => void} cancel
 */
export function scheduleLibraryAuthorEnrichment({ books = [], userSeriesLibrary = [] } = {}) {
  if (running) return () => {};
  if (Date.now() - lastRunAt < MIN_GAP_MS) return () => {};

  const authorSet = new Set();
  for (const b of books || []) {
    const a = (b?.author || '').split(',')[0].trim();
    if (a && a.toLowerCase() !== 'auteur inconnu') authorSet.add(a);
  }
  for (const s of userSeriesLibrary || []) {
    const a = (s?.author || s?.authors?.[0] || '').split(',')[0].trim();
    if (a) authorSet.add(a);
  }
  if (authorSet.size === 0) return () => {};

  let cancelled = false;
  const delay = isMobileClient() ? 4500 : 2500;
  const limit = isMobileClient() ? 6 : 12;

  const timer = setTimeout(async () => {
    if (cancelled || running) return;
    running = true;
    lastRunAt = Date.now();
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/authors/ensure-from-library?limit=${limit}`,
        {
          method: 'POST',
          headers: {
            ...authHeaders(),
            'Content-Type': 'application/json',
          },
        }
      );
      if (!res.ok) {
        console.warn('[authors] ensure-from-library', res.status);
        return;
      }
      const data = await res.json().catch(() => ({}));
      if (data?.ensured_count) {
        console.log(
          `[authors] ${data.ensured_count} fiche(s) pré-créée(s) / ${data.total_library_authors || '?'} auteurs biblio`
        );
      }
    } catch (err) {
      console.warn('[authors] enrichissement:', err?.message || err);
    } finally {
      running = false;
    }
  }, delay);

  return () => {
    cancelled = true;
    clearTimeout(timer);
  };
}
