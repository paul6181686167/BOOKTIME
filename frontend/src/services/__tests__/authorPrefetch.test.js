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
});
