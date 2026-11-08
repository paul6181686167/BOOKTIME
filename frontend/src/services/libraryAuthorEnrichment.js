/**
 * Pré-crée les fiches auteurs des livres de la bibliothèque (arrière-plan).
 * Même esprit que libraryMetaEnrichment pour les livres.
 *
 * Le serveur traite un lot d'auteurs par appel et indique combien il en reste :
 * on enchaîne les lots jusqu'à ce que toute la bibliothèque soit couverte.
 */
import { API_BASE_URL } from '../config/environment';
import { isMobileClient } from '../utils/device';
import logger from '../utils/logger';
import { getToken } from './apiClient';

let running = false;
let lastRunAt = 0;
const MIN_GAP_MS = 5 * 60 * 1000;
const BATCH_PAUSE_MS = 1500;
const MAX_BATCHES = 12;

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Enchaîne les lots tant que le serveur signale des fiches à construire. */
async function runBatches(limit) {
  for (let batch = 0; batch < MAX_BATCHES; batch += 1) {
    const res = await fetch(`${API_BASE_URL}/api/authors/ensure-from-library?limit=${limit}`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      logger.warn('[authors] ensure-from-library', res.status);
      return;
    }
    const data = await res.json().catch(() => ({}));
    if (data?.ensured_count) {
      logger.debug(
        `[authors] ${data.ensured_count} fiche(s) pré-créée(s) / ${data.total_library_authors || '?'} auteurs biblio`
      );
    }
    if (!data?.remaining) return;
    await wait(BATCH_PAUSE_MS);
  }
}

/**
 * @returns {() => void} cancel (annule seulement le départ ; un lot commencé va à son terme)
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
  const delay = isMobileClient() ? 3000 : 2000;
  const limit = isMobileClient() ? 6 : 12;

  const timer = setTimeout(async () => {
    if (cancelled || running) return;
    running = true;
    lastRunAt = Date.now();
    try {
      await runBatches(limit);
    } catch (err) {
      logger.warn('[authors] enrichissement:', err?.message || err);
    } finally {
      running = false;
    }
  }, delay);

  return () => {
    cancelled = true;
    clearTimeout(timer);
  };
}
