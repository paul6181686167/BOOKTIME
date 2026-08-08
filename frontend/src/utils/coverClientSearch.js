/**
 * Recherche de couverture côté navigateur :
 * Open Library → Wikipedia → Google Books (file anti-429).
 * Les échecs ne sont PAS mis en cache (évite de bloquer un livre après un timeout).
 */
import { isUsableCoverUrl, normalizeCoverUrl } from './helpers';
import { sanitizeBookTitle } from './openLibraryBookDisplay';

const cache = new Map(); // uniquement les succès
const CACHE_PREFIX = 'bt_cover_v5:';

let gbCooldownUntil = 0;

const cleanTitle = (title) => {
  let t = sanitizeBookTitle(title);
  t = t.replace(
    /\s*[,:\-–—]?\s*(tome|t\.?|vol\.?|volume|book|n°|no\.?)\s*\d+.*$/i,
    ''
  );
  return t.trim() || sanitizeBookTitle(title);
};

/** Variantes FR/EN pour titres courts (ex. Choses → Les Choses). */
const titleVariants = (title) => {
  const base = cleanTitle(title);
  if (!base) return [];
  const out = [base];
  const lower = base.toLowerCase();
  const hasArticle =
    /^(les|le|la|l'|l’|the|a|an)\s+/i.test(base) || /^l['’]/i.test(base);
  if (!hasArticle) {
    out.push(`Les ${base}`, `Le ${base}`, `La ${base}`, `L'${base}`, `The ${base}`);
  }
  // Dédup
  const seen = new Set();
  return out.filter((t) => {
    const k = t.toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
};

const cacheKey = (title, author, isbn) =>
  `${cleanTitle(title).toLowerCase()}|${String(author || '')
    .toLowerCase()
    .trim()}|${String(isbn || '').replace(/\D/g, '')}`;

function readSession(key) {
  try {
    return sessionStorage.getItem(CACHE_PREFIX + key);
  } catch (_) {
    return null;
  }
}

function writeSession(key, value) {
  if (!value) return;
  try {
    sessionStorage.setItem(CACHE_PREFIX + key, value);
  } catch (_) {
    /* quota */
  }
}

export function hardenGoogleBooksCover(url) {
  if (!url) return '';
  let u = String(url).replace('http://', 'https://');
  u = u.replace(/([?&])zoom=\d/i, '$1zoom=0');
  if (!/[?&]edge=/.test(u)) {
    u += (u.includes('?') ? '&' : '?') + 'edge=curl';
  }
  return u;
}

async function fetchJson(url, timeoutMs = 12000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    if (r.status === 429) return { __rateLimited: true };
    if (!r.ok) return null;
    return r.json();
  } catch (_) {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function coverFromCoverI(coverI) {
  const n = Number(coverI);
  if (!Number.isFinite(n) || n <= 0) return null;
  return `https://covers.openlibrary.org/b/id/${n}-M.jpg`;
}

async function coverFromOlWork(olKey) {
  const m = String(olKey || '').match(/(OL\d+W)\b/i);
  if (!m) return null;
  const data = await fetchJson(
    `https://openlibrary.org/works/${m[1]}.json`,
    10000
  );
  if (!data || data.__rateLimited) return null;
  for (const c of data.covers || []) {
    const url = coverFromCoverI(c);
    if (url) return url;
  }
  return null;
}

async function coverFromIsbn(isbn) {
  const clean = String(isbn || '').replace(/[^0-9Xx]/g, '');
  if (clean.length < 10) return null;
  const data = await fetchJson(
    `https://openlibrary.org/isbn/${clean}.json`,
    10000
  );
  if (data && !data.__rateLimited) {
    for (const c of data.covers || []) {
      const url = coverFromCoverI(c);
      if (url) return url;
    }
    if (data.works?.[0]?.key) {
      const fromWork = await coverFromOlWork(data.works[0].key);
      if (fromWork) return fromWork;
    }
  }
  // Pas d'URL ISBN brute : souvent une image vide
  return null;
}

async function searchOpenLibrary(title, author) {
  const variants = titleVariants(title);
  if (!variants.length) return null;

  for (const base of variants.slice(0, 3)) {
    const q = author ? `${base} ${author}` : base;
    const data = await fetchJson(
      `https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=8&fields=cover_i,isbn,key,title`,
      12000
    );
    if (!data) continue;
    if (data.__rateLimited) return '__429__';
    for (const doc of data.docs || []) {
      const url = coverFromCoverI(doc?.cover_i);
      if (url) return url;
    }
  }
  return null;
}

const norm = (s) =>
  String(s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

/**
 * Wikipedia : refuse les pages auteur (sinon photo d'auteur au lieu du livre).
 */
async function searchWikipediaCover(title, author) {
  const base = cleanTitle(title);
  if (!base) return null;
  const authorNorm = norm(author);
  const titleNorm = norm(base);

  const pickThumb = (data, pageTitle) => {
    if (!data || data.__rateLimited) return null;
    if (data.type === 'disambiguation') return null;
    const pageNorm = norm(pageTitle || data.title);
    const desc = String(data.description || data.extract || '').slice(0, 280);
    const blob = `${pageTitle || ''} ${data.title || ''} ${desc}`;
    // Page personne (acteur, auteur…) → photo, pas couverture
    const isPerson =
      /\b(actress|actor|actrice|acteur|singer|chanteur|chanteuse|écrivain|écrivaine|writer|author|novelist|romancier|romanci[eè]re|personnalité|politician|footballer|footballeur|painter|peintre)\b/i.test(
        desc
      ) &&
      !/\b(novel|roman|novella|livre|récit|ouvrage|thriller|manga|bande dessin)/i.test(blob);
    if (isPerson) return null;
    // Page = nom de l'auteur seul → ignorer
    if (authorNorm && pageNorm === authorNorm) return null;
    if (authorNorm && pageNorm.startsWith(authorNorm) && !pageNorm.includes(titleNorm.split(' ')[0] || '___')) {
      // "Georges Perec" alors qu'on cherche "Choses"
      if (!titleNorm.split(/\s+/).some((w) => w.length > 3 && pageNorm.includes(w))) {
        return null;
      }
    }
    // Exiger un chevauchement de mots significatifs avec le titre du livre
    const titleWords = titleNorm.split(/\s+/).filter((w) => w.length > 3);
    if (titleWords.length >= 2) {
      const hits = titleWords.filter((w) => pageNorm.includes(w)).length;
      if (hits < Math.min(2, titleWords.length)) return null;
    }
    const thumb = data.originalimage?.source || data.thumbnail?.source;
    if (!thumb || /\.svg($|\?)/i.test(thumb)) return null;
    // Portraits Commons fréquents
    if (/\/(commons\/)?a\/a[0-9]\/.*portrait/i.test(thumb)) return null;
    return String(thumb).split('?')[0].replace('http://', 'https://');
  };

  const summary = async (lang, pageTitle) => {
    const url = `https://${lang}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(
      pageTitle
    )}`;
    return pickThumb(await fetchJson(url, 7000), pageTitle);
  };

  const directSlugs = [
    ...titleVariants(title),
    `${base} (roman)`,
    `${base} (novel)`,
    `${base} (série)`,
    `${base} (series)`,
  ];

  for (const lang of ['fr', 'en']) {
    for (const slug of directSlugs.slice(0, 6)) {
      const hit = await summary(lang, slug);
      if (hit) return hit;
    }

    const q = encodeURIComponent(
      author ? `"${base}" ${author}` : `"${base}" roman OR novel OR livre`
    );
    const search = await fetchJson(
      `https://${lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch=${q}&srlimit=6&format=json&origin=*`,
      7000
    );
    for (const row of search?.query?.search || []) {
      if (!row?.title) continue;
      if (authorNorm && norm(row.title) === authorNorm) continue;
      const hit = await summary(lang, row.title);
      if (hit) return hit;
    }
  }
  return null;
}

async function searchGoogleBooks(title, author, isbn) {
  if (Date.now() < gbCooldownUntil) return null;

  let q = '';
  const clean = String(isbn || '').replace(/[^0-9Xx]/g, '');
  if (clean.length >= 10) {
    q = `isbn:${clean}`;
  } else {
    const parts = [];
    const t = cleanTitle(title);
    if (t) parts.push(`intitle:${t}`);
    if (author) parts.push(`inauthor:${author}`);
    q = parts.join('+') || t;
  }
  if (!q) return null;

  const data = await fetchJson(
    `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&maxResults=8&printType=books`,
    10000
  );
  if (data?.__rateLimited) {
    gbCooldownUntil = Date.now() + 12 * 60 * 1000;
    return '__429__';
  }
  if (!data) return null;

  for (const item of data.items || []) {
    const links = item?.volumeInfo?.imageLinks || {};
    const thumb =
      links.medium ||
      links.large ||
      links.thumbnail ||
      links.smallThumbnail;
    if (thumb) return hardenGoogleBooksCover(thumb);
  }
  return null;
}

const queue = [];
let busy = false;

function pump() {
  if (busy || !queue.length) return;
  busy = true;
  const job = queue.shift();
  Promise.resolve()
    .then(job.run)
    .then(job.resolve, job.reject)
    .finally(() => {
      setTimeout(() => {
        busy = false;
        pump();
      }, 280);
    });
}

function enqueue(run) {
  return new Promise((resolve, reject) => {
    queue.push({ run, resolve, reject });
    pump();
  });
}

/**
 * @param {string} title
 * @param {string} [author]
 * @param {{ isbn?: string, ol_key?: string }} [opts]
 */
export async function searchCoverInBrowser(title, author = '', opts = {}) {
  const a = author && author !== 'Auteur inconnu' ? author : '';
  const isbn = opts.isbn || '';
  const olKey = opts.ol_key || '';
  const key = cacheKey(title, a, isbn);

  // Cache succès uniquement
  if (cache.has(key)) {
    const hit = cache.get(key);
    if (hit) return hit;
  }
  const sessionHit = readSession(key);
  if (sessionHit) {
    cache.set(key, sessionHit);
    return sessionHit;
  }

  return enqueue(async () => {
    if (cache.get(key)) return cache.get(key);

    let cover = null;

    // 1) OL work / ISBN (métadonnées → cover_i)
    if (olKey) {
      cover = await coverFromOlWork(olKey);
    }
    if (!isUsableCoverUrl(cover) && isbn) {
      cover = await coverFromIsbn(isbn);
    }

    // 2) Open Library search (souvent le plus fiable pour les romans)
    if (!isUsableCoverUrl(cover)) {
      cover = await searchOpenLibrary(title, a);
      if (cover === '__429__') cover = null;
    }

    // 3) Wikipedia (séries / classiques) — pas les pages auteur
    if (!isUsableCoverUrl(cover)) {
      cover = await searchWikipediaCover(title, a);
    }

    // 4) Google Books — le front filtre les « image not available »
    if (!isUsableCoverUrl(cover)) {
      cover = await searchGoogleBooks(title, a, isbn);
      if (cover === '__429__') cover = null;
      else if (cover) cover = hardenGoogleBooksCover(cover);
    }

    if (isUsableCoverUrl(cover)) {
      const finalUrl = normalizeCoverUrl(cover) || cover;
      cache.set(key, finalUrl);
      writeSession(key, finalUrl);
      return finalUrl;
    }

    // Pas de cache négatif
    return null;
  });
}

export default searchCoverInBrowser;
