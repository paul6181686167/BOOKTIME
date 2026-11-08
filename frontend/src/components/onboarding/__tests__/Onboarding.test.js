import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';

import OnboardingLibraryPicker from '../OnboardingLibraryPicker';
import OnboardingGate from '../OnboardingGate';
import * as service from '../../../services/onboardingService';

expect.extend(toHaveNoViolations);

jest.mock('react-hot-toast', () => ({ toast: { success: jest.fn(), error: jest.fn() } }));
jest.mock('../../../services/onboardingService', () => ({
  fetchOnboardingWorks: jest.fn(),
  addOnboardingWorks: jest.fn(),
  serverLibraryIsEmpty: jest.fn(),
  isOnboardingDone: jest.fn(),
  markOnboardingDone: jest.fn(),
}));

const ROMANS = {
  genres: ['Classiques', 'Fantasy'],
  works: [
    { id: 'roman-le-petit-prince', title: 'Le Petit Prince', author: 'Antoine de Saint-Exupéry', genre: 'Classiques', category: 'roman', cover_url: '' },
    { id: 'roman-dune', title: 'Dune', author: 'Frank Herbert', genre: 'Fantasy', category: 'roman', cover_url: 'https://example.test/dune.jpg' },
  ],
};
const GRAPHIC = {
  genres: ['Shōnen'],
  works: [
    { id: 'graphic_novel-one-piece', title: 'One Piece', author: 'Eiichirō Oda', genre: 'Shōnen', category: 'manga', cover_url: '' },
  ],
};

beforeEach(() => {
  jest.clearAllMocks();
  service.fetchOnboardingWorks.mockImplementation(async (group) => (group === 'roman' ? ROMANS : GRAPHIC));
  service.addOnboardingWorks.mockResolvedValue({ added: 2, skipped: 0 });
});

describe('OnboardingLibraryPicker', () => {
  test('coche des oeuvres sur deux étapes puis les ajoute en une fois', async () => {
    const onFinish = jest.fn();
    render(<OnboardingLibraryPicker onFinish={onFinish} />);

    const dune = await screen.findByRole('button', { name: /Dune, Frank Herbert/ });
    expect(dune).toHaveAttribute('aria-pressed', 'false');
    userEvent.click(dune);
    expect(dune).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('1 œuvre sélectionnée')).toBeInTheDocument();

    userEvent.click(screen.getByRole('button', { name: /Suivant : Romans graphiques/ }));
    const onePiece = await screen.findByRole('button', { name: /One Piece, Eiichirō Oda/ });
    userEvent.click(onePiece);
    expect(screen.getByText(/2 œuvres sélectionnées/)).toBeInTheDocument();

    userEvent.click(screen.getByRole('button', { name: /Terminer \(2\)/ }));
    await waitFor(() => expect(onFinish).toHaveBeenCalledWith(2));
    expect(service.addOnboardingWorks).toHaveBeenCalledTimes(1);
    expect(service.addOnboardingWorks).toHaveBeenCalledWith(['roman-dune', 'graphic_novel-one-piece']);
  });

  test('le filtre par genre et la recherche restreignent la grille', async () => {
    render(<OnboardingLibraryPicker onFinish={jest.fn()} />);
    await screen.findByRole('button', { name: /Dune/ });

    userEvent.click(screen.getByRole('button', { name: 'Classiques' }));
    expect(screen.queryByRole('button', { name: /Dune/ })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Le Petit Prince/ })).toBeInTheDocument();

    userEvent.click(screen.getByRole('button', { name: 'Tous' }));
    userEvent.type(screen.getByRole('searchbox', { name: /Filtrer/ }), 'herbert');
    expect(screen.getByRole('button', { name: /Dune/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Le Petit Prince/ })).not.toBeInTheDocument();
  });

  test('« Ignorer » ne peut pas faire perdre une sélection et n\'ajoute rien', async () => {
    const onFinish = jest.fn();
    render(<OnboardingLibraryPicker onFinish={onFinish} />);
    const dune = await screen.findByRole('button', { name: /Dune/ });

    userEvent.click(dune);
    expect(screen.queryByRole('button', { name: /Ignorer/ })).not.toBeInTheDocument();
    userEvent.click(dune);

    userEvent.click(screen.getByRole('button', { name: /Ignorer et voir ma bibliothèque/ }));
    expect(onFinish).toHaveBeenCalledWith(0);
    expect(service.addOnboardingWorks).not.toHaveBeenCalled();
  });

  test('une erreur d\'ajout garde l\'écran ouvert et la sélection', async () => {
    const onFinish = jest.fn();
    service.addOnboardingWorks.mockRejectedValueOnce(new Error('boom'));
    render(<OnboardingLibraryPicker onFinish={onFinish} />);
    userEvent.click(await screen.findByRole('button', { name: /Dune/ }));
    userEvent.click(screen.getByRole('button', { name: /Suivant/ }));
    userEvent.click(await screen.findByRole('button', { name: /Terminer/ }));

    await waitFor(() => expect(service.addOnboardingWorks).toHaveBeenCalled());
    expect(onFinish).not.toHaveBeenCalled();
    expect(await screen.findByRole('button', { name: /Terminer \(1\)/ })).toBeEnabled();
  });

  test('aucune violation d\'accessibilité détectée', async () => {
    const { baseElement } = render(<OnboardingLibraryPicker onFinish={jest.fn()} />);
    await screen.findByRole('button', { name: /Dune/ });
    const dialog = within(baseElement).getByRole('dialog');
    expect(await axe(dialog)).toHaveNoViolations();
  });
});

describe('OnboardingGate', () => {
  test('ne montre rien si l\'accueil a déjà été fait', () => {
    service.isOnboardingDone.mockReturnValue(true);
    render(<OnboardingGate userKey="u1" libraryEmpty onDone={jest.fn()} />);
    expect(service.serverLibraryIsEmpty).not.toHaveBeenCalled();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  test('ne montre rien si la bibliothèque n\'est pas vide côté serveur', async () => {
    service.isOnboardingDone.mockReturnValue(false);
    service.serverLibraryIsEmpty.mockResolvedValue(false);
    render(<OnboardingGate userKey="u1" libraryEmpty onDone={jest.fn()} />);
    await waitFor(() => expect(service.serverLibraryIsEmpty).toHaveBeenCalled());
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  test('ne vérifie rien tant que la bibliothèque locale n\'est pas vide', () => {
    service.isOnboardingDone.mockReturnValue(false);
    render(<OnboardingGate userKey="u1" libraryEmpty={false} onDone={jest.fn()} />);
    expect(service.serverLibraryIsEmpty).not.toHaveBeenCalled();
  });

  test('affiche l\'accueil pour un compte vide, mémorise la fin et prévient le parent', async () => {
    const onDone = jest.fn();
    service.isOnboardingDone.mockReturnValue(false);
    service.serverLibraryIsEmpty.mockResolvedValue(true);
    render(<OnboardingGate userKey="u1" libraryEmpty onDone={onDone} />);

    userEvent.click(await screen.findByRole('button', { name: /Dune/ }));
    userEvent.click(screen.getByRole('button', { name: /Suivant/ }));
    userEvent.click(await screen.findByRole('button', { name: /Terminer/ }));

    await waitFor(() => expect(onDone).toHaveBeenCalledWith(2));
    expect(service.markOnboardingDone).toHaveBeenCalledWith('u1');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
