/**
 * Recherche de couverture côté navigateur :
 * Open Library → IA/Amazon/AbeBooks → Wikipedia → Google Books.
 * Les échecs ne sont PAS mis en cache (évite de bloquer un livre après un timeout).
 */
import { isUsableCoverUrl, normalizeCoverUrl } from './helpers';
import { sanitizeBookTitle } from './openLibraryBookDisplay';

const cache = new Map(); // uniquement les succès
const CACHE_PREFIX = 'bt_cover_v6:';

let gbCooldownUntil = 0;

const cleanTitle = (title) => {
  let t = sanitizeBookTitle(title);
  t = t.replace(
    /\s*[,:\-–—]?\s*(tome|t\.?|vol\.?|volume|book|n°|no\.?)\s*\d+.*$/i,
    ''
  );
  // Ponctuation de fin (questions FR)
  t = t.replace(/[?？!！.…]+$/g, '').trim();
  return t.trim() || sanitizeBookTitle(title);
};

const norm = (s) =>
  String(s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();

/** Score de proximité titre (0–100). */
function titleScore(query, candidate) {
  const q = norm(query);
  const c = norm(candidate);
  if (!q || !c) return 0;
  if (q === c) return 100;
  if (c.startsWith(q) || q.startsWith(c)) return 90;
  if (c.includes(q) || q.includes(c)) return 75;
  const qw = q.split(/\s+/).filter((w) => w.length > 2);
  if (!qw.length) return 0;
  const hits = qw.filter((w) => c.includes(w)).length;
  return Math.round((hits / qw.length) * 70);
}

/**
 * Variantes de recherche : articles, typos fréquents, corruption OL « Cui » ↔ Q.I.
 */
const titleVariants = (title) => {
  const base = cleanTitle(title);
  if (!base) return [];
  const out = [base];

  // Typos / orthographes proches
  const typoMap = [
    [/\bau pied du paradis\b/i, 'Un pied au paradis'],
    [/\bun pied au paradis\b/i, 'Au pied du paradis'],
    [/\bjulitte\b/i, 'Juliette'],
  ];
  for (const [re, repl] of typoMap) {
    if (re.test(base)) out.push(base.replace(re, repl));
  }

  // Open Library a parfois indexé « Cui » au lieu de « Q.I. » / « QI »
  if (/\bq\.?\s*i\.?\b/i.test(base) || /\bqi\b/i.test(base)) {
    out.push(base.replace(/\bq\.?\s*i\.?\b/gi, 'Cui').replace(/\bqi\b/gi, 'Cui'));
    out.push(base.replace(/\bq\.?\s*i\.?\b/gi, 'QI').replace(/\bcui\b/gi, 'QI'));
  }
  if (/\bcui\b/i.test(base)) {
    out.push(base.replace(/\bcui\b/gi, 'Q.I.'));
    out.push(base.replace(/\bcui\b/gi, 'QI'));
  }

  const hasArticle = /^(les|le|la|l['’]|un|une|the|a|an)\s+/i.test(base);
  if (!hasArticle) {
    out.push(`Les ${base}`, `Le ${base}`, `La ${base}`, `L'${base}`, `Un ${base}`, `The ${base}`);
  }

  // Sans accents
  const folded = base.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  if (folded !== base) out.push(folded);

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

/** ISBN-13 (978…) → ISBN-10 pour les CDN Amazon. */
export function isbn13to10(isbn) {
  const d = String(isbn || '').replace(/[^0-9Xx]/g, '');
  if (d.length === 10) return d.toUpperCase();
  if (d.length !== 13 || !d.startsWith('978')) return null;
  const core = d.slice(3, 12);
  let sum = 0;
  for (let i = 0; i < 9; i += 1) sum += (10 - i) * parseInt(core[i], 10);
  const check = (11 - (sum % 11)) % 11;
  return core + (check === 10 ? 'X' : String(check));
}

function pickBestIsbn(isbns = []) {
  const list = (isbns || []).map((x) => String(x).replace(/[^0-9Xx]/g, '')).filter(Boolean);
  const isbn13 = list.find((x) => x.length === 13 && x.startsWith('978'));
  const isbn10 = list.find((x) => x.length === 10) || (isbn13 ? isbn13to10(isbn13) : null);
  return { isbn10, isbn13: isbn13 || null };
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

function coverFromOcaid(ocaid) {
  const id = String(ocaid || '').trim();
  if (!id || id.length < 3) return null;
  return `https://archive.org/services/img/${encodeURIComponent(id)}`;
}

function coverFromAmazonIsbn(isbn) {
  const isbn10 = isbn13to10(isbn);
  if (!isbn10) return null;
  return `https://images-na.ssl-images-amazon.com/images/P/${isbn10}.01.LZZZZZZZ.jpg`;
}

function coverFromAbeBooksIsbn(isbn) {
  const d = String(isbn || '').replace(/[^0-9Xx]/g, '');
  if (d.length < 10) return null;
  return `https://pictures.abebooks.com/isbn/${d}-us.jpg`;
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

  // 1) Amazon (ISBN-10) — souvent le seul à avoir les éditions FR récentes
  const amz = coverFromAmazonIsbn(clean);
  if (amz) return amz;

  // 2) AbeBooks
  const abe = coverFromAbeBooksIsbn(clean);
  if (abe) return abe;

  // 3) OL métadonnées édition
  const data = await fetchJson(
    `https://openlibrary.org/isbn/${clean}.json`,
    10000
  );
  if (data && !data.__rateLimited) {
    for (const c of data.covers || []) {
      const url = coverFromCoverI(c);
      if (url) return url;
    }
    if (data.ocaid) {
      const ia = coverFromOcaid(data.ocaid);
      if (ia) return ia;
    }
    if (data.works?.[0]?.key) {
      const fromWork = await coverFromOlWork(data.works[0].key);
      if (fromWork) return fromWork;
    }
  }
  return null;
}

async function coverFromEditionKey(editionKey) {
  const m = String(editionKey || '').match(/(OL\d+M)\b/i);
  if (!m) return null;
  const data = await fetchJson(
    `https://openlibrary.org/books/${m[1]}.json`,
    10000
  );
  if (!data || data.__rateLimited) return null;
  for (const c of data.covers || []) {
    const url = coverFromCoverI(c);
    if (url) return url;
  }
  if (data.ocaid) {
    const ia = coverFromOcaid(data.ocaid);
    if (ia) return ia;
  }
  // source_records amazon:ISBN
  for (const src of data.source_records || []) {
    const am = String(src).match(/^amazon:(\d{9}[\dXx])$/i);
    if (am) {
      const url = coverFromAmazonIsbn(am[1]);
      if (url) return url;
    }
  }
  const { isbn10, isbn13 } = pickBestIsbn([
    ...(data.isbn_10 || []),
    ...(data.isbn_13 || []),
  ]);
  if (isbn10) {
    const url = coverFromAmazonIsbn(isbn10);
    if (url) return url;
  }
  if (isbn13) {
    const url = coverFromAbeBooksIsbn(isbn13);
    if (url) return url;
  }
  return null;
}

async function searchOpenLibrary(title, author) {
  const variants = titleVariants(title);
  if (!variants.length) return null;
  const queryTitle = cleanTitle(title);

  const attempts = [];
  for (const base of variants.slice(0, 5)) {
    if (author) attempts.push(`${base} ${author}`);
    attempts.push(base);
  }

  for (const q of attempts) {
    const data = await fetchJson(
      `https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=10&fields=cover_i,isbn,key,title,edition_key,ia,author_name`,
      12000
    );
    if (!data) continue;
    if (data.__rateLimited) return '__429__';

    const ranked = (data.docs || [])
      .map((doc) => ({ doc, score: titleScore(queryTitle, doc?.title) }))
      .filter((x) => x.score >= 45)
      .sort((a, b) => b.score - a.score);

    for (const { doc } of ranked) {
      const url = coverFromCoverI(doc?.cover_i);
      if (url) return url;

      // IA (ocaid listée dans search)
      if (Array.isArray(doc.ia) && doc.ia[0]) {
        const ia = coverFromOcaid(doc.ia[0]);
        if (ia) return ia;
      }

      // ISBN → Amazon / AbeBooks
      const { isbn10, isbn13 } = pickBestIsbn(doc.isbn || []);
      if (isbn10) {
        const amz = coverFromAmazonIsbn(isbn10);
        if (amz) return amz;
      }
      if (isbn13) {
        const abe = coverFromAbeBooksIsbn(isbn13);
        if (abe) return abe;
      }

      // Dig edition (ocaid / amazon source)
      if (Array.isArray(doc.edition_key) && doc.edition_key[0]) {
        const fromEd = await coverFromEditionKey(doc.edition_key[0]);
        if (fromEd) return fromEd;
      }
    }
  }
  return null;
}

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
    const isPerson =
      /\b(actress|actor|actrice|acteur|singer|chanteur|chanteuse|écrivain|écrivaine|writer|author|novelist|romancier|romanci[eè]re|personnalité|politician|footballer|footballeur|painter|peintre)\b/i.test(
        desc
      ) &&
      !/\b(novel|roman|novella|livre|récit|ouvrage|thriller|manga|bande dessin)/i.test(blob);
    if (isPerson) return null;
    if (authorNorm && pageNorm === authorNorm) return null;
    if (
      authorNorm &&
      pageNorm.startsWith(authorNorm) &&
      !pageNorm.includes(titleNorm.split(' ')[0] || '___')
    ) {
      if (!titleNorm.split(/\s+/).some((w) => w.length > 3 && pageNorm.includes(w))) {
        return null;
      }
    }
    const titleWords = titleNorm.split(/\s+/).filter((w) => w.length > 3);
    if (titleWords.length >= 2) {
      const hits = titleWords.filter((w) => pageNorm.includes(w)).length;
      if (hits < Math.min(2, titleWords.length)) return null;
    }
    const thumb = data.originalimage?.source || data.thumbnail?.source;
    if (!thumb || /\.svg($|\?)/i.test(thumb)) return null;
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
    for (const slug of directSlugs.slice(0, 8)) {
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

  const queries = [];
  const cleanIsbn = String(isbn || '').replace(/[^0-9Xx]/g, '');
  if (cleanIsbn.length >= 10) queries.push(`isbn:${cleanIsbn}`);

  for (const t of titleVariants(title).slice(0, 3)) {
    const parts = [];
    if (t) parts.push(`intitle:${t}`);
    if (author) parts.push(`inauthor:${author}`);
    if (parts.length) queries.push(parts.join('+'));
    queries.push(author ? `${t} ${author}` : t);
  }

  for (const q of queries) {
    if (!q) continue;
    const data = await fetchJson(
      `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(q)}&maxResults=8&printType=books`,
      10000
    );
    if (data?.__rateLimited) {
      gbCooldownUntil = Date.now() + 12 * 60 * 1000;
      return '__429__';
    }
    if (!data) continue;

    const want = norm(cleanTitle(title));
    const ranked = (data.items || [])
      .map((item) => ({
        item,
        score: titleScore(want, item?.volumeInfo?.title),
      }))
      .filter((x) => x.score >= 40 || !want)
      .sort((a, b) => b.score - a.score);

    for (const { item } of ranked) {
      const links = item?.volumeInfo?.imageLinks || {};
      const thumb =
        links.medium ||
        links.large ||
        links.thumbnail ||
        links.smallThumbnail;
      if (thumb) return hardenGoogleBooksCover(thumb);
    }
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
      }, 220);
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

    // 1) OL work / ISBN fourni
    if (olKey) {
      cover = await coverFromOlWork(olKey);
    }
    if (!isUsableCoverUrl(cover) && isbn) {
      cover = await coverFromIsbn(isbn);
    }

    // 2) Open Library search (+ IA / Amazon / AbeBooks via docs)
    if (!isUsableCoverUrl(cover)) {
      cover = await searchOpenLibrary(title, a);
      if (cover === '__429__') cover = null;
    }

    // 3) Wikipedia
    if (!isUsableCoverUrl(cover)) {
      cover = await searchWikipediaCover(title, a);
    }

    // 4) Google Books
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

    return null;
  });
}

export default searchCoverInBrowser;
