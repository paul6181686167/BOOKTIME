/** Couleurs des barres système (status / navigation Android) selon le thème. */

export function getThemeChrome(theme) {
  if (theme === 'void') {
    return {
      page: '#050505',
      statusBar: '#050505',
      navigationBar: '#050505',
      darkNavigationButtons: false,
      statusBarStyle: 'DARK', // icônes claires
    };
  }
  if (theme === 'dark') {
    return {
      page: '#234f37',
      statusBar: '#234f37',
      navigationBar: '#234f37',
      darkNavigationButtons: false,
      statusBarStyle: 'DARK',
    };
  }
  return {
    page: '#bce8cb',
    statusBar: '#16a34a',
    navigationBar: '#bce8cb',
    darkNavigationButtons: true,
    statusBarStyle: 'DARK',
  };
}
