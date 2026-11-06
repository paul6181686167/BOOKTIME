/**
 * Estimation du temps de lecture à partir de la bibliothèque.
 *
 * Romans : mots estimés = pages x mots par page, puis temps = mots / vitesse de lecture.
 * Romans graphiques et mangas : le texte est peu dense, on compte un temps moyen par page.
 */

/** Vitesse moyenne de lecture silencieuse d'un adulte (mots par minute). */
export const WORDS_PER_MINUTE = 238;

export const READING_PROFILES = {
  roman: {
    label: 'Romans',
    wordsPerPage: 280,
    // Pages d'un roman quand le nombre de pages est inconnu
    defaultPages: 320,
  },
  bd: {
    label: 'Romans graphiques',
    minutesPerPage: 0.8,
    defaultPages: 60,
  },
  manga: {
    label: 'Mangas',
    minutesPerPage: 0.4,
    defaultPages: 190,
  },
};

export const READING_CATEGORIES = ['roman', 'bd', 'manga'];

const toCategory = (raw) => {
  const c = String(raw || '').toLowerCase();
  if (c === 'bd' || c === 'graphic_novel' || c === 'graphic_novels' || c === 'comics') return 'bd';
  if (c === 'manga') return 'manga';
  return 'roman';
};

const toPositiveInt = (v) => {
  const n = Math.floor(Number(v));
  return Number.isFinite(n) && n > 0 ? n : 0;
};

/** Vitesses de lecture proposées dans les paramètres (mots par minute). */
export const READING_SPEEDS = [
  { id: 'slow', label: 'Tranquille', wpm: 180 },
  { id: 'normal', label: 'Moyenne', wpm: WORDS_PER_MINUTE },
  { id: 'fast', label: 'Rapide', wpm: 300 },
];

/** Vitesse enregistrée valide, sinon la vitesse moyenne. */
export function normalizeWpm(value) {
  const n = Number(value);
  return READING_SPEEDS.some((s) => s.wpm === n) ? n : WORDS_PER_MINUTE;
}

/** Minutes nécessaires pour lire `pages` pages d'une catégorie. */
export function minutesForPages(category, pages, wordsPerMinute = WORDS_PER_MINUTE) {
  const profile = READING_PROFILES[category] || READING_PROFILES.roman;
  if (profile.wordsPerPage) {
    return (pages * profile.wordsPerPage) / wordsPerMinute;
  }
  // Pages illustrées : le temps par page suit le rythme de lecture de l'utilisateur
  return (pages * profile.minutesPerPage * WORDS_PER_MINUTE) / wordsPerMinute;
}

/** Pages lues d'un livre : tout si terminé, la page courante si en cours. */
export function pagesReadForBook(book) {
  if (!book) return { pages: 0, guessed: false };
  const category = toCategory(book.category);
  const defaultPages = READING_PROFILES[category].defaultPages;
  const total = toPositiveInt(book.total_pages);

  if (book.status === 'completed') {
    return total ? { pages: total, guessed: false } : { pages: defaultPages, guessed: true };
  }
  if (book.status === 'reading') {
    const current = toPositiveInt(book.current_page);
    if (!current) return { pages: 0, guessed: false };
    return { pages: total ? Math.min(current, total) : current, guessed: false };
  }
  return { pages: 0, guessed: false };
}

/**
 * Résumé du temps de lecture par catégorie et au total.
 * Les séries (cartes agrégées) sont ignorées : leurs tomes sont déjà des livres.
 */
export function summarizeReadingTime(books, wordsPerMinute = WORDS_PER_MINUTE) {
  const byCategory = {};
  READING_CATEGORIES.forEach((c) => {
    byCategory[c] = { books: 0, pages: 0, minutes: 0, words: 0 };
  });
  let guessedBooks = 0;

  (books || []).forEach((book) => {
    if (!book || book.isSeriesCard) return;
    const { pages, guessed } = pagesReadForBook(book);
    if (!pages) return;
    const category = toCategory(book.category);
    const entry = byCategory[category];
    entry.books += book.status === 'completed' ? 1 : 0;
    entry.pages += pages;
    entry.minutes += minutesForPages(category, pages, wordsPerMinute);
    if (READING_PROFILES[category].wordsPerPage) {
      entry.words += pages * READING_PROFILES[category].wordsPerPage;
    }
    if (guessed) guessedBooks += 1;
  });

  const totalMinutes = READING_CATEGORIES.reduce((s, c) => s + byCategory[c].minutes, 0);
  return {
    byCategory,
    totalMinutes: Math.round(totalMinutes),
    guessedBooks,
  };
}

/** « 142 h 30 », « 45 min », « 0 min ». */
export function formatDuration(totalMinutes) {
  const m = Math.max(0, Math.round(totalMinutes || 0));
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const rest = m % 60;
  return rest ? `${h.toLocaleString('fr-FR')} h ${String(rest).padStart(2, '0')}` : `${h.toLocaleString('fr-FR')} h`;
}

/** « 5,9 jours » : le même temps converti en jours de 24 h, quand il dépasse une journée. */
export function formatAsDays(totalMinutes) {
  const days = (totalMinutes || 0) / 60 / 24;
  if (days < 1) return '';
  const rounded = Math.round(days * 10) / 10;
  return `${rounded.toLocaleString('fr-FR')} jour${rounded >= 2 ? 's' : ''} sans s’arrêter`;
}

/** « 1,2 million de mots », « 85 000 mots ». */
export function formatWords(words) {
  const w = Math.round(words || 0);
  if (w >= 1_000_000) {
    return `${(Math.round(w / 100_000) / 10).toLocaleString('fr-FR')} million${w >= 2_000_000 ? 's' : ''} de mots`;
  }
  return `${(Math.round(w / 1000) * 1000).toLocaleString('fr-FR')} mots`;
}
