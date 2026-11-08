/**
 * Noyau curé (~50 000 tomes).
 * On n'indexe pas le JSON entier (trop lourd) : la recherche passe par
 * GET /api/catalog/expanded/search, et les hits sont mis en cache local.
 * L'overlay JS (~103 séries riches) reste prioritaire en cas d'homonyme.
 */
import { API_BASE_URL } from '../config/environment';
import { getToken } from '../services/apiClient';
import { FuzzyMatcher } from './fuzzyMatcher';

let loaded = false;
let seriesList = [];
const byNormName = new Map();
const byVolumeTitle = new Map();
const byKey = new Map();

export function isExpandedCatalogReady() {
  return loaded;
}

export function getExpandedSeriesList() {
  return seriesList;
}

export function resetExpandedCatalog() {
  loaded = false;
  seriesList = [];
  byNormName.clear();
  byVolumeTitle.clear();
  byKey.clear();
}

export function indexExpandedSeriesForTests(list) {
  resetExpandedCatalog();
  rememberExpandedHits(list);
}

function indexOne(data) {
  if (!data || !data.name) return;
  const key = data.key || data.qid;
  if (key && byKey.has(key)) return;
  seriesList.push(data);
  if (key) byKey.set(key, data);
  const names = [data.name, data.name_en].filter(Boolean);
  for (const n of names) {
    const norm = FuzzyMatcher.normalizeString(n);
    if (norm && !byNormName.has(norm)) {
      byNormName.set(norm, { key: key || data.name, data });
    }
  }
  const titles = data.volume_titles || {};
  Object.values(titles).forEach((title) => {
    const norm = FuzzyMatcher.normalizeString(String(title || ''));
    if (norm && norm.length >= 4 && !byVolumeTitle.has(norm)) {
      byVolumeTitle.set(norm, { key: key || data.name, data });
    }
  });
}

export function rememberExpandedHits(rows) {
  if (!Array.isArray(rows)) return;
  rows.forEach(indexOne);
  loaded = seriesList.length > 0;
}

export function resolveExpandedSeriesByName(name) {
  if (!name || !seriesList.length) return null;
  const norm = FuzzyMatcher.normalizeString(name);
  if (!norm) return null;
  return byNormName.get(norm) || null;
}

export function resolveExpandedSeriesByVolumeTitle(title) {
  if (!title || !seriesList.length) return null;
  const norm = FuzzyMatcher.normalizeString(title);
  if (!norm || norm.length < 4) return null;
  const exact = byVolumeTitle.get(norm);
  if (exact) return exact;
  for (const [indexed, entry] of byVolumeTitle.entries()) {
    if (indexed.includes(norm) || norm.includes(indexed)) return entry;
  }
  return null;
}

/**
 * Correspondances rapides sur le cache local (hits déjà vus), sans fuzzy lourd.
 */
export function matchExpandedSeries(query, limit = 5) {
  if (!seriesList.length || !query) return [];
  const qn = FuzzyMatcher.normalizeString(query);
  if (qn.length < 2) return [];
  const hits = [];
  for (const data of seriesList) {
    const name = FuzzyMatcher.normalizeString(data.name || '');
    const nameEn = FuzzyMatcher.normalizeString(data.name_en || '');
    let score = 0;
    let matchType = 'expanded_name';
    if (name === qn || nameEn === qn) {
      score = 100;
      matchType = 'exact_name';
    } else if (name.startsWith(qn) || nameEn.startsWith(qn)) {
      score = 90;
      matchType = 'prefix_name';
    } else if (qn.length >= 4 && (name.includes(qn) || nameEn.includes(qn))) {
      score = 75;
      matchType = 'partial_name';
    } else if (qn.length >= 4) {
      const titles = data.volume_titles || {};
      for (const title of Object.values(titles)) {
        const tn = FuzzyMatcher.normalizeString(String(title || ''));
        if (tn === qn || tn.includes(qn)) {
          score = 70;
          matchType = 'volume_title';
          break;
        }
      }
    }
    if (score) {
      hits.push({
        series: data,
        confidence: 100000 + score,
        match_reasons: [matchType, 'expanded_catalog'],
        matchType,
        originalScore: score,
        matchDetails: `${matchType} ${score}% avec "${data.name}"`,
        category: data.category,
        seriesKey: data.key || data.qid,
        targetMatched: data.name,
      });
    }
  }
  hits.sort((a, b) => b.confidence - a.confidence || (b.series.volumes || 0) - (a.series.volumes || 0));
  return hits.slice(0, limit);
}

export async function searchExpandedCatalog(query, limit = 8, signal) {
  const token = getToken();
  const q = String(query || '').trim();
  if (!token || q.length < 2) return [];
  const res = await fetch(
    `${API_BASE_URL}/api/catalog/expanded/search?q=${encodeURIComponent(q)}&limit=${limit}`,
    { headers: { Authorization: `Bearer ${token}` }, signal }
  );
  if (!res.ok) return [];
  const data = await res.json();
  const rows = data?.results || [];
  rememberExpandedHits(rows);
  return rows;
}

/** Conservé pour compat : plus de téléchargement global du catalogue. */
export async function ensureExpandedCatalog() {
  return seriesList;
}
