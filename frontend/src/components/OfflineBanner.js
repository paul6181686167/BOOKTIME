import React, { useEffect, useState } from 'react';
import {
  getPendingCount,
  subscribeOfflineQueue,
  flushOfflineQueue,
} from '../utils/offlineWriteQueue';

/**
 * Bandeau hors ligne / file d'attente : visible sur mobile et bureau.
 */
const OfflineBanner = () => {
  const [offline, setOffline] = useState(
    typeof navigator !== 'undefined' ? !navigator.onLine : false
  );
  const [pending, setPending] = useState(() => getPendingCount());

  useEffect(() => {
    const goOffline = () => setOffline(true);
    const goOnline = () => {
      setOffline(false);
      flushOfflineQueue().catch(() => {});
    };
    window.addEventListener('offline', goOffline);
    window.addEventListener('online', goOnline);
    const unsub = subscribeOfflineQueue(setPending);
    return () => {
      window.removeEventListener('offline', goOffline);
      window.removeEventListener('online', goOnline);
      unsub();
    };
  }, []);

  if (!offline && pending === 0) return null;

  const label = offline
    ? pending > 0
      ? `Hors ligne — ${pending} modification${pending > 1 ? 's' : ''} en attente de synchronisation`
      : 'Hors ligne — bibliothèque en cache disponible'
    : `${pending} modification${pending > 1 ? 's' : ''} en attente de synchronisation`;

  return (
    <div
      className="fixed left-0 right-0 z-50 bg-amber-500 text-amber-950 text-center text-xs font-medium py-1.5 px-3 md:text-sm"
      style={{ top: 'env(safe-area-inset-top)' }}
      role="status"
    >
      {label}
    </div>
  );
};

export default OfflineBanner;
