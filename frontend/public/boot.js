/*
 * Amorçage de la page, exécuté avant le premier affichage.
 * Fichier externe (et non un <script> dans index.html) pour que la politique de sécurité
 * du contenu puisse interdire tout script inline (script-src 'self').
 */
(function () {
  try {
    // Appliquer le thème AVANT le paint (évite barre système verte / splash vert)
    var t = localStorage.getItem('booktime-theme') || '';
    if (t === 'cinema') t = 'void';
    var page = '#bce8cb';
    if (t === 'void') page = '#050505';
    else if (t === 'dark') page = '#234f37';
    else if (!t && window.matchMedia('(prefers-color-scheme: dark)').matches) page = '#234f37';
    var meta = document.getElementById('bt-theme-color');
    if (meta) meta.setAttribute('content', page);
    var ms = document.querySelector('meta[name="msapplication-navbutton-color"]');
    if (ms) ms.setAttribute('content', page);
    // Même règle que ThemeContext : sombre si choisi, ou si rien n'est choisi et que l'OS est sombre
    var isDark = t === 'dark' || t === 'void' || (!t && window.matchMedia('(prefers-color-scheme: dark)').matches);
    var scheme = document.querySelector('meta[name="color-scheme"]');
    if (scheme) scheme.setAttribute('content', isDark ? 'dark' : 'light');
    var boot = document.getElementById('bt-boot-bg');
    if (!boot) {
      boot = document.createElement('style');
      boot.id = 'bt-boot-bg';
      document.head.appendChild(boot);
    }
    boot.textContent = 'html,body,#root{background-color:' + page + ' !important;}';
    var root = document.documentElement;
    root.style.backgroundColor = page;
    root.style.colorScheme = isDark ? 'dark' : 'light';
    if (t === 'dark' || t === 'void') root.classList.add('dark');
    if (t === 'void') root.classList.add('cinema');
  } catch (e) {
    /* ignore */
  }

  // Cache l'écran de chargement une fois la page prête
  window.addEventListener('load', function () {
    document.body.classList.add('loaded');
  });
})();
