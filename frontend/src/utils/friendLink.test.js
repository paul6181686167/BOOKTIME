import {
  buildFriendLink,
  formatFriendCode,
  normalizeFriendCode,
  parseFriendCode,
} from './friendLink';

describe('friendLink', () => {
  test('normalise et valide un code', () => {
    expect(normalizeFriendCode('abcd-2345')).toBe('ABCD2345');
    expect(normalizeFriendCode('ABCD2340')).toBe('');
    expect(normalizeFriendCode('')).toBe('');
  });

  test('construit et formate le lien', () => {
    expect(buildFriendLink('abcd2345')).toMatch(/\/ami\/ABCD2345$/);
    expect(formatFriendCode('abcd2345')).toBe('ABCD-2345');
    expect(formatFriendCode('nope')).toBe('');
  });

  test('retrouve le code dans un lien, une requête ou un code seul', () => {
    expect(parseFriendCode('https://booktime-fawn.vercel.app/ami/abcd2345')).toBe('ABCD2345');
    expect(parseFriendCode('https://autre.site/ami/ABCD-2345?x=1')).toBe('ABCD2345');
    expect(parseFriendCode('https://x.fr/?ami=abcd2345')).toBe('ABCD2345');
    expect(parseFriendCode('  abcd 2345 ')).toBe('ABCD2345');
    expect(parseFriendCode('https://x.fr/livre/12')).toBe('');
    expect(parseFriendCode(null)).toBe('');
  });
});
