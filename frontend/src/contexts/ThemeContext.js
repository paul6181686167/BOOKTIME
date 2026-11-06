import React, { createContext, useContext, useState, useEffect, useLayoutEffect, useCallback } from 'react';
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

function applyThemeToDocument(theme) {
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

  // Avant paint : Chrome Android lit theme-color tout de suite au changement
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
    window.addEventListener('pageshow', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      window.removeEventListener('pageshow', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
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
