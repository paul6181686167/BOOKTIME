import { clearExternalRatingsCache, fetchExternalRatings } from '../externalRatingsService';

beforeEach(() => {
  clearExternalRatingsCache();
  localStorage.setItem('token', 't');
  global.fetch = jest.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({ ratings: [{ source: 'a', score: 4 }], links: [] }) })
  );
});
afterEach(() => {
  localStorage.clear();
  delete global.fetch;
});

test('interroge le serveur avec le jeton puis sert la réponse depuis la mémoire', async () => {
  const query = { title: 'La Peste', author: 'Camus', kind: 'book' };
  const a = await fetchExternalRatings(query);
  const b = await fetchExternalRatings(query);
  expect(a).toEqual(b);
  expect(global.fetch).toHaveBeenCalledTimes(1);
  const [url, options] = global.fetch.mock.calls[0];
  expect(url).toContain('/api/ratings/external?');
  expect(url).toContain('title=La+Peste');
  expect(options.headers.Authorization).toBe('Bearer t');
});

test('ne mémorise pas une réponse vide', async () => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ ratings: [], links: [] }) }));
  await fetchExternalRatings({ title: 'Rien' });
  await fetchExternalRatings({ title: 'Rien' });
  expect(global.fetch).toHaveBeenCalledTimes(2);
});

test('sans connexion ou sans titre, aucune requête', async () => {
  localStorage.removeItem('token');
  expect(await fetchExternalRatings({ title: 'X' })).toEqual({ ratings: [], links: [] });
  localStorage.setItem('token', 't');
  expect(await fetchExternalRatings({ title: '' })).toEqual({ ratings: [], links: [] });
  expect(global.fetch).not.toHaveBeenCalled();
});

test('signale une erreur serveur', async () => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 500 }));
  await expect(fetchExternalRatings({ title: 'Erreur' })).rejects.toThrow('HTTP 500');
});
