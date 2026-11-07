import { useEffect, useState } from 'react';
import {
  PROFILE_STORAGE_KEY,
  COLLECTIONS_CHANGED_EVENT,
  buildCollectionColorMap,
} from '../utils/collectionsStorage';

/**
 * Table « clé d'élément → couleurs de ses collections », tenue à jour quand une
 * collection est créée, modifiée ou supprimée (même depuis un autre onglet).
 */
export default function useCollectionColors() {
  const [map, setMap] = useState(() => buildCollectionColorMap());

  useEffect(() => {
    const refresh = () => setMap(buildCollectionColorMap());
    const onStorage = (e) => {
      if (!e.key || e.key === PROFILE_STORAGE_KEY) refresh();
    };
    window.addEventListener(COLLECTIONS_CHANGED_EVENT, refresh);
    window.addEventListener('storage', onStorage);
    // Au montage : rattrape un changement survenu entre le rendu et l'abonnement
    refresh();
    return () => {
      window.removeEventListener(COLLECTIONS_CHANGED_EVENT, refresh);
      window.removeEventListener('storage', onStorage);
    };
  }, []);

  return map;
}
