import {
  COLLECTION_COLORS,
  createCollection,
  addItemToCollection,
  setCollectionColor,
  collectionColor,
  getCollections,
  buildCollectionColorMap,
  colorsForGridItem,
  collectionRimShadow,
  COLLECTIONS_CHANGED_EVENT,
  saveCollections,
} from '../collectionsStorage';

describe('couleurs des collections', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('attribue une couleur différente à chaque nouvelle collection', () => {
    const a = createCollection('Coups de cœur');
    const b = createCollection('À offrir');
    expect(a.collection.color).toBe(COLLECTION_COLORS[0].hex);
    expect(b.collection.color).toBe(COLLECTION_COLORS[1].hex);
  });

  it('respecte la couleur choisie et permet de la changer', () => {
    const { collection } = createCollection('SF', '#a855f7');
    expect(collectionColor(getCollections()[0])).toBe('#a855f7');
    expect(setCollectionColor(collection.id, '#ef4444').ok).toBe(true);
    expect(collectionColor(getCollections()[0])).toBe('#ef4444');
    expect(setCollectionColor(collection.id, 'rouge').ok).toBe(false);
  });

  it('donne une couleur stable aux anciennes collections sans couleur', () => {
    saveCollections([{ id: 42, name: 'Ancienne', items: [] }]);
    const first = collectionColor(getCollections()[0]);
    expect(COLLECTION_COLORS.map((c) => c.hex)).toContain(first);
    expect(collectionColor(getCollections()[0])).toBe(first);
  });

  it('retrouve les couleurs d\'un livre ou d\'une série de la grille', () => {
    const a = createCollection('A', '#22c55e').collection;
    const b = createCollection('B', '#3b82f6').collection;
    addItemToCollection(a.id, { type: 'book', id: 'b1', title: 'L1' });
    addItemToCollection(b.id, { type: 'book', id: 'b1', title: 'L1' });
    addItemToCollection(b.id, { type: 'series', id: 's1', title: 'S1' });

    const map = buildCollectionColorMap();
    expect(colorsForGridItem(map, { id: 'b1' })).toEqual(['#22c55e', '#3b82f6']);
    expect(colorsForGridItem(map, { id: 'x', librarySeriesId: 's1', isSeriesCard: true })).toEqual(['#3b82f6']);
    expect(colorsForGridItem(map, { id: 's1', isSeriesCard: true })).toEqual(['#3b82f6']);
    expect(colorsForGridItem(map, { id: 'inconnu' })).toBeUndefined();
  });

  it('construit l\'ombre avec un liseré par couleur', () => {
    expect(collectionRimShadow(undefined)).toBeUndefined();
    expect(collectionRimShadow(['#22c55e'])).toMatch(/^0 0 0 2px #22c55e, /);
    expect(collectionRimShadow(['#22c55e', '#3b82f6'])).toContain('0 0 0 4px #3b82f6');
  });

  it('prévient les grilles à chaque modification', () => {
    const spy = jest.fn();
    window.addEventListener(COLLECTIONS_CHANGED_EVENT, spy);
    createCollection('X');
    window.removeEventListener(COLLECTIONS_CHANGED_EVENT, spy);
    expect(spy).toHaveBeenCalled();
  });
});
