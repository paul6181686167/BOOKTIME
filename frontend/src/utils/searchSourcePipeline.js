/**
 * Pipeline recherche / sources : priorités **Wikidata > Open Library > Google Books**
 * (aligné sur `sourceMerge.js` pour la modale série ; ici : cartes recherche + quotas partagés).
 */

import { normalizeTitleKey } from './sourceMerge';

/** Quotas par défaut pour `enrichVolumeRowsGoogleBooksIsbnThenIntitle` (modale série). */
export const DEFAULT_SERIES_MODAL_GOOGLE_BOOKS = {
  maxIsbn: 6,
  maxIntitle: 3,
};

function seriesCardDedupKey(card) {
  const name = card?.name || card?.title || '';
  const author = card?.author || '';
  return `${normalizeTitleKey(name)}|${normalizeTitleKey(author).slice(0, 48)}`;
}

/**
 * Priorité Wikidata : si une carte série Wikidata statique existe pour le même nom de
 * série normalisé qu'une autre carte série (Open Library, curée ou saga), on conserve la
 * carte WD et on retire les doublons non-WD. La couverture et les tomes des cartes retirées
 * sont récupérés sur la carte WD si elle en manque (meilleure UX, source unique).
 *
 * @param {object[]} finalResults résultats mélangés (séries + livres)
 * @returns {object[]}
 */
export function dedupeWikidataStaticSeriesOverOpenLibrary(finalResults) {
  if (!Array.isArray(finalResults) || finalResults.length === 0) return finalResults;

  // Carte WD de référence par clé (titre|auteur normalisé)
  const wdByKey = new Map();
  finalResults.forEach((item) => {
    if (item?.isSeriesCard && item.isStaticWikidataCard && item.wikidata_qid) {
      const k = seriesCardDedupKey(item);
      if (!wdByKey.has(k)) wdByKey.set(k, item);
    }
  });
  if (wdByKey.size === 0) return finalResults;

  // Récupérer couverture / tomes des doublons non-WD vers la carte WD correspondante.
  finalResults.forEach((item) => {
    if (!item?.isSeriesCard || item.isStaticWikidataCard) return;
    const wd = wdByKey.get(seriesCardDedupKey(item));
    if (!wd) return;
    if (!wd.cover_url && item.cover_url) wd.cover_url = item.cover_url;
    if ((!Array.isArray(wd.books) || wd.books.length === 0) && Array.isArray(item.books) && item.books.length) {
      wd.books = item.books;
    }
  });

  return finalResults.filter((item) => {
    if (!item?.isSeriesCard || item.isStaticWikidataCard) return true;
    const k = seriesCardDedupKey(item);
    return !wdByKey.has(k);
  });
}

/**
 * Déduplication finale des cartes série par NOM normalisé (indépendamment de l'auteur).
 * Garantit une seule carte par série, même si plusieurs sources la produisent
 * (curé + Wikidata + saga + heuristique). Priorité : Wikidata, sinon meilleur relevanceScore.
 * La couverture, les tomes et le total le plus élevé sont reportés sur la carte conservée.
 *
 * @param {object[]} results résultats mélangés (séries + livres)
 * @returns {object[]}
 */
export function dedupeSeriesCardsByName(results) {
  if (!Array.isArray(results) || results.length === 0) return results;

  const isBetter = (candidate, current) => {
    const candWd = !!candidate.isStaticWikidataCard;
    const curWd = !!current.isStaticWikidataCard;
    if (candWd !== curWd) return candWd; // Wikidata prioritaire
    return (candidate.relevanceScore || 0) > (current.relevanceScore || 0);
  };

  const winnerByName = new Map(); // nameKey → carte conservée
  const nonSeries = [];
  const seriesOrder = [];

  results.forEach((item) => {
    if (!item?.isSeriesCard) {
      nonSeries.push(item);
      return;
    }
    const key = normalizeTitleKey(item.name || item.title || '');
    if (!key) {
      seriesOrder.push(item);
      return;
    }
    const current = winnerByName.get(key);
    if (!current) {
      winnerByName.set(key, item);
      seriesOrder.push(key);
      return;
    }
    const winner = isBetter(item, current) ? item : current;
    const loser = winner === item ? current : item;
    if (!winner.cover_url && loser.cover_url) winner.cover_url = loser.cover_url;
    if ((!Array.isArray(winner.books) || winner.books.length === 0) && Array.isArray(loser.books) && loser.books.length) {
      winner.books = loser.books;
    }
    // Compléter l'auteur si la carte gagnante (souvent Wikidata) n'en a pas.
    if (!winner.author && loser.author) winner.author = loser.author;
    // Ne récupérer le total du perdant que si le gagnant n'en a pas (ne pas écraser
    // un total curé faisant autorité par un simple nombre de livres trouvés).
    if (!(winner.totalBooks > 0) && loser.totalBooks > 0) winner.totalBooks = loser.totalBooks;
    winner.relevanceScore = Math.max(winner.relevanceScore || 0, loser.relevanceScore || 0);
    winnerByName.set(key, winner);
  });

  const dedupedSeries = seriesOrder.map((entry) =>
    typeof entry === 'string' ? winnerByName.get(entry) : entry
  );
  return [...dedupedSeries, ...nonSeries];
}

/**
 * Catégorie livre/série (roman | bd | manga) à partir d’une entrée recherche Wikidata statique.
 * @param {object} entry ligne API `/api/static-wikidata/series/search` (lite)
 */
export function inferCategoryFromWikidataSearchEntry(entry) {
  if (!entry || typeof entry !== 'object') return 'roman';
  // Catégorie calculée côté backend (type Wikidata P31 + genres P136) : on lui fait confiance.
  if (entry.category === 'manga' || entry.category === 'bd' || entry.category === 'roman') {
    return entry.category;
  }
  const blob = [
    entry.name,
    entry.name_fr,
    entry.name_en,
    entry.label,
    entry.type,
    entry.author_label,
    entry.author,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  if (
    /\b(manga|manhwa|manhua|light novel|webtoon|sh[ōo]nen|shounen|seinen|josei|kodomo|sh[ōo]jo)\b/i.test(
      blob
    )
  ) {
    return 'manga';
  }
  if (
    /\b(comic|comics|comic book|graphic novel|roman graphique|bande dessin[ée]e|fumetti|marvel|dc comics|bd franco|franco-belgian)\b/i.test(
      blob
    )
  ) {
    return 'bd';
  }
  return 'roman';
}
