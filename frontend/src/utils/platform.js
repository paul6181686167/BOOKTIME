/**
 * Détection de la plateforme d'exécution (web vs application native Capacitor).
 *
 * Dans l'app Android, Capacitor sert le bundle depuis https://localhost : les
 * heuristiques basées sur le hostname ne suffisent donc pas à distinguer le
 * natif du développement local. On combine un drapeau figé au build et le pont
 * Capacitor injecté au runtime.
 */

const NATIVE_BUILD_FLAG = process.env.REACT_APP_NATIVE_BUILD === 'true';

export const isNativeApp = () => {
  if (NATIVE_BUILD_FLAG) return true;
  if (typeof window === 'undefined') return false;
  if (window.location.protocol === 'capacitor:') return true;
  return Boolean(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());
};

export const getNativePlatform = () => {
  if (typeof window === 'undefined' || !window.Capacitor) return null;
  return typeof window.Capacitor.getPlatform === 'function'
    ? window.Capacitor.getPlatform()
    : null;
};

export const isAndroidApp = () => isNativeApp() && getNativePlatform() === 'android';

export default { isNativeApp, getNativePlatform, isAndroidApp };
