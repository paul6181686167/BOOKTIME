import React, { useEffect, useState } from 'react';

/**
 * Bandeau discret quand le réseau est coupé (surtout utile en PWA mobile).
 */
const OfflineBanner = () => {
  const [offline, setOffline] = useState(
    typeof navigator !== 'undefined' ? !navigator.onLine : false
  );

  useEffect(() => {
    const goOffline = () => setOffline(true);
    const goOnline = () => setOffline(false);
    window.addEventListener('offline', goOffline);
    window.addEventListener('online', goOnline);
    return () => {
      window.removeEventListener('offline', goOffline);
      window.removeEventListener('online', goOnline);
    };
  }, []);

  if (!offline) return null;

  return (
    <div
      className="md:hidden fixed left-0 right-0 z-50 bg-amber-500 text-amber-950 text-center text-xs font-medium py-1.5 px-3"
      style={{ top: 'env(safe-area-inset-top)' }}
      role="status"
    >
      Hors ligne — bibliothèque en cache disponible
    </div>
  );
};

export default OfflineBanner;
