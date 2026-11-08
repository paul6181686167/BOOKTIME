import React, { useEffect, useState } from 'react';
import {
  SLOW_BACKEND_EVENT,
  isBackendCurrentlySlow,
} from '../../utils/slowBackendNotice';

/**
 * Bandeau non bloquant : le serveur Render met du temps à répondre (souvent un réveil).
 */
export default function SlowBackendBanner() {
  const [slow, setSlow] = useState(() => isBackendCurrentlySlow());

  useEffect(() => {
    const onChange = (event) => setSlow(!!event.detail?.slow);
    window.addEventListener(SLOW_BACKEND_EVENT, onChange);
    return () => window.removeEventListener(SLOW_BACKEND_EVENT, onChange);
  }, []);

  if (!slow) return null;

  return (
    <div
      className="fixed left-0 right-0 z-50 bg-booktime-700 text-white text-center text-xs font-medium py-1.5 px-3 md:text-sm"
      style={{ top: 'env(safe-area-inset-top)' }}
      role="status"
    >
      Le serveur démarre — s&apos;il a dormi, compte 15 à 60 secondes.
    </div>
  );
}
