import {
  readUpcomingLocalCache,
  writeUpcomingLocalCache,
} from '../upcomingService';

describe('cache local À venir', () => {
  beforeEach(() => localStorage.clear());

  test('écrit et relit les groupes', () => {
    writeUpcomingLocalCache({
      groups: { this_week: [{ id: '1', title: 'Tome 12' }] },
      suggestions: [],
      counts: { total: 1 },
    });
    const cached = readUpcomingLocalCache();
    expect(cached.groups.this_week[0].title).toBe('Tome 12');
    expect(cached.counts.total).toBe(1);
  });

  test('ignore un payload en erreur', () => {
    writeUpcomingLocalCache({ error: true, groups: { this_week: [] } });
    expect(readUpcomingLocalCache()).toBeNull();
  });
});
