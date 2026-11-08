import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ProfileModal from '../ProfileModal';
import { bookService } from '../../../services/bookService';
import friendsService from '../../../services/friendsService';
import { __resetFriendsUnread } from '../../../hooks/useFriendsUnread';

jest.mock('react-hot-toast', () => {
  const toast = () => {};
  toast.success = () => {};
  toast.error = () => {};
  return { __esModule: true, toast, default: toast };
});
jest.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'u1', display_name: 'Alice', email: 'alice@example.com' },
    logout: jest.fn(),
  }),
}));
jest.mock('../../../contexts/ThemeContext', () => ({
  useTheme: () => ({ theme: 'light', setTheme: jest.fn() }),
}));
jest.mock('../ProfileIdentityCard', () => ({
  __esModule: true,
  default: () => <div data-testid="identity-card" />,
  UserAvatar: () => <span data-testid="avatar" />,
}));
jest.mock('../../friends/FriendsPanel', () => ({
  __esModule: true,
  default: ({ embedded }) => <div data-testid="friends-panel">{embedded ? 'intégré' : 'fenêtre'}</div>,
}));
jest.mock('../IsbnScannerModal', () => ({ __esModule: true, default: () => null }));

beforeEach(() => {
  localStorage.setItem('token', 't');
  jest.spyOn(bookService, 'getStats').mockResolvedValue({
    total_books: 4,
    completed_books: 2,
    completion_dates: {},
  });
  jest.spyOn(friendsService, 'unreadSummary').mockResolvedValue({
    unread_messages: 2,
    pending_requests: 1,
  });
});

afterEach(() => {
  jest.restoreAllMocks();
  __resetFriendsUnread();
  localStorage.clear();
});

const open = () => render(<ProfileModal isOpen onClose={jest.fn()} libraryBooks={[]} />);

describe('onglets du profil', () => {
  test("l'onglet Calendrier n'existe plus et Profil est le premier onglet", async () => {
    open();
    await waitFor(() => expect(bookService.getStats).toHaveBeenCalled());
    expect(screen.queryByRole('button', { name: /^Calendrier$/ })).not.toBeInTheDocument();
    const labels = screen
      .getAllByRole('button')
      .map((b) => b.textContent)
      .filter((t) => /^(Profil|Stats|Objectif|Auteurs suivis|Collections)/.test(t));
    expect(labels[0]).toMatch(/^Profil/);
    expect(labels).toHaveLength(5);
  });

  test('Profil affiche l\'identité et les amis ; la pastille compte les nouveautés', async () => {
    open();
    expect(screen.getByTestId('identity-card')).toBeInTheDocument();
    expect(screen.getByTestId('friends-panel')).toHaveTextContent('intégré');
    expect(screen.getByText('Amis et messages')).toBeInTheDocument();
    expect(await screen.findByLabelText('3 nouveautés dans les amis')).toBeInTheDocument();
  });

  test('Stats contient le calendrier de lecture, sans les amis', async () => {
    open();
    fireEvent.click(screen.getByRole('button', { name: /^Stats/ }));
    expect(await screen.findByText(/Calendrier · activité de lecture/)).toBeInTheDocument();
    expect(screen.getByText(/Terminez des livres pour voir/)).toBeInTheDocument();
    expect(screen.queryByTestId('friends-panel')).not.toBeInTheDocument();
    expect(screen.queryByTestId('identity-card')).not.toBeInTheDocument();
  });
});
