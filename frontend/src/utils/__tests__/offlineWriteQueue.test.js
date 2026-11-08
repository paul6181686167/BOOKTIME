import {
  enqueueCreateBook,
  enqueueUpdateBook,
  enqueueDeleteBook,
  enqueueCreateSeries,
  enqueueToggleVolume,
  flushOfflineQueue,
  getPendingCount,
  getQueueJobs,
  clearOfflineQueue,
  mergePendingBooks,
  shouldEnqueueWrite,
  isNetworkFailure,
  QUEUE_KEY,
} from '../offlineWriteQueue';
import { saveLibraryCache, loadLibraryCache } from '../offlineLibraryCache';

describe('file d’attente hors ligne', () => {
  const originalOnLine = navigator.onLine;

  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('token', 'test-token');
    localStorage.setItem('user', JSON.stringify({ id: 'u1' }));
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false });
    global.fetch = jest.fn();
  });

  afterEach(() => {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: originalOnLine });
    jest.restoreAllMocks();
    clearOfflineQueue();
  });

  test('un ajout hors ligne est mis en file et visible dans le cache', () => {
    const local = enqueueCreateBook({ title: 'Dune', author: 'Herbert', category: 'roman' });
    expect(local.id).toMatch(/^offline_book_/);
    expect(local._pendingSync).toBe(true);
    expect(getPendingCount()).toBe(1);
    const cached = loadLibraryCache({})?.books || [];
    expect(cached.some((b) => b.title === 'Dune' && b._pendingSync)).toBe(true);
  });

  test('deux mises à jour du même livre sont fusionnées', () => {
    saveLibraryCache([{ id: 'b1', title: '1984', status: 'to_read' }], {});
    enqueueUpdateBook('b1', { status: 'reading' });
    enqueueUpdateBook('b1', { rating: 5, review: 'Superbe' });
    const jobs = getQueueJobs();
    expect(jobs).toHaveLength(1);
    expect(jobs[0].payload).toEqual({ status: 'reading', rating: 5, review: 'Superbe' });
    const cached = loadLibraryCache({})?.books || [];
    expect(cached[0]).toMatchObject({
      id: 'b1',
      status: 'reading',
      rating: 5,
      review: 'Superbe',
      _pendingSync: true,
    });
  });

  test('supprimer un livre encore non envoyé retire le job de création', () => {
    const local = enqueueCreateBook({ title: 'Temp', author: 'X' });
    enqueueDeleteBook(local.id);
    expect(getPendingCount()).toBe(0);
    expect((loadLibraryCache({})?.books || []).some((b) => b.id === local.id)).toBe(false);
  });

  test('une note fusionne dans le job de création local', () => {
    const local = enqueueCreateBook({ title: 'Circe', author: 'Miller' });
    enqueueUpdateBook(local.id, { review: 'Magnifique', rating: 5 });
    const jobs = getQueueJobs();
    expect(jobs).toHaveLength(1);
    expect(jobs[0].type).toBe('createBook');
    expect(jobs[0].payload.review).toBe('Magnifique');
    expect(jobs[0].payload.rating).toBe(5);
  });

  test('un tome lu est enregistré dans la file', () => {
    enqueueCreateSeries({
      series_name: 'Harry Potter',
      volumes: [{ volume_number: 1, is_read: false }],
    });
    const id = getQueueJobs()[0].clientId;
    enqueueToggleVolume(id, 1, true);
    expect(getQueueJobs()).toHaveLength(1);
    expect(getQueueJobs()[0].payload.volumes[0].is_read).toBe(true);
  });

  test('flush envoie les jobs puis vide la file', async () => {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    enqueueCreateBook({ title: 'Dune', author: 'Herbert' });
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'server-1', title: 'Dune' }),
    });
    const result = await flushOfflineQueue();
    expect(result.flushed).toBe(1);
    expect(result.remaining).toBe(0);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/books'),
      expect.objectContaining({ method: 'POST' })
    );
    const cached = loadLibraryCache({})?.books || [];
    expect(cached.some((b) => b.id === 'server-1')).toBe(true);
    expect(cached.some((b) => String(b.id).startsWith('offline_book_'))).toBe(false);
  });

  test('une mise à jour fusionne dans le POST de création, puis le cache prend l’id serveur', async () => {
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    const local = enqueueCreateBook({ title: 'Dune', author: 'Herbert' });
    enqueueUpdateBook(local.id, { status: 'completed' });
    expect(getPendingCount()).toBe(1);
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: 'server-1', title: 'Dune', status: 'completed' }),
    });
    const result = await flushOfflineQueue();
    expect(result.flushed).toBe(1);
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.status).toBe('completed');
    const cached = loadLibraryCache({})?.books || [];
    expect(cached.some((b) => b.id === 'server-1')).toBe(true);
  });

  test('mergePendingBooks réinjecte les ajouts dans une liste serveur', () => {
    enqueueCreateBook({ title: 'Nouveau', author: 'A' });
    const merged = mergePendingBooks([{ id: 'b1', title: 'Ancien' }]);
    expect(merged.map((b) => b.title).sort()).toEqual(['Ancien', 'Nouveau']);
  });

  test('shouldEnqueueWrite détecte l’absence de réseau', () => {
    expect(shouldEnqueueWrite()).toBe(true);
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
    expect(shouldEnqueueWrite()).toBe(false);
    expect(isNetworkFailure({ message: 'Network Error', code: 'ERR_NETWORK' })).toBe(true);
    expect(isNetworkFailure({ response: { status: 500 } })).toBe(false);
  });

  test('la file est stockée sous la clé attendue', () => {
    enqueueCreateBook({ title: 'X' });
    const raw = JSON.parse(localStorage.getItem(QUEUE_KEY));
    expect(raw.userId).toBe('u1');
    expect(raw.jobs).toHaveLength(1);
  });
});
