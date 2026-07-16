/**
 * Fusion des métadonnées volume : **Wikidata > Open Library > Google Books**
 * (règle produit BOOKTIME — champs manquants complétés par la source suivante).
 */

function parseVolumeNumber(bookLike) {
  if (!bookLike) return null;
  const vn = bookLike.volume_number ?? bookLike.volume;
  if (vn != null && vn !== '') {
    const n = parseInt(String(vn).replace(/^0+/, ''), 10);
    if (!Number.isNaN(n) && n >= 0) return n;
  }
  const blob = `${bookLike.title || ''} ${bookLike.original_title || ''}`;
  const m = blob.match(/\b(?:tome|vol\.?|volume|book)\s*(\d{1,3})\b/i);
  if (m) {
    const v = parseInt(m[1], 10);
    if (!Number.isNaN(v)) return v;
  }
  return null;
}

/** Clé de rapprochement titre (minuscules, sans accents forts). */
export function normalizeTitleKey(s) {
  if (!s) return '';
  return String(s)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, ' ');
}

function firstIsbn(wdWork) {
  const arr = wdWork?.isbns;
  if (Array.isArray(arr) && arr.length) return String(arr[0]).replace(/[-\s]/g, '');
  return '';
}

/**
 * Fusionne un triplet optionnel WD / OL / GB en une ligne d’affichage unique.
 * @param {{ wdWork?: object, olBook?: object, gbItem?: object }} sources
 */
export function mergeVolumeDisplay({ wdWork = null, olBook = null, gbItem = null }) {
  const wdTitle = wdWork ? (wdWork.title_fr || wdWork.title_en || '').trim() : '';
  const olTitle = olBook ? (olBook.display_title || olBook.title || '').trim() : '';
  const gbTitle = gbItem ? (String(gbItem.title || '').trim()) : '';

  const title = wdTitle || olTitle || gbTitle || 'Œuvre';
  const altTitle = wdTitle && olTitle && olTitle !== wdTitle ? olTitle : olBook?.original_title || '';

  const volume_number =
    parseVolumeNumber({ volume_number: wdWork?.volume, title: wdTitle }) ??
    parseVolumeNumber(olBook) ??
    parseVolumeNumber({ title: gbTitle, volume_number: gbItem?.volume_number }) ??
    1;

  const cover_url =
    (olBook && olBook.cover_url) ||
    (gbItem && (gbItem.thumbnail || '').replace(/^http:\/\//i, 'https://')) ||
    '';

  const isbn =
    firstIsbn(wdWork) ||
    (olBook?.isbn ? String(olBook.isbn).replace(/[-\s]/g, '') : '') ||
    gbItem?.isbn_13 ||
    gbItem?.isbn_10 ||
    '';

  const first_publish_year =
    (wdWork?.publication_date && parseInt(String(wdWork.publication_date).slice(0, 4), 10)) ||
    olBook?.first_publish_year ||
    (gbItem?.published_date && parseInt(String(gbItem.published_date).slice(0, 4), 10)) ||
    null;

  const sources_used = [];
  if (wdWork) sources_used.push('wikidata');
  if (olBook) sources_used.push('openlibrary');
  if (gbItem) sources_used.push('google_books');

  return {
    title,
    display_title: title,
    original_title: altTitle || null,
    volume_number,
    first_publish_year: Number.isNaN(first_publish_year) ? null : first_publish_year,
    cover_url,
    isbn: isbn || null,
    ol_key: olBook?.ol_key || null,
    work_qid: wdWork?.work_qid || null,
    isFromStaticWikidata: !!wdWork,
    merged_sources: sources_used,
  };
}

/**
 * Associe chaque œuvre Wikidata statique à au plus un livre OL (même tome ou titre proche),
 * fusionne les champs, puis ajoute les livres OL non appariés (OL seul).
 */
export function mergeStaticWdWorksWithOpenLibrary(works, olBooks) {
  const worksArr = Array.isArray(works) ? works : [];
  const olArr = Array.isArray(olBooks) ? [...olBooks] : [];
  if (!worksArr.length) {
    return olArr.map((ob) => mergeVolumeDisplay({ olBook: ob }));
  }

  const merged = [];
  for (const wdWork of worksArr) {
    const vnWd = parseVolumeNumber({ volume_number: wdWork.volume, title: wdWork.title_fr || wdWork.title_en });
    let bestIdx = -1;
    let bestOl = null;
    olArr.forEach((b, idx) => {
      const vnOl = parseVolumeNumber(b);
      if (vnWd != null && vnOl != null && vnWd === vnOl) {
        bestOl = b;
        bestIdx = idx;
      }
    });
    if (bestIdx < 0) {
      const tk = normalizeTitleKey(wdWork.title_fr || wdWork.title_en || '');
      let score = 0;
      olArr.forEach((b, idx) => {
        const tk2 = normalizeTitleKey(b.title || '');
        if (!tk || !tk2) return;
        const s =
          tk === tk2 ? 3 : tk.includes(tk2) || tk2.includes(tk) ? 2 : 0;
        if (s > score) {
          score = s;
          bestOl = b;
          bestIdx = idx;
        }
      });
    }
    if (bestIdx >= 0) {
      const [picked] = olArr.splice(bestIdx, 1);
      merged.push(mergeVolumeDisplay({ wdWork, olBook: picked }));
    } else {
      merged.push(mergeVolumeDisplay({ wdWork, olBook: null }));
    }
  }
  for (const ob of olArr) {
    merged.push(mergeVolumeDisplay({ wdWork: null, olBook: ob }));
  }
  merged.sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0));
  return merged;
}

