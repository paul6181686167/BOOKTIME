/**
 * Qualité / nettoyage des résumés (Open Library, Google Books, Wikidata…).
 */

const OL_JUNK_SECTION =
  /(?:^|\n)\s*(?:Also contained in|Contenu dans|See also|Voir aussi|External links|Liens externes|References|Références)\s*:?\s*[\s\S]*$/i;

/**
 * Retire le bruit OL/Wiki (markdown, sections annexes, URLs).
 */
function repairEncoding(text) {
  let t = String(text || '');
  if (/Ã.|Â.|â€/.test(t)) {
    try {
      const repaired = decodeURIComponent(escape(t));
      if (repaired && !repaired.includes('\uFFFD')) t = repaired;
    } catch {
      /* garder le texte d'origine */
    }
  }
  t = t.replace(/\uFFFD/g, '');
  t = t.replace(/fran[\uFFFD]?aise/gi, (m) => (m[0] === 'F' ? 'Française' : 'française'));
  t = t.replace(/([dlLnNsS]|qu|Qu)''/g, "$1'");
  t = t.replace(/''/g, "'");
  return t;
}

export function sanitizeSynopsis(text) {
  let t = repairEncoding(String(text || ''));
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
  if (/profil d['’ ]une [oœ]uvre|fiche de lecture|commentaire compos|analyse critique|dans la collection\s+["«']?\s*profil/i.test(cleaned.slice(0, 500))) {
    return false;
  }
  if (/^also contained in\b/i.test(cleaned)) return false;
  // Homonyme chanson / album / film (ex. « For Whom the Bell Tolls » = Metallica)
  const head = cleaned.slice(0, 450);
  const offBook = /\b(chanson|chansons|album|single|morceau|morceaux|film|cin[eé]ma|t[eé]l[eé]vision|[eé]pisode|r[eé]alisateur)\b|bande[- ]originale|jeu vid[eé]o|du groupe|piste de l['’ ]?album/i;
  const bookish = /\b(roman|romans|novel|novella|livre|livres|book|books|r[eé]cit|nouvelle|nouvelles)\b/i;
  if (offBook.test(head) && !bookish.test(head)) return false;
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
  'be', 'or', 'which', 'who', 'into', 'has', 'have', 'its', 'about',
  'after', 'before', 'when', 'where', 'while', 'through', 'over', 'under',
]);
const ES_STOP = new Set([
  'el', 'los', 'las', 'una', 'unos', 'unas', 'es', 'son', 'del', 'al', 'se',
  'su', 'sus', 'como', 'pero', 'este', 'esta', 'estos', 'estas', 'está', 'están',
  'hay', 'muy', 'más', 'también', 'cuando', 'donde', 'sobre', 'hasta', 'desde',
  'porque', 'sin', 'entre', 'tiene', 'tienen', 'solo', 'sólo', 'único', 'unico',
]);
/** Mots vraiment français (pas partagés avec l'espagnol : la, de, en, un, que, son, le). */
const FR_UNIQUE = new Set([
  'les', 'une', 'des', 'du', 'et', 'est', 'sont', 'cette', 'ces', 'aux',
  'qui', 'dans', 'pour', 'par', 'avec', 'mais', 'leur', 'leurs',
  'sa', 'ses', 'plus',
]);
/** Mots vraiment espagnols (pas partagés avec le français). */
const ES_UNIQUE = new Set([
  'el', 'los', 'las', 'una', 'unos', 'unas', 'es', 'son', 'del', 'al', 'se',
  'su', 'sus', 'está', 'están', 'hay', 'más', 'también', 'pero', 'este', 'esta',
  'tiene', 'tienen', 'porque',
]);
const EN_MARKERS = new Set([
  'novel', 'novella', 'story', 'stories', 'book', 'books', 'published', 'author',
  'series', 'character', 'characters', 'fiction', 'science', 'fantasy', 'thriller',
  'edition', 'volume', 'volumes', 'chapter', 'chapters', 'english', 'american',
]);
const FR_MARKERS = new Set([
  'roman', 'récit', 'histoire', 'publié', 'publie', 'auteur', 'tome', 'tomes',
  'série', 'serie', 'personnage', 'personnages', 'édition', 'edition', 'chapitre',
]);

