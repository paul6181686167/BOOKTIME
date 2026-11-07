import {
  mergeCollections,
  pullCollections,
  pushCollections,
} from '../collectionsSync';
import {
  createCollection,
  addItemToCollection,
  getCollections,
  getSyncState,
  saveCollections,
} from '../../utils/collectionsStorage';

const json = (status, data) => Promise.resolve({ status, ok: status < 300, json: () => Promise.resolve(data) });

describe('collectionsSync', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('token', 'tok');
    localStorage.setItem('user', JSON.stringify({ id: 'u1' }));
    global.fetch = jest.fn();
  });

  describe('mergeCollections', () => {
    it('réunit les éléments, garde la couleur locale et ne crée pas de doublon de nom', () => {
      const local = [
        { id: 1, name: 'SF', color: '#ef4444', items: [{ key: 'book:a', type: 'book', id: 'a', title: 'A' }] },
        { id: 9, name: 'Local seul', items: [] },
      ];
      const remote = [
        { id: 7, name: 'sf', color: '#22c55e', items: [{ key: 'book:b', type: 'book', id: 'b', title: 'B' }] },
      ];
      const out = mergeCollections(local, remote);
      expect(out.map((c) => c.name)).toEqual(['sf', 'Local seul']);
      expect(out[0].items.map((i) => i.key).sort()).toEqual(['book:a', 'book:b']);
      expect(out[0].color).toBe('#ef4444');
    });
  });

  describe('pullCollections', () => {
    it('migre les collections locales existantes vers le compte à la première synchronisation', async () => {
      createCollection('Anciennes', '#22c55e');
      global.fetch
        .mockReturnValueOnce(json(200, { collections: [], version: 0 })) // GET
        .mockReturnValueOnce(json(200, { collections: [], version: 1 })); // PUT

      await pullCollections();

      const put = global.fetch.mock.calls[1];
      expect(put[1].method).toBe('PUT');
      const body = JSON.parse(put[1].body);
      expect(body.base_version).toBe(0);
      expect(body.collections[0].name).toBe('Anciennes');
      expect(getSyncState()).toMatchObject({ userId: 'u1', version: 1, dirty: false });
    });

    it('reprend les collections du compte sur un appareil vide', async () => {
      global.fetch.mockReturnValueOnce(
        json(200, {
          collections: [{ id: 3, name: 'Du compte', color: '#3b82f6', items: [] }],
          version: 4,
        })
      );
      await pullCollections();
      expect(getCollections().map((c) => c.name)).toEqual(['Du compte']);
      expect(getSyncState()).toMatchObject({ userId: 'u1', version: 4, dirty: false });
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    it("n'envoie jamais les collections d'un autre compte", async () => {
      saveCollections([{ id: 1, name: 'Autre compte', items: [] }]);
      localStorage.setItem(
        'booktime_collections_sync',
        JSON.stringify({ userId: 'u-autre', version: 2, dirty: true })
      );
      global.fetch.mockReturnValueOnce(json(200, { collections: [], version: 0 }));

      await pullCollections();

      expect(getCollections()).toEqual([]);
      expect(global.fetch).toHaveBeenCalledTimes(1); // pas de PUT
      expect(getSyncState()).toMatchObject({ userId: 'u1', dirty: false });
    });

    it('ne fait rien sans connexion', async () => {
      localStorage.clear();
      expect(await pullCollections()).toBe(false);
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('pushCollections', () => {
    it('fusionne puis renvoie après un conflit 409', async () => {
      localStorage.setItem(
        'booktime_collections_sync',
        JSON.stringify({ userId: 'u1', version: 1, dirty: true })
      );
      const { collection } = createCollection('Locale', '#22c55e');
      addItemToCollection(collection.id, { type: 'book', id: 'l1', title: 'Local' });
      global.fetch
        .mockReturnValueOnce(
          json(409, {
            conflict: true,
            version: 5,
            collections: [{ id: 50, name: 'Distante', items: [] }],
          })
        )
        .mockReturnValueOnce(json(200, { collections: [], version: 6 }));

      expect(await pushCollections()).toBe(true);

      const retry = JSON.parse(global.fetch.mock.calls[1][1].body);
      expect(retry.base_version).toBe(5);
      expect(retry.collections.map((c) => c.name).sort()).toEqual(['Distante', 'Locale']);
      expect(getSyncState()).toMatchObject({ version: 6, dirty: false });
    });

    it('reste « à envoyer » quand le réseau est coupé', async () => {
      createCollection('Hors ligne');
      global.fetch.mockRejectedValueOnce(new Error('offline'));
      expect(await pushCollections()).toBe(false);
      expect(getSyncState().dirty).toBe(true);
    });
  });
});
