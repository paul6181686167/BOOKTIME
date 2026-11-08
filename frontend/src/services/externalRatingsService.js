import { API_BASE_URL } from '../config/environment';
import { getToken } from './apiClient';

const cache = new Map();

/**
 * Notes d'autres sites (Open Library, Google Books, AniList, MyAnimeList) pour un livre
 * ou une série, ramenées sur 5, plus des liens de recherche Babelio / Goodreads.
 * Résultat gardé en mémoire pour la session (la fiche est souvent rouverte).
 */
export async function fetchExternalRatings({ title, author = '', isbn = '', kind = 'book', category = '' }) {
  const token = getToken();
  if (!token || !(title || isbn)) return { ratings: [], links: [] };

  const params = new URLSearchParams({ title: title || '', author, isbn, kind, category });
  const key = params.toString();
  if (cache.has(key)) return cache.get(key);

  const res = await fetch(`${API_BASE_URL}/api/ratings/external?${key}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const result = { ratings: data.ratings || [], links: data.links || [] };
  // Réponse vide = peut-être une source en panne : on ne la fige pas
  if (result.ratings.length > 0) cache.set(key, result);
  return result;
}

export function clearExternalRatingsCache() {
  cache.clear();
}
