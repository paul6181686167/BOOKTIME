import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FriendsHome from '../FriendsHome';
import friendsService from '../../../services/friendsService';

jest.mock('react-hot-toast', () => {
  const toast = () => {};
  toast.success = () => {};
  toast.error = () => {};
  return { __esModule: true, default: toast };
});
jest.mock('qrcode', () => ({
  toDataURL: () => Promise.resolve('data:image/png;base64,AAAA'),
}));
jest.mock('../QrScanModal', () => ({
  __esModule: true,
  default: ({ onCode }) => (
    <button type="button" onClick={() => onCode('ZZZZ2222')}>
      faux-scan
    </button>
  ),
}));

beforeEach(() => {
  jest.spyOn(friendsService, 'listFriends').mockResolvedValue({ friends: [] });
  jest.spyOn(friendsService, 'listRequests').mockResolvedValue({ incoming: [], outgoing: [] });
  jest.spyOn(friendsService, 'myCode').mockResolvedValue({
    code: 'ABCD2345',
    username: 'alice',
    display_name: 'Alice',
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

const card = (state = 'none') => ({
  user: { id: 'u9', display_name: 'Bob', username: 'bob', bio: '', avatar_url: '', state },
  is_me: false,
});

describe('partage de profil et ajout par code', () => {
  test('affiche le QR code, le pseudo et le code ami', async () => {
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Partager mon profil' }));
    expect(await screen.findByAltText(/QR code de ton profil/)).toBeInTheDocument();
    expect(screen.getByText('@alice')).toBeInTheDocument();
    expect(screen.getByText('ABCD-2345')).toBeInTheDocument();
  });

  test('un lien ouvert affiche le lecteur et permet de l’ajouter', async () => {
    jest.spyOn(friendsService, 'byCode').mockResolvedValue(card());
    const send = jest.spyOn(friendsService, 'sendRequest').mockResolvedValue({ state: 'pending_out' });
    render(<FriendsHome inviteCode="ZZZZ2222" onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    expect(await screen.findByText('Bob')).toBeInTheDocument();
    expect(friendsService.byCode).toHaveBeenCalledWith('ZZZZ2222');
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter' }));
    await waitFor(() => expect(send).toHaveBeenCalledWith('u9'));
    expect(await screen.findByText('Demande envoyée')).toBeInTheDocument();
  });

  test('un QR code scanné retrouve le lecteur', async () => {
    const byCode = jest.spyOn(friendsService, 'byCode').mockResolvedValue(card('friends'));
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Scanner un QR code' }));
    fireEvent.click(await screen.findByText('faux-scan'));
    expect(await screen.findByText('Bob')).toBeInTheDocument();
    expect(byCode).toHaveBeenCalledWith('ZZZZ2222');
    expect(screen.getByText('Ami')).toBeInTheDocument();
  });

  test('un code inconnu affiche l’erreur du serveur', async () => {
    jest.spyOn(friendsService, 'byCode').mockRejectedValue(new Error('Ce code ne correspond à aucun lecteur.'));
    render(<FriendsHome inviteCode="ZZZZ2222" onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    expect(await screen.findByText('Ce code ne correspond à aucun lecteur.')).toBeInTheDocument();
  });
});
