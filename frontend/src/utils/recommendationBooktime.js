/**
 * Transforme les recommandations brutes (OL / GB) en items Booktime
 * (titres FR, cartes série, shape compatible modales).
 */
import { displayBookTitleFrFirst, mergeOpenLibraryBooksByVolume } from './openLibraryBookDisplay';
import { attributeBookToSeries } from './seriesAttribution';

/**
 * @param {object} reco - Item API recommandations
 * @returns {object} Livre shape Booktime / Open Library
 */
export function recoToBooktimeBook(reco) {
  if (!reco) return null;
  const meta = reco.metadata && typeof reco.metadata === 'object' ? reco.metadata : {};
  const olKey =
    reco.ol_key ||
    meta.ol_key ||
    (typeof reco.book_id === 'string' && reco.book_id.includes('works/')
      ? reco.book_id
      : '') ||
    '';
  const title =
    reco.display_title ||
    reco.title_fr ||
    meta.display_title ||
    meta.title_fr ||
    reco.title ||
    meta.title ||
    '';
  const book = {
    ...meta,
    ...reco,
    ol_key: olKey,
    book_id: reco.book_id || olKey,
    title,
    original_title: reco.original_title || meta.original_title || meta.title || reco.title,
    title_fr: reco.title_fr || meta.title_fr || null,
    saga: reco.saga || meta.saga || '',
    author: reco.author || meta.author || '',
    cover_url: reco.cover_url || meta.cover_url || null,
    category: reco.category || meta.category || 'roman',
    subjects: reco.subjects || meta.subjects || [],
    publication_year: reco.publication_year || meta.publication_year || meta.first_publish_year,
    isFromOpenLibrary: true,
    reason: reco.reason || (Array.isArray(reco.reasons) ? reco.reasons[0] : undefined),
    score: reco.score ?? reco.confidence_score,
    source: reco.source,
  };
  book.display_title = displayBookTitleFrFirst(book);
  book.title = book.display_title || book.title;
  book.id = book.id || (olKey ? `ol_${olKey}` : `reco_${book.book_id || book.title}`);
  return book;
}

