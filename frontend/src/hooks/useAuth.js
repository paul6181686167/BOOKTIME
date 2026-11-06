import { createContext, useState, useContext, useEffect } from 'react';
import AuthService from '../services/authService';

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
  const authService = new AuthService();

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const currentUser = authService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
    }
    setLoading(false);
  }, []);

  const login = async (email, password, rememberMe = true) => {
    try {
      const result = await authService.login(email, password, rememberMe);
      if (result.success) {
        setUser(result.user);
        return result;
      }
      return result;
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Erreur de connexion' };
    }
  };

  const register = async (email, password) => {
    try {
      const result = await authService.register(email, password);
      if (result.success) {
        setUser(result.user);
        return result;
      }
      return result;
    } catch (error) {
      console.error('Register error:', error);
      return { success: false, error: 'Erreur d\'inscription' };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  // Fusionne des champs (nom, biographie, photo) dans l'utilisateur courant et dans le stockage local
  const updateUser = (patch) => {
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
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, updateUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
