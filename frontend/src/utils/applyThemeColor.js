/** Chrome Android : force la couleur de barre système (= fond), jamais l’accent #16a34a. */

const MANIFEST_BASE = {
  short_name: 'Booktime',
  name: 'Booktime – Ta bibliothèque personnelle',
  description: 'Suis tes lectures, découvre des séries et gère ta bibliothèque.',
  icons: [
    { src: '/favicon.ico', sizes: '64x64 32x32 24x24 16x16', type: 'image/x-icon' },
    { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
    { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
    { src: '/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
  ],
  start_url: '/?homescreen=1&v=12',
  scope: '/',
  id: 'booktime-v12-chrome',
  display: 'standalone',
  display_override: ['standalone', 'browser'],
  orientation: 'portrait-primary',
  categories: ['books', 'lifestyle', 'entertainment'],
  lang: 'fr',
  dir: 'ltr',
  prefer_related_applications: false,
};

let blobUrl = null;

function setBootBackground(color) {
  let style = document.getElementById('bt-boot-bg');
  if (!style) {
    style = document.createElement('style');
    style.id = 'bt-boot-bg';
    document.head.appendChild(style);
  }
  style.textContent = `html,body,#root{background-color:${color} !important;}`;
}

function replaceThemeColorMetas(color) {
  document.querySelectorAll('meta[name="theme-color"]').forEach((el) => el.remove());

  const specs = [
    { id: 'bt-theme-color', media: null },
    { id: 'bt-theme-color-light', media: '(prefers-color-scheme: light)' },
    { id: 'bt-theme-color-dark', media: '(prefers-color-scheme: dark)' },
  ];

  specs.forEach(({ id, media }) => {
    const meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    meta.id = id;
    if (media) meta.setAttribute('media', media);
    meta.setAttribute('content', color);
    document.head.appendChild(meta);
  });

  // msApplication (Edge / anciens Chromium)
  let ms = document.querySelector('meta[name="msapplication-navbutton-color"]');
  if (!ms) {
    ms = document.createElement('meta');
    ms.setAttribute('name', 'msapplication-navbutton-color');
    document.head.appendChild(ms);
  }
  ms.setAttribute('content', color);
}

function syncManifestTheme(color) {
  const manifest = {
    ...MANIFEST_BASE,
    theme_color: color,
    background_color: color,
  };
  const blob = new Blob([JSON.stringify(manifest)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  let link = document.querySelector('link[rel="manifest"]');
  if (!link) {
    link = document.createElement('link');
    link.setAttribute('rel', 'manifest');
    document.head.appendChild(link);
  }
  link.setAttribute('href', url);
  if (blobUrl) URL.revokeObjectURL(blobUrl);
  blobUrl = url;
}

/**
 * Applique la couleur de chrome (barre système + fonds document).
 * @param {string} color hex (#050505, #234f37, #bce8cb)
 */
export function applyThemeColor(color) {
  if (typeof document === 'undefined' || !color) return;

  const root = document.documentElement;
  root.style.backgroundColor = color;
  if (document.body) document.body.style.backgroundColor = color;
  const appRoot = document.getElementById('root');
  if (appRoot) appRoot.style.backgroundColor = color;

  setBootBackground(color);
  replaceThemeColorMetas(color);
  syncManifestTheme(color);
}
