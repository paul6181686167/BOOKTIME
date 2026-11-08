import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { clickableProps } from '../utils/a11y';
import LoginPage from '../components/user/LoginPage';
import ModalOverlay from '../components/common/ModalOverlay';
import BookGrid from '../components/books/BookGrid';

expect.extend(toHaveNoViolations);

jest.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ login: jest.fn(), register: jest.fn() }),
}));
jest.mock('../utils/backendWake', () => ({
  wakeBackend: () => Promise.resolve({ ok: true }),
  isBackendRemote: () => false,
  WAKE_HINT_DELAY_MS: 2800,
}));
jest.mock('react-hot-toast', () => ({
  toast: Object.assign(jest.fn(), {
    success: jest.fn(),
    error: jest.fn(),
    loading: jest.fn(),
    dismiss: jest.fn(),
  }),
}));
jest.mock('../hooks/useCollectionColors', () => () => ({}));

describe('clickableProps', () => {
  it('rend un élément activable au clavier (Entrée et Espace)', () => {
    const onActivate = jest.fn();
    render(<div {...clickableProps(onActivate, 'Ouvrir Dune')}>Dune</div>);
    const el = screen.getByRole('button', { name: 'Ouvrir Dune' });
    expect(el).toHaveAttribute('tabindex', '0');
    fireEvent.keyDown(el, { key: 'Enter' });
    fireEvent.keyDown(el, { key: ' ' });
    fireEvent.keyDown(el, { key: 'a' });
    expect(onActivate).toHaveBeenCalledTimes(2);
  });

  it("ignore les touches venant d'un bouton imbriqué", () => {
    const onActivate = jest.fn();
    render(
      <div {...clickableProps(onActivate, 'Carte')}>
        <button type="button" aria-label="Retirer">
          x
        </button>
      </div>
    );
    fireEvent.keyDown(screen.getByRole('button', { name: 'Retirer' }), { key: 'Enter' });
    expect(onActivate).not.toHaveBeenCalled();
  });
});

describe('accessibilité (axe)', () => {
  it('la page de connexion n a aucune violation et ses champs sont nommés', async () => {
    const { container } = render(<LoginPage />);
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Mot de passe')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'BookTime' })).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it('le mot de passe peut être affiché puis masqué', () => {
    render(<LoginPage />);
    const input = screen.getByLabelText('Mot de passe');
    expect(input).toHaveAttribute('type', 'password');
    fireEvent.click(screen.getByRole('button', { name: 'Afficher le mot de passe' }));
    expect(input).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: 'Masquer le mot de passe' }));
    expect(input).toHaveAttribute('type', 'password');
  });

  it('les fenêtres modales n ont aucune violation', async () => {
    render(
      <ModalOverlay onClose={() => {}} ariaLabel="Exemple">
        <h2>Titre</h2>
        <button type="button">Fermer</button>
      </ModalOverlay>
    );
    expect(await axe(document.body)).toHaveNoViolations();
  });

  it('la grille de livres est utilisable au clavier', async () => {
    const onItemClick = jest.fn();
    const books = [
      { id: '1', title: 'Dune', author: 'Frank Herbert', category: 'roman', status: 'to_read' },
    ];
    const { container } = render(<BookGrid books={books} onBookClick={onItemClick} onItemClick={onItemClick} />);
    const card = screen.getByRole('button', { name: /Dune/ });
    card.focus();
    expect(card).toHaveFocus();
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(onItemClick).toHaveBeenCalled();
    expect(await axe(container, { rules: { 'color-contrast': { enabled: false } } })).toHaveNoViolations();
  });
});
