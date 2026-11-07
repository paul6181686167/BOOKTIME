/**
 * Collections personnalisées (étagères) — persistées en localStorage.
 * Chaque collection contient des livres et/ou des séries de la bibliothèque.
 */

export const PROFILE_STORAGE_KEY = 'booktime_profile_data';

export function loadProfileData() {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

export function saveProfileData(data) {
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(data));
}

/** Normalise books[] legacy → items[] */
export function normalizeCollection(c) {
  if (!c || typeof c !== 'object') return c;
  const items = Array.isArray(c.items)
    ? c.items
    : Array.isArray(c.books)
      ? c.books.map((b) =>
          typeof b === 'string'
            ? { key: `book:${b}`, type: 'book', id: b, title: b, author: '', cover_url: null }
            : {
                key: b.key || `${b.type || 'book'}:${b.id}`,
                type: b.type || 'book',
                id: b.id,
                title: b.title || 'Sans titre',
                author: b.author || '',
                cover_url: b.cover_url || null,
              }
        )
      : [];
  return { ...c, items };
}

/** Couleurs proposées pour distinguer les collections (liseré des vignettes). */
export const COLLECTION_COLORS = [
  { id: 'green', label: 'Vert', hex: '#22c55e' },
  { id: 'blue', label: 'Bleu', hex: '#3b82f6' },
  { id: 'red', label: 'Rouge', hex: '#ef4444' },
  { id: 'orange', label: 'Orange', hex: '#f97316' },
  { id: 'yellow', label: 'Jaune', hex: '#eab308' },
  { id: 'purple', label: 'Violet', hex: '#a855f7' },
  { id: 'pink', label: 'Rose', hex: '#ec4899' },
  { id: 'teal', label: 'Turquoise', hex: '#14b8a6' },
];

/** Émis à chaque modification : les grilles de la bibliothèque se mettent à jour. */
export const COLLECTIONS_CHANGED_EVENT = 'booktime:collections-changed';

const HEX_RE = /^#[0-9a-f]{6}$/i;

/** Couleur par défaut stable (dérivée de l'identifiant) pour les anciennes collections. */
export function defaultCollectionColor(id) {
  const s = String(id ?? '');
  let h = 0;
  for (let i = 0; i < s.length; i += 1) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return COLLECTION_COLORS[h % COLLECTION_COLORS.length].hex;
}

/** Couleur effective d'une collection (valide, sinon couleur par défaut). */
export function collectionColor(c) {
  return c && typeof c.color === 'string' && HEX_RE.test(c.color)
    ? c.color
    : defaultCollectionColor(c?.id);
}

export function getCollections() {
  const data = loadProfileData();
  return (data.collections || []).map(normalizeCollection);
}

export function saveCollections(collections) {
  const data = loadProfileData();
  saveProfileData({ ...data, collections });
  try {
    if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
      window.dispatchEvent(new Event(COLLECTIONS_CHANGED_EVENT));
    }
  } catch {
    /* ignore */
  }
  return collections.map(normalizeCollection);
}

/**
 * Table « clé d'élément → couleurs des collections qui le contiennent ».
 * Clés : `book:<id>` ou `series:<id>`.
 */
export function buildCollectionColorMap(collections = getCollections()) {
  const map = new Map();
  collections.forEach((raw) => {
    const c = normalizeCollection(raw);
    const color = collectionColor(c);
    (c.items || []).forEach((it) => {
      const list = map.get(it.key) || [];
      if (!list.includes(color)) list.push(color);
      map.set(it.key, list);
    });
  });
  return map;
}

/** Couleurs de collection d'une vignette de la grille (livre ou série). */
export function colorsForGridItem(map, item) {
  if (!map || !map.size || !item) return undefined;
  if (item.isSeriesCard) {
    const ids = [item.librarySeriesId, item.id].filter(Boolean).map(String);
    for (const id of ids) {
      const found = map.get(`series:${id}`);
      if (found) return found;
    }
    return undefined;
  }
  return item.id != null ? map.get(`book:${item.id}`) : undefined;
}

