import React from 'react';
import { act, render, screen } from '@testing-library/react';
import toast from 'react-hot-toast';
import friendsService from '../../services/friendsService';
import useFriendsUnread, {
  FRIENDS_UNREAD_CHANGED_EVENT,
  __resetFriendsUnread,
} from '../useFriendsUnread';
import NotificationBadge from '../../components/common/NotificationBadge';

jest.mock('react-hot-toast', () => jest.fn());

function Probe() {
  const count = useFriendsUnread();
  return <NotificationBadge count={count} />;
}

let summary;
beforeEach(() => {
  summary = { unread_messages: 2, pending_requests: 1 };
  localStorage.setItem('token', 't');
  jest.spyOn(friendsService, 'unreadSummary').mockImplementation(() => Promise.resolve(summary));
  toast.mockClear();
});
afterEach(() => {
  __resetFriendsUnread();
  localStorage.clear();
  jest.restoreAllMocks();
});

test('affiche le nombre non lu sans prévenir au démarrage', async () => {
  render(<Probe />);
  expect(await screen.findByTestId('notification-badge')).toHaveTextContent('3');
  expect(toast).not.toHaveBeenCalled();
});

test('prévient d’un nouveau message puis masque le badge quand tout est lu', async () => {
  render(<Probe />);
  await screen.findByTestId('notification-badge');

  summary = { unread_messages: 3, pending_requests: 1 };
  await act(async () => {
    window.dispatchEvent(new Event(FRIENDS_UNREAD_CHANGED_EVENT));
  });
  expect(screen.getByTestId('notification-badge')).toHaveTextContent('4');
  expect(toast).toHaveBeenCalledTimes(1);

  summary = { unread_messages: 0, pending_requests: 0 };
  await act(async () => {
    window.dispatchEvent(new Event(FRIENDS_UNREAD_CHANGED_EVENT));
  });
  expect(screen.queryByTestId('notification-badge')).toBeNull();
});

test('ne sonde pas le serveur sans connexion', async () => {
  localStorage.removeItem('token');
  render(<Probe />);
  await act(async () => {});
  expect(friendsService.unreadSummary).not.toHaveBeenCalled();
  expect(screen.queryByTestId('notification-badge')).toBeNull();
});
