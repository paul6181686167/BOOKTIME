/**
 * Affichage fiche livre : pages lues, ligne de métadonnées, sujets propres.
 */

const LANG_LABELS = {
  fr: 'Français',
  fre: 'Français',
  fra: 'Français',
  français: 'Français',
  francais: 'Français',
  en: 'Anglais',
  eng: 'Anglais',
  english: 'Anglais',
  anglais: 'Anglais',
  es: 'Espagnol',
  spa: 'Espagnol',
  espagnol: 'Espagnol',
  de: 'Allemand',
  ger: 'Allemand',
  deu: 'Allemand',
  it: 'Italien',
  ita: 'Italien',
  ja: 'Japonais',
  jpn: 'Japonais',
  japonais: 'Japonais',
};

const COMPLETED_STATUSES = new Set(['completed', 'to_reread']);

export function isCompletedStatus(status) {
  return COMPLETED_STATUSES.has(status);
}

/** Pages lues à afficher : un livre terminé sans page courante compte comme 100 %. */
export function getPagesRead(book, totalPages, status) {
  const st = status || book?.status;
  const total = Number(totalPages) || Number(book?.total_pages) || 0;
  const cur = Number(book?.current_page);
  if (isCompletedStatus(st) && total > 0 && !(cur > 0)) return total;
  return Number.isFinite(cur) && cur > 0 ? cur : 0;
}

export function getProgressPercent(book, totalPages, status, editCurrentPage) {
  const total = Number(totalPages) || Number(book?.total_pages) || 0;
  if (!total) return 0;
  const st = status || book?.status;
  if (editCurrentPage != null && editCurrentPage !== '') {
    return Math.min(100, (Number(editCurrentPage) / total) * 100);
  }
  if (isCompletedStatus(st)) {
    const cur = Number(book?.current_page);
    if (!(cur > 0) || cur >= total) return 100;
  }
  return Math.min(100, (getPagesRead(book, total, st) / total) * 100);
}

export function pickFirstPublisher(publisher) {
  if (!publisher) return '';
  if (Array.isArray(publisher)) {
    return String(publisher.find(Boolean) || '').trim();
  }
  const parts = String(publisher)
    .split(/\s*,\s*/)
    .map((p) => p.trim())
    .filter(Boolean);
  if (!parts.length) return '';
  const frHints = [
    'gallimard',
    'albin',
    'pocket',
    'folio',
    'livre de poche',
    'flammarion',
    'seuil',
    'actes sud',
    'casterman',
    'glénat',
    'glenat',
    'kana',
    'pika',
    'kurokawa',
    'delcourt',
    'dargaud',
    'dupuis',
    'j’ai lu',
    "j'ai lu",
    'le lombard',
    'albert rené',
  ];
  const preferred = parts.find((p) =>
    frHints.some((h) => p.toLowerCase().includes(h))
  );
  return preferred || parts[0];
}

export function formatLanguageLabel(lang) {
  if (!lang) return '';
  const key = String(lang).trim().toLowerCase();
  if (LANG_LABELS[key]) return LANG_LABELS[key];
  return String(lang).trim().replace(/^\w/, (c) => c.toUpperCase());
}

export function formatBookMetaLine(book) {
  if (!book) return '';
  const bits = [];
  const genre = Array.isArray(book.genre) ? book.genre.filter(Boolean)[0] : book.genre;
  if (genre && String(genre).trim()) bits.push(String(genre).trim());
  const publisher = pickFirstPublisher(book.publisher);
  if (publisher) bits.push(publisher);
  const year = book.publication_year || book.first_publish_year;
  if (year) bits.push(String(year).slice(0, 4));
  const lang =
    book.reading_language ||
    book.original_language ||
    book.language ||
    (Array.isArray(book.available_languages) ? book.available_languages[0] : '');
  const langLabel = formatLanguageLabel(lang);
  if (langLabel) bits.push(langLabel);
  return bits.join(' · ');
}

/** Sujets OL bruts (nyt:…, identifiants, dates seules) à ne pas afficher. */
export function isDisplayableSubject(raw) {
  const t = String(typeof raw === 'string' ? raw : raw?.name || '').trim();
  if (!t) return false;
  if (/^[a-z0-9._-]+:/i.test(t) && t.includes('=')) return false;
  if (/^[a-z]{2,8}:/i.test(t) && !/\s/.test(t)) return false;
  if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return false;
  if (t.length > 60) return false;
  return true;
}

function isBlankField(v) {
  if (v == null) return true;
  if (typeof v === 'string') return !v.trim();
  if (Array.isArray(v)) return v.filter(Boolean).length === 0;
  return false;
}

/**
 * Complète une fiche livre avec le référentiel curé (éditeur, année, ISBN, pages, résumé, couverture).
 * N’écrase jamais une valeur déjà présente sur le livre.
 */
export function enrichBookFromCuratedSeries(book, attribution, volumeNumber) {
  if (!book) return book;
  const data = attribution?.seriesData;
  if (!data) return book;
  const details =
    volumeNumber != null && data.volume_details
      ? data.volume_details[volumeNumber] || data.volume_details[String(volumeNumber)] || {}
      : {};
  const out = { ...book };
  if (isBlankField(out.publisher)) {
    out.publisher = details.publisher || data.publisher || '';
  }
  if (isBlankField(out.publication_year) && isBlankField(out.first_publish_year)) {
    const y = details.published_year || data.first_published;
    if (y) out.publication_year = String(y).slice(0, 4);
  }
  if (isBlankField(out.isbn) && details.isbn) out.isbn = details.isbn;
  if (!(Number(out.total_pages) > 0) && Number(details.pages) > 0) {
    out.total_pages = Number(details.pages);
  }
  if (isBlankField(out.cover_url)) {
    out.cover_url = details.cover_url || data.cover_url || '';
  }
  if (isBlankField(out.description)) {
    out.description = details.description || data.description || '';
  }
  if (isBlankField(out.genre) && data.genre) out.genre = data.genre;
  if (isBlankField(out.author) && Array.isArray(data.authors) && data.authors[0]) {
    out.author = data.authors[0];
  }
  if (isBlankField(out.category) && data.category) out.category = data.category;
  if (
    isBlankField(out.reading_language) &&
    isBlankField(out.original_language) &&
    isBlankField(out.language) &&
    data.language
  ) {
    out.language = data.language;
  }
  return out;
}

export function displayableSubjects(list, limit = 8) {
  const items = (list || [])
    .map((s) => (typeof s === 'string' ? s : s?.name || ''))
    .filter(isDisplayableSubject);
  const score = (t) =>
    (/[àâäéèêëïîôùûç]/i.test(t) ? 2 : 0) +
    (/\b(roman|policier|fantastique|aventure|jeunesse|bande|dessin|science[- ]fiction)/i.test(t)
      ? 1
      : 0);
  return [...items].sort((a, b) => score(b) - score(a)).slice(0, limit);
}
