/**
 * Fusionne éditeur / genre / langue (et détails de tome) sur le catalogue curé.
 */
import { EXTENDED_SERIES_DATABASE as RAW_SERIES_DATABASE } from './seriesDatabaseExtended';
import { catalogMetaForKey } from './seriesCatalogMeta';

function blank(v) {
  return v == null || (typeof v === 'string' && !v.trim());
}

function mergeVolumeDetails(base = {}, extra = {}) {
  const out = { ...extra, ...base };
  const nums = new Set([...Object.keys(extra), ...Object.keys(base)]);
  nums.forEach((n) => {
    out[n] = { ...(extra[n] || {}), ...(base[n] || {}) };
  });
  return out;
}

export function completeSeriesEntry(key, data) {
  if (!data || typeof data !== 'object') return data;
  const extra = catalogMetaForKey(key);
  const publisher = !blank(data.publisher) ? data.publisher : extra.publisher;
  const genre = !blank(data.genre) ? data.genre : extra.genre;
  const language = !blank(data.language) ? data.language : extra.language;
  const cover_url = !blank(data.cover_url) ? data.cover_url : extra.cover_url;
  return {
    ...data,
    publisher: publisher || data.publisher,
    genre: genre || data.genre,
    language: language || data.language,
    cover_url: cover_url || data.cover_url,
    volume_details: mergeVolumeDetails(data.volume_details, extra.volume_details),
  };
}

function buildCompletedDatabase() {
  const out = {};
  Object.entries(RAW_SERIES_DATABASE).forEach(([cat, bucket]) => {
    out[cat] = {};
    Object.entries(bucket || {}).forEach(([key, data]) => {
      out[cat][key] = completeSeriesEntry(key, data);
    });
  });
  return out;
}

/** Catalogue curé avec éditeur / genre / langue renseignés. */
export const EXTENDED_SERIES_DATABASE = buildCompletedDatabase();
export default EXTENDED_SERIES_DATABASE;
