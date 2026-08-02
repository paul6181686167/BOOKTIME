/**
 * Détecte les faux résumés (métadonnées Wikidata / compteurs de tomes)
 * stockés sur les fiches series_library rétrogradées en livre individuel.
 */
export function isUsableSynopsis(text) {
  const t = String(text || '').trim();
  if (t.length < 28) return false;
  if (/^wikidata\b/i.test(t)) return false;
  if (/wikidata\s*[·•|]/i.test(t)) return false;
  if (/^s[ée]rie\s+de\s+\d+\s+tome/i.test(t)) return false;
  if (/^s[ée]rie\s+(roman|bd|manga)\b/i.test(t)) return false;
  if (/^collection\s+de\s+\d+\s+livre/i.test(t)) return false;
  return true;
}
