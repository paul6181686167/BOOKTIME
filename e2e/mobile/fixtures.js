/**
 * Simulation de l'API pour les tests e2e mobiles : aucun backend n'est nécessaire.
 * L'utilisateur est connecté via localStorage et toutes les routes /api/* sont interceptées.
 */
const LONG_SYNOPSIS = Array.from(
  { length: 40 },
  (_, i) => `Paragraphe ${i + 1} du résumé : une phrase assez longue pour remplir la fiche et la faire défiler.`
).join('\n\n');

const BOOKS = [
  {
    id: 'book-1',
    title: "L'Étranger",
    author: 'Albert Camus',
    category: 'roman',
    status: 'to_read',
    description: LONG_SYNOPSIS,
    total_pages: 186,
    current_page: 0,
    cover_url: '',
    isbn: '9782070360024',
    description_source: 'isbn_back_cover',
  },
  {
    id: 'book-2',
    title: 'La Peste',
    author: 'Albert Camus',
    category: 'roman',
    status: 'completed',
    description: LONG_SYNOPSIS,
    total_pages: 336,
    current_page: 336,
    cover_url: '',
    isbn: '9782070360420',
    description_source: 'isbn_back_cover',
  },
];

// Fiche auteur telle que renvoyée par /api/authors/{nom}/profile (cache serveur)
const AUTHOR_PROFILE = {
  found: true,
  author: {
    name: 'Albert Camus',
    bio: LONG_SYNOPSIS,
    genres: ['Roman', 'Essai'],
    birth_date: '1913-11-07',
    death_date: '1960-01-04',
    nationality: 'Française',
    photo_url: '',
  },
  series: [],
  individual_books: Array.from({ length: 25 }, (_, i) => ({
    title: `Œuvre ${i + 1} d'Albert Camus`,
    first_publish_year: 1930 + i,
    cover_url: '',
  })),
};

const USER = {
  id: 'e2e-user',
  email: 'e2e@booktime.test',
  display_name: 'Lecteur E2E',
  name: 'Lecteur E2E',
};

/** Connecte l'utilisateur de test avant le chargement de l'application. */
async function loginAs(page) {
  await page.addInitScript((user) => {
    localStorage.setItem('token', 'e2e-token');
    localStorage.setItem('user', JSON.stringify(user));
    // Pas de bandeau d'accueil / consentement susceptible de masquer l'écran
    localStorage.setItem('booktime_onboarded', '1');
  }, USER);
}

/** Intercepte l'API : renvoie des données fixes, sans jamais sortir sur le réseau. */
async function mockApi(page) {
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url());
    const p = url.pathname;
    const method = route.request().method();
    const json = (body, status = 200) =>
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
        headers: { 'access-control-allow-origin': '*' },
      });

    if (method === 'OPTIONS') {
      // Préambule CORS : le joker « * » ne couvre pas l'en-tête Authorization,
      // on renvoie donc explicitement les en-têtes demandés.
      return route.fulfill({
        status: 204,
        headers: {
          'access-control-allow-origin': '*',
          'access-control-allow-headers':
            route.request().headers()['access-control-request-headers'] || 'authorization, content-type',
          'access-control-allow-methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
        },
      });
    }
    if (p === '/api/books/all') return json(BOOKS);
    if (p === '/api/stats') {
      return json({ total_books: BOOKS.length, completed_books: 1, reading_books: 0, to_read_books: 1 });
    }
    if (p === '/api/auth/me') return json({ ...USER, settings: {} });
    if (p === '/api/collections') return json({ collections: [], version: 0 });
    if (p === '/api/ratings/external') {
      return json({
        ratings: [
          { source: 'openlibrary', label: 'Open Library', score: 4.2, count: 1234, url: 'https://openlibrary.org/works/OL1W', scope: 'book' },
          { source: 'googlebooks', label: 'Google Books', score: 3.5, count: null, url: null, scope: 'book' },
        ],
        links: [{ label: 'Babelio', url: 'https://www.babelio.com/x' }, { label: 'Goodreads', url: 'https://www.goodreads.com/x' }],
      });
    }
    if (/^\/api\/books\/[^/]+\/synopsis$/.test(p)) {
      return json({ description: LONG_SYNOPSIS, source: 'isbn_back_cover', replaced: false });
    }
    if (/^\/api\/authors\/[^/]+\/(profile|ensure)$/.test(p)) return json(AUTHOR_PROFILE);
    if (p === '/api/authors/following') return json({ authors: [] });
    if (/^\/api\/authors\/[^/]+\/books$/.test(p)) return json({ books: AUTHOR_PROFILE.individual_books });
    if (p.startsWith('/api/series')) return json([]);
    if (p.startsWith('/api/notifications')) return json({ notifications: [], unread: 0 });
    return json({});
  });
  // Couvertures et ressources externes : jamais de réseau réel
  await page.route(/^https?:\/\/(?!127\.0\.0\.1|localhost).*/, (route) => {
    const type = route.request().resourceType();
    if (type === 'image') {
      return route.fulfill({
        status: 200,
        contentType: 'image/svg+xml',
        body: '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="3"><rect width="2" height="3" fill="#888"/></svg>',
      });
    }
    return route.abort();
  });
}

module.exports = { BOOKS, AUTHOR_PROFILE, USER, loginAs, mockApi };
