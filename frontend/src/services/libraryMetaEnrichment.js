/**
 * Précharge résumé, pages et couvertures manquantes en arrière-plan.
 * Couvertures : priorité à la recherche navigateur (fiable), puis persist backend.
 */
import { API_BASE_URL } from '../config/environment';
import { isUsableSynopsis } from '../utils/synopsisQuality';
import { evaluateOwnedSeriesForDisplay } from '../utils/seriesAttribution';
import { isMobileClient } from '../utils/device';
import {
  isGoogleBooksCoverUrl,
  isUsableCoverUrl,
  normalizeCoverUrl,
} from '../utils/helpers';
import { searchCoverInBrowser } from '../utils/coverClientSearch';
import { bookService } from './bookService';
import { updateSeriesLibraryEntry } from './seriesLibraryService';

function enrichmentLimits() {
  const mobile = isMobileClient();
  return {
    concurrency: 1,
    startDelayMs: mobile ? 3000 : 1500,
    betweenMs: mobile ? 800 : 500,
    maxPerRun: mobile ? 20 : 60,
    maxRounds: mobile ? 3 : 5,
  };
}

const succeeded = new Set();
const failedAt = new Map();
const FAIL_COOLDOWN_MS = 90 * 1000;
let running = false;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function needsCover(url) {
  if (!isUsableCoverUrl(normalizeCoverUrl(url) || url)) return true;
  // Google Books = souvent le faux « image not available »
  if (isGoogleBooksCoverUrl(url)) return true;
  return false;
}

function canAttempt(key) {
  if (succeeded.has(key)) return false;
  const t = failedAt.get(key);
  if (t && Date.now() - t < FAIL_COOLDOWN_MS) return false;
  return true;
}

function markSuccess(key) {
  succeeded.add(key);
  failedAt.delete(key);
}

function markFail(key) {
  failedAt.set(key, Date.now());
}

function isRealLibraryId(id) {
  if (!id || typeof id !== 'string') return false;
  return !(
    id.startsWith('ol_') ||
    id.startsWith('wd_') ||
    id.startsWith('series_') ||
    id.startsWith('library-series-') ||
    id.startsWith('jikan_') ||
    id.startsWith('gbooks_')
  );
}

function collectCoverCandidates(books, seriesLibrary) {
  const out = [];
  const seen = new Set();

  for (const b of books || []) {
    if (!b?.id || b.isFromOpenLibrary || b.isSeriesCard) continue;
    if (!needsCover(b.cover_url)) continue;
    if (!isRealLibraryId(b.id)) continue;
    const key = `book-cover:${b.id}`;
    if (!canAttempt(key) || seen.has(key)) continue;
    seen.add(key);
    out.push({
      key,
      kind: 'book-cover',
      id: b.id,
      title: b.title || b.display_title || '',
      author: b.author || '',
      isbn: b.isbn,
      ol_key: b.ol_key,
      item: b,
    });
  }

  for (const s of seriesLibrary || []) {
    if (!s?.id || !isRealLibraryId(s.id)) continue;
    if (!needsCover(s.cover_image_url || s.cover_url)) continue;
    const key = `series-cover:${s.id}`;
    if (!canAttempt(key) || seen.has(key)) continue;
    seen.add(key);
    out.push({
      key,
      kind: 'series-cover',
      id: s.id,
      title: s.series_name || s.name || '',
      author: (Array.isArray(s.authors) && s.authors[0]) || s.author || '',
      isbn: s.isbn,
      ol_key: s.ol_key,
      item: s,
    });
  }

  return out;
}

function collectMetaCandidates(books, seriesLibrary) {
  const out = [];
  for (const b of books || []) {
    if (!b?.id || b.isFromOpenLibrary || b.isSeriesCard || b.isDemotedSeries) continue;
    if (!isRealLibraryId(b.id)) continue;
    const needsDesc = !isUsableSynopsis(b.description);
    const needsPages = !(b.total_pages > 0);
    if (!needsDesc && !needsPages) continue;
    const key = `book-meta:${b.id}`;
    if (!canAttempt(key)) continue;
    out.push({
      key,
      kind: 'book-meta',
      id: b.id,
      title: b.title || '',
      author: b.author || '',
      isbn: b.isbn,
      ol_key: b.ol_key,
      needsDesc,
      needsPages,
    });
  }
  for (const s of seriesLibrary || []) {
    if (!s?.id || !isRealLibraryId(s.id)) continue;
    if (!evaluateOwnedSeriesForDisplay(s).demote) continue;
    const needsDesc = !isUsableSynopsis(s.description_fr);
    const needsPages = !(s.total_pages > 0);
    if (!needsDesc && !needsPages) continue;
    const key = `demoted:${s.id}`;
    if (!canAttempt(key)) continue;
    out.push({
      key,
      kind: 'demoted',
      id: s.id,
      title: s.series_name || s.name || '',
      author: (Array.isArray(s.authors) && s.authors[0]) || s.author || '',
      isbn: s.isbn,
      ol_key: s.ol_key,
      needsDesc,
      needsPages,
    });
  }
  return out;
}

