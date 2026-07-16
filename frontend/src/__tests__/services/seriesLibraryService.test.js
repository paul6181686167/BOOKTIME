import { generateVolumesList } from '../../services/seriesLibraryService';

describe('generateVolumesList', () => {
  it('priorise mergedLibraryVolumes pour une série Wikidata statique', () => {
    const v = generateVolumesList(
      {
        name: 'Test Saga',
        fromStaticWikidata: true,
        mergedLibraryVolumes: [
          { volume_number: 2, display_title: 'Deux', title: 'Two', work_qid: 'Q2' },
          { volume_number: 1, title: 'Un seul', work_qid: 'Q1' },
        ],
      },
      {}
    );
    expect(v.map((x) => x.volume_number)).toEqual([1, 2]);
    expect(v[0].volume_title).toBe('Un seul');
    expect(v[1].volume_title).toBe('Deux');
    expect(v[0].wikidata_work_qid).toBe('Q1');
    expect(v[1].wikidata_work_qid).toBe('Q2');
  });

  it('priorise mergedLibraryVolumes même sans flag Wikidata statique (ex. WD live)', () => {
    const v = generateVolumesList(
      {
        name: 'Saga OL',
        fromStaticWikidata: false,
        mergedLibraryVolumes: [
          { volume_number: 1, title: 'Vol fusionné', work_qid: null },
        ],
      },
      {}
    );
    expect(v).toHaveLength(1);
    expect(v[0].volume_title).toBe('Vol fusionné');
    expect(v[0].wikidata_work_qid).toBeUndefined();
  });

  it('génère des tomes génériques pour une série populaire hors référentiel', () => {
    const v = generateVolumesList(
      {
        name: 'Série hors référentiel XYZ',
        author: 'Auteur Test',
        authors: ['Auteur Test'],
        category: 'roman',
        total_volumes: 3,
        volumes: 3,
      },
      {}
    );
    expect(v).toHaveLength(3);
    expect(v[0].volume_number).toBe(1);
    expect(v[0].volume_title).toContain('XYZ');
  });
});
