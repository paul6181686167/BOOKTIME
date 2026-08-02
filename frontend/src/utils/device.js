/** Détection client mobile (viewport ou UA). */
export function isMobileClient() {
  if (typeof window === 'undefined') return false;
  try {
    if (window.matchMedia('(max-width: 768px)').matches) return true;
  } catch (_) {
    /* ignore */
  }
  return /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent || '');
}
