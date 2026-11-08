import {
  formatBookMetaLine,
  getPagesRead,
  getProgressPercent,
  isDisplayableSubject,
  pickFirstPublisher,
} from '../bookDisplay';

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
