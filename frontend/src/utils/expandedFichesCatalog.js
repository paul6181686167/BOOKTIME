/**
 * Catalogue étendu (~10 000 tomes Wikidata), chargé une fois depuis
 * GET /api/catalog/expanded. Le référentiel curé JS reste prioritaire.
 */
import { API_BASE_URL } from '../config/environment';
import { getToken } from '../services/apiClient';
import { FuzzyMatcher } from './fuzzyMatcher';

let loaded = false;
let loading = null;
let seriesList = [];
const byNormName = new Map();
const byVolumeTitle = new Map();

export function isExpandedCatalogReady() {
  return loaded;
}

export function getExpandedSeriesList() {
  return seriesList;
}

export function resetExpandedCatalog() {
  loaded = false;
  loading = null;
  seriesList = [];
  byNormName.clear();
  byVolumeTitle.clear();
}

export function indexExpandedSeriesForTests(list) {
  indexSeries(list);
}

function indexSeries(list) {
  seriesList = Array.isArray(list) ? list : [];
  byNormName.clear();
  byVolumeTitle.clear();
  for (const data of seriesList) {
    if (!data || !data.name) continue;
    const names = [data.name, data.name_en].filter(Boolean);
    for (const n of names) {
      const norm = FuzzyMatcher.normalizeString(n);
      if (norm && !byNormName.has(norm)) {
        byNormName.set(norm, { key: data.key || data.qid, data });
      }
    }
    const titles = data.volume_titles || {};
    Object.values(titles).forEach((title) => {
      const norm = FuzzyMatcher.normalizeString(String(title || ''));
      if (norm && norm.length >= 4 && !byVolumeTitle.has(norm)) {
        byVolumeTitle.set(norm, { key: data.key || data.qid, data });
      }
    });
  }
  loaded = true;
}

export function resolveExpandedSeriesByName(name) {
  if (!name || !loaded) return null;
  const norm = FuzzyMatcher.normalizeString(name);
  if (!norm) return null;
  return byNormName.get(norm) || null;
}

export function resolveExpandedSeriesByVolumeTitle(title) {
  if (!title || !loaded) return null;
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
 * Correspondances rapides (exact / préfixe / sous-chaîne), sans fuzzy sur 1 000+ séries.
 */
export function matchExpandedSeries(query, limit = 5) {
  if (!loaded || !query) return [];
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
        confidence: 95000 + score,
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

export async function ensureExpandedCatalog() {
  if (loaded) return seriesList;
  if (loading) return loading;
  loading = (async () => {
    try {
      const token = getToken();
      if (!token) return seriesList;
      const res = await fetch(`${API_BASE_URL}/api/catalog/expanded`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return seriesList;
      const data = await res.json();
      indexSeries(data?.series || []);
      return seriesList;
    } catch {
      return seriesList;
    } finally {
      loading = null;
    }
  })();
  return loading;
}
