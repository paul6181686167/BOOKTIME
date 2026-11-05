import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Capacitor, registerPlugin } from '@capacitor/core';
import { isNativeApp } from '../../utils/platform';
import { useTheme } from '../../contexts/ThemeContext';
import { getThemeChrome } from '../../utils/themeChrome';

const EXIT_CONFIRM_DELAY = 2000;

const SystemBars = registerPlugin('SystemBars');

async function applyNativeChrome(theme) {
  if (!isNativeApp()) return;
  const chrome = getThemeChrome(theme);

  try {
    const { StatusBar, Style } = await import('@capacitor/status-bar');
    // Laisse le fond CSS se voir ; évite le vert accent forcé par capacitor.config
    await StatusBar.setOverlaysWebView({ overlay: true }).catch(() => {});
    await StatusBar.setBackgroundColor({ color: chrome.statusBar }).catch(() => {});
    await StatusBar.setStyle({
      style: chrome.statusBarStyle === 'LIGHT' ? Style.Light : Style.Dark,
    }).catch(() => {});
  } catch (_) {
    /* plugin absent */
  }

  if (Capacitor.getPlatform() === 'android') {
    try {
      await SystemBars.setNavigationBarColor({
        color: chrome.page,
        darkButtons: chrome.darkNavigationButtons,
        edgeToEdge: true,
      });
    } catch (_) {
      /* plugin natif pas encore sync */
    }
  }
}

/**
 * Barre système Android (retour/accueil) = fond de l’app.
 * Barre d’onglets Booktime = pastille oblongue séparée.
 */
const NativeAppShell = () => {
  const { theme } = useTheme();

  useEffect(() => {
    if (!isNativeApp()) return undefined;
    applyNativeChrome(theme);
    const t1 = window.setTimeout(() => applyNativeChrome(theme), 300);
    const t2 = window.setTimeout(() => applyNativeChrome(theme), 1200);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [theme]);

  useEffect(() => {
    if (!isNativeApp()) return undefined;

    let removeBackButton;
    let exitArmedUntil = 0;

    const setup = async () => {
      await applyNativeChrome(theme);

      const { App } = await import('@capacitor/app');

      const listener = await App.addListener('backButton', ({ canGoBack }) => {
        if (canGoBack) {
          window.history.back();
          return;
        }
        if (Date.now() < exitArmedUntil) {
          App.exitApp();
          return;
        }
        exitArmedUntil = Date.now() + EXIT_CONFIRM_DELAY;
        toast('Appuie encore une fois pour quitter', { duration: EXIT_CONFIRM_DELAY });
      });
      removeBackButton = () => listener.remove();
    };

    setup();
    return () => {
      if (removeBackButton) removeBackButton();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
};

export default NativeAppShell;
