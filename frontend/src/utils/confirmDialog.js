/**
 * Confirmation applicative (remplace window.confirm, qui est bloquant, non stylé et
 * parfois supprimé par les navigateurs mobiles / WebView).
 *
 *   if (!(await confirmAction('Supprimer cette série ?'))) return;
 *
 * Le composant <ConfirmHost /> (monté une fois dans l'application) affiche la fenêtre.
 * Sans hôte monté (tests, page isolée), on retombe sur window.confirm.
 */
let host = null;

export function registerConfirmHost(show) {
  host = show;
  return () => {
    if (host === show) host = null;
  };
}

export function confirmAction(message, options = {}) {
  return new Promise((resolve) => {
    if (!host) {
      resolve(typeof window !== 'undefined' && typeof window.confirm === 'function' ? window.confirm(message) : false);
      return;
    }
    host({
      message,
      confirmLabel: options.confirmLabel || 'Confirmer',
      cancelLabel: options.cancelLabel || 'Annuler',
      danger: options.danger !== false,
      resolve,
    });
  });
}
