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

// Le référentiel curé est un import statique immuable : les résolutions sont donc
// déterministes et mémoïsables. Sans ce cache, une recherche déclenche des dizaines
// de parcours complets du référentiel (fuzzy + Levenshtein) sur le thread principal.
const MEMO_LIMIT = 2000;
const memoGet = (cache, key, compute) => {
  if (cache.has(key)) return cache.get(key);
  const value = compute();
  if (cache.size >= MEMO_LIMIT) cache.clear();
  cache.set(key, value);
  return value;
};

const NAME_RESOLUTION_CACHE = new Map();
const BOOK_SERIES_CACHE = new Map();

/**
 * Résout un nom de série (libellé brut) vers l'entrée curée correspondante.
 * @returns {{ key: string, data: object }|null}
 */
export const resolveCuratedSeriesByName = (seriesName) => {
  if (!seriesName) return null;
  const norm = FuzzyMatcher.normalizeString(seriesName);
  if (!norm) return null;
  return memoGet(NAME_RESOLUTION_CACHE, norm, () => {
    if (CURATED_NAME_INDEX.has(norm)) return CURATED_NAME_INDEX.get(norm);
    // Repli fuzzy léger (tolérance orthographique) sur les noms canoniques.
    for (const [indexedNorm, entry] of CURATED_NAME_INDEX.entries()) {
      if (indexedNorm.length < 4) continue;
      if (FuzzyMatcher.fuzzyMatch(norm, indexedNorm, 2) >= 90) return entry;
    }
    return null;
  });
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
  const candidates = bookTitleCandidates(book);
  const cacheKey = `${candidates.join('\u0000')}\u0001${author}`;
  const cached = memoGet(BOOK_SERIES_CACHE, cacheKey, () => {
    for (const title of candidates) {
      // 0. Match exact sur le nom / variation curée (ex. « Dog Man » → série BD)
      const exact = resolveCuratedSeriesByName(title);
      if (
        exact?.data &&
        ((Number(exact.data.volumes) || 0) > 1 ||
          Object.keys(exact.data.volume_titles || {}).length > 1)
      ) {
        // Si auteurs connus : accepter si pas d'auteur fourni, ou auteur proche
        const authors = exact.data.authors || [];
        const authorOk =
          !author ||
          !authors.length ||
          authors.some(
            (sa) =>
              FuzzyMatcher.fuzzyMatch(
                FuzzyMatcher.normalizeString(author),
                FuzzyMatcher.normalizeString(sa)
              ) >= 50 ||
              FuzzyMatcher.normalizeString(author).includes(
                FuzzyMatcher.normalizeString(sa).split(' ').pop()
              )
          );
        if (authorOk) {
          return {
            seriesKey: exact.key,
            seriesName: exact.data.name,
            seriesData: exact.data,
            source: 'curated',
            confidence: 99,
            method: 'curated_exact_name',
          };
        }
      }

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
  });
  // Copie défensive : les appelants enrichissent parfois l'attribution retournée.
  return cached ? { ...cached } : null;
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
  // Ignorer si la « saga » n'est que le titre du livre (faux positif OL fréquent)
  const saga = (book.saga || '').trim();
  if (saga) {
    const sagaNorm = FuzzyMatcher.normalizeString(saga);
    const titleNorm = FuzzyMatcher.normalizeString(book.title || '');
    const sameAsTitle =
      sagaNorm &&
      titleNorm &&
      (sagaNorm === titleNorm ||
        titleNorm.includes(sagaNorm) ||
        sagaNorm.includes(titleNorm));
    // Saga = titre du livre et pas de série curée multi-tomes → livre individuel
    const resolved = resolveCuratedSeriesByName(saga);
    const curatedVolumes = resolved?.data?.volumes;
    const isMulti =
      (typeof curatedVolumes === 'number' && curatedVolumes > 1) ||
      (Array.isArray(resolved?.data?.volume_titles) &&
        resolved.data.volume_titles.length > 1);

    if (sameAsTitle && !isMulti) {
      return null;
    }

    return {
      seriesKey: resolved?.key || `saga_${sagaNorm}`,
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
const QUERY_SERIES_CACHE = new Map();

export const findCuratedSeriesByQuery = (query) => {
  if (!query || !String(query).trim()) return null;
  const q = String(query).trim();
  return memoGet(QUERY_SERIES_CACHE, q.toLowerCase(), () => {
    const direct = resolveCuratedSeriesByName(q);
    if (direct) return { seriesKey: direct.key, seriesName: direct.data.name, seriesData: direct.data };
    const detection = SeriesDetector.searchInSeriesDatabase(q, '');
    if (detection.belongsToSeries) {
      const resolved = resolveCuratedSeriesByName(detection.seriesName);
      if (resolved) return { seriesKey: resolved.key, seriesName: resolved.data.name, seriesData: resolved.data };
    }
    return null;
  });
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
 * Normalise un titre de tome pour détecter les doublons d'éditions OL.
 */
export const normalizeOwnedVolumeTitle = (raw) => {
  let t = String(raw || '');
  // Retirer mentions édition / audio avant normalisation
  t = t.replace(/\([^)]*\)/g, ' ');
  t = FuzzyMatcher.normalizeString(t);
  if (!t) return '';
  t = t.replace(/\s*[-–—:]?\s*tome\s*\d+\s*$/i, '').trim();
  t = t.replace(/\b(three )?audio compact discs?\b/g, ' ').trim();
  t = t.replace(/\b(edition|editions|audiobook|livre audio)\b/g, ' ').trim();
  // "des fiançailles" ≈ "de fiançailles"
  t = t.replace(/\bdes\b/g, 'de');
  t = t.replace(/\s+/g, ' ').trim();
  return t;
};

/**
 * Compte les tomes réellement distincts (ignore les doublons OL du même livre).
 * Regroupe aussi les titres quasi-identiques (fuzzy >= 90).
 */
export const countDistinctOwnedVolumes = (volumes) => {
  if (!Array.isArray(volumes) || !volumes.length) return 0;
  const norms = [];
  for (const v of volumes) {
    const t = normalizeOwnedVolumeTitle(v?.volume_title || v?.title || '');
    if (!t) continue;
    const isDup = norms.some((n) => FuzzyMatcher.fuzzyMatch(t, n, 2) >= 90);
    if (!isDup) norms.push(t);
  }
  return norms.length;
};

const curatedVolumeCount = (seriesData) => {
  if (!seriesData) return 0;
  if (Number.isFinite(seriesData.volumes) && seriesData.volumes > 0) {
    return seriesData.volumes;
  }
  if (seriesData.volume_titles && typeof seriesData.volume_titles === 'object') {
    return Object.keys(seriesData.volume_titles).length;
  }
  if (Array.isArray(seriesData.volume_titles)) {
    return seriesData.volume_titles.length;
  }
  return 0;
};

/**
 * Décide si une entrée series_library doit s'afficher comme série ou livre.
 * - Vraie série curée (SdA, HP…) → série même si 1 seul tome en bibliothèque
 * - Doublons du même titre (ex. Long Dimanche ×11) → livre individuel
 * - 0–1 tome distinct sans référentiel multi-tomes → livre individuel
 *
 * @returns {{ demote: boolean, totalBooks: number, curated: object|null, distinctOwned: number }}
 */
export const evaluateOwnedSeriesForDisplay = (series) => {
  const name = series?.series_name || series?.name || '';
  const volArr = Array.isArray(series?.volumes) ? series.volumes : [];
  const curated = resolveCuratedSeriesByName(name);
  const curatedCount = curatedVolumeCount(curated?.data);
  const distinctOwned = countDistinctOwnedVolumes(volArr);
  const storedTotal =
    Number(series?.total_volumes) > 0 ? Number(series.total_volumes) : volArr.length;

  const volumeNumbers = volArr
    .map((v) => Number(v?.volume_number))
    .filter((n) => Number.isFinite(n) && n > 0);
  const uniqueVolumeNumbers = new Set(volumeNumbers);
  // Toutes les entrées en "tome 1" = éditions du même livre (ex. Long Dimanche ×11)
  const allSameVolumeNumber =
    volArr.length > 1 && uniqueVolumeNumbers.size > 0 && uniqueVolumeNumbers.size <= 1;

  // Faux multi-tome : plein d'entrées mais un seul titre distinct (ou quasi)
  const isFakeMulti =
    volArr.length > 1 && (distinctOwned <= 1 || allSameVolumeNumber);

  if (curatedCount > 1 && !allSameVolumeNumber) {
    return {
      demote: false,
      totalBooks: Math.max(
        curatedCount,
        distinctOwned,
        storedTotal > 1 && !isFakeMulti ? storedTotal : 0
      ),
      curated,
      distinctOwned,
    };
  }

  // Série curée mais bibliothèque = doublons du même tome → quand même série
  // (ex. SdA avec un seul tome stocké plusieurs fois) si curatedCount > 1
  if (curatedCount > 1) {
    return {
      demote: false,
      totalBooks: curatedCount,
      curated,
      distinctOwned: Math.max(distinctOwned, 1),
    };
  }

  if (isFakeMulti || distinctOwned <= 1) {
    return { demote: true, totalBooks: 1, curated, distinctOwned };
  }

  return {
    demote: false,
    totalBooks: Math.max(storedTotal, distinctOwned),
    curated,
    distinctOwned,
  };
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