function langScores(text) {
  const t = String(text || '').trim();
  const accentN = (t.match(/[àâäéèêëïîôùûüçœæÀÂÄÉÈÊËÏÎÔÙÛÜÇŒÆ]/g) || []).length;
  const tokens = t.toLowerCase().match(/[a-zàâäáéèêëïîíôóùûúüçœæñ']+/gi) || [];
  return {
    len: t.length,
    accentN,
    tokens,
    frHits: tokens.filter((w) => FR_STOP.has(w)).length,
    enHits: tokens.filter((w) => EN_STOP.has(w)).length,
    esHits: tokens.filter((w) => ES_STOP.has(w)).length,
    frUnique: tokens.filter((w) => FR_UNIQUE.has(w)).length,
    esUnique: tokens.filter((w) => ES_UNIQUE.has(w)).length,
    frMark: tokens.filter((w) => FR_MARKERS.has(w)).length,
    enMark: tokens.filter((w) => EN_MARKERS.has(w)).length,
  };
}

/** Anglais dominant, même avec 1–2 accents (noms propres). */
function englishDominant({ enHits, frHits }) {
  return enHits >= 6 && enHits >= frHits * 2;
}

/** Espagnol dominant (ex. résumé Google Books non traduit, y compris texte mixte). */
export function looksSpanish(text) {
  const s = langScores(text);
  if (s.len < 20 || !s.tokens.length) return false;
  if (s.esUnique >= 3 && s.esUnique > s.frUnique) return true;
  if (s.esUnique >= 2 && s.esUnique >= s.frUnique && s.frUnique <= 4) return true;
  if (s.esHits >= 3 && s.esHits > s.frHits) return true;
  // Ouverture espagnole d'un blurb concaténé ES + EN + FR
  if (s.len > 350) {
    const head = String(text).slice(0, 400);
    const hs = langScores(head);
    if (hs.esUnique >= 3 && hs.esUnique > hs.frUnique) return true;
  }
  return false;
}

/**
 * Extrait les paragraphes français d'un résumé concaténé (ES/EN/FR).
 * Ignore les blocs tronqués (commençant en minuscule).
 */
export function extractFrenchSynopsis(text) {
  const cleaned = sanitizeSynopsis(text);
  if (!cleaned) return '';
  const chunks = cleaned
    .split(/\bENGLISH DESCRIPTION\b[:\s]*/i)
    .flatMap((block) => block.split(/\n\s*\n+/))
    .map((p) => p.trim())
    .filter((p) => p.length >= 40);
  const french = chunks.filter((p) => {
    if (/^[a-zàâäéèêëïîôùûüç]/.test(p)) return false;
    return looksFrench(p) && !looksSpanish(p) && !looksEnglish(p);
  });
  if (!french.length) return '';
  const joined = french.join('\n\n');
  return isUsableSynopsis(joined) ? sanitizeSynopsis(joined) : '';
}

/** Heuristique : le texte ressemble davantage au français qu'à l'anglais. */
export function looksFrench(text) {
  const s = langScores(text);
  if (s.len < 20 || !s.tokens.length) return false;
  if (englishDominant(s)) return false;
  if (looksSpanish(text)) return false;
  if (s.accentN >= 3 && s.frHits + 1 >= s.enHits) return true;
  if (s.accentN >= 1 && s.frHits >= s.enHits) return true;
  if (s.frHits >= 3 && s.frHits > s.enHits) return true;
  if (s.frHits >= 2 && s.enHits === 0) return true;
  if (s.frMark >= 2 && s.frMark >= s.enHits) return true;
  return false;
}

export function looksEnglish(text) {
  const s = langScores(text);
  if (s.len < 20 || !s.tokens.length) return false;
  if (englishDominant(s)) return true;
  if (looksFrench(text)) return false;
  if (s.enMark >= 2 && s.enHits >= s.frHits) return true;
  return s.enHits >= 3 && s.enHits > s.frHits;
}

/**
 * Choisit le meilleur résumé : français d'abord.
 * `{ rejectEnglish: true }` (alias `{ frenchOnly: true }`) n'accepte que du français.
 */
export function preferFrenchSynopsis(...candidates) {
  let rejectEnglish = false;
  const rawList = [];
  for (const raw of candidates) {
    if (raw && typeof raw === 'object' && !Array.isArray(raw) && ('rejectEnglish' in raw || 'frenchOnly' in raw)) {
      rejectEnglish = !!(raw.rejectEnglish || raw.frenchOnly);
      continue;
    }
    rawList.push(raw);
  }
  const usable = [];
  for (const raw of rawList) {
    const extracted = extractFrenchSynopsis(raw);
    if (extracted) {
      usable.push(extracted);
      continue;
    }
    const text = displaySynopsis(raw);
    if (text) usable.push(text);
  }
  if (!usable.length) return '';
  const fr = usable.find((t) => looksFrench(t) && !looksSpanish(t) && !looksEnglish(t));
  if (fr) return fr;
  if (rejectEnglish) return '';
  const nonEn = usable.find((t) => !looksEnglish(t) && !looksSpanish(t));
  if (nonEn) return nonEn;
  return usable[0];
}
