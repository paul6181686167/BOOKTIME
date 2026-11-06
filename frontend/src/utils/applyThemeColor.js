/** Chrome Android : barre système = fond du thème app (pas le mode OS). */

let nudgeTimer = 0;

function setBootBackground(color) {
  let style = document.getElementById('bt-boot-bg');
  if (!style) {
    style = document.createElement('style');
    style.id = 'bt-boot-bg';
    document.head.appendChild(style);
  }
  style.textContent = `html,body,#root{background-color:${color} !important;}`;
}

/**
 * Une seule meta theme-color, sans media query.
 * Les media (prefers-color-scheme) figeaient la barre sur le thème OS (souvent « Foncé »).
 */
function setThemeColorMeta(color) {
  document
    .querySelectorAll('meta[name="theme-color"][media]')
    .forEach((el) => el.remove());

  let meta =
    document.getElementById('bt-theme-color') ||
    document.querySelector('meta[name="theme-color"]:not([media])');

  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    meta.id = 'bt-theme-color';
    document.head.insertBefore(meta, document.head.firstChild);
  }

  // Chrome ne repeint parfois que si la valeur change clairement
  const nudge =
    color === '#050505'
      ? '#050506'
      : color === '#234f37'
        ? '#234f38'
        : color === '#bce8cb'
          ? '#bce8cc'
          : '#000001';

  meta.setAttribute('content', nudge);
  if (nudgeTimer) window.clearTimeout(nudgeTimer);
  nudgeTimer = window.setTimeout(() => {
    meta.setAttribute('content', color);
  }, 40);

  let ms = document.querySelector('meta[name="msapplication-navbutton-color"]');
  if (!ms) {
    ms = document.createElement('meta');
    ms.setAttribute('name', 'msapplication-navbutton-color');
    document.head.appendChild(ms);
  }
  ms.setAttribute('content', color);
}

function setColorScheme(theme) {
  const scheme = theme === 'light' ? 'light' : 'dark';
  document.documentElement.style.colorScheme = scheme;
  let meta = document.querySelector('meta[name="color-scheme"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'color-scheme');
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', scheme);
}

/**
 * @param {string} color hex
 * @param {'light'|'dark'|'void'} [theme]
 */
export function applyThemeColor(color, theme) {
  if (typeof document === 'undefined' || !color) return;

  const root = document.documentElement;
  root.style.backgroundColor = color;
  if (document.body) document.body.style.backgroundColor = color;
  const appRoot = document.getElementById('root');
  if (appRoot) appRoot.style.backgroundColor = color;

  setBootBackground(color);
  if (theme) setColorScheme(theme);
  setThemeColorMeta(color);
}
