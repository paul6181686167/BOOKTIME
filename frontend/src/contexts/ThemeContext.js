import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getThemeChrome } from '../utils/themeChrome';

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

function applyThemeToDocument(theme) {
  const root = document.documentElement;
  root.classList.toggle('dark', theme === 'dark' || theme === 'void');
  root.classList.toggle('cinema', theme === 'void');

  const chrome = getThemeChrome(theme);
  // Fond document = thème (visible derrière la barre système Android transparente)
  root.style.backgroundColor = chrome.page;
  if (document.body) {
    document.body.style.backgroundColor = chrome.page;
  }
  const appRoot = document.getElementById('root');
  if (appRoot) {
    appRoot.style.backgroundColor = chrome.page;
  }
  // Chrome Android : theme-color = couleur de la barre système (pas le vert accent)
  let themeMeta = document.querySelector('meta[name="theme-color"]:not([media])');
  if (!themeMeta) {
    document.querySelectorAll('meta[name="theme-color"]').forEach((el) => el.remove());
    themeMeta = document.createElement('meta');
    themeMeta.setAttribute('name', 'theme-color');
    document.head.appendChild(themeMeta);
  }
  themeMeta.setAttribute('content', chrome.page);
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

  useEffect(() => {
    applyThemeToDocument(theme);
    try {
      localStorage.setItem('booktime-theme', theme);
    } catch (_) {
      /* ignore */
    }
  }, [theme]);

  const setTheme = useCallback((next) => {
    const normalized = normalizeTheme(next);
    if (normalized) setThemeState(normalized);
  }, []);

  /** Clair → Foncé → Très foncé → Clair */
  const cycleTheme = useCallback(() => {
    setThemeState((prev) => {
      const i = THEMES.indexOf(prev);
      return THEMES[(i + 1) % THEMES.length];
    });
  }, []);

  // Compat anciens composants (toggle binaire)
  const toggleTheme = useCallback(() => {
    setThemeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

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