async function fetchJson(url, options = {}, timeoutMs = 12000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(url, { ...options, cache: 'no-store', signal: ctrl.signal });
    if (!r.ok) return null;
    return r.json();
  } catch (_) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

async function resolveSynopsis(item) {
  const params = new URLSearchParams({
    title: item.title || '',
    author: item.author && item.author !== 'Auteur inconnu' ? item.author : '',
    include_pages: 'false',
  });
  if (item.isbn) params.set('isbn', item.isbn);
  if (item.ol_key) params.set('ol_key', item.ol_key);
  return fetchJson(`${API_BASE_URL}/api/books/resolve-synopsis?${params}`, {
    headers: authHeaders(),
  });
}

async function resolvePages(item) {
  const params = new URLSearchParams({
    title: item.title || '',
    author: item.author && item.author !== 'Auteur inconnu' ? item.author : '',
  });
  if (item.isbn) params.set('isbn', item.isbn);
  if (item.ol_key) params.set('ol_key', item.ol_key);
  return fetchJson(`${API_BASE_URL}/api/books/resolve-pages?${params}`, {
    headers: authHeaders(),
  });
}

async function persistCoverIfPossible(item, cover) {
  if (!isUsableCoverUrl(cover) || !localStorage.getItem('token')) return;
  try {
    if (item.isSeriesCard || item.isOwnedSeries || item.series_name) {
      const sid = item.librarySeriesId || item.seriesLibraryId || item.id;
      if (isRealLibraryId(sid)) {
        await updateSeriesLibraryEntry(
          sid,
          { cover_image_url: cover },
          localStorage.getItem('token')
        );
      }
      return;
    }
    if (isRealLibraryId(item.id)) {
      await bookService.updateBook(item.id, { cover_url: cover });
    }
  } catch (_) {
    /* ignore */
  }
}

async function enrichBookCover(item, { setBooks }) {
  const title = item.title || '';
  const author = item.author || '';
  // Navigateur d'abord (évite de saturer le backend + OL sync)
  let cover = await searchCoverInBrowser(title, author, {
    isbn: item.isbn || item.item?.isbn,
    ol_key: item.ol_key || item.item?.ol_key,
  });
  if (!isUsableCoverUrl(cover) && localStorage.getItem('token')) {
    const data = await fetchJson(
      `${API_BASE_URL}/api/books/${item.id}/cover`,
      { method: 'POST', headers: authHeaders() },
      8000
    );
    cover = normalizeCoverUrl(data?.cover_url);
  }
  if (!isUsableCoverUrl(cover)) return null;
  await persistCoverIfPossible({ id: item.id }, cover);
  if (typeof setBooks === 'function') {
    setBooks((prev) =>
      (prev || []).map((b) => (b.id === item.id ? { ...b, cover_url: cover } : b))
    );
  }
  return cover;
}

async function enrichSeriesCover(item, { setBooks, setUserSeriesLibrary }) {
  const title = item.title || '';
  const author = item.author || '';
  let cover = await searchCoverInBrowser(title, author, {
    isbn: item.isbn || item.item?.isbn,
    ol_key: item.ol_key || item.item?.ol_key,
  });
  if (!isUsableCoverUrl(cover) && localStorage.getItem('token')) {
    const data = await fetchJson(
      `${API_BASE_URL}/api/series/library/${item.id}/cover`,
      { method: 'POST', headers: authHeaders() },
      8000
    );
    cover = normalizeCoverUrl(data?.cover_url);
  }
  if (!isUsableCoverUrl(cover)) return null;
  await persistCoverIfPossible(
    { id: item.id, series_name: title, isOwnedSeries: true },
    cover
  );
  if (typeof setUserSeriesLibrary === 'function') {
    setUserSeriesLibrary((prev) =>
      (prev || []).map((s) =>
        s.id === item.id
          ? { ...s, cover_image_url: cover, cover_url: cover }
          : s
      )
    );
  }
  if (typeof setBooks === 'function') {
    setBooks((prev) =>
      (prev || []).map((b) => {
        if (!b.isSeriesCard) return b;
        const sid = b.librarySeriesId || b.seriesLibraryId || b.id;
        if (sid !== item.id) return b;
        return { ...b, cover_url: cover, cover_image_url: cover };
      })
    );
  }
  return cover;
}

