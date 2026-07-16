import {
  mergeVolumeDisplay,
  mergeStaticWdWorksWithOpenLibrary,
  normalizeTitleKey,
  enrichVolumeRowWithGoogleBooks,
  enrichVolumeRowsLimitedGoogleBooksByIsbn,
  enrichVolumeRowsLimitedGoogleBooksByIntitle,
  enrichVolumeRowsGoogleBooksIsbnThenIntitle,
  mapMergedVolumeRowsToLibraryVolumes,
  mapLiveWikidataVolumesToWorks,
} from '../../utils/sourceMerge';

describe('normalizeTitleKey', () => {
  it('normalise accents et ponctuation', () => {
    expect(normalizeTitleKey('L’Étranger')).toBe('l etranger');
  });
});

describe('mergeVolumeDisplay', () => {
  it('priorise le titre Wikidata sur Open Library', () => {
    const out = mergeVolumeDisplay({
      wdWork: { title_fr: 'Titre FR', title_en: 'Title EN', volume: 2 },
      olBook: { title: 'Different OL Title', volume_number: 2 },
    });
    expect(out.title).toBe('Titre FR');
    expect(out.volume_number).toBe(2);
    expect(out.merged_sources).toEqual(['wikidata', 'openlibrary']);
  });

  it('complète la couverture depuis Open Library si absente côté WD', () => {
    const out = mergeVolumeDisplay({
      wdWork: { title_fr: 'Solo', volume: 1 },
      olBook: { title: 'Solo', cover_url: 'https://covers.openlibrary.org/b/id/1-L.jpg', volume_number: 1 },
    });
    expect(out.cover_url).toBe('https://covers.openlibrary.org/b/id/1-L.jpg');
  });

  it('sans Wikidata, retombe sur Open Library puis Google Books (titre)', () => {
    const out = mergeVolumeDisplay({
      olBook: null,
      gbItem: { title: 'GB Only', published_date: '2010-05-01' },
    });
    expect(out.title).toBe('GB Only');
    expect(out.first_publish_year).toBe(2010);
    expect(out.merged_sources).toEqual(['google_books']);
  });
});

describe('mergeStaticWdWorksWithOpenLibrary', () => {
  it('apparie par numéro de tome et garde le titre WD', () => {
    const works = [
      { work_qid: 'Q1', title_fr: 'Tome WD 3', title_en: 'Vol 3', volume: '3' },
    ];
    const olBooks = [
      { title: 'Random OL', volume_number: 3, cover_url: 'https://example.com/c.jpg', ol_key: '/works/OL1' },
    ];
    const merged = mergeStaticWdWorksWithOpenLibrary(works, olBooks);
    expect(merged).toHaveLength(1);
    expect(merged[0].title).toBe('Tome WD 3');
    expect(merged[0].cover_url).toBe('https://example.com/c.jpg');
    expect(merged[0].ol_key).toBe('/works/OL1');
    expect(merged[0].work_qid).toBe('Q1');
  });

  it('ajoute les livres OL non appariés en fin de liste', () => {
    const works = [{ work_qid: 'Q1', title_fr: 'Alpha', volume: '1' }];
    const olBooks = [
      { title: 'Alpha OL', volume_number: 1 },
      { title: 'Bonus volume 5', volume_number: 5, ol_key: '/works/bonus' },
    ];
    const merged = mergeStaticWdWorksWithOpenLibrary(works, olBooks);
    expect(merged.map((m) => m.volume_number)).toEqual([1, 5]);
    expect(merged[1].title).toBe('Bonus volume 5');
    expect(merged[1].work_qid).toBeNull();
  });

  it('sans œuvres WD, retourne une entrée par livre OL', () => {
    const olBooks = [{ title: 'Seul OL', volume_number: 2 }];
    const merged = mergeStaticWdWorksWithOpenLibrary([], olBooks);
    expect(merged).toHaveLength(1);
    expect(merged[0].title).toBe('Seul OL');
    expect(merged[0].volume_number).toBe(2);
  });
});

describe('enrichVolumeRowWithGoogleBooks', () => {
  it('remplit la couverture sans écraser le titre', () => {
    const base = {
      title: 'Titre WD',
      volume_number: 1,
      cover_url: '',
      first_publish_year: 2020,
      isbn: '9781234567897',
      merged_sources: ['wikidata', 'openlibrary'],
    };
    const gb = {
      google_books_id: 'abc',
      title: 'Wrong title',
      thumbnail: 'http://books.google.com/books/thumb.jpg',
      published_date: '2019',
    };
    const out = enrichVolumeRowWithGoogleBooks(base, gb);
    expect(out.title).toBe('Titre WD');
    expect(out.cover_url).toBe('https://books.google.com/books/thumb.jpg');
    expect(out.google_books_id).toBe('abc');
    expect(out.merged_sources).toContain('google_books');
  });

  it('ne remplace pas une couverture déjà présente', () => {
    const base = {
      title: 'X',
      cover_url: 'https://existing/cover.jpg',
      first_publish_year: null,
      isbn: '9780000000000',
      merged_sources: ['wikidata'],
    };
    const out = enrichVolumeRowWithGoogleBooks(base, {
      thumbnail: 'https://gb/other.jpg',
      published_date: '2021-01',
    });
    expect(out.cover_url).toBe('https://existing/cover.jpg');
    expect(out.first_publish_year).toBe(2021);
  });
});

