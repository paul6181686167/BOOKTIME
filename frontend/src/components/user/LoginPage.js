import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import { API_BASE_URL } from '../../config/environment';
import { wakeBackend, isBackendRemote } from '../../utils/backendWake';

// Login Page Component
function LoginPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [rememberMe, setRememberMe] = useState(true);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);
  const loadingStartRef = useRef(null);

  const [backendReady, setBackendReady] = useState(!isBackendRemote());

  // Réveil Render (plan gratuit) ou vérif backend local
  useEffect(() => {
    let cancelled = false;
    const toastId = isBackendRemote() ? 'backend-wake' : null;
    if (toastId) {
      toast.loading('Réveil du serveur (30–60 s la 1ère fois)…', { id: toastId });
    }
    wakeBackend({
      onProgress: (msg) => {
        if (toastId) toast.loading(msg, { id: toastId });
      },
    }).then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setBackendReady(true);
        if (toastId) toast.success('Serveur prêt', { id: toastId, duration: 2500 });
      } else if (toastId) {
        toast.error(
          'Serveur distant lent ou indisponible. Lance le backend en local (voir TESTER_LOCAL.md).',
          { id: toastId, duration: 8000 }
        );
      }
    });
    return () => {
      cancelled = true;
    };
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
        result = await login(formData.email, formData.password, rememberMe);
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
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail) return;
    setForgotLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      });
      if (res.ok) {
        setForgotSent(true);
      } else {
        const d = await res.json();
        toast.error(d.detail || 'Erreur lors de l\'envoi');
      }
    } catch {
      toast.error('Erreur réseau. Réessaie dans un instant.');
    } finally {
      setForgotLoading(false);
    }
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
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 font-mono">
            API : {API_BASE_URL}
            {!backendReady && isBackendRemote() ? ' · réveil…' : ''}
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

            {isLogin && (
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Rester connecté
                </span>
              </label>
            )}

            <button
              type="submit"
              disabled={loading || (!formData.email || !formData.password)}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'Créer un compte')}
            </button>

            {isLogin && (
              <button
                type="button"
                onClick={() => { setShowForgot(true); setForgotSent(false); setForgotEmail(''); }}
                className="w-full text-sm text-green-600 dark:text-green-400 hover:underline text-center mt-1"
              >
                Mot de passe oublié ?
              </button>
            )}
          </form>
        </div>
      </div>

      {/* Modal mot de passe oublié */}
      {showForgot && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 w-full max-w-md">
            {forgotSent ? (
              <div className="text-center">
                <div className="text-4xl mb-4">📧</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Email envoyé !</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Si <strong>{forgotEmail}</strong> est associé à un compte, tu recevras un lien de réinitialisation dans quelques minutes.
                </p>
                <button
                  onClick={() => setShowForgot(false)}
                  className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-medium"
                >
                  Fermer
                </button>
              </div>
            ) : (
              <>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Mot de passe oublié</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
                  Saisis ton adresse email. Tu recevras un lien pour réinitialiser ton mot de passe (valable 1 heure).
                </p>
                <form onSubmit={handleForgotPassword} className="space-y-4">
                  <input
                    type="email"
                    value={forgotEmail}
                    onChange={e => setForgotEmail(e.target.value)}
                    placeholder="vous@exemple.com"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    required
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={forgotLoading || !forgotEmail}
                    className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-medium disabled:opacity-50"
                  >
                    {forgotLoading ? 'Envoi en cours…' : 'Envoyer le lien'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForgot(false)}
                    className="w-full text-gray-500 dark:text-gray-400 py-2 text-sm hover:underline"
                  >
                    Annuler
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default LoginPage;