async function enrichBookMeta(item, { setBooks }) {
  let description = null;
  let pages = null;
  let needsDesc = item.needsDesc;
  let needsPages = item.needsPages;

  const syn = await fetchJson(
    `${API_BASE_URL}/api/books/${item.id}/synopsis?persist=true`,
    { headers: authHeaders() },
    10000
  );
  if (syn) {
    if (needsDesc && isUsableSynopsis(syn.description)) {
      description = syn.description.trim();
      needsDesc = false;
    }
    const n = parseInt(syn.pages, 10);
    if (needsPages && n > 0) {
      pages = n;
      needsPages = false;
    }
  }

  if (needsDesc && (item.title || '').trim()) {
    const data = await resolveSynopsis(item);
    if (isUsableSynopsis(data?.description)) {
      description = data.description.trim();
    }
  }

  if (needsPages && (item.title || '').trim()) {
    const data = await resolvePages(item);
    const n = parseInt(data?.pages, 10);
    if (n > 0) pages = n;
  }

  if (!description && !(pages > 0)) return false;
  const patch = {};
  if (description) patch.description = description;
  if (pages > 0) patch.total_pages = pages;
  try {
    await bookService.updateBook(item.id, patch);
  } catch (_) {
    /* ignore */
  }
  if (typeof setBooks === 'function') {
    setBooks((prev) =>
      (prev || []).map((b) =>
        b.id === item.id
          ? {
              ...b,
              ...(description ? { description } : {}),
              ...(pages > 0 ? { total_pages: pages } : {}),
            }
          : b
      )
    );
  }
  return true;
}

async function enrichDemoted(item, { setUserSeriesLibrary }) {
  let description = null;
  let pages = null;
  if (item.needsDesc && (item.title || '').trim()) {
    const data = await resolveSynopsis(item);
    if (isUsableSynopsis(data?.description)) description = data.description.trim();
  }
  if (item.needsPages && (item.title || '').trim()) {
    const data = await resolvePages(item);
    const n = parseInt(data?.pages, 10);
    if (n > 0) pages = n;
  }
  const patch = {};
  if (description) patch.description_fr = description;
  if (pages > 0) patch.total_pages = pages;
  if (!Object.keys(patch).length) return false;
  const token = localStorage.getItem('token');
  if (!token) return false;
  await updateSeriesLibraryEntry(item.id, patch, token);
  if (typeof setUserSeriesLibrary === 'function') {
    setUserSeriesLibrary((prev) =>
      (prev || []).map((s) =>
        s.id === item.id
          ? {
              ...s,
              ...(description ? { description_fr: description } : {}),
              ...(pages > 0 ? { total_pages: pages } : {}),
            }
          : s
      )
    );
  }
  return true;
}

async function runQueue(candidates, workerFn, limits) {
  if (!candidates.length) return;
  let cursor = 0;
  const worker = async () => {
    while (cursor < candidates.length) {
      const idx = cursor;
      cursor += 1;
      const item = candidates[idx];
      try {
        const ok = await workerFn(item);
        if (ok) markSuccess(item.key);
        else markFail(item.key);
      } catch (_) {
        markFail(item.key);
      }
      await sleep(limits.betweenMs);
    }
  };
  await Promise.all(
    Array.from(
      { length: Math.min(limits.concurrency, candidates.length) },
      () => worker()
    )
  );
}

