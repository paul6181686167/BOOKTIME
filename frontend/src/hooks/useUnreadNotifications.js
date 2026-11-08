import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/environment';
import { getToken } from '../services/apiClient';

/**
 * Nombre de notifications non lues (sorties de tomes / livres d'auteurs suivis).
 * Un seul sondage partagé entre tous les composants qui affichent le badge :
 * au démarrage, toutes les 5 minutes, et au retour dans l'application.
 */
export const NOTIFICATIONS_CHANGED_EVENT = 'booktime:notifications-changed';
const POLL_MS = 5 * 60 * 1000;

let unread = 0;
let loaded = false;
let timer = null;
const listeners = new Set();

function setUnread(next) {
  if (next === unread) return;
  unread = next;
  listeners.forEach((fn) => fn(unread));
}

export async function refreshUnreadNotifications() {
  const token = getToken();
  if (!token) {
    loaded = false;
    setUnread(0);
    return;
  }
  try {
    const res = await fetch(`${API_BASE_URL}/api/notifications/unread-count`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const data = await res.json();
    const count = Number(data?.unread) || 0;
    // Prévient seulement des nouveautés arrivées pendant l'utilisation, pas au démarrage
    if (loaded && count > unread) {
      toast('Nouvelle sortie disponible ! Voir « À venir ».', { icon: '🔔', id: 'new-release' });
    }
    loaded = true;
    setUnread(count);
  } catch {
    /* hors ligne : on garde le dernier compteur */
  }
}

function onVisible() {
  if (document.visibilityState === 'visible') refreshUnreadNotifications();
}

function start() {
  refreshUnreadNotifications();
  timer = setInterval(refreshUnreadNotifications, POLL_MS);
  document.addEventListener('visibilitychange', onVisible);
  window.addEventListener(NOTIFICATIONS_CHANGED_EVENT, refreshUnreadNotifications);
}

function stop() {
  clearInterval(timer);
  timer = null;
  document.removeEventListener('visibilitychange', onVisible);
  window.removeEventListener(NOTIFICATIONS_CHANGED_EVENT, refreshUnreadNotifications);
}

export default function useUnreadNotifications() {
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
export function __resetUnreadNotifications() {
  stop();
  listeners.clear();
  unread = 0;
  loaded = false;
}
