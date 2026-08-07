import React, { useEffect, useState } from 'react';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { isNativeApp } from '../utils/platform';

const DISMISS_KEY = 'booktime_pwa_install_dismissed';

/**
 * Bannière mobile « Installer Booktime » (beforeinstallprompt + iOS).
 */
const PwaInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [visible, setVisible] = useState(false);
  const [isIos, setIsIos] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // L'app est déjà installée depuis le Play Store : rien à proposer.
    if (isNativeApp()) return;

    const dismissed = localStorage.getItem(DISMISS_KEY);
    if (dismissed) return;

    const standalone =
      window.matchMedia('(display-mode: standalone)').matches ||
      window.navigator.standalone === true;
    if (standalone) return;

    const ua = window.navigator.userAgent || '';
    const ios = /iPad|iPhone|iPod/.test(ua) && !window.MSStream;
    setIsIos(ios);

    const onBeforeInstall = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setVisible(true);
    };

    window.addEventListener('beforeinstallprompt', onBeforeInstall);

    // iOS : pas d'événement beforeinstallprompt → hint manuel
    if (ios) {
      const t = setTimeout(() => setVisible(true), 2500);
      return () => {
        clearTimeout(t);
        window.removeEventListener('beforeinstallprompt', onBeforeInstall);
      };
    }

    return () => window.removeEventListener('beforeinstallprompt', onBeforeInstall);
  }, []);

  const dismiss = () => {
    setVisible(false);
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      /* ignore */
    }
  };

  const install = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    try {
      await deferredPrompt.userChoice;
    } catch {
      /* ignore */
    }
    setDeferredPrompt(null);
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      className="md:hidden fixed left-3 right-3 z-50 rounded-xl bg-gray-900 text-white shadow-lg border border-gray-700"
      style={{ bottom: 'calc(4.25rem + env(safe-area-inset-bottom))' }}
      role="dialog"
      aria-label="Installer Booktime"
    >
      <div className="flex items-start gap-3 p-3">
        <img
          src={`${process.env.PUBLIC_URL || ''}/icon-192.png`}
          alt=""
          className="w-10 h-10 rounded-lg flex-shrink-0"
          width={40}
          height={40}
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold">Installer Booktime</p>
          <p className="text-xs text-gray-300 mt-0.5 leading-snug">
            {isIos
              ? 'Sur Safari : Partager → Sur l’écran d’accueil'
              : 'Ajoute l’app à ton écran d’accueil pour un accès rapide.'}
          </p>
          {!isIos && deferredPrompt && (
            <button
              type="button"
              onClick={install}
              className="mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-green-600 hover:bg-green-500 active:bg-green-700"
            >
              <ArrowDownTrayIcon className="w-4 h-4" aria-hidden="true" />
              Installer
            </button>
          )}
        </div>
        <button
          type="button"
          onClick={dismiss}
          className="p-1 text-gray-400 hover:text-white"
          aria-label="Fermer"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default PwaInstallPrompt;
