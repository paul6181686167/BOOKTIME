import { useEffect } from 'react';
import { startOfflineWriteQueue } from '../utils/offlineWriteQueue';

/** Démarre la file d'attente hors ligne tant qu'un utilisateur est connecté. */
export default function useOfflineWriteQueue(userId) {
  useEffect(() => {
    if (!userId) return undefined;
    return startOfflineWriteQueue();
  }, [userId]);
}
