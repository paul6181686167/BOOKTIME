import { displayBookTitleFrFirst, sanitizeBookTitle } from '../openLibraryBookDisplay';

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
});
