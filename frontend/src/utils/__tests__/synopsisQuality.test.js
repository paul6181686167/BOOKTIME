import {
  displaySynopsis,
  isUsableSynopsis,
  looksEnglish,
  looksFrench,
  preferFrenchSynopsis,
  sanitizeSynopsis,
} from '../synopsisQuality';

describe('isUsableSynopsis', () => {
  test('rejects Wikidata / series counters', () => {
    expect(isUsableSynopsis('Wikidata · 0 œuvre(s) · pop. —/100')).toBe(false);
    expect(isUsableSynopsis('Série de 7 tome(s) de Ray Bradbury')).toBe(false);
    expect(isUsableSynopsis('Série roman populaire.')).toBe(false);
  });

  test('rejects a song page that shares the book title', () => {
    const song =
      "For Whom The Bell Tolls (« Pour qui sonne le glas » en français) est la troisième piste de l'album Ride the Lightning du groupe Metallica. Elle est également disponible sur les albums live du groupe.";
    expect(isUsableSynopsis(song)).toBe(false);
  });

  test('keeps a novel that was adapted to film', () => {
    const novel =
      "Pour qui sonne le glas est un roman d'Ernest Hemingway publié en 1940, pendant la guerre d'Espagne. Il a ensuite été adapté au cinéma.";
    expect(isUsableSynopsis(novel)).toBe(true);
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

describe('preferFrenchSynopsis', () => {
  test('prefers French over English', () => {
    const en =
      'The War of the Worlds is a science fiction novel by H. G. Wells that was first published in 1898.';
    const fr =
      "La Guerre des mondes est un roman de science-fiction de H. G. Wells publié en 1898, qui a marqué l'histoire du genre.";
    expect(looksFrench(fr)).toBe(true);
    expect(looksEnglish(en)).toBe(true);
    expect(preferFrenchSynopsis(en, fr)).toBe(sanitizeSynopsis(fr));
  });

  test('rejectEnglish hides English-only blurbs', () => {
    const en =
      'The War of the Worlds is a science fiction novel by H. G. Wells that was first published in 1898.';
    expect(preferFrenchSynopsis(en, { rejectEnglish: true })).toBe('');
  });

  test('rejects Spanish stored as if it were French', () => {
    const es =
      'Ryland Grace es el único superviviente en una misión desesperada. Es la última oportunidad y, si fracasa, la humanidad y la Tierra misma perecerán. Proyecto Hail Mary es una emocionante novela de ciencia ficción escrita por Andy Weir (autor de El marciano). La historia sigue a Ryland Grace, un hombre que despierta solo en una nave espacial sin recordar quién es ni por qué está allí.';
    expect(looksFrench(es)).toBe(false);
    expect(preferFrenchSynopsis(es, { rejectEnglish: true })).toBe('');
  });

  test('rejects mixed Spanish+English+French Hail Mary dump', () => {
    const mixed =
      "Ryland Grace es el único superviviente en una misión desesperada. Es la última oportunidad y, si fracasa, la humanidad y la Tierra misma perecerán. Proyecto Hail Mary es una emocionante novela de ciencia ficción escrita por Andy Weir (autor de El marciano). La historia sigue a Ryland Grace, un hombre que despierta solo en una nave espacial sin recordar quién es ni por qué está allí.\n\nA medida que recupera la memoria, descubre que es la última esperanza de la humanidad para evitar una catástrofe a escala planetaria. Con ingenio, Grace deberá enfrentarse a lo desconocido en una misión desesperada y sorprendente.\n\nENGLISH DESCRIPTION THE #1 NEW YORK TIMES BEST-SELLER FROM THE AUTHOR OF THE MARTIAN - A lone astronaut must save the earth from disaster. He has two problems: he can't remember his own name, and he is not alone.\n\ns parler de la nature de sa mission ou de la façon de la terminer. Tout ce qu'il sait, c'est qu'il dort depuis très, très longtemps. Et il vient d'être réveillé pour se retrouver à des millions de kilomètres de chez lui.";
    expect(looksFrench(mixed)).toBe(false);
    expect(preferFrenchSynopsis(mixed, { rejectEnglish: true })).toBe('');
  });
});

describe('sanitizeSynopsis encoding', () => {
  test('repairs replacement characters and doubled apostrophes', () => {
    const raw = "langue fran\uFFFDaise d''Antoine de Saint-Exupéry";
    const cleaned = sanitizeSynopsis(raw);
    expect(cleaned).toMatch(/française/);
    expect(cleaned).toContain("d'Antoine");
    expect(cleaned).not.toContain("d''");
  });
});
