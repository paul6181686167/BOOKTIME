import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import AdminPage, { timeAgo } from '../AdminPage';
import adminService, { AdminError } from '../../services/adminService';

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: { success: jest.fn(), error: jest.fn() },
}));
jest.mock('../../services/adminService', () => {
  class AdminError extends Error {
    constructor(message, status) {
      super(message);
      this.status = status;
    }
  }
  return {
    __esModule: true,
    AdminError,
    default: { getStats: jest.fn(), listUsers: jest.fn(), banUser: jest.fn(), unbanUser: jest.fn() },
  };
});

const days = Array.from({ length: 14 }, (_, i) => ({ date: `2026-11-${String(i + 1).padStart(2, '0')}`, count: i % 3 }));
const STATS = {
  users: { total: 1234, banned: 2, online: 7, active_24h: 40, new_today: 3, new_7d: 20, signups_per_day: days },
  books: {
    total: 5678, completed: 100, reading: 50, to_read: 30, added_today: 12, added_7d: 80,
    by_category: { roman: 1, bd: 2, manga: 3, autre: 4 }, added_per_day: days, series_in_libraries: 9,
  },
  engagement: {
    reviews: 11, ratings: 22, favorites: 33, messages: 44, messages_24h: 5,
    book_recommendations: 6, friendships: 7, friend_requests_pending: 8,
  },
};
const USER = {
  id: 'u1', email: 'alice@mail.fr', display_name: 'Alice', online: true, banned: false,
  books_count: 2, reviews_count: 1, last_seen: null, is_admin: false,
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <AdminPage />
    </MemoryRouter>
  );

beforeEach(() => {
  jest.clearAllMocks();
  adminService.getStats.mockResolvedValue(STATS);
  adminService.listUsers.mockResolvedValue({ total: 1, users: [USER] });
});

test('timeAgo formate les durées en français', () => {
  const now = Date.parse('2026-11-06T12:00:00Z');
  expect(timeAgo(null, now)).toBe('jamais');
  expect(timeAgo('2026-11-06T11:59:50Z', now)).toBe("à l'instant");
  expect(timeAgo('2026-11-06T11:55:00Z', now)).toBe('il y a 5 min');
  expect(timeAgo('2026-11-06T09:00:00Z', now)).toBe('il y a 3 h');
  expect(timeAgo('2026-11-04T12:00:00Z', now)).toBe('il y a 2 j');
});

test('affiche les chiffres en direct et la liste des comptes', async () => {
  renderPage();
  expect(await screen.findByText('Inscrits')).toBeInTheDocument();
  expect(screen.getByText(/5\s?678/)).toBeInTheDocument(); // livres inscrits
  expect(screen.getByText('Alice')).toBeInTheDocument();
  expect(screen.getByText('Livres inscrits')).toBeInTheDocument();
});

test('bannir demande confirmation puis appelle le serveur avec le motif', async () => {
  adminService.banUser.mockResolvedValue({ success: true });
  renderPage();
  fireEvent.click(await screen.findByRole('button', { name: 'Bannir' }));
  fireEvent.change(screen.getByLabelText('Motif du bannissement'), { target: { value: 'spam' } });
  fireEvent.click(screen.getAllByRole('button', { name: 'Bannir' }).pop());
  await waitFor(() => expect(adminService.banUser).toHaveBeenCalledWith('u1', 'spam'));
});

test('débannir un compte banni', async () => {
  adminService.listUsers.mockResolvedValue({ total: 1, users: [{ ...USER, banned: true, banned_reason: 'spam' }] });
  adminService.unbanUser.mockResolvedValue({ success: true });
  renderPage();
  expect(await screen.findByText('Motif : spam')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Débannir' }));
  await waitFor(() => expect(adminService.unbanUser).toHaveBeenCalledWith('u1'));
});

test('un non-administrateur voit un refus', async () => {
  adminService.getStats.mockRejectedValue(new AdminError('Accès réservé aux administrateurs.', 403));
  renderPage();
  expect(await screen.findByText(/réservée aux administrateurs/)).toBeInTheDocument();
});
