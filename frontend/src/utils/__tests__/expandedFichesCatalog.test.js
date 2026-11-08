import {
  indexExpandedSeriesForTests,
  matchExpandedSeries,
  resetExpandedCatalog,
  resolveExpandedSeriesByName,
  resolveExpandedSeriesByVolumeTitle,
} from '../expandedFichesCatalog';
import { attributeBookToSeries } from '../seriesAttribution';
import SearchOptimizer from '../searchOptimizer';

const SAMPLE = [
  {
    key: 'shannara',
    qid: 'Q123',
    name: 'Shannara',
    name_en: 'The Sword of Shannara series',
    authors: ['Terry Brooks'],
    category: 'roman',
    volumes: 3,
    volume_titles: { 1: 'Les Épées de Shannara', 2: 'Les Pierres de Shannara' },
    volume_details: { 1: { cover_url: 'https://covers.openlibrary.org/b/olid/OL1W-L.jpg' } },
    cover_url: 'https://covers.openlibrary.org/b/olid/OL1W-L.jpg',
    wikidata_qid: 'Q123',
  },
];

afterEach(() => {
  resetExpandedCatalog();
});

test('matchExpandedSeries trouve une série par préfixe', () => {
  indexExpandedSeriesForTests(SAMPLE);
  const hits = matchExpandedSeries('shan');
  expect(hits.length).toBeGreaterThan(0);
  expect(hits[0].series.name).toBe('Shannara');
});

test('résout un tome par son titre', () => {
  indexExpandedSeriesForTests(SAMPLE);
  const hit = resolveExpandedSeriesByVolumeTitle('Les Épées de Shannara');
  expect(hit.data.name).toBe('Shannara');
});

test('attribution d’un tome étendu hors curé', () => {
  indexExpandedSeriesForTests(SAMPLE);
  const attr = attributeBookToSeries({
    title: 'Les Épées de Shannara',
    author: 'Terry Brooks',
  });
  expect(attr).not.toBeNull();
  expect(attr.source).toBe('expanded');
  expect(attr.seriesName).toBe('Shannara');
});

test('la carte de recherche expose la couverture du tome 1', () => {
  indexExpandedSeriesForTests(SAMPLE);
  const cards = SearchOptimizer.generateSeriesCardsForSearch('Shannara', []);
  const card = cards.find((c) => c.name === 'Shannara');
  expect(card).toBeTruthy();
  expect(card.cover_url).toContain('OL1W');
  expect(card.totalBooks).toBe(3);
  expect(card.wikidata_qid).toBe('Q123');
});

test('sans chargement, le catalogue étendu ne masque pas un standalone', () => {
  expect(resolveExpandedSeriesByName('Shannara')).toBeNull();
  expect(
    attributeBookToSeries({ title: 'Un Roman Totalement Inédit Sans Série', author: 'Auteur Inconnu XYZ' })
  ).toBeNull();
});
