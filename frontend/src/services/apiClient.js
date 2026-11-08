/**
 * Client API central.
 *
 * - `getToken()` / `authHeaders()` : unique point d'accès au jeton de session. Le jour où
 *   le jeton passera en cookie httpOnly, seul ce fichier aura à changer.
 * - `apiFetch()` : fetch vers le backend avec en-tête d'authentification et délai maximum.
 * - `installUnauthorizedWatcher()` : détecte les réponses 401 de n'importe quel appel au
 *   backend (fetch ou axios) et prévient l'application, qui déconnecte proprement
 *   l'utilisateur au lieu de laisser chaque écran échouer en silence.
 */
import { API_BASE_URL } from '../config/environment';

export const UNAUTHORIZED_EVENT = 'booktime:unauthorized';

const DEFAULT_TIMEOUT_MS = 30000;
// Routes où un 401 signifie « identifiants refusés », pas « session expirée »
const AUTH_ROUTES = /\/api\/auth\/(login|register|logout|forgot-password|reset-password|change-password)/;
// Suppression de compte : un 401 = mauvais mot de passe saisi, pas une session expirée
const DELETE_ACCOUNT = /\/api\/auth\/me\/?$/;

export function getToken() {
  try {
    return localStorage.getItem('token');
  } catch {
    return null;
  }
}

/** En-têtes avec le jeton de session (si connecté), à fusionner avec `extra`. */
export function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : { ...extra };
}

function resolveUrl(path) {
  return /^https?:\/\//i.test(path) ? path : `${API_BASE_URL}${path}`;
}

/**
 * fetch vers le backend.
 * @param {string} path  chemin (`/api/books`) ou URL complète
 * @param {RequestInit & {timeoutMs?: number, auth?: boolean}} options
 */
export async function apiFetch(path, { timeoutMs = DEFAULT_TIMEOUT_MS, auth = true, headers, signal, ...rest } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener('abort', () => controller.abort(), { once: true });
  }
  try {
    return await fetch(resolveUrl(path), {
      ...rest,
      headers: auth ? authHeaders(headers) : { ...headers },
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

let lastNotified = 0;

/** Signale une session expirée (au plus une fois toutes les 5 s, même si 10 appels échouent). */
export function notifyUnauthorized() {
  const now = Date.now();
  if (now - lastNotified < 5000) return;
  lastNotified = now;
  window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
}

function sentToken(input, init) {
  const headers = (init && init.headers) || (input && typeof input !== 'string' && input.headers);
  if (!headers) return null;
  const value =
    typeof headers.get === 'function'
      ? headers.get('Authorization')
      : headers.Authorization || headers.authorization;
  return value ? String(value).replace(/^Bearer\s+/i, '') : null;
}

function targetsBackend(input) {
  const url = typeof input === 'string' ? input : (input && input.url) || '';
  if (!url.startsWith(API_BASE_URL) && !url.startsWith('/api/')) return false;
  return !AUTH_ROUTES.test(url);
}

let installed = false;

/** Enveloppe window.fetch une seule fois pour repérer les 401 du backend. */
export function installUnauthorizedWatcher() {
  if (installed || typeof window === 'undefined' || typeof window.fetch !== 'function') return;
  installed = true;
  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const response = await originalFetch(input, init);
    const isDeleteAccount =
      String((init && init.method) || (input && input.method) || '').toUpperCase() === 'DELETE' &&
      DELETE_ACCOUNT.test(typeof input === 'string' ? input : (input && input.url) || '');
    if (response.status === 401 && !isDeleteAccount && targetsBackend(input)) {
      const used = sentToken(input, init);
      // Ignore les réponses tardives d'une ancienne session (reconnexion entre-temps)
      if (used && used === getToken()) notifyUnauthorized();
    }
    return response;
  };
}
