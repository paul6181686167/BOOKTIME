import React, { createContext, useContext, useState, useEffect, useLayoutEffect, useCallback, useRef } from 'react';
import { getThemeChrome } from '../utils/themeChrome';
import { applyThemeColor } from '../utils/applyThemeColor';

const ThemeContext = createContext();

export const THEMES = ['light', 'dark', 'void'];

export const THEME_LABELS = {
  light: 'Clair',
  dark: 'Foncé',
  void: 'Très foncé',
};

function normalizeTheme(raw) {
  if (raw === 'void' || raw === 'cinema') return 'void';
  if (raw === 'dark' || raw === 'light') return raw;
  return null;
}

function readInitialTheme() {
  try {
    const saved = localStorage.getItem('booktime-theme');
    const normalized = normalizeTheme(saved);
    if (normalized) return normalized;
  } catch (_) {
    /* ignore */
  }
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

export function applyThemeToDocument(theme) {
  const root = document.documentElement;
  root.classList.toggle('dark', theme === 'dark' || theme === 'void');
  root.classList.toggle('cinema', theme === 'void');

  const chrome = getThemeChrome(theme);
  applyThemeColor(chrome.page, theme);

  const apple = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]');
  if (apple) {
    apple.setAttribute(
      'content',
      theme === 'light' ? 'default' : 'black-translucent'
    );
  }
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(readInitialTheme);

  useLayoutEffect(() => {
    applyThemeToDocument(theme);
    try {
      localStorage.setItem('booktime-theme', theme);
    } catch (_) {
      /* ignore */
    }
  }, [theme]);

  useEffect(() => {
    const refresh = () => applyThemeToDocument(theme);
    const onVis = () => {
      if (document.visibilityState === 'visible') refresh();
    };
    window.addEventListener('pageshow', refresh);
    document.addEventListener('visibilitychange', onVis);
    return () => {
      window.removeEventListener('pageshow', refresh);
      document.removeEventListener('visibilitychange', onVis);
    };
  }, [theme]);

  const themeRef = useRef(theme);
  themeRef.current = theme;

  // Changement de thème demandé par l'utilisateur.
  // App native : NativeAppShell applique la couleur de la barre système (SystemBars).
  const changeTheme = useCallback((next) => {
    const normalized = normalizeTheme(next);
    if (!normalized || normalized === themeRef.current) return;

    applyThemeToDocument(normalized);
    try {
      localStorage.setItem('booktime-theme', normalized);
    } catch (_) {
      /* ignore */
    }
    themeRef.current = normalized;
    setThemeState(normalized);

  }, []);

  const setTheme = changeTheme;

  const cycleTheme = useCallback(() => {
    const i = THEMES.indexOf(themeRef.current);
    changeTheme(THEMES[(i + 1) % THEMES.length]);
  }, [changeTheme]);

  const toggleTheme = useCallback(() => {
    changeTheme(themeRef.current === 'light' ? 'dark' : 'light');
  }, [changeTheme]);
  const isDark = theme === 'dark' || theme === 'void';
  const isVoid = theme === 'void';

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        cycleTheme,
        toggleTheme,
        isDark,
        isVoid,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};
