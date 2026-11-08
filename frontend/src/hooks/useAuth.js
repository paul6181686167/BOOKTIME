import { createContext, useState, useContext, useEffect, useCallback, useMemo, useRef } from 'react';
import toast from 'react-hot-toast';
import AuthService from '../services/authService';
import { UNAUTHORIZED_EVENT } from '../services/apiClient';
import logger from '../utils/logger';

// Auth Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  // Une seule instance pour toute la vie du composant (et pas une par rendu)
  const authServiceRef = useRef(null);
  if (!authServiceRef.current) authServiceRef.current = new AuthService();
  const authService = authServiceRef.current;

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const currentUser = authService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    setLoading(false);
  }, [authService]);

  const login = useCallback(
    async (email, password, rememberMe = true) => {
      try {
        const result = await authService.login(email, password, rememberMe);
        if (result.success) {
          setUser(result.user);
        }
        return result;
      } catch (error) {
        logger.error('Login error:', error);
        return { success: false, error: 'Erreur de connexion' };
      }
    },
    [authService]
  );

  const register = useCallback(
    async (email, password, acceptTerms = false) => {
      try {
        const result = await authService.register(email, password, acceptTerms);
        if (result.success) {
          setUser(result.user);
        }
        return result;
      } catch (error) {
        logger.error('Register error:', error);
        return { success: false, error: 'Erreur d\'inscription' };
      }
    },
    [authService]
  );

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, [authService]);

  // Session expirée : n'importe quel appel au backend a reçu un 401
  useEffect(() => {
    const onUnauthorized = () => {
      if (!authService.getCurrentUser()) return;
      authService.logout();
      setUser(null);
      toast.error('Ta session a expiré. Reconnecte-toi pour continuer.', { id: 'session-expired' });
    };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [authService]);

  // Fusionne des champs (nom, biographie, photo) dans l'utilisateur courant et dans le stockage local
  const updateUser = useCallback((patch) => {
    setUser((prev) => {
      if (!prev) return prev;
      const next = { ...prev, ...patch };
      try {
        localStorage.setItem('user', JSON.stringify(next));
      } catch (_) {
        /* stockage plein : l'état en mémoire reste à jour */
      }
      return next;
    });
  }, []);

  // Valeur stable : les consommateurs ne se re-rendent que si l'utilisateur ou le chargement change
  const value = useMemo(
    () => ({ user, login, register, logout, updateUser, loading }),
    [user, login, register, logout, updateUser, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
