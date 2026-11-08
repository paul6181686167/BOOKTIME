import { apiFetch } from './apiClient';

/**
 * Écran d'accueil « Qu'as-tu déjà lu ? » : sélection d'oeuvres pour constituer
 * sa bibliothèque avant d'y accéder.
 */

const flagKey = (userKey) => `booktime-onboarding-done:${userKey}`;

export function isOnboardingDone(userKey) {
  try {
    return localStorage.getItem(flagKey(userKey)) === '1';
  } catch {
    return false;
  }
}

export function markOnboardingDone(userKey) {
  try {
    localStorage.setItem(flagKey(userKey), '1');
  } catch {
    /* stockage indisponible : l'écran pourra réapparaître, sans conséquence */
  }
}

async function readJson(res, fallbackMessage) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : fallbackMessage);
  }
  return data;
}

/** group : « roman » ou « graphic_novel ». */
export async function fetchOnboardingWorks(group) {
  const res = await apiFetch(`/api/catalog/onboarding?group=${encodeURIComponent(group)}`);
  const data = await readJson(res, 'Impossible de charger la sélection');
  return {
    works: Array.isArray(data.works) ? data.works : [],
    genres: Array.isArray(data.genres) ? data.genres : [],
  };
}

/** Ajoute les oeuvres cochées (identifiants du catalogue) comme livres terminés. */
export async function addOnboardingWorks(ids) {
  const res = await apiFetch('/api/catalog/onboarding', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  });
  return readJson(res, "Impossible d'ajouter les livres");
}

/**
 * Vrai si le serveur confirme que la bibliothèque est vide.
 * En cas d'erreur réseau on répond faux : mieux vaut ne pas afficher l'écran
 * d'accueil qu'ajouter des doublons à une bibliothèque qu'on n'a pas pu lire.
 */
export async function serverLibraryIsEmpty() {
  try {
    const res = await apiFetch('/api/books?limit=1');
    if (!res.ok) return false;
    const data = await res.json();
    if (Array.isArray(data)) return data.length === 0;
    return (data.total ?? (data.items || []).length) === 0;
  } catch {
    return false;
  }
}
