/**
 * Affichage et regroupement des livres Open Library côté client.
 */

function frenchAccentScore(str) {
  if (!str) return 0;
  return (str.match(/[àâäéèêëïîôùûçœæ]/gi) || []).length;
}

/**
 * Corrige les corruptions fréquentes de titres (ex. « Q.I. » → « Cui »).
 */
export function sanitizeBookTitle(title) {
  let t = String(title || '').trim();
  if (!t) return '';
  // « Juliette a-t-elle un grand Cui ? » → Q.I.
  t = t.replace(/\bCui\b/gi, 'Q.I.');
  t = t.replace(/\bQ\s*\.\s*I\s*\.?/gi, 'Q.I.');
  t = t.replace(/\bQI\b/g, 'Q.I.');
  return t;
}

/** Alias d'affichage FR pour titres EN fréquents (recos / recherche). */
const FR_DISPLAY_ALIASES = {
  hobbit: 'Le Hobbit',
  'the hobbit': 'Le Hobbit',
  'two towers': 'Les Deux Tours',
  'the two towers': 'Les Deux Tours',
  'fellowship of the ring': "La Communauté de l'Anneau",
  'the fellowship of the ring': "La Communauté de l'Anneau",
  'return of the king': 'Le Retour du Roi',
  'the return of the king': 'Le Retour du Roi',
  'song of achilles': "Le Chant d'Achille",
  'the song of achilles': "Le Chant d'Achille",
  circe: 'Circé',
  'snow crash': 'Le Samouraï virtuel',
  odyssey: "L'Odyssée",
  'the odyssey': "L'Odyssée",
  'ὀδύσσεια': "L'Odyssée",
  iliade: "L'Iliade",
  'the iliad': "L'Iliade",
  'brief lives': 'Vies brèves',
  'norse mythology': 'Mythes nordiques',
  "hitchhiker's guide to the galaxy": 'Le Guide du voyageur galactique',
  'the hitchhiker\'s guide to the galaxy': 'Le Guide du voyageur galactique',
  'the martian': 'Seul sur Mars',
  'six of crows': 'Six de Cœur',
  "ender's game": 'La Stratégie Ender',
  'the lightning thief': 'Le Voleur de foudre',
  'the lost hero': 'Le Héros perdu',
  'for whom the bell tolls': 'Pour qui sonne le glas',
  'the sun also rises': 'Le soleil se lève aussi',
  'a farewell to arms': "L'Adieu aux armes",
  'the complete short stories of ernest hemingway': "Nouvelles complètes d'Ernest Hemingway",
  'the short stories of ernest hemingway': "Nouvelles complètes d'Ernest Hemingway",
};

function aliasFrenchDisplayTitle(title) {
  const t = String(title || '').trim();
  if (!t) return '';
  // Titres grecs classiques
  if (/ὀδύσσ|οδυσσ|odysseia/i.test(t)) return "L'Odyssée";
  if (/ἰλιάς|ιλιας|iliad/i.test(t) && t.length < 40) return "L'Iliade";
  const key = t.toLowerCase();
  const head = key.split(/[:/]/)[0].trim();
  if (FR_DISPLAY_ALIASES[key]) return FR_DISPLAY_ALIASES[key];
  if (FR_DISPLAY_ALIASES[head]) return FR_DISPLAY_ALIASES[head];
  const stripped = key.replace(/^(the|a|an)\s+/, '');
  if (FR_DISPLAY_ALIASES[stripped]) return FR_DISPLAY_ALIASES[stripped];
  return '';
}

