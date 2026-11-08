import { useEffect } from 'react';

// Précharge en temps mort les écrans les plus ouverts, pour que le chargement
// différé ne se paie pas au moment du clic.
const useIdlePreload = () => {
  useEffect(() => {
    let cancelled = false;
    const preload = () => {
      if (cancelled) return;
      import('../components/BookDetailModal');
      import('../components/SeriesDetailModal');
      import('../components/UpcomingPanel');
    };
    const hasIdle = typeof window.requestIdleCallback === 'function';
    const handle = hasIdle
      ? window.requestIdleCallback(preload, { timeout: 4000 })
      : setTimeout(preload, 2500);
    return () => {
      cancelled = true;
      if (hasIdle) window.cancelIdleCallback(handle);
      else clearTimeout(handle);
    };
  }, []);
};

export default useIdlePreload;
