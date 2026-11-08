import { isNativeApp } from './platform';

/**
 * Enregistrement du Service Worker Booktime (PWA).
 * Activé en production, ou en local si REACT_APP_ENABLE_SW=true.
 * Vérifie les mises à jour à chaque ouverture / retour sur l'app.
 *
 * Quand une nouvelle version prend la main, l'application n'est plus rechargée de force :
 * on prévient l'interface (bandeau « Nouvelle version disponible », voir UpdateBanner).
 * Seule exception : si l'application est en arrière-plan, on recharge tout de suite, car
 * personne n'est en train d'y saisir quoi que ce soit.
 */
export const UPDATE_READY_EVENT = 'booktime:update-ready';

let updateReady = false;

export const isUpdateReady = () => updateReady;

/** Recharge la page pour charger la dernière version. */
export const applyUpdate = () => {
  window.location.reload();
};

function signalUpdate() {
  if (updateReady) return;
  updateReady = true;
  if (document.visibilityState === 'hidden') {
    applyUpdate();
    return;
  }
  window.dispatchEvent(new Event(UPDATE_READY_EVENT));
}

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

  // Première installation : il n'y a rien à « mettre à jour », on ne dérange personne
  const hadController = !!navigator.serviceWorker.controller;
  const onUpdate = () => {
    if (hadController) signalUpdate();
  };

  navigator.serviceWorker.addEventListener('controllerchange', onUpdate);
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SW_UPDATED') {
      onUpdate();
    }
  });

  // Un fichier JS d'une ancienne version qui n'existe plus : seul un rechargement répare
  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason;
    const text = String((reason && (reason.name || reason.message)) || '');
    if (/ChunkLoadError|Loading chunk|Loading CSS chunk/i.test(text)) signalUpdate();
  });

  const askSkipWaiting = (registration) => {
    if (registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }
  };

  const watchUpdates = (registration) => {
    askSkipWaiting(registration);

    registration.addEventListener('updatefound', () => {
      const installing = registration.installing;
      if (!installing) return;
      installing.addEventListener('statechange', () => {
        if (
          installing.state === 'installed' &&
          (registration.waiting || navigator.serviceWorker.controller)
        ) {
          askSkipWaiting(registration);
          if (registration.waiting) {
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
          } else {
            installing.postMessage({ type: 'SKIP_WAITING' });
          }
        }
      });
    });

    const check = () => {
      registration.update().catch(() => {});
    };

    // Au retour sur l'app (PWA mobile souvent gelée en arrière-plan)
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') check();
    });
    window.addEventListener('focus', check);

    // Filet de sécurité si l'app reste ouverte longtemps
    setInterval(check, 15 * 60 * 1000);
    check();
  };

  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(`${process.env.PUBLIC_URL || ''}/sw.js`)
      .then(watchUpdates)
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
