import { isNativeApp } from './platform';

/**
 * Enregistrement du Service Worker Booktime (PWA).
 * Activé en production, ou en local si REACT_APP_ENABLE_SW=true.
 */
export function registerServiceWorker() {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  // Dans l'app native, les assets sont déjà embarqués dans l'APK : le cache du
  // SW ferait doublon et pourrait servir un shell obsolète après une mise à jour.
  if (isNativeApp()) {
    unregisterServiceWorker();
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
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
  // getRegistrations() plutôt que ready : cette dernière ne se résout jamais
  // quand aucun service worker n'est enregistré.
  navigator.serviceWorker
    .getRegistrations()
    .then((registrations) => registrations.forEach((r) => r.unregister()))
    .catch(() => {});
}
