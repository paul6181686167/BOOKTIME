import React from 'react';

// Écran d'attente le temps qu'un morceau de code différé arrive
const RouteFallback = () => (
  <div className="min-h-screen min-h-dvh flex items-center justify-center bg-honeycomb">
    <div role="status" aria-label="Chargement en cours" className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-700 dark:border-green-400"></div>
  </div>
);

export default RouteFallback;
