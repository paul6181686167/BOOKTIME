import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';

// Login Page Component
function LoginPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const loadingStartRef = useRef(null);

  // Réveil automatique du backend Render (free tier s'endort après 15 min)
  useEffect(() => {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    fetch(`${backendUrl}/health`, { method: 'GET', signal: AbortSignal.timeout(30000) })
      .then(r => r.json())
      .then(d => {
        if (d.database !== 'connected') {
          toast('Connexion en cours…', { icon: '⏳', duration: 4000 });
        }
      })
      .catch(() => {
        // Render en cours de réveil — on réessaie silencieusement dans 10s
        setTimeout(() => {
          fetch(`${backendUrl}/health`, { method: 'GET', signal: AbortSignal.timeout(30000) }).catch(() => {});
        }, 10000);
      });
  }, []);

  useEffect(() => {
    if (!loading) return;
    loadingStartRef.current = Date.now();
    const id = setInterval(() => {
      if (loadingStartRef.current && Date.now() - loadingStartRef.current > 30000) {
        setLoading(false);
        toast.error('Le serveur met du temps à démarrer. Réessaie dans 30 secondes.');
      }
    }, 1000);
    return () => clearInterval(id);
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.password) return;

    setLoading(true);
    try {
      let result;
      if (isLogin) {
        result = await login(formData.email, formData.password);
      } else {
        result = await register(formData.email, formData.password);
      }

      console.log('📡 Résultat reçu:', result);

      if (result.success) {
        toast.success(isLogin ? 'Connexion réussie !' : 'Inscription réussie !');
        console.log('✅ Succès - rechargement dans 1s');
        // Force immediate navigation after successful auth
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        console.log('❌ Erreur:', result.error);
        toast.error(result.error || 'Une erreur est survenue');
      }
    } catch (error) {
      console.error('Exception:', error);
      toast.error('Erreur de connexion');
    } finally {
      loadingStartRef.current = null;
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              🐝
            </div>
          </div>
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            BookTime
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Votre bibliothèque personnelle
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-2xl rounded-2xl p-8 space-y-6 border dark:border-gray-700">
          <div className="flex mb-6 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                isLogin ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Connexion
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                !isLogin ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Inscription
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="vous@exemple.com"
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Mot de passe
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder={isLogin ? '' : 'Minimum 6 caractères'}
                minLength={isLogin ? undefined : 6}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>

            {!isLogin && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  💡 Mot de passe minimum 6 caractères.
                </p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (!formData.email || !formData.password)}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'Créer un compte')}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
