/**
 * Qualité / nettoyage des résumés (Open Library, Google Books, Wikidata…).
 */

const OL_JUNK_SECTION =
  /(?:^|\n)\s*(?:Also contained in|Contenu dans|See also|Voir aussi|External links|Liens externes|References|Références)\s*:?\s*[\s\S]*$/i;

/**
 * Retire le bruit OL/Wiki (markdown, sections annexes, URLs).
 */
export function sanitizeSynopsis(text) {
  let t = String(text || '');
  if (!t.trim()) return '';

  t = t.replace(/<[^>]+>/g, ' ');
  // Couper dès « Also contained in: » etc.
  t = t.replace(OL_JUNK_SECTION, '');
  // [label](url) → label
  t = t.replace(/\[([^\]]+)\]\((?:https?:\/\/)?[^)]+\)/gi, '$1');
  // Liens markdown orphelins / URLs
  t = t.replace(/https?:\/\/[^\s)]+/gi, ' ');
  t = t.replace(/\[([^\]]+)\]/g, '$1');
  // Gras / italique markdown brut (**texte**, *texte*, __texte__)
  t = t.replace(/\*\*([^*]+)\*\*/g, '$1');
  t = t.replace(/__([^_]+)__/g, '$1');
  t = t.replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,]|$)/g, '$1$2');
  t = t.replace(/\*{1,2}/g, '');
  t = t.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n');
  t = t.replace(/[ \t]{2,}/g, ' ').trim();
  return t;
}

/**
 * Détecte les faux résumés (métadonnées Wikidata / compteurs / bruit OL).
 */
export function isUsableSynopsis(text) {
  const cleaned = sanitizeSynopsis(text);
  if (cleaned.length < 28) return false;
  if (/^wikidata\b/i.test(cleaned)) return false;
  if (/wikidata\s*[·•|]/i.test(cleaned)) return false;
  if (/^s[ée]rie\s+de\s+\d+\s+tome/i.test(cleaned)) return false;
  if (/^s[ée]rie\s+(roman|bd|manga)\b/i.test(cleaned)) return false;
  if (/^collection\s+de\s+\d+\s+livre/i.test(cleaned)) return false;
  if (/^also contained in\b/i.test(cleaned)) return false;
  // Trop de « liens » restants → pas une 4ᵉ
  const mdLeft = (cleaned.match(/\]\(/g) || []).length;
  if (mdLeft >= 2) return false;
  return true;
}

/** Texte affichable (toujours sanitizé). */
export function displaySynopsis(text) {
  if (!isUsableSynopsis(text)) return '';
  return sanitizeSynopsis(text);
}

const FR_STOP = new Set([
  'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'en', 'dans', 'sur',
  'pour', 'par', 'avec', 'qui', 'que', 'est', 'sont', 'cette', 'ces', 'aux',
  'son', 'sa', 'ses', 'leur', 'leurs', 'plus', 'mais', 'comme', 'entre', 'ou',
]);
const EN_STOP = new Set([
  'the', 'a', 'an', 'and', 'of', 'to', 'in', 'on', 'for', 'with', 'is', 'are',
  'this', 'that', 'from', 'by', 'as', 'at', 'his', 'her', 'their', 'was', 'were',
  'be', 'or', 'which', 'who', 'into', 'has', 'have',
]);

/** Heuristique : le texte ressemble davantage au français qu'à l'anglais. */
export function looksFrench(text) {
  const t = String(text || '').trim();
  if (t.length < 20) return false;
  const accentN = (t.match(/[àâäéèêëïîôùûüçœæÀÂÄÉÈÊËÏÎÔÙÛÜÇŒÆ]/g) || []).length;
  const tokens = t.toLowerCase().match(/[a-zàâäéèêëïîôùûüçœæ']+/gi) || [];
  if (!tokens.length) return false;
  const frHits = tokens.filter((w) => FR_STOP.has(w)).length;
  const enHits = tokens.filter((w) => EN_STOP.has(w)).length;
  if (accentN >= 3) return true;
  if (accentN >= 1 && frHits >= enHits) return true;
  if (frHits >= 3 && frHits > enHits) return true;
  if (frHits >= 2 && enHits === 0) return true;
  return false;
}

export function looksEnglish(text) {
  const t = String(text || '').trim();
  if (t.length < 20) return false;
  if (looksFrench(t)) return false;
  const tokens = t.toLowerCase().match(/[a-z']+/g) || [];
  if (!tokens.length) return false;
  const enHits = tokens.filter((w) => EN_STOP.has(w)).length;
  const frHits = tokens.filter((w) => FR_STOP.has(w)).length;
  const accentN = (t.match(/[àâäéèêëïîôùûüçœæ]/gi) || []).length;
  return enHits >= 3 && enHits > frHits && accentN === 0;
}

/** Choisit le meilleur résumé : français d'abord, sinon non-anglais, sinon premier utilisable. */
export function preferFrenchSynopsis(...candidates) {
  const usable = [];
  for (const raw of candidates) {
    const text = displaySynopsis(raw);
    if (text) usable.push(text);
  }
  if (!usable.length) return '';
  const fr = usable.find(looksFrench);
  if (fr) return fr;
  const nonEn = usable.find((t) => !looksEnglish(t));
  return nonEn || usable[0];
}
