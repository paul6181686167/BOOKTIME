import {
  dedupeWikidataStaticSeriesOverOpenLibrary,
  dedupeSeriesCardsByName,
  inferCategoryFromWikidataSearchEntry,
} from '../../utils/searchSourcePipeline';

describe('searchSourcePipeline', () => {
  test('inferCategoryFromWikidataSearchEntry détecte manga', () => {
    expect(
      inferCategoryFromWikidataSearchEntry({
        name_fr: 'Death Note',
        type: 'manga series',
      })
    ).toBe('manga');
  });

  test('inferCategoryFromWikidataSearchEntry détecte bd', () => {
    expect(
      inferCategoryFromWikidataSearchEntry({
        name: 'Astérix le Gaulois — bande dessinée',
      })
    ).toBe('bd');
  });

  test('dedupeWikidataStaticSeriesOverOpenLibrary retire OL si WD même clé', () => {
    const wd = {
      isSeriesCard: true,
      isStaticWikidataCard: true,
      wikidata_qid: 'Q1',
      name: 'Harry Potter',
      author: 'J. K. Rowling',
      fromOpenLibrary: false,
    };
    const olDup = {
      isSeriesCard: true,
      fromOpenLibrary: true,
      name: 'Harry Potter',
      author: 'J. K. Rowling',
      books: [],
    };
    const book = { id: 'ol_x', title: 'Autre', isFromOpenLibrary: true };
    const out = dedupeWikidataStaticSeriesOverOpenLibrary([wd, olDup, book]);
    expect(out).toHaveLength(2);
    expect(out.find((x) => x.fromOpenLibrary && x.isSeriesCard)).toBeUndefined();
  });

  test('dedupeSeriesCardsByName fusionne carte curée + WD de même nom (1 seule carte, WD prioritaire)', () => {
    const curated = {
      isSeriesCard: true,
      fromStaticDB: true,
      name: 'Le Seigneur des Anneaux',
      author: 'J.R.R. Tolkien',
      cover_url: 'cover.jpg',
      totalBooks: 3,
      relevanceScore: 96000,
      books: [{ id: 'a' }],
    };
    const wd = {
      isSeriesCard: true,
      isStaticWikidataCard: true,
      wikidata_qid: 'Q15228',
      name: 'Le Seigneur des anneaux',
      author: '',
      cover_url: null,
      totalBooks: 0,
      relevanceScore: 45000,
      books: [],
    };
    const book = { id: 'ol_z', title: 'Un livre', isFromOpenLibrary: true };
    const out = dedupeSeriesCardsByName([curated, wd, book]);
    const seriesCards = out.filter((x) => x.isSeriesCard);
    expect(seriesCards).toHaveLength(1);
    const kept = seriesCards[0];
    expect(kept.isStaticWikidataCard).toBe(true); // Wikidata prioritaire
    expect(kept.cover_url).toBe('cover.jpg'); // couverture récupérée
    expect(kept.totalBooks).toBe(3); // total le plus élevé
    expect(out.find((x) => !x.isSeriesCard)).toBeDefined(); // le livre est conservé
  });
});