function normSeed(s) {
  return (s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Regroupe une liste de recos en cartes série + livres individuels (format recherche Booktime).
 * @param {object[]} recommendations
 * @param {{ seedLabel?: string }} [options] — exclut la série seed (ex. Percy Jackson)
 * @returns {object[]}
 */
export function groupRecosAsBooktimeItems(recommendations, options = {}) {
  const seedN = normSeed(options.seedLabel || '');
  const seedTokens = seedN.split(/\s+/).filter((w) => w.length >= 4);

  const list = (recommendations || [])
    .map(recoToBooktimeBook)
    .filter(Boolean)
    .filter((book) => {
      if (!seedN) return true;
      const blob = normSeed(
        `${book.title || ''} ${book.display_title || ''} ${book.saga || ''} ${book.name || ''}`
      );
      if (blob.includes(seedN)) return false;
      if (seedTokens.length >= 2 && seedTokens.every((t) => blob.includes(t))) return false;
      return true;
    });
  if (!list.length) return [];

  const seriesGroups = new Map();
  const attributed = new Set();

  list.forEach((book) => {
    const attr = attributeBookToSeries(book);
    if (!attr) return;
    const seriesN = normSeed(attr.seriesName);
    // Ne jamais créer une carte pour la série seed elle-même
    if (seedN && (seriesN === seedN || seriesN.includes(seedN) || seedN.includes(seriesN))) {
      return;
    }
    if (seedTokens.length >= 2 && seedTokens.every((t) => seriesN.includes(t))) {
      return;
    }
    if (!seriesGroups.has(attr.seriesKey)) {
      seriesGroups.set(attr.seriesKey, { attr, books: [] });
    }
    seriesGroups.get(attr.seriesKey).books.push(book);
    if (book.ol_key) attributed.add(book.ol_key);
    else attributed.add(book.id);
  });

  const seriesCards = [];
  seriesGroups.forEach(({ attr, books: groupBooks }) => {
    // Série Booktime : ≥2 tomes trouvés, OU série curée multi-tomes (ex. Dog Man)
    const merged = mergeOpenLibraryBooksByVolume(groupBooks);
    const curatedMulti =
      attr.seriesData &&
      ((Number(attr.seriesData.volumes) || 0) > 1 ||
        Object.keys(attr.seriesData.volume_titles || {}).length > 1);
    if (merged.length < 2 && !curatedMulti) {
      return;
    }
    merged.forEach((b) => {
      if (b.ol_key) attributed.add(b.ol_key);
      else if (b.id) attributed.add(b.id);
    });
    const cover = merged.find((b) => b.cover_url)?.cover_url || null;
    const author = groupBooks.find((b) => b.author)?.author || '';
    const reason =
      groupBooks.find((b) => b.reason)?.reason ||
      `Série proche de ta sélection`;
    const fromGb = groupBooks.some(
      (b) => b.isFromGoogleBooks || String(b.source || '').endsWith('_gb')
    );
    seriesCards.push({
      isSeriesCard: true,
      fromOpenLibrary: !fromGb,
      isFromOpenLibrary: !fromGb,
      isFromGoogleBooks: fromGb,
      id: `series_reco_${attr.seriesKey}`,
      name: attr.seriesName,
      title: attr.seriesName,
      display_title: attr.seriesName,
      author,
      category: attr.seriesData?.category || groupBooks[0]?.category || 'roman',
      cover_url: cover,
      totalBooks: attr.seriesData?.volumes || merged.length,
      books: merged,
      description: attr.seriesData?.description || `Série · ${merged.length} tome(s)`,
      reason,
      score: Math.max(...groupBooks.map((b) => b.score || 0), 0),
      source: groupBooks[0]?.source || 'seed_similarity',
      book_id: merged[0]?.ol_key || merged[0]?.book_id,
    });
  });

  const attributedKeys = attributed;
  const standalone = list.filter((b) => {
    const key = b.ol_key || b.id;
    return !attributedKeys.has(key);
  });

  // Séries d'abord, puis livres — priorité aux items avec couverture
  const sortCover = (a, b) => Number(!!b.cover_url) - Number(!!a.cover_url);
  return [...seriesCards.sort(sortCover), ...standalone.sort(sortCover)];
}

/** Normalise un titre pour comparaison ownership (casse, accents, ponctuation). */
export function normOwnedTitle(s) {
  return (s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function collectOwnedIndex(userBooks = [], userSeries = []) {
  const titles = new Set();
  const olKeys = new Set();
  const series = new Set();

  const addTitle = (t) => {
    const n = normOwnedTitle(t);
    if (n) titles.add(n);
  };
  const addOl = (k) => {
    if (!k) return;
    const s = String(k).trim();
    if (!s) return;
    olKeys.add(s);
    olKeys.add(s.replace(/^\/+/, ''));
  };
  const addSeries = (name) => {
    const n = normOwnedTitle(name);
    if (n) series.add(n);
  };

  (userBooks || []).forEach((b) => {
    addTitle(b.title);
    addTitle(b.display_title);
    addTitle(b.original_title);
    addTitle(b.title_fr);
    addOl(b.ol_key);
    addOl(b.book_id);
    if (b.isSeriesCard) {
      addSeries(b.name || b.title || b.series_name);
    }
    addSeries(b.saga || b.saga_name || b.series_name);
  });

  (userSeries || []).forEach((s) => {
    addSeries(s.series_name || s.name || s.title);
  });

  return { titles, olKeys, series };
}

/**
 * True si la reco (livre ou carte série) est déjà dans la bibliothèque.
 */
export function isRecoAlreadyOwned(item, userBooks = [], userSeries = []) {
  if (!item) return false;
  const { titles, olKeys, series } = collectOwnedIndex(userBooks, userSeries);

  if (item.isSeriesCard) {
    const name = normOwnedTitle(item.name || item.title || item.display_title || '');
    if (name && series.has(name)) return true;
    // Tous les tomes listés déjà possédés → carte inutile
    const books = Array.isArray(item.books) ? item.books : [];
    if (books.length > 0) {
      const allOwned = books.every((b) => {
        const t = normOwnedTitle(b.title || b.display_title || b.original_title || '');
        const ol = b.ol_key || b.book_id;
        if (ol && (olKeys.has(String(ol)) || olKeys.has(String(ol).replace(/^\/+/, '')))) {
          return true;
        }
        return t && titles.has(t);
      });
      if (allOwned) return true;
    }
    return false;
  }

  const candidates = [
    item.title,
    item.display_title,
    item.original_title,
    item.title_fr,
  ];
  for (const c of candidates) {
    const n = normOwnedTitle(c);
    if (n && titles.has(n)) return true;
  }
  const ol = item.ol_key || item.book_id;
  if (ol && (olKeys.has(String(ol)) || olKeys.has(String(ol).replace(/^\/+/, '')))) {
    return true;
  }
  return false;
}