export async function enrichLibraryMetadata({
  books,
  userSeriesLibrary,
  setBooks,
  setUserSeriesLibrary,
} = {}) {
  if (running) return;
  if (!localStorage.getItem('token')) return;

  const limits = enrichmentLimits();
  running = true;
  try {
    for (let round = 0; round < limits.maxRounds; round += 1) {
      const covers = collectCoverCandidates(books, userSeriesLibrary).slice(
        0,
        limits.maxPerRun
      );
      if (!covers.length) break;
      await runQueue(
        covers,
        async (item) => {
          if (item.kind === 'series-cover') {
            return !!(await enrichSeriesCover(item, {
              setBooks,
              setUserSeriesLibrary,
            }));
          }
          return !!(await enrichBookCover(item, { setBooks }));
        },
        limits
      );
    }

    const meta = collectMetaCandidates(books, userSeriesLibrary).slice(0, 15);
    await runQueue(
      meta,
      async (item) => {
        if (item.kind === 'demoted') {
          return enrichDemoted(item, { setUserSeriesLibrary });
        }
        return enrichBookMeta(item, { setBooks });
      },
      { ...limits, concurrency: 1 }
    );
  } finally {
    running = false;
  }
}

/** File visible : un peu plus large, OL/Wiki en priorité */
const visibleCoverQueue = [];
let visibleCoverActive = 0;
const VISIBLE_COVER_MAX = 6;
const visibleCoverInflight = new Map();

function pumpVisibleCoverQueue() {
  while (visibleCoverActive < VISIBLE_COVER_MAX && visibleCoverQueue.length) {
    const job = visibleCoverQueue.shift();
    visibleCoverActive += 1;
    Promise.resolve()
      .then(job.run)
      .then(job.resolve, job.reject)
      .finally(() => {
        visibleCoverActive -= 1;
        if (job.cacheKey) visibleCoverInflight.delete(job.cacheKey);
        pumpVisibleCoverQueue();
      });
  }
}

function enqueueVisibleCover(cacheKey, run) {
  if (visibleCoverInflight.has(cacheKey)) {
    return visibleCoverInflight.get(cacheKey);
  }
  const p = new Promise((resolve, reject) => {
    visibleCoverQueue.push({ cacheKey, run, resolve, reject });
    pumpVisibleCoverQueue();
  });
  visibleCoverInflight.set(cacheKey, p);
  return p;
}

/**
 * Résout la couverture d'une vignette visible.
 * Navigateur d'abord (vraies images), puis persist.
 */
export async function resolveCoverForVisibleItem(item) {
  if (!item) return null;

  const cacheKey = item.isSeriesCard || item.isOwnedSeries
    ? `s:${item.librarySeriesId || item.seriesLibraryId || item.id}`
    : `b:${item.id}`;

  return enqueueVisibleCover(cacheKey, async () => {
    const title =
      item.name || item.title || item.display_title || item.series_name || '';
    const author = item.author || '';

    // 1) Recherche navigateur (OL work/ISBN puis GB, file anti-429)
    let cover = await searchCoverInBrowser(title, author, {
      isbn: item.isbn,
      ol_key: item.ol_key || item.open_library_key,
    });

    // 2) Essai via un tome enfant (cartes série regroupées)
    if (!isUsableCoverUrl(cover) && Array.isArray(item.books)) {
      for (const b of item.books.slice(0, 3)) {
        if (!b?.title && !b?.volume_title) continue;
        cover = await searchCoverInBrowser(
          b.title || b.volume_title,
          b.author || author,
          { isbn: b.isbn, ol_key: b.ol_key }
        );
        if (isUsableCoverUrl(cover)) break;
      }
    }

    // 3) Backend en dernier recours
    if (!isUsableCoverUrl(cover) && localStorage.getItem('token')) {
      if (
        (item.isSeriesCard || item.isOwnedSeries) &&
        isRealLibraryId(item.librarySeriesId || item.seriesLibraryId || item.id)
      ) {
        const sid = item.librarySeriesId || item.seriesLibraryId || item.id;
        const data = await fetchJson(
          `${API_BASE_URL}/api/series/library/${sid}/cover`,
          { method: 'POST', headers: authHeaders() },
          8000
        );
        cover = normalizeCoverUrl(data?.cover_url);
      } else if (isRealLibraryId(item.id)) {
        const data = await fetchJson(
          `${API_BASE_URL}/api/books/${item.id}/cover`,
          { method: 'POST', headers: authHeaders() },
          8000
        );
        cover = normalizeCoverUrl(data?.cover_url);
      }
    }

    if (!isUsableCoverUrl(cover)) return null;
    persistCoverIfPossible(item, cover).catch(() => {});
    return cover;
  });
}

export function scheduleLibraryMetaEnrichment(args, delayMs) {
  const wait = delayMs ?? enrichmentLimits().startDelayMs;
  const timer = setTimeout(() => {
    enrichLibraryMetadata(args).catch(() => {});
  }, wait);
  return () => clearTimeout(timer);
}

export default enrichLibraryMetadata;
