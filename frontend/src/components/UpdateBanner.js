import React, { useEffect, useState } from 'react';
import { UPDATE_READY_EVENT, applyUpdate, isUpdateReady } from '../utils/registerServiceWorker';

/**
 * Bandeau « Nouvelle version disponible ».
 *
 * Remplace l'ancien rechargement automatique, qui pouvait couper une saisie ou un
 * ajout de livre en cours. L'utilisateur choisit le moment de recharger.
 */
const UpdateBanner = () => {
  const [ready, setReady] = useState(isUpdateReady());
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const onReady = () => {
      setReady(true);
      setDismissed(false);
    };
    window.addEventListener(UPDATE_READY_EVENT, onReady);
    return () => window.removeEventListener(UPDATE_READY_EVENT, onReady);
  }, []);

  if (!ready || dismissed) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="update-banner"
      className="fixed left-3 right-3 z-[60] mx-auto flex max-w-md items-center gap-3 rounded-xl border border-white/10 bg-gray-900 px-4 py-3 text-sm text-white shadow-lg"
      style={{ bottom: 'calc(env(safe-area-inset-bottom) + 76px)' }}
    >
      <span className="flex-1">Une nouvelle version de Booktime est disponible.</span>
      <button
        type="button"
        onClick={applyUpdate}
        className="min-h-[44px] rounded-lg bg-booktime-600 px-3 font-semibold text-white hover:bg-booktime-700"
      >
        Mettre à jour
      </button>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        aria-label="Plus tard"
        className="min-h-[44px] min-w-[44px] rounded-lg text-gray-300 hover:text-white"
      >
        ✕
      </button>
    </div>
  );
};

export default UpdateBanner;