/**
 * Complète une ligne déjà fusionnée (WD > OL) avec un item Google Books simplifié (`simplify_item` backend).
 * Ne remplace pas le titre ni les clés structurantes ; couverture / année / ISBN / id GB si manquants.
 */
export function enrichVolumeRowWithGoogleBooks(mergedRow, gbItem) {
  if (!mergedRow || !gbItem) return mergedRow;
  const out = { ...mergedRow };
  const sources = new Set(out.merged_sources || []);
  let touched = false;
  const thumb = (gbItem.thumbnail || '').replace(/^http:\/\//i, 'https://').trim();
  if (!out.cover_url && thumb) {
    out.cover_url = thumb;
    touched = true;
  }
  if (out.first_publish_year == null && gbItem.published_date) {
    const y = parseInt(String(gbItem.published_date).slice(0, 4), 10);
    if (!Number.isNaN(y)) {
      out.first_publish_year = y;
      touched = true;
    }
  }
  if (!out.isbn && (gbItem.isbn_13 || gbItem.isbn_10)) {
    const raw = String(gbItem.isbn_13 || gbItem.isbn_10 || '').replace(/[-\s]/g, '');
    if (raw) {
      out.isbn = raw;
      touched = true;
    }
  }
  if (gbItem.google_books_id) {
    out.google_books_id = gbItem.google_books_id;
    touched = true;
  }
  if (touched) sources.add('google_books');
  out.merged_sources = [...sources];
  return out;
}

/**
 * Enrichissement Google Books **par ISBN uniquement** (quota : au plus `maxLookups` appels réseau).
 * Ne touche aux lignes que si couverture ou année manquante (ISBN déjà présent sur la ligne).
 *
 * @param {object[]} rows
 * @param {{ fetchBook: (path: string) => Promise<Response>, maxLookups?: number }} opts
 */
export async function enrichVolumeRowsLimitedGoogleBooksByIsbn(rows, { fetchBook, maxLookups = 6 }) {
  const out = Array.isArray(rows) ? [...rows] : [];
  let used = 0;
  const max = Math.max(0, Math.min(Number(maxLookups) || 0, 20));
  for (let i = 0; i < out.length && used < max; i++) {
    const row = out[i];
    if (!row?.isbn) continue;
    if (row.cover_url && row.first_publish_year != null) continue;
    const clean = String(row.isbn).replace(/[^0-9Xx]/g, '');
    if (clean.length !== 10 && clean.length !== 13) continue;
    try {
      const res = await fetchBook(`/api/google-books/isbn/${encodeURIComponent(clean)}?limit=1`);
      if (!res.ok) continue;
      const data = await res.json();
      const gbItem = (data.items && data.items[0]) || null;
      if (gbItem) {
        out[i] = enrichVolumeRowWithGoogleBooks(out[i], gbItem);
        used += 1;
      }
    } catch {
      /* requête isolée : on continue */
    }
  }
  return out;
}

function stripForGoogleBooksQueryPart(s, maxLen) {
  return String(s || '')
    .replace(/[\r\n\u0000]/g, ' ')
    .replace(/"/g, '')
    .trim()
    .slice(0, maxLen);
}

function rowHasValidIsbn10Or13(row) {
  if (!row?.isbn) return false;
  const c = String(row.isbn).replace(/[^0-9Xx]/g, '');
  return c.length === 10 || c.length === 13;
}

/**
 * Repli Google Books : recherche `intitle:` + `inauthor:` (max `maxLookups` appels).
 * Réservé aux lignes encore incomplètes **sans** ISBN 10/13 exploitable (l’ISBN est traité par `enrichVolumeRowsLimitedGoogleBooksByIsbn`).
 */
export async function enrichVolumeRowsLimitedGoogleBooksByIntitle(rows, {
  fetchBook,
  authorName = '',
  maxLookups = 3,
}) {
  const author = stripForGoogleBooksQueryPart(authorName, 48);
  if (!author) return Array.isArray(rows) ? [...rows] : [];
  const out = Array.isArray(rows) ? [...rows] : [];
  let used = 0;
  const max = Math.max(0, Math.min(Number(maxLookups) || 0, 8));
  for (let i = 0; i < out.length && used < max; i++) {
    const row = out[i];
    if (row.cover_url && row.first_publish_year != null) continue;
    if (rowHasValidIsbn10Or13(row)) continue;
    const title = stripForGoogleBooksQueryPart(row.display_title || row.title, 72);
    if (title.length < 4) continue;
    const q = `intitle:${title} inauthor:${author}`;
    try {
      const res = await fetchBook(
        `/api/google-books/volumes?q=${encodeURIComponent(q)}&limit=1`
      );
      if (!res.ok) continue;
      const data = await res.json();
      const gbItem = (data.items && data.items[0]) || null;
      if (gbItem) {
        out[i] = enrichVolumeRowWithGoogleBooks(out[i], gbItem);
        used += 1;
      }
    } catch {
      /* ignore */
    }
  }
  return out;
}

/** Chaîne ISBN puis repli intitle+auteur (quotas séparés). */
export async function enrichVolumeRowsGoogleBooksIsbnThenIntitle(rows, {
  fetchBook,
  authorName = '',
  maxIsbn = 6,
  maxIntitle = 3,
}) {
  let out = await enrichVolumeRowsLimitedGoogleBooksByIsbn(rows, { fetchBook, maxLookups: maxIsbn });
  out = await enrichVolumeRowsLimitedGoogleBooksByIntitle(out, {
    fetchBook,
    authorName,
    maxLookups: maxIntitle,
  });
  return out;
}

/**
 * Adapte les volumes JSON de Wikidata live (`/wikidata/series/by-name/volumes`)
 * au format attendu par `mergeStaticWdWorksWithOpenLibrary`.
 */
export function mapLiveWikidataVolumesToWorks(volumes) {
  const arr = Array.isArray(volumes) ? volumes : [];
  return arr.map((v, i) => {
    const vn = v.volume_number != null ? v.volume_number : i + 1;
    const y = v.publication_year;
    const isbnRaw =
      v.isbn != null && String(v.isbn).trim() !== ''
        ? String(v.isbn).replace(/[-\s]/g, '')
        : '';
    return {
      title_fr: (v.title || '').trim(),
      title_en: '',
      volume: String(vn),
      publication_date: y != null && String(y).length >= 4 ? `${String(y).slice(0, 4)}-01-01` : '',
      work_qid: v.work_qid || null,
      isbns: isbnRaw ? [isbnRaw] : [],
    };
  });
}

/**
 * Convertit les lignes fusionnées (modale WD statique + OL + GB) au format attendu par la bibliothèque séries.
 * @param {string} seriesName
 * @param {object[]} rows sorties `mergeStaticWdWorksWithOpenLibrary` + `display_title` éventuel
 */
export function mapMergedVolumeRowsToLibraryVolumes(seriesName, rows) {
  const name = seriesName || 'Série';
  const arr = Array.isArray(rows) ? rows : [];
  return arr
    .slice()
    .sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0))
    .map((row, i) => {
      const vn = row.volume_number != null ? row.volume_number : i + 1;
      const label = (row.display_title || row.title || '').trim() || `${name} - Tome ${vn}`;
      const out = {
        volume_number: vn,
        volume_title: label,
        is_read: false,
        date_read: null,
      };
      if (row.work_qid) out.wikidata_work_qid = row.work_qid;
      return out;
    });
}
