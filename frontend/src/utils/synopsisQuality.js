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
