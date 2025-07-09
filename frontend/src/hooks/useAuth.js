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

  const login = async (firstName, lastName) => {
    try {
      const result = await authService.login(firstName, lastName);
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

  const register = async (firstName, lastName) => {
    try {
      const result = await authService.register(firstName, lastName);
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

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
