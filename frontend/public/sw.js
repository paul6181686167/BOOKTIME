/* Booktime PWA Service Worker */
const SW_VERSION = 'booktime-v7-honeycomb';
const SHELL_CACHE = `${SW_VERSION}-shell`;
const RUNTIME_CACHE = `${SW_VERSION}-runtime`;
const API_CACHE = `${SW_VERSION}-api`;

const SHELL_URLS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
  '/icon-192.png',
  '/icon-512.png',
  '/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith('booktime-') && !key.startsWith(SW_VERSION))
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

function isApiLibraryRequest(url) {
  // Bibliothèque : stale-while-revalidate (affichage rapide).
  // Jamais les résolutions méta (résumé / pages).
  const path = url.pathname;
  const full = path + url.search;
  if (/resolve-synopsis|resolve-pages|\/synopsis/i.test(full)) {
    return false;
  }
  if (path.includes('/api/books')) return true;
  if (path.includes('/api/series/library')) return true;
  if (path.includes('/api/series/reading-preferences')) return true;
  return false;
}

function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

function isStaticAsset(url) {
  return /\.(?:js|css|png|jpg|jpeg|webp|svg|ico|woff2?|ttf|json)$/i.test(url.pathname);
}

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw error;
  }
}

async function isNonEmptyJsonArray(response) {
  try {
    const data = await response.clone().json();
    if (Array.isArray(data)) return data.length > 0;
    if (Array.isArray(data?.items)) return data.items.length > 0;
    if (Array.isArray(data?.books)) return data.books.length > 0;
    if (Array.isArray(data?.series)) return data.series.length > 0;
    // Objet non-liste (stats, etc.) : OK à cacher
    return data && typeof data === 'object';
  } catch (_) {
    return false;
  }
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then(async (response) => {
      if (response && response.ok) {
        // Ne pas mettre en cache une bibliothèque vide (évite d'écraser l'UI)
        const path = new URL(request.url).pathname;
        const isLib =
          path.includes('/api/books') || path.includes('/api/series/library');
        if (!isLib || (await isNonEmptyJsonArray(response))) {
          cache.put(request, response.clone());
        }
      }
      return response;
    })
    .catch(() => cached);

  return cached || networkPromise;
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response && response.ok) {
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Same-origin navigations → network first, fallback shell
  if (isNavigationRequest(request) && url.origin === self.location.origin) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put('/index.html', copy));
          return response;
        })
        .catch(async () => {
          const cache = await caches.open(SHELL_CACHE);
          return (
            (await cache.match('/index.html')) ||
            (await cache.match('/')) ||
            new Response('Hors ligne', {
              status: 503,
              headers: { 'Content-Type': 'text/plain; charset=utf-8' },
            })
          );
        })
    );
    return;
  }

  // Bibliothèque → cache d'abord (puis refresh réseau) pour mobile / Render lent
  if (isApiLibraryRequest(url)) {
    event.respondWith(staleWhileRevalidate(request, API_CACHE));
    return;
  }

  // Same-origin static assets
  if (url.origin === self.location.origin && isStaticAsset(url)) {
    event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE));
    return;
  }

  // Same-origin other GETs
  if (url.origin === self.location.origin) {
    event.respondWith(staleWhileRevalidate(request, RUNTIME_CACHE));
  }
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
