/**
 * ATTRIBUTION SÉRIE - Module partagé recherche + bibliothèque
 *
 * Donne, pour un livre, la série à laquelle il appartient (ou null si standalone),
 * en appliquant un ordre de rattachement unique et stable :
 *   1. Référentiel curé EXTENDED_SERIES_DATABASE (nom / variations / titres de tomes,
 *      avec respect des `exclusions`). Les `keywords` génériques ne servent JAMAIS
 *      à masquer un livre (uniquement gérés en interne par SeriesDetector avec garde-fou
 *      « nom/variation présent dans le titre »).
 *   2. Index Wikidata statique (résultats déjà récupérés via /api/static-wikidata/series/search)
 *      — UNIQUEMENT côté recherche (matcher passé en option). Jamais d'appel réseau ici.
 *   3. Champ `saga` d'Open Library / de la bibliothèque.
 *
 * L'heuristique « auteur + mots du query » (fallback de groupe, spécifique recherche)
 * reste gérée par l'appelant, sur les livres restés sans attribution.
 *
 * Chaque attribution renvoie `{ seriesKey, seriesName, seriesData, source }`
 * permettant de fusionner les sources (nom canonique + nombre de tomes curé).
 */

import { EXTENDED_SERIES_DATABASE } from './seriesDatabaseExtended';
import { SeriesDetector } from './seriesDetector';
import { FuzzyMatcher } from './fuzzyMatcher';

// Index : nom/variation normalisé → { key, data } (résolution du nom canonique curé)
const buildCuratedNameIndex = () => {
  const index = new Map();
  for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
    for (const [key, data] of Object.entries(category)) {
      const names = [data.name, ...(data.variations || [])].filter(Boolean);
      for (const n of names) {
        const norm = FuzzyMatcher.normalizeString(n);
        if (norm && !index.has(norm)) index.set(norm, { key, data });
      }
    }
  }
  return index;
};
const CURATED_NAME_INDEX = buildCuratedNameIndex();

/**
 * Résout un nom de série (libellé brut) vers l'entrée curée correspondante.
 * @returns {{ key: string, data: object }|null}
 */
export const resolveCuratedSeriesByName = (seriesName) => {
  if (!seriesName) return null;
  const norm = FuzzyMatcher.normalizeString(seriesName);
  if (!norm) return null;
  if (CURATED_NAME_INDEX.has(norm)) return CURATED_NAME_INDEX.get(norm);
  // Repli fuzzy léger (tolérance orthographique) sur les noms canoniques.
  for (const [indexedNorm, entry] of CURATED_NAME_INDEX.entries()) {
    if (indexedNorm.length < 4) continue;
    if (FuzzyMatcher.fuzzyMatch(norm, indexedNorm, 2) >= 90) return entry;
  }
  return null;
};

const bookTitleCandidates = (book) => {
  const out = [];
  const dt = (book?.display_title || '').trim();
  const t = (book?.title || '').trim();
  if (dt) out.push(dt);
  if (t && t !== dt) out.push(t);
  return out;
};

/**
 * Étape 1 — Rattachement via le référentiel curé (ignore volontairement `saga`,
 * pour respecter l'ordre curé > saga).
 * @returns {{ seriesKey, seriesName, seriesData, source, confidence, method }|null}
 */
export const findCuratedSeriesForBook = (book) => {
  if (!book) return null;
  const author = book.author || '';
  for (const title of bookTitleCandidates(book)) {
    // a. Patterns titre + auteur (Harry Potter, LOTR, …)
    const byPattern = SeriesDetector.analyzeBookTitle(title, author);
    // b. Recherche dans le référentiel (nom / variations / titres de tomes, exclusions gérées)
    const detection = byPattern.belongsToSeries
      ? byPattern
      : SeriesDetector.searchInSeriesDatabase(title, author);
    if (detection.belongsToSeries) {
      const resolved = resolveCuratedSeriesByName(detection.seriesName);
      return {
        seriesKey: resolved?.key || `curated_${FuzzyMatcher.normalizeString(detection.seriesName)}`,
        seriesName: resolved?.data?.name || detection.seriesName,
        seriesData: resolved?.data || null,
        source: 'curated',
        confidence: detection.confidence,
        method: detection.method,
      };
    }
  }
  return null;
};

