/**
 * Transforme les recommandations brutes (OL / GB) en items Booktime
 * (titres FR, cartes série, shape compatible modales).
 */
import { displayBookTitleFrFirst, mergeOpenLibraryBooksByVolume } from './openLibraryBookDisplay';
import {
  attributeBookToSeries,
  findCuratedSeriesByQuery,
} from './seriesAttribution';

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

function bookRecoKey(book) {
  return book?.ol_key || book?.id || '';
}

function isMultiSeriesAttr(attr) {
  if (!attr?.seriesData) return false;
  const d = attr.seriesData;
  return (
    (Number(d.volumes) || 0) > 1 ||
    Object.keys(d.volume_titles || {}).length > 1
  );
}

/** Titre / métadonnées qui indiquent clairement un tome d'une série. */
function looksLikeSeriesVolume(book) {
  if (!book) return false;
  const vol = Number(book.volume_number);
  if (Number.isFinite(vol) && vol > 0) return true;
  const t = `${book.title || ''} ${book.display_title || ''} ${book.original_title || ''}`;
  return /(?:^|[\s\-–—:])(?:tome|volume|vol\.?|#)\s*\d+/i.test(t);
}

/** Extrait « Nom de série » depuis « Nom - Tome 2 » / « Nom Tome 3 ». */
function extractSeriesHintFromTitle(title) {
  const t = (title || '').trim();
  if (!t) return null;
  const m =
    t.match(/^(.*?)\s*[-–—:]\s*(?:tome|volume|vol\.?|#)\s*\d+/i) ||
    t.match(/^(.*?)\s+(?:tome|volume|vol\.?)\s*\d+\s*$/i);
  if (!m) return null;
  const hint = (m[1] || '').trim();
  return hint.length >= 3 ? hint : null;
}

function shouldExcludeSeedSeries(seriesName, seedN, seedTokens) {
  if (!seedN) return false;
  const seriesN = normSeed(seriesName);
  if (!seriesN) return false;
  if (seriesN === seedN || seriesN.includes(seedN) || seedN.includes(seriesN)) {
    return true;
  }
  if (seedTokens.length >= 2 && seedTokens.every((tok) => seriesN.includes(tok))) {
    return true;
  }
  return false;
}

function buildSeriesCard(attr, groupBooks) {
  const merged = mergeOpenLibraryBooksByVolume(groupBooks);
  const cover = merged.find((b) => b.cover_url)?.cover_url || groupBooks[0]?.cover_url || null;
  const author =
    groupBooks.find((b) => b.author)?.author ||
    attr.seriesData?.authors?.[0] ||
    '';
  const reason =
    groupBooks.find((b) => b.reason)?.reason || 'Série proche de ta sélection';
  const fromGb = groupBooks.some(
    (b) => b.isFromGoogleBooks || String(b.source || '').endsWith('_gb')
  );
  const totalBooks =
    attr.seriesData?.volumes ||
    Object.keys(attr.seriesData?.volume_titles || {}).length ||
    merged.length ||
    groupBooks.length;
  return {
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
    totalBooks,
    books: merged.length ? merged : groupBooks,
    description:
      attr.seriesData?.description ||
      `Série · ${totalBooks || merged.length || groupBooks.length} tome(s)`,
    reason,
    score: Math.max(...groupBooks.map((b) => b.score || 0), 0),
    source: groupBooks[0]?.source || 'seed_similarity',
    book_id: merged[0]?.ol_key || merged[0]?.book_id || groupBooks[0]?.ol_key,
  };
}

/**
 * Regroupe une liste de recos en cartes série + livres individuels (format recherche Booktime).
 * Un tome rattaché à une série (curée / saga / « Tome N ») → carte série, jamais vignette tome.
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

  const resolveAttr = (book) => {
    let attr = attributeBookToSeries(book);
    if (attr && shouldExcludeSeedSeries(attr.seriesName, seedN, seedTokens)) {
      return null;
    }
    if (attr) return attr;

    // Repli : « Foo - Tome 2 » → série Foo (curée si connue)
    const hint =
      extractSeriesHintFromTitle(book.display_title) ||
      extractSeriesHintFromTitle(book.title) ||
      extractSeriesHintFromTitle(book.original_title);
    if (!hint) return null;
    if (shouldExcludeSeedSeries(hint, seedN, seedTokens)) return null;
    const curated = findCuratedSeriesByQuery(hint);
    if (curated?.seriesData) {
      return {
        seriesKey: curated.key || `hint_${normSeed(curated.seriesName || hint)}`,
        seriesName: curated.seriesName || curated.seriesData.name || hint,
        seriesData: curated.seriesData,
        source: 'title_hint',
      };
    }
    if (looksLikeSeriesVolume(book) || (book.saga && normSeed(book.saga) === normSeed(hint))) {
      return {
        seriesKey: `hint_${normSeed(hint)}`,
        seriesName: hint,
        seriesData: null,
        source: 'title_hint',
      };
    }
    return null;
  };

  const seriesGroups = new Map();

  list.forEach((book) => {
    const attr = resolveAttr(book);
    if (!attr) return;
    if (!seriesGroups.has(attr.seriesKey)) {
      seriesGroups.set(attr.seriesKey, { attr, books: [] });
    }
    seriesGroups.get(attr.seriesKey).books.push(book);
  });

  const seriesCards = [];
  const attributed = new Set();

  seriesGroups.forEach(({ attr, books: groupBooks }) => {
    const merged = mergeOpenLibraryBooksByVolume(groupBooks);
    const promote =
      isMultiSeriesAttr(attr) ||
      merged.length >= 2 ||
      groupBooks.length >= 2 ||
      groupBooks.some((b) => looksLikeSeriesVolume(b)) ||
      // Saga OL distincte du titre = tome d'une série même si 1 seul résultat
      (attr.source === 'saga' && !!attr.seriesName) ||
      attr.source === 'title_hint';

    if (!promote) return;

    const card = buildSeriesCard(attr, groupBooks);
    seriesCards.push(card);
    (card.books || groupBooks).forEach((b) => {
      const key = bookRecoKey(b);
      if (key) attributed.add(key);
    });
  });

  let standalone = list.filter((b) => !attributed.has(bookRecoKey(b)));

  // 2e passe : livre isolé = nom / tome d'une série curée → carte série
  const promoted = [];
  standalone = standalone.filter((book) => {
    const attr = resolveAttr(book);
    if (!attr) return true;
    const promote =
      isMultiSeriesAttr(attr) ||
      looksLikeSeriesVolume(book) ||
      attr.source === 'title_hint' ||
      attr.source === 'saga';
    if (!promote) return true;
    const already = seriesCards.some(
      (c) => normSeed(c.name) === normSeed(attr.seriesName)
    );
    if (already) return false;
    promoted.push(buildSeriesCard(attr, [book]));
    return false;
  });
  seriesCards.push(...promoted);

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
