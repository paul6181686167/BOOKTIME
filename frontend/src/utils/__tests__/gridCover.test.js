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

  it('privilégie la couverture du tome 1, pas d’un tome ultérieur', () => {
    const item = {
      isSeriesCard: true,
      name: 'Série',
      cover_url: 'https://covers.openlibrary.org/b/id/999-M.jpg',
      books: [
        { volume_number: 2, cover_url: 'https://covers.openlibrary.org/b/id/222-M.jpg' },
        { volume_number: 1, cover_url: 'https://covers.openlibrary.org/b/id/111-M.jpg' },
      ],
    };
    expect(resolveCoverForGridItem(item)).toContain('/b/id/111-');
  });

  it('utilise volume_details[1] du catalogue curé', () => {
    const item = {
      isSeriesCard: true,
      name: 'Poudremages',
      volume_details: {
        1: { cover_url: 'https://covers.openlibrary.org/b/id/8402583-L.jpg' },
      },
    };
    expect(resolveCoverForGridItem(item)).toContain('8402583');
  });
});
