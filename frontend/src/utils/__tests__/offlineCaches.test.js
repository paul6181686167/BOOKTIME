import { clearUserCaches } from '../offlineCaches';

describe('clearUserCaches', () => {
  afterEach(() => { delete global.caches; localStorage.clear(); });

  test('efface les données de compte et les caches API, garde le shell', async () => {
    localStorage.setItem('booktime_offline_library_v1', '[]');
    localStorage.setItem('booktime_author_profile:camus', '{}');
    localStorage.setItem('booktime_theme', 'dark');
    const store = new Set(['booktime-v19-api', 'booktime-v19-detail', 'booktime-v19-shell']);
    global.caches = {
      keys: async () => [...store],
      delete: async (k) => store.delete(k),
    };
    await clearUserCaches();
    expect(localStorage.getItem('booktime_offline_library_v1')).toBeNull();
    expect(localStorage.getItem('booktime_author_profile:camus')).toBeNull();
    expect(localStorage.getItem('booktime_theme')).toBe('dark');
    expect([...store]).toEqual(['booktime-v19-shell']);
  });
});
