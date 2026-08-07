/**
 * POSSESSION D'UN LIVRE — règle unique et partagée.
 *
 * La recherche et l'affichage calculaient chacun « ce livre est-il déjà dans ma
 * bibliothèque ? » avec des règles différentes. Comme l'affichage s'exécutait en
 * dernier, son verdict écrasait l'autre : la comparaison la plus fine était donc
 * inopérante, et le badge « déjà possédé » dépendait de l'ordre d'exécution.
 *
 * Tout doit passer par ce module. L'index se construit une fois par bibliothèque,
 * ce qui remplace un balayage complet des livres (avec expressions régulières)
 * pour chaque résultat de recherche par une recherche à coût constant.
 */

const normalize = (value) =>
  (value || '')
    .toLowerCase()
    .trim()
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ');

const normalizeIsbn = (value) => (value || '').replace(/[-\s]/g, '');

// Titres trop courts écartés : « Ça » ou « Moi » produiraient des faux positifs.
const titleAuthorKey = (title, author) => {
  const t = normalize(title);
  if (!t || t.length <= 3) return '';
  return `${t}\u0000${normalize(author)}`;
};

/**
 * Construit l'index de possession à partir de la bibliothèque locale.
 * @param {object[]} localBooks
 */
export const buildOwnershipIndex = (localBooks) => {
  const olKeys = new Set();
  const isbns = new Set();
  const titleAuthors = new Set();

  for (const book of localBooks || []) {
    if (!book) continue;
    if (book.ol_key) olKeys.add(book.ol_key);
    const isbn = normalizeIsbn(book.isbn);
    if (isbn) isbns.add(isbn);
    // Titre courant ET titre d'origine : une bibliothèque francisée doit
    // reconnaître un résultat encore en langue d'origine, et réciproquement.
    for (const title of [book.title, book.display_title, book.original_title]) {
      const key = titleAuthorKey(title, book.author);
      if (key) titleAuthors.add(key);
    }
  }

  return { olKeys, isbns, titleAuthors };
};

/**
 * @param {object} book résultat de recherche
 * @param {ReturnType<typeof buildOwnershipIndex>} index
 * @returns {boolean}
 */
export const isBookOwned = (book, index) => {
  if (!book || !index) return false;
  if (book.ol_key && index.olKeys.has(book.ol_key)) return true;
  const isbn = normalizeIsbn(book.isbn);
  if (isbn && index.isbns.has(isbn)) return true;
  for (const title of [book.display_title, book.title, book.original_title]) {
    const key = titleAuthorKey(title, book.author);
    if (key && index.titleAuthors.has(key)) return true;
  }
  return false;
};
