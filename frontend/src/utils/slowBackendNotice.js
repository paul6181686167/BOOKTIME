/**
 * Détecte un backend Render qui dort : dès qu'un appel API traîne, on prévient
 * au lieu de laisser un spinner muet.
 */
import { API_BASE_URL } from '../config/environment';

export const SLOW_BACKEND_EVENT = 'booktime:slow-backend';
export const SLOW_BACKEND_MS = 2800;

const SKIP = /\/(?:version\.json)$/i;

let inflight = 0;
let slowTimer = null;
let slow = false;

function backendUrl(url) {
  const s = String(url || '');
  if (!s) return false;
  if (SKIP.test(s)) return false;
  if (s.startsWith(API_BASE_URL) || s.startsWith('/api/') || s.startsWith('/ping')) return true;
  try {
    return new URL(s, API_BASE_URL).origin === new URL(API_BASE_URL).origin;
  } catch {
    return false;
  }
}

function emit(nextSlow) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(SLOW_BACKEND_EVENT, { detail: { slow: nextSlow } }));
}

function markSlow() {
  if (slow) return;
  slow = true;
  emit(true);
}

function markFast() {
  if (!slow) return;
  slow = false;
  emit(false);
}

/** @returns {() => void} à appeler quand la requête se termine */
export function beginBackendRequest(url) {
  if (!backendUrl(url)) return () => {};
  inflight += 1;
  if (inflight === 1 && !slowTimer) {
    slowTimer = setTimeout(markSlow, SLOW_BACKEND_MS);
  }
  let done = false;
  return () => {
    if (done) return;
    done = true;
    inflight = Math.max(0, inflight - 1);
    if (inflight === 0) {
      clearTimeout(slowTimer);
      slowTimer = null;
      markFast();
    }
  };
}

export function attachAxiosSlowInterceptor(instance) {
  if (!instance?.interceptors) return;
  instance.interceptors.request.use((config) => {
    const url = `${config.baseURL || ''}${config.url || ''}`;
    config.__btSlowEnd = beginBackendRequest(url);
    return config;
  });
  const finish = (config) => {
    if (typeof config?.__btSlowEnd === 'function') config.__btSlowEnd();
  };
  instance.interceptors.response.use(
    (res) => {
      finish(res.config);
      return res;
    },
    (err) => {
      finish(err.config);
      return Promise.reject(err);
    }
  );
}

export function isBackendCurrentlySlow() {
  return slow;
}

/** Tests uniquement. */
export function __resetSlowBackendNotice() {
  inflight = 0;
  clearTimeout(slowTimer);
  slowTimer = null;
  slow = false;
}
