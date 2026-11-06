import { coverFallbackCandidates, resolveCoverForGridItem } from '../helpers';

describe('couvertures de cartes série', () => {
  it('ne plante pas quand volumes est un nombre (série détectée par la recherche)', () => {
    const item = { isSeriesCard: true, name: 'Harry Potter', volumes: 3 };
    expect(() => resolveCoverForGridItem(item)).not.toThrow();
    expect(resolveCoverForGridItem(item)).toBeNull();
    expect(() => coverFallbackCandidates(item)).not.toThrow();
  });

  it('utilise la couverture d’un tome quand books est une liste', () => {
    const item = {
      isSeriesCard: true,
      name: 'Série',
      books: [{ cover_url: 'https://covers.openlibrary.org/b/id/123-M.jpg' }],
    };
    expect(resolveCoverForGridItem(item)).toContain('/b/id/123-');
  });
});
