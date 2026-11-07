import { clearAuthorPrefetch, prefetchAuthor, primaryAuthor, readAuthorProfile } from '../authorPrefetch';

const PROFILE = { found: true, author: { name: 'Camus', bio: 'Écrivain français.' }, series: [], individual_books: [] };

let calls;

function mockFetch(handler) {
  calls = [];
  global.fetch = jest.fn((url, options = {}) => {
    calls.push({ url: String(url), method: options.method || 'GET' });
    const body = handler(String(url), options.method || 'GET');
    return Promise.resolve({ ok: body !== null, json: () => Promise.resolve(body) });
  });
}

beforeEach(() => {
  clearAuthorPrefetch();
});

afterEach(() => {
  delete global.fetch;
});

describe('authorPrefetch', () => {
  test('utilise le premier auteur d’une liste', () => {
    expect(primaryAuthor('Albert Camus, Autre Auteur')).toBe('Albert Camus');
    expect(primaryAuthor('  Hugo ')).toBe('Hugo');
  });

  test('lit la fiche une seule fois, même demandée plusieurs fois', async () => {
    mockFetch(() => PROFILE);
    const [a, b] = await Promise.all([readAuthorProfile('Camus'), readAuthorProfile('camus')]);
    expect(a).toEqual(PROFILE);
    expect(b).toEqual(PROFILE);
    await readAuthorProfile('Camus');
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toContain('/api/authors/Camus/profile');
  });

  test('construit la fiche manquante une fois, puis la garde en mémoire', async () => {
    mockFetch((url, method) => (method === 'POST' ? PROFILE : { found: false }));
    const built = await prefetchAuthor('Camus, Coauteur');
    expect(built).toEqual(PROFILE);
    expect(calls.map((c) => `${c.method} ${decodeURIComponent(c.url.split('/api/authors/')[1])}`)).toEqual([
      'GET Camus/profile',
      'POST Camus/ensure',
    ]);
    // L'écran auteur retrouve la fiche sans nouvelle requête
    expect(await readAuthorProfile('Camus')).toEqual(PROFILE);
    expect(calls).toHaveLength(2);
  });

  test('ne redemande pas la construction d’une fiche introuvable', async () => {
    mockFetch(() => ({ found: false }));
    await prefetchAuthor('Inconnu');
    await prefetchAuthor('Inconnu');
    expect(calls.filter((c) => c.method === 'POST')).toHaveLength(1);
  });

  test('ignore les auteurs inconnus', async () => {
    mockFetch(() => PROFILE);
    expect(await prefetchAuthor('Auteur inconnu')).toBeNull();
    expect(await readAuthorProfile('')).toBeNull();
    expect(calls).toHaveLength(0);
  });

  describe('hors ligne', () => {
    test('garde la dernière fiche lue et la ressert sans réseau', async () => {
      localStorage.clear();
      mockFetch(() => PROFILE);
      await readAuthorProfile('Camus');
      expect(JSON.parse(localStorage.getItem('booktime_author_profile:camus')).author.name).toBe('Camus');

      clearAuthorPrefetch();
      global.fetch = jest.fn(() => Promise.reject(new TypeError('Failed to fetch')));
      expect(await readAuthorProfile('Camus')).toEqual(PROFILE);
      // pas mémorisée : au retour du réseau, la vraie fiche est relue
      mockFetch(() => ({ found: true, author: { name: 'Camus', bio: 'À jour' } }));
      expect((await readAuthorProfile('Camus')).author.bio).toBe('À jour');
    });

    test('ne renvoie rien si la fiche n’a jamais été consultée', async () => {
      localStorage.clear();
      global.fetch = jest.fn(() => Promise.reject(new TypeError('Failed to fetch')));
      expect(await readAuthorProfile('Inconnu Total')).toBeNull();
    });

    test('limite le nombre de fiches conservées', async () => {
      localStorage.clear();
      mockFetch(() => PROFILE);
      for (let i = 0; i < 45; i += 1) {
        // eslint-disable-next-line no-await-in-loop
        await readAuthorProfile(`Auteur ${i}`);
      }
      const stored = Object.keys(localStorage).filter((k) => k.startsWith('booktime_author_profile:'));
      expect(stored).toHaveLength(40);
      expect(localStorage.getItem('booktime_author_profile:auteur 0')).toBeNull();
      expect(localStorage.getItem('booktime_author_profile:auteur 44')).not.toBeNull();
    });
  });
});
