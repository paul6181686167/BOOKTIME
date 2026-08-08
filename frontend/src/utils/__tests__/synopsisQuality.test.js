import { displaySynopsis, isUsableSynopsis, sanitizeSynopsis } from '../synopsisQuality';

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

  test('strips Also contained in markdown junk', () => {
    const raw = `
A Clockwork Orange is a dystopian novel by Anthony Burgess, published in 1962.

Also contained in:
[A Clockwork Orange and Honey for the Bears](https://openlibrary.org/works/OL23787405W)
[A Clockwork Orange / The Wanting Seed](https://openlibrary.org/works/OL17306508W)
`;
    const cleaned = sanitizeSynopsis(raw);
    expect(cleaned).toMatch(/dystopian novel/i);
    expect(cleaned).not.toMatch(/Also contained/i);
    expect(cleaned).not.toMatch(/openlibrary\.org/i);
    expect(cleaned).not.toMatch(/\]\(/);
    expect(isUsableSynopsis(raw)).toBe(true);
    expect(displaySynopsis(raw)).toMatch(/dystopian novel/i);
  });
});
