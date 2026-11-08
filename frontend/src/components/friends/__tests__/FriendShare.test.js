import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import FriendsHome from '../FriendsHome';
import friendsService from '../../../services/friendsService';

jest.mock('react-hot-toast', () => {
  const toast = () => {};
  toast.success = () => {};
  toast.error = () => {};
  return { __esModule: true, default: toast };
});
jest.mock('qrcode', () => ({
  toString: () => Promise.resolve('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'),
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
  delete navigator.share;
});

const card = (state = 'none') => ({
  user: { id: 'u9', display_name: 'Bob', username: 'bob', bio: '', avatar_url: '', state },
  is_me: false,
});

describe('partage de profil et ajout par code', () => {
  test('« Afficher le QR code » affiche le QR, le pseudo et le code ami', async () => {
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    expect(screen.queryByRole('button', { name: 'Scanner un QR code' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Afficher le QR code' }));
    const img = await screen.findByAltText(/QR code de ton profil/);
    expect(img.getAttribute('src')).toMatch(/^data:image\/svg\+xml/);
    expect(screen.getByText('@alice')).toBeInTheDocument();
    expect(screen.getByText('ABCD-2345')).toBeInTheDocument();
  });

  test('si le QR code ne peut pas être créé, le code ami reste affiché', async () => {
    jest.resetModules();
    const qrcode = require('qrcode');
    jest.spyOn(qrcode, 'toString').mockRejectedValue(new Error('boom'));
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Afficher le QR code' }));
    expect(await screen.findByText(/n'a pas pu être créé/)).toBeInTheDocument();
    expect(screen.getByText('ABCD-2345')).toBeInTheDocument();
  });

  test('une erreur serveur propose de réessayer', async () => {
    const spy = jest.spyOn(friendsService, 'myCode').mockRejectedValueOnce(new Error('Serveur lent'));
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Afficher le QR code' }));
    expect(await screen.findByText('Serveur lent')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));
    expect(await screen.findByAltText(/QR code de ton profil/)).toBeInTheDocument();
    expect(spy).toHaveBeenCalledTimes(2);
  });

  test('« Partager mon profil » propose les réseaux avec le lien de connexion', async () => {
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Partager mon profil' }));
    const dialog = await screen.findByRole('dialog', { name: 'Partager mon profil' });
    const list = await within(dialog).findByRole('list', { name: 'Envoyer le lien avec' });
    const link = 'https://booktime-fawn.vercel.app/ami/ABCD2345';
    const whatsapp = within(list).getByRole('link', { name: /WhatsApp/ });
    expect(whatsapp.getAttribute('href')).toContain('https://wa.me/?text=');
    expect(decodeURIComponent(whatsapp.getAttribute('href'))).toContain(link);
    expect(within(list).getByRole('link', { name: /Telegram/ }).getAttribute('href')).toContain(
      encodeURIComponent(link)
    );
    ['Facebook', 'X', 'SMS', 'E-mail'].forEach((label) =>
      expect(within(list).getByRole('link', { name: new RegExp(label) })).toBeInTheDocument()
    );
    expect(within(dialog).getByLabelText("Ton lien d'ami")).toHaveValue(link);
  });

  test('« Autres applications… » ouvre la feuille de partage de l’appareil', async () => {
    const share = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'share', { value: share, configurable: true });
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Partager mon profil' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Autres applications…' }));
    await waitFor(() => expect(share).toHaveBeenCalled());
    expect(share.mock.calls[0][0].url).toBe('https://booktime-fawn.vercel.app/ami/ABCD2345');
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

  test('un QR code scanné retrouve le lecteur (depuis la fenêtre du QR code)', async () => {
    const byCode = jest.spyOn(friendsService, 'byCode').mockResolvedValue(card('friends'));
    render(<FriendsHome onOpenChat={jest.fn()} onOpenProfile={jest.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: 'Afficher le QR code' }));
    fireEvent.click(await screen.findByRole('button', { name: "Scanner celui d'un ami" }));
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
