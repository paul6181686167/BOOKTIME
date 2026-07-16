import { buildMergedLibraryVolumeRowsFromOlBooks } from '../../utils/openLibraryBookDisplay';

describe('buildMergedLibraryVolumeRowsFromOlBooks', () => {
  it('retourne null si aucun livre', () => {
    expect(buildMergedLibraryVolumeRowsFromOlBooks([])).toBeNull();
    expect(buildMergedLibraryVolumeRowsFromOlBooks(null)).toBeNull();
  });

  it('regroupe par tome et expose display_title', () => {
    const rows = buildMergedLibraryVolumeRowsFromOlBooks([
      { title: 'Saga T1', volume_number: 1, cover_url: 'https://a.jpg' },
      { title: 'Saga T1 alt', volume_number: 1, cover_url: '' },
    ]);
    expect(rows).toHaveLength(1);
    expect(rows[0].volume_number).toBe(1);
    expect(rows[0].merged_sources).toEqual(['openlibrary']);
  });
});