/**
 * Construit un matcher Wikidata à partir des résultats de
 * GET /api/static-wikidata/series/search (lite). Le matcher rattache un livre
 * à une série WD si son titre correspond (exact / fuzzy / inclusion) à un nom de série.
 * @param {object[]} wikidataResults lignes `{ qid, name, name_fr, name_en, label, author_label }`
 * @returns {(book:object) => ({ qid, name, entry }|null)}
 */
export const buildWikidataSeriesMatcher = (wikidataResults) => {
  const entries = (Array.isArray(wikidataResults) ? wikidataResults : [])
    .filter((e) => e && e.qid)
    .map((e) => ({
      qid: e.qid,
      displayName: e.name_fr || e.name || e.name_en || e.label || e.qid,
      names: [e.name_fr, e.name, e.name_en, e.label]
        .filter(Boolean)
        .map((n) => ({ raw: n, norm: FuzzyMatcher.normalizeString(n) }))
        .filter((n) => n.norm),
      entry: e,
    }));

  return (book) => {
    if (!entries.length) return null;
    for (const title of bookTitleCandidates(book)) {
      const titleNorm = FuzzyMatcher.normalizeString(title);
      if (!titleNorm) continue;
      for (const e of entries) {
        for (const n of e.names) {
          if (n.norm.length < 4) continue;
          const exactOrFuzzy = FuzzyMatcher.fuzzyMatch(titleNorm, n.norm, 3) >= 88;
          const seriesNameInTitle = n.norm.length >= 6 && titleNorm.includes(n.norm);
          if (exactOrFuzzy || seriesNameInTitle) {
            return { qid: e.qid, name: e.displayName, entry: e.entry };
          }
        }
      }
    }
    return null;
  };
};

/**
 * Attribution complète d'un livre à une série, dans l'ordre curé → Wikidata → saga.
 * @param {object} book
 * @param {object} [options]
 * @param {(book:object)=>object|null} [options.wikidataMatcher] matcher WD (recherche uniquement)
 * @returns {{ seriesKey, seriesName, seriesData, source, wikidata_qid?, wdEntry? }|null}
 */
export const attributeBookToSeries = (book, { wikidataMatcher } = {}) => {
  if (!book) return null;

  // 1. Référentiel curé (prioritaire)
  const curated = findCuratedSeriesForBook(book);
  if (curated) return curated;

  // 2. Index Wikidata (recherche uniquement)
  if (typeof wikidataMatcher === 'function') {
    const wd = wikidataMatcher(book);
    if (wd) {
      return {
        seriesKey: `wd_${wd.qid}`,
        seriesName: wd.name,
        seriesData: null,
        source: 'wikidata',
        wikidata_qid: wd.qid,
        wdEntry: wd.entry,
      };
    }
  }

  // 3. Champ saga (Open Library / bibliothèque)
  const saga = (book.saga || '').trim();
  if (saga) {
    const resolved = resolveCuratedSeriesByName(saga);
    return {
      seriesKey: resolved?.key || `saga_${FuzzyMatcher.normalizeString(saga)}`,
      seriesName: resolved?.data?.name || saga,
      seriesData: resolved?.data || null,
      source: 'saga',
    };
  }

  return null;
};

/**
 * Résout la REQUÊTE utilisateur vers une série curée (nom / variations).
 * Sert au rattachement inter-langues : pour "seigneur des anneaux", tous les tomes de
 * Tolkien (y compris les titres anglais absents des `volume_titles` FR) sont rattachés.
 * @returns {{ seriesKey, seriesName, seriesData }|null}
 */
