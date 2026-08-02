import { isUsableSynopsis } from '../synopsisQuality';

describe('isUsableSynopsis', () => {
  test('rejects Wikidata / series counters', () => {
    expect(isUsableSynopsis('Wikidata · 0 œuvre(s) · pop. —/100')).toBe(false);
    expect(isUsableSynopsis('Série de 7 tome(s) de Ray Bradbury')).toBe(false);
    expect(isUsableSynopsis('Série roman populaire.')).toBe(false);
  });

  test('accepts a real blurb', () => {
    expect(
      isUsableSynopsis(
        "Dans une Amérique futuriste, les pompiers brûlent les livres. Guy Montag commence à douter."
      )
    ).toBe(true);
  });
});
