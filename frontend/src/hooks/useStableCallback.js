import { useCallback, useEffect, useRef } from 'react';

// Donne une identité stable à un callback tout en appelant toujours sa dernière
// version. Nécessaire pour que React.memo protège réellement les cartes de la
// grille : sans cela, un handler recréé à chaque rendu invalide la mémoïsation.
const useStableCallback = (fn) => {
  const ref = useRef(fn);
  useEffect(() => {
    ref.current = fn;
  });
  return useCallback((...args) => ref.current?.(...args), []);
};

export default useStableCallback;
