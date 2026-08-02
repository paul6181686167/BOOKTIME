/**
 * Précharge résumé + nb de pages en arrière-plan (sans ouvrir la fiche).
 * Cible : livres sans méta + séries rétrogradées (ex-vignettes 0/0).
 */
import { API_BASE_URL } from '../config/environment';
import { isUsableSynopsis } from '../utils/synopsisQuality';
import { evaluateOwnedSeriesForDisplay } from '../utils/seriesAttribution';
import { isMobileClient } from '../utils/device';
import { bookService } from './bookService';
import { updateSeriesLibraryEntry } from './seriesLibraryService';

function enrichmentLimits() {
  const mobile = isMobileClient();
  return {
    concurrency: mobile ? 1 : 2,
    startDelayMs: mobile ? 6000 : 1200,
    betweenMs: mobile ? 1000 : 350,
    maxPerRun: mobile ? 4 : 40,
  };
}

/** Évite de retenter le même item dans la session (succès ou échec). */
const attempted = new Set();
let running = false;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function collectCandidates(books, seriesLibrary) {
  const out = [];

  for (const b of books || []) {
    if (!b?.id || b.isSeriesCard || b.isDemotedSeries || b.isFromOpenLibrary) continue;
    const needsDesc = !isUsableSynopsis(b.description);
    const needsPages = !(b.total_pages > 0);
    if (!needsDesc && !needsPages) continue;
    const key = `book:${b.id}`;
    if (attempted.has(key)) continue;
    out.push({
      key,
      kind: 'book',
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
    if (!s?.id) continue;
    if (!evaluateOwnedSeriesForDisplay(s).demote) continue;
    const needsDesc = !isUsableSynopsis(s.description_fr);
    const needsPages = !(s.total_pages > 0);
    if (!needsDesc && !needsPages) continue;
    const key = `demoted:${s.id}`;
    if (attempted.has(key)) continue;
    out.push({
      key,
      kind: 'demoted',
      id: s.id,
      title: s.series_name || s.name || '',
      author:
        (Array.isArray(s.authors) && s.authors[0]) || s.author || '',
      isbn: s.isbn,
      ol_key: s.ol_key,
      needsDesc,
      needsPages,
    });
  }

  return out;
}

async function fetchJson(url, options = {}) {
  const r = await fetch(url, { ...options, cache: 'no-store' });
  if (!r.ok) return null;
  return r.json();
}

async function resolveSynopsis(item) {
  const params = new URLSearchParams({
    title: item.title || '',
    author:
      item.author && item.author !== 'Auteur inconnu' ? item.author : '',
    include_pages: 'false',
  });
  if (item.isbn) params.set('isbn', item.isbn);
  if (item.ol_key) params.set('ol_key', item.ol_key);
  return fetchJson(
    `${API_BASE_URL}/api/books/resolve-synopsis?${params}`,
    { headers: authHeaders() }
  );
}

async function resolvePages(item) {
  const params = new URLSearchParams({
    title: item.title || '',
    author:
      item.author && item.author !== 'Auteur inconnu' ? item.author : '',
  });
  if (item.isbn) params.set('isbn', item.isbn);
  if (item.ol_key) params.set('ol_key', item.ol_key);
  return fetchJson(
    `${API_BASE_URL}/api/books/resolve-pages?${params}`,
    { headers: authHeaders() }
  );
}

async function enrichBook(item, { setBooks }) {
  let description = null;
  let pages = null;
  let needsDesc = item.needsDesc;
  let needsPages = item.needsPages;

  const syn = await fetchJson(
    `${API_BASE_URL}/api/books/${item.id}/synopsis?persist=true`,
    { headers: authHeaders() }
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
      needsDesc = false;
    }
  }

  if (needsPages && (item.title || '').trim()) {
    const data = await resolvePages(item);
    const n = parseInt(data?.pages, 10);
    if (n > 0) {
      pages = n;
      needsPages = false;
    }
  }

  const patch = {};
  if (description) patch.description = description;
  if (pages > 0) patch.total_pages = pages;
  if (!Object.keys(patch).length) return;

  // synopsis?persist=true a déjà écrit en base ; re-PUT seulement si resolve-* a complété
  if (description || pages) {
    try {
      await bookService.updateBook(item.id, patch);
    } catch (_) {
      /* déjà éventuellement persisté via synopsis */
    }
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
}

async function enrichDemoted(item, { setUserSeriesLibrary }) {
  let description = null;
  let pages = null;

  if (item.needsDesc && (item.title || '').trim()) {
    const data = await resolveSynopsis(item);
    if (isUsableSynopsis(data?.description)) {
      description = data.description.trim();
    }
  }

  if (item.needsPages && (item.title || '').trim()) {
    const data = await resolvePages(item);
    const n = parseInt(data?.pages, 10);
    if (n > 0) pages = n;
  }

  const patch = {};
  if (description) patch.description_fr = description;
  if (pages > 0) patch.total_pages = pages;
  if (!Object.keys(patch).length) return;

  const token = localStorage.getItem('token');
  if (!token) return;
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
}

/**
 * Lance l'enrichissement en file d'attente (idempotent par session).
 */
export async function enrichLibraryMetadata({
  books,
  userSeriesLibrary,
  setBooks,
  setUserSeriesLibrary,
} = {}) {
  if (running) return;
  if (!localStorage.getItem('token')) return;

  const limits = enrichmentLimits();
  const candidates = collectCandidates(books, userSeriesLibrary).slice(
    0,
    limits.maxPerRun
  );
  if (!candidates.length) return;

  running = true;
  try {
    let cursor = 0;
    const worker = async () => {
      while (cursor < candidates.length) {
        const idx = cursor;
        cursor += 1;
        const item = candidates[idx];
        attempted.add(item.key);
        try {
          if (item.kind === 'book') {
            await enrichBook(item, { setBooks });
          } else {
            await enrichDemoted(item, { setUserSeriesLibrary });
          }
        } catch (_) {
          /* non bloquant */
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
  } finally {
    running = false;
  }
}

/**
 * Démarre après un court délai (laisse l'UI peindre / le backend se réveiller).
 * Retourne une fonction d'annulation du timer (pas de l'enrichissement en cours).
 */
export function scheduleLibraryMetaEnrichment(args, delayMs) {
  const wait = delayMs ?? enrichmentLimits().startDelayMs;
  const timer = setTimeout(() => {
    enrichLibraryMetadata(args).catch(() => {});
  }, wait);
  return () => clearTimeout(timer);
}

export default enrichLibraryMetadata;
