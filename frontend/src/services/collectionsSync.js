/**
 * Synchronisation des collections avec le compte (GET/PUT /api/collections).
 *
 * Les collections restent d'abord enregistrées localement (rapide, fonctionne hors ligne) ;
 * ce service les envoie au serveur après chaque modification et les récupère au démarrage,
 * ce qui les partage entre le site et l'application.
 */
import { API_BASE_URL } from '../config/environment';
import {
  COLLECTIONS_CHANGED_EVENT,
  getCollections,
  getSyncState,
  normalizeCollection,
  saveCollections,
  setSyncState,
} from '../utils/collectionsStorage';
import { getToken } from './apiClient';

const PUSH_DEBOUNCE_MS = 1000;
const FOCUS_PULL_MIN_INTERVAL_MS = 30000;

function currentUserId() {
  try {
    return JSON.parse(localStorage.getItem('user'))?.id || null;
  } catch {
    return null;
  }
}

function authHeaders() {
  const token = getToken();
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : null;
}

function sameName(a, b) {
  return (a?.name || '').trim().toLowerCase() === (b?.name || '').trim().toLowerCase();
}

/**
 * Fusionne deux listes de collections sans rien perdre : même collection = même
 * identifiant (ou même nom) ; éléments réunis ; couleur locale prioritaire.
 */
export function mergeCollections(local = [], remote = []) {
  const result = remote.map((c) => {
    const n = normalizeCollection(c);
    return { ...n, items: [...(n.items || [])] };
  });
  local.forEach((raw) => {
    const l = normalizeCollection(raw);
    const found = result.find((r) => String(r.id) === String(l.id)) || result.find((r) => sameName(r, l));
    if (!found) {
      result.push({ ...l, items: [...(l.items || [])] });
      return;
    }
    const keys = new Set((found.items || []).map((it) => it.key));
    (l.items || []).forEach((it) => {
      if (!keys.has(it.key)) {
        keys.add(it.key);
        found.items.push(it);
      }
    });
    if (l.color) found.color = l.color;
  });
  return result;
}

async function request(method, body) {
  const headers = authHeaders();
  if (!headers) return { status: 0 };
  const res = await fetch(`${API_BASE_URL}/api/collections`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  return { status: res.status, data };
}

let pushing = null;

/** Envoie les collections locales. Gère un conflit (409) par fusion puis un nouvel envoi. */
export async function pushCollections() {
  if (pushing) return pushing;
  pushing = (async () => {
    try {
      for (let attempt = 0; attempt < 2; attempt += 1) {
        const state = getSyncState();
        const res = await request('PUT', {
          base_version: Number.isInteger(state.version) ? state.version : 0,
          collections: getCollections(),
        });
        if (res.status === 200 && res.data) {
          setSyncState({ userId: currentUserId(), version: res.data.version, dirty: false });
          return true;
        }
        if (res.status === 409 && res.data) {
          const merged = mergeCollections(getCollections(), res.data.collections || []);
          saveCollections(merged, { fromSync: true });
          setSyncState({ version: res.data.version, dirty: true });
          continue;
        }
        return false;
      }
      return false;
    } catch {
      return false; // hors ligne : on réessaiera à la prochaine modification / ouverture
    } finally {
      pushing = null;
    }
  })();
  return pushing;
}

/** Récupère l'état du compte et le réconcilie avec le local. */
export async function pullCollections() {
  try {
    const userId = currentUserId();
    if (!userId) return false;
    const res = await request('GET');
    if (res.status !== 200 || !res.data) return false;
    const remote = res.data.collections || [];
    const remoteVersion = res.data.version || 0;

    let state = getSyncState();
    // Données locales d'un autre compte : on les écarte, on ne les envoie jamais
    if (state.userId && state.userId !== userId) {
      saveCollections(remote, { fromSync: true });
      setSyncState({ userId, version: remoteVersion, dirty: false });
      return true;
    }

    const local = getCollections();
    // Première synchronisation de ce compte : les collections locales existantes sont migrées
    if (!state.userId) {
      setSyncState({ userId, version: remoteVersion, dirty: local.length > 0 });
      state = getSyncState();
      if (local.length > 0) {
        const merged = mergeCollections(local, remote);
        saveCollections(merged, { fromSync: true });
        return pushCollections();
      }
    }

    if (state.dirty) {
      const merged = mergeCollections(local, remote);
      saveCollections(merged, { fromSync: true });
      setSyncState({ version: remoteVersion });
      return pushCollections();
    }

    if (remoteVersion !== state.version || remote.length !== local.length) {
      saveCollections(remote, { fromSync: true });
      setSyncState({ userId, version: remoteVersion, dirty: false });
    }
    return true;
  } catch {
    return false;
  }
}

/**
 * Démarre la synchronisation : récupération initiale, envoi après chaque modification,
 * récupération au retour sur l'application. Renvoie une fonction d'arrêt.
 */
export function startCollectionsSync() {
  if (typeof window === 'undefined') return () => {};
  let timer = null;
  let lastPull = 0;

  const schedulePush = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (getSyncState().dirty) pushCollections();
    }, PUSH_DEBOUNCE_MS);
  };
  const onChanged = () => {
    if (getSyncState().dirty) schedulePush();
  };
  const pullNow = () => {
    lastPull = Date.now();
    return pullCollections();
  };
  const onVisible = () => {
    if (document.visibilityState !== 'visible') return;
    if (Date.now() - lastPull < FOCUS_PULL_MIN_INTERVAL_MS) return;
    pullNow();
  };

  window.addEventListener(COLLECTIONS_CHANGED_EVENT, onChanged);
  document.addEventListener('visibilitychange', onVisible);
  pullNow();

  return () => {
    clearTimeout(timer);
    window.removeEventListener(COLLECTIONS_CHANGED_EVENT, onChanged);
    document.removeEventListener('visibilitychange', onVisible);
  };
}
