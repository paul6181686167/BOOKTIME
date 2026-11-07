import { useEffect } from 'react';
import { startCollectionsSync } from '../services/collectionsSync';

/** Synchronise les collections avec le compte tant qu'un utilisateur est connecté. */
export default function useCollectionsSync(userId) {
  useEffect(() => {
    if (!userId) return undefined;
    return startCollectionsSync();
  }, [userId]);
}
