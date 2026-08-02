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

export function getCollections() {
  const data = loadProfileData();
  return (data.collections || []).map(normalizeCollection);
}

export function saveCollections(collections) {
  const data = loadProfileData();
  saveProfileData({ ...data, collections });
  return collections.map(normalizeCollection);
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

export function createCollection(name) {
  const trimmed = (name || '').trim();
  if (!trimmed) return { ok: false, reason: 'empty' };
  const collections = getCollections();
  if (collections.some((c) => c.name.toLowerCase() === trimmed.toLowerCase())) {
    return { ok: false, reason: 'exists' };
  }
  const created = { id: Date.now(), name: trimmed, items: [] };
  const next = [...collections, created];
  saveCollections(next);
  return { ok: true, collection: created, collections: next };
}

export function deleteCollection(collectionId) {
  const next = getCollections().filter((c) => String(c.id) !== String(collectionId));
  saveCollections(next);
  return { ok: true, collections: next };
}
