/** Chrome Android : barre système = fond du thème app. */

let applyTimer = 0;

function setBootBackground(color) {
  let style = document.getElementById('bt-boot-bg');
  if (!style) {
    style = document.createElement('style');
    style.id = 'bt-boot-bg';
    document.head.appendChild(style);
  }
  // Couvre aussi les zones safe-area (barre geste Android souvent translucide)
  style.textContent = `
    :root { --bt-chrome: ${color}; }
    html, body, #root { background-color: ${color} !important; }
    .mobile-slideshow { background-color: ${color} !important; }
    #bt-chrome-fill {
      position: fixed;
      left: 0;
      right: 0;
      top: -80px;
      bottom: -80px;
      z-index: -1;
      pointer-events: none;
      background-color: ${color};
    }
  `;
}

function ensureChromeFill() {
  if (document.getElementById('bt-chrome-fill')) return;
  const el = document.createElement('div');
  el.id = 'bt-chrome-fill';
  el.setAttribute('aria-hidden', 'true');
  document.body
    ? document.body.prepend(el)
    : document.documentElement.appendChild(el);
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
 * Recrée la meta (Chrome garde parfois une référence morte).
 * Flash contrasté obligatoire : un nudge ±1 hex est ignoré sur Android.
 */
function setThemeColorMeta(color) {
  document.querySelectorAll('meta[name="theme-color"]').forEach((el) => el.remove());

  const flash = color === '#bce8cb' ? '#050505' : '#bce8cb';

  const meta = document.createElement('meta');
  meta.setAttribute('name', 'theme-color');
  meta.id = 'bt-theme-color';
  meta.setAttribute('content', flash);
  document.head.insertBefore(meta, document.head.firstChild);

  // Aussi les media = même couleur app (évite le piège du thème OS)
  ['(prefers-color-scheme: light)', '(prefers-color-scheme: dark)'].forEach((media, i) => {
    const m = document.createElement('meta');
    m.setAttribute('name', 'theme-color');
    m.id = `bt-theme-color-${i}`;
    m.setAttribute('media', media);
    m.setAttribute('content', flash);
    document.head.appendChild(m);
  });

  if (applyTimer) window.clearTimeout(applyTimer);
  applyTimer = window.setTimeout(() => {
    document.querySelectorAll('meta[name="theme-color"]').forEach((el) => {
      el.setAttribute('content', color);
    });
  }, 50);

  let ms = document.querySelector('meta[name="msapplication-navbutton-color"]');
  if (!ms) {
    ms = document.createElement('meta');
    ms.setAttribute('name', 'msapplication-navbutton-color');
    document.head.appendChild(ms);
  }
  ms.setAttribute('content', color);
}

/**
 * @param {string} color hex
 * @param {'light'|'dark'|'void'} [theme]
 */
export function applyThemeColor(color, theme) {
  if (typeof document === 'undefined' || !color) return;

  const root = document.documentElement;
  root.style.setProperty('--bt-chrome', color);
  root.style.backgroundColor = color;
  if (document.body) {
    document.body.style.backgroundColor = color;
    ensureChromeFill();
  }
  const appRoot = document.getElementById('root');
  if (appRoot) appRoot.style.backgroundColor = color;

  setBootBackground(color);
  if (theme) setColorScheme(theme);
  setThemeColorMeta(color);
}
