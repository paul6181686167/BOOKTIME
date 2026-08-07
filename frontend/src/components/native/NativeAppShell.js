import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { isNativeApp } from '../../utils/platform';

const EXIT_CONFIRM_DELAY = 2000;

/**
 * Réglages propres à l'application Android : barre de statut aux couleurs de
 * l'app et bouton retour matériel. Ne rend rien et reste inerte sur le web.
 */
const NativeAppShell = () => {
  useEffect(() => {
    if (!isNativeApp()) return undefined;

    let removeBackButton;
    let exitArmedUntil = 0;

    const setup = async () => {
      const [{ App }, { StatusBar, Style }] = await Promise.all([
        import('@capacitor/app'),
        import('@capacitor/status-bar'),
      ]);

      StatusBar.setStyle({ style: Style.Dark }).catch(() => {});
      StatusBar.setBackgroundColor({ color: '#16a34a' }).catch(() => {});

      const listener = await App.addListener('backButton', ({ canGoBack }) => {
        if (canGoBack) {
          window.history.back();
          return;
        }
        // Racine de l'app : une seconde pression rapide confirme la sortie.
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
  }, []);

  return null;
};

export default NativeAppShell;
