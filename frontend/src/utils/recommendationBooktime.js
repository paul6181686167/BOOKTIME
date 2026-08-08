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

/**
 * Regroupe une liste de recos en cartes série + livres individuels (format recherche Booktime).
 * @param {object[]} recommendations
 * @returns {object[]}
 */
export function groupRecosAsBooktimeItems(recommendations) {
  const list = (recommendations || []).map(recoToBooktimeBook).filter(Boolean);
  if (!list.length) return [];

  const seriesGroups = new Map();
  const attributed = new Set();

  list.forEach((book) => {
    const attr = attributeBookToSeries(book);
    if (!attr) return;
    if (!seriesGroups.has(attr.seriesKey)) {
      seriesGroups.set(attr.seriesKey, { attr, books: [] });
    }
    seriesGroups.get(attr.seriesKey).books.push(book);
    if (book.ol_key) attributed.add(book.ol_key);
    else attributed.add(book.id);
  });

  const seriesCards = [];
  seriesGroups.forEach(({ attr, books: groupBooks }) => {
    // Une série Booktime : au moins 2 tomes, sinon on laisse en livre
    const merged = mergeOpenLibraryBooksByVolume(groupBooks);
    if (merged.length < 2 && !attr.seriesData) {
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
    seriesCards.push({
      isSeriesCard: true,
      fromOpenLibrary: true,
      isFromOpenLibrary: true,
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