export const findCuratedSeriesByQuery = (query) => {
  if (!query || !String(query).trim()) return null;
  const q = String(query).trim();
  const direct = resolveCuratedSeriesByName(q);
  if (direct) return { seriesKey: direct.key, seriesName: direct.data.name, seriesData: direct.data };
  const detection = SeriesDetector.searchInSeriesDatabase(q, '');
  if (detection.belongsToSeries) {
    const resolved = resolveCuratedSeriesByName(detection.seriesName);
    if (resolved) return { seriesKey: resolved.key, seriesName: resolved.data.name, seriesData: resolved.data };
  }
  return null;
};

const titleMatchesExclusion = (title, seriesData) => {
  if (!seriesData || !Array.isArray(seriesData.exclusions)) return false;
  const t = FuzzyMatcher.normalizeString(title);
  if (!t) return false;
  return seriesData.exclusions.some((exc) => {
    const e = FuzzyMatcher.normalizeString(exc);
    return e && t.includes(e);
  });
};

const authorMatchesSeries = (author, seriesData) => {
  if (!author || !seriesData || !Array.isArray(seriesData.authors) || !seriesData.authors.length) {
    return false;
  }
  const a = FuzzyMatcher.normalizeString(author);
  return seriesData.authors.some((sa) => FuzzyMatcher.fuzzyMatch(a, FuzzyMatcher.normalizeString(sa)) >= 70);
};

/**
 * Rattache un livre à la série de la requête si l'auteur correspond et que le titre n'est
 * pas exclu. Permet de masquer les tomes en langue étrangère non présents dans `volume_titles`.
 * @param {object} book
 * @param {{ seriesKey, seriesName, seriesData }} querySeries résultat de findCuratedSeriesByQuery
 * @returns {{ seriesKey, seriesName, seriesData, source }|null}
 */
export const attachBookToQuerySeries = (book, querySeries) => {
  if (!book || !querySeries || !querySeries.seriesData) return null;
  const title = book.display_title || book.title || '';
  if (titleMatchesExclusion(title, querySeries.seriesData)) return null;
  if (!authorMatchesSeries(book.author, querySeries.seriesData)) return null;
  return {
    seriesKey: querySeries.seriesKey,
    seriesName: querySeries.seriesName,
    seriesData: querySeries.seriesData,
    source: 'curated',
  };
};

/**
 * Nombre de tomes à afficher pour une carte série :
 * total curé (faisant autorité) si la série est dans le référentiel, sinon nombre de tomes trouvés.
 */
export const resolveSeriesTotalBooks = (seriesData, foundCount) => {
  if (seriesData && Number.isFinite(seriesData.volumes) && seriesData.volumes > 0) {
    return seriesData.volumes;
  }
  return foundCount || 0;
};

/**
 * Enrichit une carte série Wikidata (spotlight) à partir du référentiel curé, par son nom :
 * auteur + nombre de tomes faisant autorité (au lieu du `work_count` brut Wikidata).
 * Sans correspondance curée, renvoie les valeurs de repli fournies.
 * @returns {{ author: string, totalBooks: number, category?: string, seriesName?: string }}
 */
export const enrichWikidataCardFromCurated = (wdName, fallback = {}) => {
  const resolved = resolveCuratedSeriesByName(wdName);
  if (resolved && resolved.data) {
    const d = resolved.data;
    return {
      author: (Array.isArray(d.authors) && d.authors[0]) || fallback.author || '',
      totalBooks: Number.isFinite(d.volumes) && d.volumes > 0 ? d.volumes : (fallback.totalBooks || 0),
      category: d.category || fallback.category,
      seriesName: d.name || fallback.seriesName,
    };
  }
  return {
    author: fallback.author || '',
    totalBooks: fallback.totalBooks || 0,
    category: fallback.category,
    seriesName: fallback.seriesName,
  };
};
