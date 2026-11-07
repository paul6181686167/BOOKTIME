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

/** Fiche déjà construite côté serveur (lecture seule, rapide). Partagée entre appels simultanés. */
export function readAuthorProfile(name) {
  if (!isRealAuthor(name)) return Promise.resolve(null);
  const key = keyOf(name);
  if (profiles.has(key)) return profiles.get(key);

  const promise = getJson(`${API_BASE_URL}/api/authors/${encodeURIComponent(primaryAuthor(name))}/profile`)
    .catch(() => null)
    .then((data) => {
      if (data?.found && data.author) return data;
      // Pas de fiche : on ne mémorise pas l'échec, un nouvel appel pourra la trouver
      profiles.delete(key);
      return null;
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
