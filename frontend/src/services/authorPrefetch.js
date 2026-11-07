/**
 * Préchargement des fiches auteurs : la fiche est lue (ou construite) dès l'ouverture d'une fiche
 * livre ou série, pour que l'écran auteur s'affiche sans attente au clic sur le nom.
 */
import { API_BASE_URL } from '../config/environment';

const profiles = new Map(); // clé auteur -> Promise<données | null> (lecture rapide du cache serveur)
const ensured = new Set(); // auteurs pour lesquels la construction a déjà été demandée
const RETRY_MS = 10 * 60 * 1000;

/** Premier auteur d'une liste « A, B » : c'est sous ce nom que la fiche est enregistrée. */
export function primaryAuthor(name) {
  const text = String(name || '').trim();
  return text.split(',')[0].trim() || text;
}

function keyOf(name) {
  return primaryAuthor(name).toLowerCase().replace(/\s+/g, ' ');
}

function isRealAuthor(name) {
  const key = keyOf(name);
  return !!key && !['auteur inconnu', 'unknown', 'n/a'].includes(key);
}

function headers() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function getJson(url, options = {}) {
  const res = await fetch(url, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
  if (!res.ok) return null;
  return res.json().catch(() => null);
}

// Dernières fiches consultées, gardées pour le hors ligne (les plus récentes d'abord)
const STORE_PREFIX = 'booktime_author_profile:';
const STORE_INDEX = 'booktime_author_profile_index';
const MAX_STORED = 40;

function storeProfile(key, data) {
  try {
    const index = (JSON.parse(localStorage.getItem(STORE_INDEX)) || []).filter((k) => k !== key);
    index.unshift(key);
    index.splice(MAX_STORED).forEach((old) => localStorage.removeItem(STORE_PREFIX + old));
    localStorage.setItem(STORE_PREFIX + key, JSON.stringify(data));
    localStorage.setItem(STORE_INDEX, JSON.stringify(index.slice(0, MAX_STORED)));
  } catch (_) {
    /* quota plein ou stockage indisponible : le hors ligne est facultatif */
  }
}

function readStoredProfile(key) {
  try {
    const data = JSON.parse(localStorage.getItem(STORE_PREFIX + key));
    return data?.found && data.author ? data : null;
  } catch (_) {
    return null;
  }
}

/** Fiche déjà construite côté serveur (lecture seule, rapide). Partagée entre appels simultanés. */
export function readAuthorProfile(name) {
  if (!isRealAuthor(name)) return Promise.resolve(null);
  const key = keyOf(name);
  if (profiles.has(key)) return profiles.get(key);

  const promise = getJson(`${API_BASE_URL}/api/authors/${encodeURIComponent(primaryAuthor(name))}/profile`)
    .then(
      (data) => ({ data, offline: false }),
      () => ({ data: null, offline: true })
    )
    .then(({ data, offline }) => {
      if (data?.found && data.author) {
        storeProfile(key, data);
        return data;
      }
      // Pas de fiche : on ne mémorise pas l'échec, un nouvel appel pourra la trouver
      profiles.delete(key);
      // Hors ligne : dernière version connue de la fiche (non mémorisée en session)
      const noNetwork =
        offline || (typeof navigator !== 'undefined' && navigator.onLine === false);
      return noNetwork ? readStoredProfile(key) : null;
    });
  profiles.set(key, promise);
  return promise;
}

/**
 * Lit la fiche ; si elle n'existe pas encore, demande au serveur de la construire (une fois),
 * puis la garde en mémoire. Sans effet visible : à appeler à l'ouverture d'une fiche livre.
 */
export function prefetchAuthor(name) {
  if (!isRealAuthor(name)) return Promise.resolve(null);
  const key = keyOf(name);
  return readAuthorProfile(name).then(async (cached) => {
    if (cached || ensured.has(key)) return cached;
    ensured.add(key);
    setTimeout(() => ensured.delete(key), RETRY_MS);
    try {
      const built = await getJson(
        `${API_BASE_URL}/api/authors/${encodeURIComponent(primaryAuthor(name))}/ensure`,
        { method: 'POST' }
      );
      if (built?.found && built.author) {
        profiles.set(key, Promise.resolve(built));
        return built;
      }
    } catch (_) {
      /* préchargement : sans conséquence */
    }
    return null;
  });
}

/** Oublie les fiches en mémoire (tests, déconnexion). */
export function clearAuthorPrefetch() {
  profiles.clear();
  ensured.clear();
}
