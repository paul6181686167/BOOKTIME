import {
  attributeBookToSeries,
  attachBookToQuerySeries,
  buildWikidataSeriesMatcher,
  enrichWikidataCardFromCurated,
  findCuratedSeriesByQuery,
  resolveSeriesTotalBooks,
} from '../../utils/seriesAttribution';

describe('seriesAttribution', () => {
  test('rattache un tome LOTR (titre de volume) à la série curée', () => {
    const book = { title: "La Communauté de l'Anneau", author: 'J.R.R. Tolkien' };
    const attr = attributeBookToSeries(book);
    expect(attr).not.toBeNull();
    expect(attr.source).toBe('curated');
    expect(attr.seriesName).toBe('Le Seigneur des Anneaux');
  });

  test('rattache un tome anglais LOTR via la série de la requête + auteur (inter-langues)', () => {
    // Titre anglais absent des volume_titles FR : non rattachable par titre seul.
    const book = { title: 'The Fellowship of the Ring', author: 'J.R.R. Tolkien' };
    expect(attributeBookToSeries(book)).toBeNull();

    // Mais via la requête "seigneur des anneaux" + auteur Tolkien → rattaché.
    const querySeries = findCuratedSeriesByQuery('seigneur des anneaux');
    expect(querySeries).not.toBeNull();
    const attr = attachBookToQuerySeries(book, querySeries);
    expect(attr).not.toBeNull();
    expect(attr.seriesName).toBe('Le Seigneur des Anneaux');
  });

  test('le rattachement par requête respecte les exclusions (Le Hobbit non masqué)', () => {
    const querySeries = findCuratedSeriesByQuery('seigneur des anneaux');
    const hobbit = { title: 'The Hobbit', author: 'J.R.R. Tolkien' };
    expect(attachBookToQuerySeries(hobbit, querySeries)).toBeNull();
  });

  test('rattache "Red Rising" via variation curée, même sans saga OL', () => {
    const book = { title: 'Red Rising', author: 'Pierce Brown' };
    const attr = attributeBookToSeries(book);
    expect(attr).not.toBeNull();
    expect(attr.source).toBe('curated');
    expect(attr.seriesName).toBe('Red Rising');
    // Le compteur reflète le total curé, jamais le nombre de livres trouvés (même si supérieur).
    expect(resolveSeriesTotalBooks(attr.seriesData, 1)).toBe(attr.seriesData.volumes);
    expect(resolveSeriesTotalBooks(attr.seriesData, 99)).toBe(attr.seriesData.volumes);
  });

  test('enrichWikidataCardFromCurated remplit auteur + total curé pour LOTR', () => {
    const enriched = enrichWikidataCardFromCurated('Le Seigneur des anneaux', {
      author: '',
      totalBooks: 999,
    });
    expect(enriched.author).toBe('J.R.R. Tolkien');
    expect(enriched.totalBooks).toBe(3); // total curé, pas le work_count Wikidata
  });

  test('enrichWikidataCardFromCurated garde le repli si série non curée', () => {
    const enriched = enrichWikidataCardFromCurated('Série Totalement Inconnue ZZZ', {
      author: 'Auteur Repli',
      totalBooks: 7,
    });
    expect(enriched.author).toBe('Auteur Repli');
    expect(enriched.totalBooks).toBe(7);
  });

  test('un vrai standalone reste non rattaché', () => {
    const book = { title: 'Un Roman Totalement Inédit Sans Série', author: 'Auteur Inconnu XYZ' };
    expect(attributeBookToSeries(book)).toBeNull();
  });

  test('rattachement par saga quand ni curé ni Wikidata', () => {
    const book = { title: 'Tome obscur', author: 'Quelqu’un', saga: 'Ma Saga Perso' };
    const attr = attributeBookToSeries(book);
    expect(attr).not.toBeNull();
    expect(attr.source).toBe('saga');
    expect(attr.seriesName).toBe('Ma Saga Perso');
  });

  test('matcher Wikidata rattache un livre dont le titre = nom de série WD (hors curé)', () => {
    // Série volontairement absente du référentiel curé pour tester la voie Wikidata.
    const matcher = buildWikidataSeriesMatcher([
      { qid: 'Q999', name_fr: 'Série Wikidata Fictive Inédite' },
    ]);
    const attr = attributeBookToSeries(
      { title: 'Série Wikidata Fictive Inédite', author: 'Auteur Test' },
      { wikidataMatcher: matcher }
    );
    expect(attr).not.toBeNull();
    expect(attr.source).toBe('wikidata');
    expect(attr.wikidata_qid).toBe('Q999');
  });
});