/** Ombre portée de la vignette + liseré(s) aux couleurs des collections. */
export function collectionRimShadow(colors, baseShadow = '0 8px 24px rgba(0,0,0,0.55)') {
  if (!colors || !colors.length) return undefined;
  const rims = colors.slice(0, 3).map((color, i) => `0 0 0 ${(i + 1) * 2}px ${color}`);
  return [...rims, baseShadow].join(', ');
}

export function setCollectionColor(collectionId, color) {
  if (!HEX_RE.test(color || '')) return { ok: false, reason: 'invalid' };
  const collections = getCollections();
  const idx = collections.findIndex((c) => String(c.id) === String(collectionId));
  if (idx < 0) return { ok: false, reason: 'missing' };
  const next = [...collections];
  next[idx] = { ...collections[idx], color };
  saveCollections(next);
  return { ok: true, collections: next };
}

/** Première couleur de la palette non encore utilisée (sinon la suivante en rotation). */
export function nextFreeCollectionColor(collections = getCollections()) {
  const used = new Set(collections.map((c) => collectionColor(c)));
  const free = COLLECTION_COLORS.find((c) => !used.has(c.hex));
  return (free || COLLECTION_COLORS[collections.length % COLLECTION_COLORS.length]).hex;
}

export function makeCollectionItem({ type, id, title, author, cover_url }) {
  const t = type === 'series' ? 'series' : 'book';
  return {
    key: `${t}:${id}`,
    type: t,
    id: String(id),
    title: title || 'Sans titre',
    author: author || '',
    cover_url: cover_url || null,
  };
}

export function collectionContains(collection, type, id) {
  const key = `${type === 'series' ? 'series' : 'book'}:${id}`;
  return (normalizeCollection(collection).items || []).some((it) => it.key === key);
}

export function addItemToCollection(collectionId, item) {
  const collections = getCollections();
  const idx = collections.findIndex((c) => String(c.id) === String(collectionId));
  if (idx < 0) return { ok: false, reason: 'missing' };
  const col = normalizeCollection(collections[idx]);
  const entry = makeCollectionItem(item);
  if ((col.items || []).some((it) => it.key === entry.key)) {
    return { ok: false, reason: 'duplicate', collections };
  }
  const next = [...collections];
  next[idx] = { ...col, items: [...(col.items || []), entry], books: undefined };
  saveCollections(next);
  return { ok: true, collections: next };
}

export function removeItemFromCollection(collectionId, itemKey) {
  const collections = getCollections();
  const idx = collections.findIndex((c) => String(c.id) === String(collectionId));
  if (idx < 0) return { ok: false, collections };
  const col = normalizeCollection(collections[idx]);
  const next = [...collections];
  next[idx] = {
    ...col,
    items: (col.items || []).filter((it) => it.key !== itemKey),
    books: undefined,
  };
  saveCollections(next);
  return { ok: true, collections: next };
}

export function createCollection(name, color) {
  const trimmed = (name || '').trim();
  if (!trimmed) return { ok: false, reason: 'empty' };
  const collections = getCollections();
  if (collections.some((c) => c.name.toLowerCase() === trimmed.toLowerCase())) {
    return { ok: false, reason: 'exists' };
  }
  // Identifiant unique, même si deux collections sont créées dans la même milliseconde
  let id = Date.now();
  while (collections.some((c) => String(c.id) === String(id))) id += 1;
  const created = {
    id,
    name: trimmed,
    items: [],
    color: HEX_RE.test(color || '') ? color : nextFreeCollectionColor(collections),
  };
  const next = [...collections, created];
  saveCollections(next);
  return { ok: true, collection: created, collections: next };
}

export function deleteCollection(collectionId) {
  const next = getCollections().filter((c) => String(c.id) !== String(collectionId));
  saveCollections(next);
  return { ok: true, collections: next };
}
