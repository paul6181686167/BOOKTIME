import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { buildTermsSections, getLegalConfig, TERMS_VERSION } from '../../../legal/terms';
import TermsContent from '../TermsContent';
import LoginPage from '../../user/LoginPage';

const mockRegister = jest.fn();
const mockLogin = jest.fn();

jest.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({ login: mockLogin, register: mockRegister }),
}));
jest.mock('../../../utils/backendWake', () => ({
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

describe('contenu des CGU', () => {
  test('couvre les sujets attendus', () => {
    const ids = buildTermsSections().map((s) => s.id);
    expect(ids).toEqual(
      expect.arrayContaining(['objet', 'compte', 'donnees', 'contenus', 'regles', 'moderation', 'responsabilite', 'droit'])
    );
    expect(TERMS_VERSION).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  test("n'invente ni éditeur ni adresse de contact", () => {
    const text = JSON.stringify(buildTermsSections());
    expect(text).not.toMatch(/@/);
    expect(getLegalConfig({})).toEqual({ editor: '', contactEmail: '' });
  });

  test("affiche l'éditeur et le contact quand ils sont configurés", () => {
    const text = JSON.stringify(buildTermsSections({ editor: 'Jeanne Martin', contactEmail: 'contact@booktime.test' }));
    expect(text).toContain('Jeanne Martin');
    expect(text).toContain('contact@booktime.test');
  });

  test('le composant rend les titres de section', () => {
    render(<TermsContent config={{ editor: '', contactEmail: '' }} />);
    expect(screen.getByRole('heading', { name: '4. Données personnelles' })).toBeInTheDocument();
  });
});

describe("inscription et acceptation des CGU", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockRegister.mockResolvedValue({ success: false, error: 'stop' });
  });

  const goToSignup = () => {
    render(<LoginPage />);
    fireEvent.click(screen.getByRole('tab', { name: 'Inscription' }));
    fireEvent.change(screen.getByPlaceholderText('vous@exemple.com'), { target: { value: 'a@b.fr' } });
    fireEvent.change(screen.getByPlaceholderText('Minimum 8 caractères'), { target: { value: 'secret123' } });
  };

  test('le bouton reste bloqué tant que les CGU ne sont pas acceptées', () => {
    goToSignup();
    expect(screen.getByRole('button', { name: 'Créer un compte' })).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(screen.getByRole('button', { name: 'Créer un compte' })).toBeEnabled();
  });

  test("l'acceptation est transmise à l'inscription", async () => {
    goToSignup();
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.click(screen.getByRole('button', { name: 'Créer un compte' }));
    await waitFor(() => expect(mockRegister).toHaveBeenCalledWith('a@b.fr', 'secret123', true));
  });

  test('lire les CGU puis accepter coche la case', () => {
    goToSignup();
    fireEvent.click(screen.getByRole('button', { name: "conditions générales d'utilisation" }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: "J'accepte" }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeChecked();
  });
});