/** Plus le score est haut, plus le titre a l'air français. */
function frenchTitleScore(title) {
  const t = String(title || '').trim();
  if (!t) return 0;
  let score = frenchAccentScore(t) * 4;
  if (/^(le|la|les|l['’]|un|une|des|du|au|aux|pour)\b/i.test(t)) score += 6;
  if (/^(the|a|an)\b/i.test(t)) score -= 4;
  if (/\b(of|and|for|with|from|whom)\b/i.test(t) && frenchAccentScore(t) === 0) score -= 3;
  return score;
}

/**
 * Titre anglais de recommandation : article anglais ou mots de liaison,
 * sans marque française. Les noms propres (« Percy Jackson ») restent tels quels.
 */
export function titleNeedsFrenchLookup(title) {
  const t = String(title || '').trim();
  if (!t || frenchTitleScore(t) >= 6) return false;
  if (/^(the|a|an)\b/i.test(t)) return true;
  return /\b(of|and|for|with|from|whom|also)\b/i.test(t) && frenchAccentScore(t) === 0;
}

function tidyFrenchTitle(title) {
  return String(title || '')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\.$/, '')
    .replace(/([lL])['’]\s+/g, "$1'");
}

/** Choisit l'édition française la plus lisible parmi les titres Open Library. */
export function pickFrenchEditionTitle(titles, englishTitle) {
  const english = String(englishTitle || '').trim().toLowerCase();
  let best = '';
  let bestScore = 0;
  for (const raw of titles || []) {
    const title = tidyFrenchTitle(raw);
    if (!title || title.toLowerCase() === english) continue;
    if (title.includes('/') || title.length > 90) continue;
    let score = frenchAccentScore(title) * 4;
    if (/^(le|la|les|l['’]|un|une|des|du|au|aux|pour)\b/i.test(title)) score += 8;
    if (/\b(the|and|of|for|with)\b/i.test(title) && frenchAccentScore(title) === 0) score -= 6;
    if (/tome\s*\d/i.test(title) && !/^(le|la|les|l['’])/i.test(title)) score -= 3;
    if (score > bestScore) {
      bestScore = score;
      best = title;
    }
  }
  return bestScore > 0 ? best : '';
}

function workKeyFromBook(book) {
  const raw = String(book?.ol_key || book?.book_id || book?.key || '');
  const withPath = raw.match(/(\/works\/OL\d+W)/i);
  if (withPath) return withPath[1];
  const bare = raw.match(/\b(OL\d+W)\b/i);
  return bare ? `/works/${bare[1]}` : '';
}

const frenchEditionCache = new Map();
let frenchLookupActive = 0;
const frenchLookupWaiters = [];

function withFrenchLookupSlot(task) {
  return new Promise((resolve, reject) => {
    const run = () => {
      frenchLookupActive += 1;
      task().then(resolve, reject).finally(() => {
        frenchLookupActive -= 1;
        const next = frenchLookupWaiters.shift();
        if (next) next();
      });
    };
    if (frenchLookupActive < 4) run();
    else frenchLookupWaiters.push(run);
  });
}

async function lookupFrenchEdition(book, english) {
  let work = workKeyFromBook(book);
  if (!work) {
    const q = [english, book?.author].filter(Boolean).join(' ');
    const searchUrl = `https://openlibrary.org/search.json?q=${encodeURIComponent(q)}&limit=1&fields=key,title`;
    const found = await fetch(searchUrl).then((r) => (r.ok ? r.json() : null)).catch(() => null);
    const key = found?.docs?.[0]?.key || '';
    if (String(key).includes('/works/')) work = key;
  }
  if (!work) return '';
  const editionsUrl =
    `https://openlibrary.org/query.json?type=/type/edition&works=${work}` +
    '&languages=/languages/fre&title=&limit=12';
  const editions = await fetch(editionsUrl).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const titles = Array.isArray(editions) ? editions.map((e) => e?.title).filter(Boolean) : [];
  return pickFrenchEditionTitle(titles, english);
}

/**
 * Titre français d'une reco : alias connu, sinon édition Open Library en français.
 * Retourne le titre courant si aucune édition française n'est trouvable.
 */
export async function resolveFrenchDisplayTitle(book) {
  const current = displayBookTitleFrFirst(book);
  if (!current || !titleNeedsFrenchLookup(current)) return current;
  const key = `${workKeyFromBook(book) || current}|${book?.author || ''}`.toLowerCase();
  if (frenchEditionCache.has(key)) return frenchEditionCache.get(key);
  try {
    const stored = sessionStorage.getItem(`bt-fr-title:${key}`);
    if (stored) {
      frenchEditionCache.set(key, stored);
      return stored;
    }
  } catch {
    /* sessionStorage indisponible */
  }
  const french = await withFrenchLookupSlot(() => lookupFrenchEdition(book, current));
  const result = french || current;
  frenchEditionCache.set(key, result);
  if (french) {
    try {
      sessionStorage.setItem(`bt-fr-title:${key}`, french);
    } catch {
      /* quota */
    }
  }
  return result;
}

/**
 * Titre à afficher en priorisant le français (langue OL, heuristique accents).
 */
export function displayBookTitleFrFirst(book) {
  if (!book) return '';
  let raw = '';
  const titleFr = (book.title_fr || '').trim();
  const display = (book.display_title || '').trim();
  if (display && titleFr && frenchTitleScore(titleFr) > frenchTitleScore(display)) {
    raw = titleFr;
  } else if (display) {
    raw = display;
  } else if (titleFr) {
    raw = titleFr;
  } else {
      const t = (book.title || '').trim();
      const o = (book.original_title || '').trim();
      const langs = book.available_languages || [];
      const langJoined = langs.map((l) => String(l).toLowerCase()).join(' ');

      if (langJoined.includes('fre') && t) {
        raw = t;
      } else {
        const scoreT = frenchAccentScore(t);
        const scoreO = frenchAccentScore(o);
        if (o && scoreO > scoreT) raw = o;
        else if (t && scoreT > scoreO) raw = t;
        else {
          const frHint = /\b(le|la|les|un|une|des|du|de|et|l['’])/i;
          if (o && frHint.test(o) && !frHint.test(t)) raw = o;
          else if (t && frHint.test(t) && !frHint.test(o)) raw = t;
          else raw = t || o;
        }
      }
  }
  const aliased = aliasFrenchDisplayTitle(raw) || aliasFrenchDisplayTitle(book?.title) || aliasFrenchDisplayTitle(book?.original_title);
  if (aliased) return sanitizeBookTitle(aliased);
  return sanitizeBookTitle(raw);
}

function extractVolumeNumberForMerge(book) {
  if (book.volume_number != null && book.volume_number !== '') {
    const n = parseInt(String(book.volume_number).replace(/^0+/, ''), 10);
    if (!Number.isNaN(n) && n >= 0) return n;
  }
  const blob = `${book.title || ''} ${book.original_title || ''}`;
  const patterns = [
    /\b(?:tome|vol\.?|volume|book)\s*(\d{1,3})\b/i,
    /[#]\s*(\d{1,3})\b/,
  ];
  for (const re of patterns) {
    const m = blob.match(re);
    if (m) {
      const v = parseInt(m[1], 10);
      if (!Number.isNaN(v)) return v;
    }
  }
  return null;
}

function volumeGroupKey(book, fallbackIndex) {
  const v = extractVolumeNumberForMerge(book);
  if (v !== null) return `v:${v}`;
  return `id:${book.ol_key || book.id || `idx:${fallbackIndex}`}`;
}

function pickPreferredOpenLibraryEdition(books) {
  if (!books || books.length === 0) return null;
  if (books.length === 1) return books[0];
  const score = (b) => {
    let s = 0;
    const langs = (b.available_languages || []).map((x) => String(x).toLowerCase());
    if (langs.some((l) => l.includes('fre'))) s += 100;
    s += frenchAccentScore(b.title) * 5;
    s += frenchAccentScore(b.original_title) * 3;
    if (b.cover_url) s += 10;
    return s;
  };
  return [...books].sort((a, b) => score(b) - score(a))[0];
}

/**
 * Une entrée par tome logique (même volume_number ou même indice extrait du titre).
 */
export function mergeOpenLibraryBooksByVolume(books) {
  if (!books || !books.length) return [];
  const keyOrder = [];
  const groups = new Map();
  books.forEach((b, idx) => {
    const k = volumeGroupKey(b, idx);
    if (!groups.has(k)) {
      keyOrder.push(k);
      groups.set(k, []);
    }
    groups.get(k).push(b);
  });
  return keyOrder.map((k) => {
    const list = groups.get(k);
    return pickPreferredOpenLibraryEdition(list);
  });
}

/** Tri par numéro de tome détecté (valeurs inconnues en dernier). */
export function sortOpenLibraryBooksByVolume(a, b) {
  const va = extractVolumeNumberForMerge(a);
  const vb = extractVolumeNumberForMerge(b);
  if (va !== null && vb !== null) return va - vb;
  if (va !== null) return -1;
  if (vb !== null) return 1;
  return 0;
}

/**
 * Lignes type `mergedLibraryVolumes` pour l’ajout bibliothèque depuis des livres OL (carte auteur, etc.).
 * @param {object[]} books
 * @returns {object[]|null}
 */
export function buildMergedLibraryVolumeRowsFromOlBooks(books) {
  const arr = Array.isArray(books) ? books : [];
  if (!arr.length) return null;
  const merged = mergeOpenLibraryBooksByVolume(arr);
  return merged.map((b) => ({
    title: b.title || '',
    display_title: displayBookTitleFrFirst(b),
    volume_number: b.volume_number || 1,
    cover_url: b.cover_url || '',
    first_publish_year: b.first_publish_year ?? null,
    work_qid: b.work_qid || null,
    isbn: b.isbn || null,
    ol_key: b.ol_key || null,
    merged_sources: ['openlibrary'],
  }));
}
