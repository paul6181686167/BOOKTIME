import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import friendsService from '../services/friendsService';
import { getToken } from '../services/apiClient';

/**
 * Messages d'amis non lus + demandes reçues.
 * Un sondage partagé : au démarrage, toutes les 20 s, et au retour dans l'app.
 */
export const FRIENDS_UNREAD_CHANGED_EVENT = 'booktime:friends-unread-changed';
const POLL_MS = 30 * 1000;

let unread = 0;
let messages = 0;
let loaded = false;
let timer = null;
const listeners = new Set();

function setUnread(nextTotal, nextMessages) {
  const totalChanged = nextTotal !== unread;
  const msgChanged = nextMessages !== messages;
  unread = nextTotal;
  messages = nextMessages;
  if (totalChanged || msgChanged) listeners.forEach((fn) => fn(unread));
}

export async function refreshFriendsUnread() {
  const token = getToken();
  if (!token) {
    loaded = false;
    setUnread(0, 0);
    return;
  }
  try {
    const data = await friendsService.unreadSummary();
    const nextMessages = Number(data?.unread_messages) || 0;
    const nextPending = Number(data?.pending_requests) || 0;
    const nextTotal = nextMessages + nextPending;
    if (loaded && nextMessages > messages) {
      toast("Nouveau message d'un ami", { icon: '💬', id: 'new-friend-message' });
    }
    loaded = true;
    setUnread(nextTotal, nextMessages);
  } catch {
    /* hors ligne : on garde le dernier compteur */
  }
}

function onVisible() {
  if (document.visibilityState === 'visible') refreshFriendsUnread();
}

function start() {
  refreshFriendsUnread();
  timer = setInterval(refreshFriendsUnread, POLL_MS);
  document.addEventListener('visibilitychange', onVisible);
  window.addEventListener(FRIENDS_UNREAD_CHANGED_EVENT, refreshFriendsUnread);
}

function stop() {
  clearInterval(timer);
  timer = null;
  document.removeEventListener('visibilitychange', onVisible);
  window.removeEventListener(FRIENDS_UNREAD_CHANGED_EVENT, refreshFriendsUnread);
}

export default function useFriendsUnread() {
  const [count, setCount] = useState(unread);
  useEffect(() => {
    listeners.add(setCount);
    setCount(unread);
    if (listeners.size === 1) start();
    return () => {
      listeners.delete(setCount);
      if (listeners.size === 0) stop();
    };
  }, []);
  return count;
}

/** Pour les tests : remet le module à zéro. */
export function __resetFriendsUnread() {
  stop();
  listeners.clear();
  unread = 0;
  messages = 0;
  loaded = false;
}
