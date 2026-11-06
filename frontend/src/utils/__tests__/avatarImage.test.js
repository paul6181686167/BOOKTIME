import { avatarInitials } from '../avatarImage';

describe('initiales de la photo de profil', () => {
  it('utilise le nom affiché quand il existe', () => {
    expect(avatarInitials({ display_name: 'Paul Berruyer', email: 'x@y.fr' })).toBe('PB');
    expect(avatarInitials({ display_name: 'paul', email: 'x@y.fr' })).toBe('PA');
    expect(avatarInitials({ display_name: '  Jean   Pierre   Dupont ' })).toBe('JD');
  });

  it('retombe sur le début de l’email, puis sur un point d’interrogation', () => {
    expect(avatarInitials({ email: 'lecteur@mail.fr' })).toBe('LE');
    expect(avatarInitials({})).toBe('?');
    expect(avatarInitials(null)).toBe('?');
  });
});
