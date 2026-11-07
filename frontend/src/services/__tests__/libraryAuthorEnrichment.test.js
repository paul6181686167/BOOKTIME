import { scheduleLibraryAuthorEnrichment } from '../libraryAuthorEnrichment';

describe('préchargement des fiches auteurs de la bibliothèque', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
    delete global.fetch;
  });

  test('enchaîne les lots jusqu’à couvrir toute la bibliothèque', async () => {
    const remaining = [10, 4, 0];
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ ensured_count: 6, total_library_authors: 20, remaining: remaining.shift() }),
      })
    );

    scheduleLibraryAuthorEnrichment({ books: [{ author: 'Albert Camus, Autre' }, { author: 'Victor Hugo' }] });
    // Jest 27 : pas de version asynchrone des faux timers, on laisse les promesses se résoudre à la main
    for (let i = 0; i < 10; i += 1) {
      jest.advanceTimersByTime(3000);
      for (let j = 0; j < 30; j += 1) {
        // eslint-disable-next-line no-await-in-loop
        await Promise.resolve();
      }
    }

    expect(global.fetch).toHaveBeenCalledTimes(3);
    expect(String(global.fetch.mock.calls[0][0])).toContain('/api/authors/ensure-from-library?limit=');
  });
});
