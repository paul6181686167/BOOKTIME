import {
  enrichBookFromCuratedSeries,
  formatBookMetaLine,
  getPagesRead,
  getProgressPercent,
  isDisplayableSubject,
  pickFirstPublisher,
} from '../bookDisplay';
import { attributeBookToSeries, resolveCuratedSeriesByName } from '../seriesAttribution';

describe('getPagesRead', () => {
  test('completed book without current_page shows total pages', () => {
    expect(getPagesRead({ status: 'completed', current_page: null }, 398, 'completed')).toBe(398);
    expect(getProgressPercent({ status: 'completed', current_page: null }, 398, 'completed')).toBe(100);
  });

  test('reading book uses current_page', () => {
    expect(getPagesRead({ status: 'reading', current_page: 40 }, 398, 'reading')).toBe(40);
  });
});

describe('pickFirstPublisher', () => {
  test('keeps a single French publisher from a concatenated list', () => {
    expect(
      pickFirstPublisher('Audible Studios on Brilliance Audio, Into Kustannus Oy, Gallimard')
    ).toBe('Gallimard');
  });
});

describe('isDisplayableSubject', () => {
  test('hides nyt raw identifiers', () => {
    expect(isDisplayableSubject('nyt:hardcover-fiction=2021-05-23')).toBe(false);
    expect(isDisplayableSubject('Science-fiction')).toBe(true);
  });
});

describe('formatBookMetaLine', () => {
  test('joins genre, publisher, year and language', () => {
    expect(
      formatBookMetaLine({
        genre: 'Science-fiction',
        publisher: 'Gallimard',
        publication_year: 2021,
        language: 'fr',
      })
    ).toBe('Science-fiction · Gallimard · 2021 · Français');
  });
});

describe('enrichBookFromCuratedSeries', () => {
  test('complète éditeur, genre et année depuis le catalogue pour un tome HP', () => {
    const book = {
      title: "Harry Potter à l'école des sorciers",
      author: 'J.K. Rowling',
      volume_number: 1,
    };
    const attr = attributeBookToSeries(book);
    const filled = enrichBookFromCuratedSeries(book, attr, 1);
    expect(filled.publisher).toBe('Gallimard Jeunesse');
    expect(filled.genre).toBe('Fantasy');
    expect(filled.isbn).toMatch(/978/);
    expect(filled.total_pages).toBe(320);
  });

  test('n’écrase pas un éditeur déjà présent', () => {
    const book = { title: 'Dune', author: 'Frank Herbert', publisher: 'Pocket' };
    const attr = attributeBookToSeries(book);
    const filled = enrichBookFromCuratedSeries(book, attr, 1);
    expect(filled.publisher).toBe('Pocket');
  });
});

describe('catalogue curé', () => {
  test('Dune a un éditeur et un genre', () => {
    const r = resolveCuratedSeriesByName('Dune');
    expect(r.data.publisher).toBe('Robert Laffont');
    expect(r.data.genre).toBe('Science-fiction');
  });
});
