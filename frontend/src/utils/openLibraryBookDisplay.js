/**
 * Affichage et regroupement des livres Open Library côté client.
 */

function frenchAccentScore(str) {
  if (!str) return 0;
  return (str.match(/[àâäéèêëïîôùûçœæ]/gi) || []).length;
}

/**
 * Titre à afficher en priorisant le français (langue OL, heuristique accents).
 */
export function displayBookTitleFrFirst(book) {
  if (!book) return '';
  if (book.display_title != null && String(book.display_title).trim() !== '') {
    return String(book.display_title).trim();
  }
  const t = (book.title || '').trim();
  const o = (book.original_title || '').trim();
  const langs = book.available_languages || [];
  const langJoined = langs.map((l) => String(l).toLowerCase()).join(' ');
  if (langJoined.includes('fre') && t) return t;
  if (o && frenchAccentScore(o) > frenchAccentScore(t)) return o;
  return t || o;
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
