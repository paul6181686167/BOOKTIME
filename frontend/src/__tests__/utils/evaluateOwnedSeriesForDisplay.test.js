import {
  evaluateOwnedSeriesForDisplay,
  countDistinctOwnedVolumes,
} from '../../utils/seriesAttribution';

describe('evaluateOwnedSeriesForDisplay', () => {
  it('garde Le Seigneur des Anneaux comme série même avec 1 tome stocké', () => {
    const v = evaluateOwnedSeriesForDisplay({
      series_name: 'Le Seigneur des Anneaux',
      total_volumes: 1,
      volumes: [{ volume_number: 1, volume_title: 'Le Seigneur des Anneaux - Tome 1' }],
    });
    expect(v.demote).toBe(false);
    expect(v.totalBooks).toBe(3);
  });

  it('garde Time Riders comme série (référentiel curé)', () => {
    const v = evaluateOwnedSeriesForDisplay({
      series_name: 'time rider',
      total_volumes: 1,
      volumes: [{ volume_number: 1, volume_title: 'time rider - Tome 1' }],
    });
    expect(v.demote).toBe(false);
    expect(v.totalBooks).toBe(9);
  });

  it('rétrograde Un long dimanche (doublons du même livre) en livre', () => {
    const volumes = Array.from({ length: 11 }, () => ({
      volume_number: 1,
      volume_title: 'Un long dimanche de fiançailles',
    }));
    const v = evaluateOwnedSeriesForDisplay({
      series_name: 'un long dimanche de fiançaille',
      total_volumes: 11,
      volumes,
    });
    expect(v.demote).toBe(true);
    expect(countDistinctOwnedVolumes(volumes)).toBe(1);
  });

  it('rétrograde Long Dimanche malgré variantes de/des et CD audio', () => {
    const volumes = [
      { volume_number: 1, volume_title: 'Un long dimanche de fiançailles' },
      { volume_number: 1, volume_title: 'Un Long Dimanche des Fiancailles' },
      { volume_number: 1, volume_title: 'Un Long Dimanche des Fiancailles (Three audio compact discs)' },
      { volume_number: 1, volume_title: 'Un long dimanche de fiancailles' },
    ];
    const v = evaluateOwnedSeriesForDisplay({
      series_name: 'un long dimanche de fiançaille',
      total_volumes: 4,
      volumes,
    });
    expect(countDistinctOwnedVolumes(volumes)).toBe(1);
    expect(v.demote).toBe(true);
  });
});
