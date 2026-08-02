/**
 * Enregistrement du Service Worker Booktime (PWA).
 * Activé en production, ou en local si REACT_APP_ENABLE_SW=true.
 */
export function registerServiceWorker() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  const enableInDev = process.env.REACT_APP_ENABLE_SW === 'true';
  if (process.env.NODE_ENV !== 'production' && !enableInDev) {
    return;
  }

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(`${process.env.PUBLIC_URL || ''}/sw.js`)
      .then((registration) => {
        registration.onupdatefound = () => {
          const installing = registration.installing;
          if (!installing) return;
          installing.onstatechange = () => {
            if (
              installing.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              // Nouvelle version prête — active au prochain chargement
              if (registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
              }
            }
          };
        };
      })
      .catch(() => {
        // SW optionnel : ne pas bloquer l'app
      });
  });
}

export function unregisterServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  navigator.serviceWorker.ready
    .then((registration) => registration.unregister())
    .catch(() => {});
}
