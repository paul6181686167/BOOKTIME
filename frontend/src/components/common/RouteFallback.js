import React from 'react';

// Écran d'attente le temps qu'un morceau de code différé arrive
const RouteFallback = () => (
  <div className="min-h-screen flex items-center justify-center bg-honeycomb">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
  </div>
);

export default RouteFallback;
