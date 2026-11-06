import {
  displayBookTitleFrFirst,
  pickFrenchEditionTitle,
  sanitizeBookTitle,
  titleNeedsFrenchLookup,
} from '../openLibraryBookDisplay';

describe('sanitizeBookTitle', () => {
  test('restores Q.I. from Cui corruption', () => {
    expect(sanitizeBookTitle('Juliette a-t-elle un grand Cui?')).toBe(
      'Juliette a-t-elle un grand Q.I.?'
    );
  });

  test('normalizes QI variants', () => {
    expect(sanitizeBookTitle('Un grand QI')).toBe('Un grand Q.I.');
    expect(sanitizeBookTitle('Un grand Q. I.')).toBe('Un grand Q.I.');
  });

  test('displayBookTitleFrFirst applies sanitize', () => {
    expect(
      displayBookTitleFrFirst({ title: 'Juliette a-t-elle un grand Cui?' })
    ).toBe('Juliette a-t-elle un grand Q.I.?');
  });

  test('displayBookTitleFrFirst traduit les titres anglais des recommandations', () => {
    expect(displayBookTitleFrFirst({ title: 'The Lightning Thief' })).toBe('Le Voleur de foudre');
    expect(displayBookTitleFrFirst({ display_title: 'The Lightning Thief' })).toBe('Le Voleur de foudre');
    expect(displayBookTitleFrFirst({ title: 'For Whom the Bell Tolls' })).toBe('Pour qui sonne le glas');
    expect(displayBookTitleFrFirst({ title: 'The Sun Also Rises' })).toBe('Le soleil se lève aussi');
    expect(displayBookTitleFrFirst({ title: 'A Farewell to Arms' })).toBe("L'Adieu aux armes");
    expect(displayBookTitleFrFirst({ title: 'The Lost Hero' })).toBe('Le Héros perdu');
    expect(displayBookTitleFrFirst({
      title: 'The Complete Short Stories of Ernest Hemingway: The Finca Vigía Edition',
    })).toBe("Nouvelles complètes d'Ernest Hemingway");
  });

  test('titleNeedsFrenchLookup ignore un titre déjà français ou un nom propre', () => {
    expect(titleNeedsFrenchLookup('Le Voleur de foudre')).toBe(false);
    expect(titleNeedsFrenchLookup('Percy Jackson')).toBe(false);
    expect(titleNeedsFrenchLookup('The Sun Also Rises')).toBe(true);
  });

  test('pickFrenchEditionTitle préfère le titre français', () => {
    expect(pickFrenchEditionTitle(
      ['Percy Jackson - Tome 1', 'Le voleur de foudre'],
      'The Lightning Thief'
    )).toBe('Le voleur de foudre');
    expect(pickFrenchEditionTitle(
      ["L' adieu aux armes."],
      'A Farewell to Arms'
    )).toBe("L'adieu aux armes");
    expect(pickFrenchEditionTitle(['Pour qui sonne le glas'], 'For Whom the Bell Tolls'))
      .toBe('Pour qui sonne le glas');
  });
});
