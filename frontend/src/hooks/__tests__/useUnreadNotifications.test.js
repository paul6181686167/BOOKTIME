import React from 'react';
import { act, render, screen } from '@testing-library/react';
import toast from 'react-hot-toast';
import useUnreadNotifications, {
  NOTIFICATIONS_CHANGED_EVENT,
  __resetUnreadNotifications,
} from '../useUnreadNotifications';
import NotificationBadge from '../../components/common/NotificationBadge';

jest.mock('react-hot-toast', () => jest.fn());

function Probe() {
  const count = useUnreadNotifications();
  return <NotificationBadge count={count} />;
}

let unread;
beforeEach(() => {
  unread = 2;
  localStorage.setItem('token', 't');
  global.fetch = jest.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({ unread }) })
  );
  toast.mockClear();
});
afterEach(() => {
  __resetUnreadNotifications();
  localStorage.clear();
  delete global.fetch;
});

test('affiche le nombre non lu sans prévenir au démarrage', async () => {
  render(<Probe />);
  expect(await screen.findByTestId('notification-badge')).toHaveTextContent('2');
  expect(toast).not.toHaveBeenCalled();
});

test('prévient d’une nouveauté puis masque le badge quand tout est lu', async () => {
  render(<Probe />);
  await screen.findByTestId('notification-badge');

  unread = 3;
  await act(async () => {
    window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED_EVENT));
  });
  expect(screen.getByTestId('notification-badge')).toHaveTextContent('3');
  expect(toast).toHaveBeenCalledTimes(1);

  unread = 0;
  await act(async () => {
    window.dispatchEvent(new Event(NOTIFICATIONS_CHANGED_EVENT));
  });
  expect(screen.queryByTestId('notification-badge')).toBeNull();
});

test('ne sonde pas le serveur sans connexion', async () => {
  localStorage.removeItem('token');
  render(<Probe />);
  await act(async () => {});
  expect(global.fetch).not.toHaveBeenCalled();
  expect(screen.queryByTestId('notification-badge')).toBeNull();
});
