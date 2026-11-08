/**
 * File d'attente des écritures hors ligne.
 *
 * Ajouts, changements de statut, tomes lus et notes faits sans réseau sont
 * enregistrés sur l'appareil, appliqués tout de suite au cache local, puis
 * envoyés dès que la connexion revient.
 */
import logger from './logger';
import {
  loadLibraryCache,
  saveLibraryCache,
  loadSeriesCache,
  saveSeriesCache,
  isLikelyOffline,
} from './offlineLibraryCache';

export const QUEUE_KEY = 'booktime_offline_queue_v1';
export const QUEUE_CHANGED_EVENT = 'booktime:offline-queue';
export const LIBRARY_CHANGED_EVENT = 'booktime:offline-library';

const MAX_JOBS = 200;
const MAX_RETRIES = 8;

function safeParse(raw, fallback) {
  try {
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function currentUserId() {
  try {
    return JSON.parse(localStorage.getItem('user'))?.id || null;
  } catch {
    return null;
  }
}

function emit(name, detail) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

function newId(prefix) {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `${prefix}_${crypto.randomUUID()}`;
  }
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function loadState() {
  if (typeof window === 'undefined') return { userId: null, jobs: [] };
  const state = safeParse(localStorage.getItem(QUEUE_KEY), null);
  if (!state || !Array.isArray(state.jobs)) return { userId: currentUserId(), jobs: [] };
  return { userId: state.userId || currentUserId(), jobs: state.jobs };
}

function saveState(state) {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(
      QUEUE_KEY,
      JSON.stringify({
        userId: state.userId || currentUserId(),
        jobs: (state.jobs || []).slice(-MAX_JOBS),
      })
    );
  } catch {
    /* quota / mode privé */
  }
  emit(QUEUE_CHANGED_EVENT, { count: (state.jobs || []).length });
}

export function getQueueJobs() {
  return loadState().jobs;
}

export function getPendingCount() {
  return loadState().jobs.length;
}

export function mergePendingBooks(serverBooks = []) {
  const jobs = loadState().jobs;
  if (!jobs.length) return serverBooks;
  const byId = new Map((serverBooks || []).map((b) => [b.id, { ...b }]));
  jobs.forEach((job) => {
    if (job.type === 'createBook') {
      const id = job.clientId;
      if (!id) return;
      byId.set(id, { ...job.payload, id, _pendingSync: true });
    } else if (job.type === 'updateBook' && job.entityId) {
      const current = byId.get(job.entityId) || { id: job.entityId };
      byId.set(job.entityId, { ...current, ...job.payload, _pendingSync: true });
    } else if (job.type === 'deleteBook' && job.entityId) {
      byId.delete(job.entityId);
    }
  });
  return Array.from(byId.values());
}

export function mergePendingSeries(serverSeries = []) {
  const jobs = loadState().jobs;
  if (!jobs.length) return serverSeries;
  const byId = new Map((serverSeries || []).map((s) => [s.id, { ...s }]));
  jobs.forEach((job) => {
    if (job.type === 'createSeries') {
      const id = job.clientId;
      if (!id) return;
      byId.set(id, {
        ...job.payload,
        id,
        series_name: job.payload.series_name || job.payload.name,
        _pendingSync: true,
      });
    } else if (job.type === 'updateSeries' && job.entityId) {
      const current = byId.get(job.entityId) || { id: job.entityId };
      byId.set(job.entityId, { ...current, ...job.payload, _pendingSync: true });
    } else if (job.type === 'toggleVolume' && job.entityId) {
      const current = byId.get(job.entityId);
      if (!current || !Array.isArray(current.volumes)) return;
      const volumes = current.volumes.map((vol) =>
        Number(vol.volume_number) === Number(job.payload.volumeNumber)
          ? {
              ...vol,
              is_read: job.payload.isRead,
              date_read: job.payload.isRead ? new Date().toISOString() : null,
            }
          : vol
      );
      byId.set(job.entityId, { ...current, volumes, _pendingSync: true });
    } else if (job.type === 'deleteSeries' && job.entityId) {
      byId.delete(job.entityId);
    }
  });
  return Array.from(byId.values());
}

export function isOfflineClientId(id) {
  return typeof id === 'string' && (id.startsWith('offline_book_') || id.startsWith('offline_series_'));
}

/** Erreur réseau (pas de réponse HTTP) — on peut mettre en file. */
export function isNetworkFailure(error) {
  if (!error) return false;
  if (error.response) return false;
  const status = error.status;
  if (typeof status === 'number' && status > 0) return false;
  const code = error.code || error.cause?.code || '';
  const message = String(error.message || error);
  return (
    isLikelyOffline() ||
    code === 'ERR_NETWORK' ||
    code === 'ECONNABORTED' ||
    /network error|failed to fetch|load failed|timeout|aborterror|the internet connection appears to be offline/i.test(
      message
    )
  );
}

export function shouldEnqueueWrite(error) {
  if (isLikelyOffline()) return true;
  return isNetworkFailure(error);
}

function patchBooks(mutator) {
  const cached = loadLibraryCache({})?.books;
  const books = Array.isArray(cached) ? [...cached] : [];
  const next = mutator(books);
  if (!Array.isArray(next)) return;
  saveLibraryCache(next, {}, { force: true });
  emit(LIBRARY_CHANGED_EVENT, { kind: 'books' });
}

function patchSeries(mutator) {
  const cached = loadSeriesCache()?.series;
  const series = Array.isArray(cached) ? [...cached] : [];
  const next = mutator(series);
  if (!Array.isArray(next)) return;
  saveSeriesCache(next, { force: true });
  emit(LIBRARY_CHANGED_EVENT, { kind: 'series' });
}

function mergeJob(jobs, job) {
  if (job.type === 'updateBook') {
    const create = jobs.find((j) => j.type === 'createBook' && j.clientId === job.entityId);
    if (create) {
      create.payload = { ...create.payload, ...job.payload };
      return jobs;
    }
    const existing = jobs.find((j) => j.type === 'updateBook' && j.entityId === job.entityId);
    if (existing) {
      existing.payload = { ...existing.payload, ...job.payload };
      existing.updatedAt = Date.now();
      return jobs;
    }
  }
  if (job.type === 'updateSeries') {
    const create = jobs.find((j) => j.type === 'createSeries' && j.clientId === job.entityId);
    if (create) {
      create.payload = { ...create.payload, ...job.payload };
      return jobs;
    }
    const existing = jobs.find((j) => j.type === 'updateSeries' && j.entityId === job.entityId);
    if (existing) {
      existing.payload = { ...existing.payload, ...job.payload };
      existing.updatedAt = Date.now();
      return jobs;
    }
  }
  if (job.type === 'toggleVolume') {
    const create = jobs.find((j) => j.type === 'createSeries' && j.clientId === job.entityId);
    if (create && Array.isArray(create.payload?.volumes)) {
      create.payload.volumes = create.payload.volumes.map((vol) =>
        Number(vol.volume_number) === Number(job.payload.volumeNumber)
          ? {
              ...vol,
              is_read: job.payload.isRead,
              date_read: job.payload.isRead ? new Date().toISOString() : null,
            }
          : vol
      );
      return jobs;
    }
    const existing = jobs.find(
      (j) =>
        j.type === 'toggleVolume' &&
        j.entityId === job.entityId &&
        Number(j.payload.volumeNumber) === Number(job.payload.volumeNumber)
    );
    if (existing) {
      existing.payload = { ...existing.payload, ...job.payload };
      existing.updatedAt = Date.now();
      return jobs;
    }
  }
  if (job.type === 'deleteBook') {
    const createIdx = jobs.findIndex((j) => j.type === 'createBook' && j.clientId === job.entityId);
    if (createIdx >= 0) {
      const next = jobs.filter((_, i) => i !== createIdx);
      return next.filter((j) => !(j.type === 'updateBook' && j.entityId === job.entityId));
    }
    return [...jobs.filter((j) => !(j.type === 'updateBook' && j.entityId === job.entityId)), job];
  }
  if (job.type === 'deleteSeries') {
    const createIdx = jobs.findIndex((j) => j.type === 'createSeries' && j.clientId === job.entityId);
    if (createIdx >= 0) {
      return jobs.filter(
        (j, i) =>
          i !== createIdx &&
          !(j.entityId === job.entityId && (j.type === 'updateSeries' || j.type === 'toggleVolume'))
      );
    }
    return [
      ...jobs.filter(
        (j) => !(j.entityId === job.entityId && (j.type === 'updateSeries' || j.type === 'toggleVolume'))
      ),
      job,
    ];
  }
  return [...jobs, job];
}

function enqueue(job) {
  const state = loadState();
  const userId = currentUserId();
  if (state.userId && userId && state.userId !== userId) {
    // Autre compte : on ne mélange pas les files. La précédente reste jusqu'à reconnexion.
    logger.warn('[offline-queue] File d’un autre compte ignorée pour l’écriture');
  }
  const nextJob = {
    id: newId('job'),
    createdAt: Date.now(),
    updatedAt: Date.now(),
    retries: 0,
    ...job,
  };
  const owner = state.userId && userId && state.userId !== userId ? userId : state.userId || userId;
  const jobs = state.userId && userId && state.userId !== userId ? [nextJob] : mergeJob(state.jobs, nextJob);
  saveState({ userId: owner, jobs });
  return nextJob;
}

function remapJobs(jobs, fromId, toId) {
  return jobs.map((job) => {
    if (job.entityId === fromId) return { ...job, entityId: toId };
    if (job.clientId === fromId) return { ...job, clientId: toId };
    return job;
  });
}

export function enqueueCreateBook(bookData) {
  const clientId = newId('offline_book');
  const local = {
    ...bookData,
    id: clientId,
    _pendingSync: true,
    date_added: bookData.date_added || new Date().toISOString(),
  };
  enqueue({ type: 'createBook', entityId: clientId, clientId, payload: bookData });
  patchBooks((books) => [...books.filter((b) => b.id !== clientId), local]);
  return local;
}

export function enqueueUpdateBook(id, updateData) {
  enqueue({ type: 'updateBook', entityId: id, payload: updateData });
  let updated = null;
  patchBooks((books) =>
    books.map((b) => {
      if (b.id !== id) return b;
      updated = { ...b, ...updateData, _pendingSync: true };
      return updated;
    })
  );
  return updated || { id, ...updateData, _pendingSync: true };
}

export function enqueueDeleteBook(id) {
  enqueue({ type: 'deleteBook', entityId: id, payload: {} });
  patchBooks((books) => books.filter((b) => b.id !== id));
  return { id, deleted: true, _pendingSync: true };
}

export function enqueueCreateSeries(seriesData) {
  const clientId = newId('offline_series');
  const local = {
    ...seriesData,
    id: clientId,
    series_name: seriesData.series_name || seriesData.name,
    _pendingSync: true,
    success: true,
  };
  enqueue({ type: 'createSeries', entityId: clientId, clientId, payload: seriesData });
  patchSeries((series) => [...series.filter((s) => s.id !== clientId), local]);
  return local;
}

export function enqueueUpdateSeries(id, data) {
  enqueue({ type: 'updateSeries', entityId: id, payload: data });
  let updated = null;
  patchSeries((series) =>
    series.map((s) => {
      if (s.id !== id) return s;
      updated = { ...s, ...data, _pendingSync: true, success: true };
      return updated;
    })
  );
  return updated || { id, ...data, success: true, _pendingSync: true };
}

export function enqueueToggleVolume(seriesId, volumeNumber, isRead) {
  enqueue({
    type: 'toggleVolume',
    entityId: seriesId,
    payload: { volumeNumber, isRead },
  });
  let updated = null;
  patchSeries((series) =>
    series.map((s) => {
      if (s.id !== seriesId) return s;
      const volumes = Array.isArray(s.volumes)
        ? s.volumes.map((vol) =>
            Number(vol.volume_number) === Number(volumeNumber)
              ? {
                  ...vol,
                  is_read: isRead,
                  date_read: isRead ? new Date().toISOString() : null,
                }
              : vol
          )
        : [];
      const readCount = volumes.filter((v) => v.is_read).length;
      const total = volumes.length || s.total_volumes || 0;
      updated = {
        ...s,
        volumes,
        completion_percentage: total ? Math.round((readCount / total) * 100) : s.completion_percentage,
        _pendingSync: true,
        success: true,
      };
      return updated;
    })
  );
  return (
    updated || {
      success: true,
      _pendingSync: true,
      series_id: seriesId,
      volume_number: volumeNumber,
      is_read: isRead,
    }
  );
}

export function enqueueDeleteSeries(id) {
  enqueue({ type: 'deleteSeries', entityId: id, payload: {} });
  patchSeries((series) => series.filter((s) => s.id !== id));
  return { id, success: true, deleted: true, _pendingSync: true };
}

function httpError(response, body) {
  const err = new Error(`Erreur ${response.status}: ${body || response.statusText}`);
  err.status = response.status;
  err.response = response;
  return err;
}

async function sendJob(job, token) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
  const { API_BASE_URL } = await import('../config/environment');

  if (job.type === 'createBook') {
    const res = await fetch(`${API_BASE_URL}/api/books`, {
      method: 'POST',
      headers,
      body: JSON.stringify(job.payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw httpError(res, typeof data.detail === 'string' ? data.detail : JSON.stringify(data));
    return data;
  }
  if (job.type === 'updateBook') {
    const res = await fetch(`${API_BASE_URL}/api/books/${encodeURIComponent(job.entityId)}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(job.payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw httpError(res, typeof data.detail === 'string' ? data.detail : JSON.stringify(data));
    return data;
  }
  if (job.type === 'deleteBook') {
    const res = await fetch(`${API_BASE_URL}/api/books/${encodeURIComponent(job.entityId)}`, {
      method: 'DELETE',
      headers,
    });
    if (!res.ok && res.status !== 404) {
      const text = await res.text().catch(() => '');
      throw httpError(res, text);
    }
    return { deleted: true };
  }
  if (job.type === 'createSeries') {
    const res = await fetch(`${API_BASE_URL}/api/series/library`, {
      method: 'POST',
      headers,
      body: JSON.stringify(job.payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw httpError(res, await safeBody(data));
    return data;
  }
  if (job.type === 'updateSeries') {
    const res = await fetch(`${API_BASE_URL}/api/series/library/${encodeURIComponent(job.entityId)}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(job.payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw httpError(res, await safeBody(data));
    return data;
  }
  if (job.type === 'toggleVolume') {
    const { volumeNumber, isRead } = job.payload;
    const res = await fetch(
      `${API_BASE_URL}/api/series/library/${encodeURIComponent(job.entityId)}/volume/${encodeURIComponent(
        volumeNumber
      )}?is_read=${isRead}`,
      { method: 'PUT', headers: { Authorization: `Bearer ${token}` } }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw httpError(res, await safeBody(data));
    return data;
  }
  if (job.type === 'deleteSeries') {
    const res = await fetch(`${API_BASE_URL}/api/series/library/${encodeURIComponent(job.entityId)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok && res.status !== 404) {
      const text = await res.text().catch(() => '');
      throw httpError(res, text);
    }
    return { success: true };
  }
  throw new Error(`Type de job inconnu: ${job.type}`);
}

function safeBody(data) {
  if (!data) return '';
  if (typeof data.detail === 'string') return data.detail;
  try {
    return JSON.stringify(data);
  } catch {
    return '';
  }
}

function applyRemoteBook(clientId, remote) {
  const remoteId = remote?.id || remote?.book?.id;
  patchBooks((books) => {
    const withoutPending = books.filter((b) => b.id !== clientId && b.id !== remoteId);
    const local = books.find((b) => b.id === clientId) || {};
    if (!remoteId) return withoutPending;
    return [...withoutPending, { ...local, ...remote, id: remoteId, _pendingSync: undefined }];
  });
}

function applyRemoteSeries(clientId, remote) {
  const remoteId = remote?.id || remote?.series?.id || remote?.series_id;
  patchSeries((series) => {
    const withoutPending = series.filter((s) => s.id !== clientId && s.id !== remoteId);
    const local = series.find((s) => s.id === clientId) || {};
    if (!remoteId) return withoutPending;
    return [
      ...withoutPending,
      {
        ...local,
        ...remote,
        ...(remote.series && typeof remote.series === 'object' ? remote.series : {}),
        id: remoteId,
        _pendingSync: undefined,
      },
    ];
  });
}

let flushing = false;

export async function flushOfflineQueue() {
  if (flushing) return { flushed: 0, remaining: getPendingCount() };
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    return { flushed: 0, remaining: getPendingCount(), offline: true };
  }
  const { getToken } = await import('../services/apiClient');
  const token = getToken();
  if (!token) return { flushed: 0, remaining: getPendingCount(), skipped: 'no-token' };

  const userId = currentUserId();
  const state = loadState();
  if (state.userId && userId && state.userId !== userId) {
    return { flushed: 0, remaining: state.jobs.length, skipped: 'other-user' };
  }

  flushing = true;
  let flushed = 0;
  try {
    let jobs = [...state.jobs];
    while (jobs.length) {
      const job = jobs[0];
      try {
        const result = await sendJob(job, token);
        if (job.type === 'createBook') {
          const remoteId = result?.id || result?.book?.id;
          if (remoteId && job.clientId && remoteId !== job.clientId) {
            applyRemoteBook(job.clientId, result);
            jobs = remapJobs(jobs.slice(1), job.clientId, remoteId);
          } else {
            applyRemoteBook(job.clientId, result);
            jobs = jobs.slice(1);
          }
        } else if (job.type === 'createSeries') {
          const remoteId = result?.id || result?.series?.id || result?.series_id;
          if (remoteId && job.clientId && remoteId !== job.clientId) {
            applyRemoteSeries(job.clientId, result);
            jobs = remapJobs(jobs.slice(1), job.clientId, remoteId);
          } else {
            applyRemoteSeries(job.clientId, result);
            jobs = jobs.slice(1);
          }
        } else {
          jobs = jobs.slice(1);
        }
        flushed += 1;
        saveState({ userId: state.userId || userId, jobs });
      } catch (error) {
        const status = error.status || error.response?.status;
        if (status === 401) {
          logger.warn('[offline-queue] Session expirée, file conservée');
          break;
        }
        if (status === 404 && (job.type === 'updateBook' || job.type === 'updateSeries' || job.type === 'toggleVolume' || job.type === 'deleteBook' || job.type === 'deleteSeries')) {
          jobs = jobs.slice(1);
          saveState({ userId: state.userId || userId, jobs });
          continue;
        }
        if (status && status >= 400 && status < 500 && status !== 408 && status !== 429) {
          logger.warn('[offline-queue] Job abandonné (erreur client):', job.type, status);
          jobs = jobs.slice(1);
          saveState({ userId: state.userId || userId, jobs });
          continue;
        }
        job.retries = (job.retries || 0) + 1;
        job.lastError = String(error.message || error);
        if (job.retries >= MAX_RETRIES) {
          logger.warn('[offline-queue] Job abandonné après trop d’essais:', job.type);
          jobs = jobs.slice(1);
        } else {
          jobs[0] = job;
          saveState({ userId: state.userId || userId, jobs });
          break;
        }
        saveState({ userId: state.userId || userId, jobs });
      }
    }
  } finally {
    flushing = false;
  }
  if (flushed > 0) emit(LIBRARY_CHANGED_EVENT, { kind: 'flush' });
  return { flushed, remaining: getPendingCount() };
}

let started = false;

export function startOfflineWriteQueue() {
  if (typeof window === 'undefined') return () => {};
  const onOnline = () => {
    flushOfflineQueue().catch((err) => logger.warn('[offline-queue] flush:', err));
  };
  const onVisible = () => {
    if (!document.hidden) onOnline();
  };
  window.addEventListener('online', onOnline);
  document.addEventListener('visibilitychange', onVisible);
  onOnline();
  if (!started) started = true;
  return () => {
    window.removeEventListener('online', onOnline);
    document.removeEventListener('visibilitychange', onVisible);
  };
}

export function subscribeOfflineQueue(listener) {
  if (typeof window === 'undefined') return () => {};
  const handler = () => listener(getPendingCount());
  window.addEventListener(QUEUE_CHANGED_EVENT, handler);
  return () => window.removeEventListener(QUEUE_CHANGED_EVENT, handler);
}

export function clearOfflineQueue() {
  saveState({ userId: currentUserId(), jobs: [] });
}