describe('enrichVolumeRowsLimitedGoogleBooksByIsbn', () => {
  it('respecte maxLookups et ignore les lignes déjà complètes', async () => {
    const rows = [
      { title: 'A', isbn: '9781111111111', cover_url: '', first_publish_year: null, merged_sources: [] },
      { title: 'B', isbn: '9782222222222', cover_url: '', first_publish_year: null, merged_sources: [] },
      { title: 'C', isbn: '9783333333333', cover_url: 'x', first_publish_year: 2000, merged_sources: [] },
    ];
    let calls = 0;
    const fetchBook = jest.fn(async () => {
      calls += 1;
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              google_books_id: `id${calls}`,
              thumbnail: `https://t${calls}.jpg`,
              published_date: '2005',
            },
          ],
        }),
      };
    });
    const out = await enrichVolumeRowsLimitedGoogleBooksByIsbn(rows, { fetchBook, maxLookups: 1 });
    expect(fetchBook).toHaveBeenCalledTimes(1);
    expect(out[0].cover_url).toMatch(/^https:\/\/t1/);
    expect(out[1].cover_url).toBe('');
    expect(out[2].cover_url).toBe('x');
  });
});

describe('enrichVolumeRowsLimitedGoogleBooksByIntitle', () => {
  it('sans auteur exploitable, ne fait aucun appel', async () => {
    const fetchBook = jest.fn();
    await enrichVolumeRowsLimitedGoogleBooksByIntitle(
      [{ title: 'X', cover_url: '' }],
      { fetchBook, authorName: '   ', maxLookups: 3 }
    );
    expect(fetchBook).not.toHaveBeenCalled();
  });

  it('ignore les lignes avec ISBN 13 et complète via intitle', async () => {
    const fetchBook = jest.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [
          {
            google_books_id: 'g1',
            thumbnail: 'https://t1.jpg',
            published_date: '2008',
          },
        ],
      }),
    }));
    const out = await enrichVolumeRowsLimitedGoogleBooksByIntitle(
      [
        { title: 'Avec Isbn', isbn: '9780000000000', cover_url: '', first_publish_year: null },
        { title: 'Sans Isbn Long', cover_url: '', first_publish_year: null },
      ],
      { fetchBook, authorName: 'Victor Hugo', maxLookups: 3 }
    );
    expect(fetchBook).toHaveBeenCalledTimes(1);
    expect(out[0].google_books_id).toBeUndefined();
    expect(out[1].cover_url).toMatch(/^https:\/\/t1/);
    expect(out[1].google_books_id).toBe('g1');
  });
});

describe('enrichVolumeRowsGoogleBooksIsbnThenIntitle', () => {
  it('enchaîne ISBN puis intitle', async () => {
    const fetchBook = jest.fn(async (path) => {
      if (path.includes('/isbn/')) {
        return { ok: false, json: async () => ({ items: [] }) };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              google_books_id: 'g2',
              thumbnail: 'https://t2.jpg',
              published_date: '1999',
            },
          ],
        }),
      };
    });
    const out = await enrichVolumeRowsGoogleBooksIsbnThenIntitle(
      [
        { title: 'R1', isbn: '9781111111111', cover_url: '', first_publish_year: null },
        { title: 'R2 sans isbn assez long', cover_url: '', first_publish_year: null },
      ],
      { fetchBook, authorName: 'Paul Auster', maxIsbn: 1, maxIntitle: 1 }
    );
    expect(fetchBook.mock.calls.map((c) => c[0]).some((p) => p.includes('/isbn/'))).toBe(true);
    expect(fetchBook.mock.calls.map((c) => c[0]).some((p) => p.includes('volumes?q'))).toBe(true);
    expect(out[0].cover_url).toBe('');
    expect(out[1].cover_url).toMatch(/^https:\/\/t2/);
  });
});

describe('mapLiveWikidataVolumesToWorks', () => {
  it('mappe titre, tome, année et ISBN pour la fusion', () => {
    const w = mapLiveWikidataVolumesToWorks([
      { title: 'Tome A', volume_number: 1, publication_year: 2020, isbn: '978-1-234-56789-7' },
    ]);
    expect(w[0].title_fr).toBe('Tome A');
    expect(w[0].volume).toBe('1');
    expect(w[0].publication_date).toBe('2020-01-01');
    expect(w[0].isbns[0]).toBe('9781234567897');
  });

  it('fusionne WD live + OL comme le WD statique', () => {
    const merged = mergeStaticWdWorksWithOpenLibrary(
      mapLiveWikidataVolumesToWorks([
        { title: 'Titre WD vol 2', volume_number: 2, publication_year: 2011 },
      ]),
      [{ title: 'OL deux', volume_number: 2, cover_url: 'https://covers.example/2.jpg', ol_key: '/w/2' }]
    );
    expect(merged).toHaveLength(1);
    expect(merged[0].title).toBe('Titre WD vol 2');
    expect(merged[0].cover_url).toBe('https://covers.example/2.jpg');
    expect(merged[0].ol_key).toBe('/w/2');
    expect(merged[0].first_publish_year).toBe(2011);
  });
});

describe('mapMergedVolumeRowsToLibraryVolumes', () => {
  it('ordonne par tome et utilise display_title', () => {
    const v = mapMergedVolumeRowsToLibraryVolumes('Ma série', [
      { volume_number: 3, display_title: 'Trois', title: 'Three', work_qid: 'Q3' },
      { volume_number: 1, title: 'Premier', work_qid: 'Q1' },
    ]);
    expect(v.map((x) => x.volume_number)).toEqual([1, 3]);
    expect(v[0].volume_title).toBe('Premier');
    expect(v[1].volume_title).toBe('Trois');
    expect(v[0].wikidata_work_qid).toBe('Q1');
  });
});
