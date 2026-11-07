/**
 * Données conservées pour la consultation hors ligne (bibliothèque, fiches auteurs,
 * réponses d'API du service worker). Elles sont propres à un compte : on les efface à la
 * déconnexion pour qu'un autre compte utilisant le même appareil ne les retrouve pas.
 */

/** Préfixes des clés localStorage qui contiennent des données d'un compte. */
export const USER_CACHE_KEY_PREFIXES = [
  'booktime_offline_library',
  'booktime_offline_series',
  'booktime_author_profile',
];

/** Suffixes des caches du service worker propres à l'utilisateur. */
const SW_USER_CACHE_SUFFIXES = ['-api', '-detail'];

export async function clearUserCaches() {
  try {
    Object.keys(localStorage)
      .filter((key) => USER_CACHE_KEY_PREFIXES.some((p) => key.startsWith(p)))
      .forEach((key) => localStorage.removeItem(key));
  } catch {
    /* stockage indisponible */
  }
  try {
    if (typeof caches !== 'undefined' && caches.keys) {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter(
            (key) =>
              key.startsWith('booktime-') && SW_USER_CACHE_SUFFIXES.some((s) => key.endsWith(s))
          )
          .map((key) => caches.delete(key))
      );
    }
  } catch {
    /* Cache API indisponible */
  }
}
