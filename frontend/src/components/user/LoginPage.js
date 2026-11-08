import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import { API_BASE_URL } from '../../config/environment';
import { wakeBackend, isBackendRemote, WAKE_HINT_DELAY_MS } from '../../utils/backendWake';
import TermsContent from '../legal/TermsContent';
import logger from '../../utils/logger';
import ModalOverlay, { MODAL_Z } from '../common/ModalOverlay';

// Login Page Component
function LoginPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [rememberMe, setRememberMe] = useState(true);
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);
  const [forgotResetUrl, setForgotResetUrl] = useState('');
  const [forgotDelivery, setForgotDelivery] = useState('');
  const loadingStartRef = useRef(null);

  const [backendReady, setBackendReady] = useState(!isBackendRemote());
  const [showWakeHint, setShowWakeHint] = useState(false);

  // Réveil Render : on n'affiche le message que si le ping traîne vraiment.
  useEffect(() => {
    let cancelled = false;
    const toastId = isBackendRemote() ? 'backend-wake' : null;
    const hintTimer = isBackendRemote()
      ? setTimeout(() => {
          if (cancelled) return;
          setShowWakeHint(true);
          if (toastId) {
            toast.loading('Le serveur démarre. S’il a dormi, compte 15 à 60 secondes.', {
              id: toastId,
            });
          }
        }, WAKE_HINT_DELAY_MS)
      : null;
    wakeBackend({
      onProgress: (msg) => {
        if (toastId) toast.loading(msg, { id: toastId });
      },
    }).then((result) => {
      if (cancelled) return;
      setBackendReady(result.ok);
      setShowWakeHint(false);
      if (!toastId) return;
      if (result.ok) {
        if (result.attempts > 1) {
          toast.success('Serveur prêt', { id: toastId, duration: 2500 });
        } else {
          toast.dismiss(toastId);
        }
      } else {
        toast.error(
          'Serveur distant lent ou indisponible. Lance le backend en local (voir TESTER_LOCAL.md).',
          { id: toastId, duration: 8000 }
        );
      }
    });
    return () => {
      cancelled = true;
      if (hintTimer) clearTimeout(hintTimer);
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
    if (!isLogin && !acceptTerms) {
      toast.error("Accepte les conditions générales d'utilisation pour créer un compte");
      return;
    }

    setLoading(true);
    try {
      let result;
      if (isLogin) {
        result = await login(formData.email, formData.password, rememberMe);
      } else {
        result = await register(formData.email, formData.password, acceptTerms);
      }

      logger.debug(' Résultat reçu:', result);

      if (result.success) {
        toast.success(isLogin ? 'Connexion réussie !' : 'Inscription réussie !');
        logger.debug(' Succès - rechargement dans 1s');
        // Force immediate navigation after successful auth
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        logger.debug(' Erreur:', result.error);
        toast.error(result.error || 'Une erreur est survenue');
      }
    } catch (error) {
      logger.error('Exception:', error);
      toast.error('Erreur de connexion');
    } finally {
      loadingStartRef.current = null;
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const openForgotModal = () => {
    setShowForgot(true);
    setForgotSent(false);
    setForgotResetUrl('');
    setForgotDelivery('');
    setForgotEmail(formData.email || '');
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail) return;
    setForgotLoading(true);
    setForgotResetUrl('');
    setForgotDelivery('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      });
      const d = await res.json().catch(() => ({}));
      if (res.ok) {
        setForgotDelivery(d.delivery || '');
        setForgotResetUrl(d.reset_url || '');
        setForgotSent(true);
      } else {
        const raw = typeof d.detail === 'string' ? d.detail : '';
        toast.error(raw || "Impossible d'envoyer l'e-mail de réinitialisation.");
      }
    } catch {
      toast.error('Erreur réseau. Réessaie dans un instant.');
    } finally {
      setForgotLoading(false);
    }
  };

  const copyResetLink = async () => {
    if (!forgotResetUrl) return;
    try {
      await navigator.clipboard.writeText(forgotResetUrl);
      toast.success('Lien copié');
    } catch {
      toast.error('Copie impossible — sélectionne le lien manuellement');
    }
  };

  return (
    <main className="min-h-screen min-h-dvh bg-honeycomb flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              B
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            BookTime
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Votre bibliothèque personnelle
          </p>
          {showWakeHint && !backendReady && isBackendRemote() && (
            <p role="status" className="text-sm text-gray-700 dark:text-gray-300 mt-2">
              Le serveur démarre — s&apos;il a dormi, compte 15 à 60 secondes.
            </p>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-2xl rounded-2xl p-8 space-y-6 border dark:border-gray-700">
          <div className="flex mb-6 bg-gray-100 dark:bg-gray-700 rounded-lg p-1" role="tablist" aria-label="Connexion ou inscription">
            <button
              type="button"
              role="tab"
              aria-selected={isLogin}
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-3 px-4 min-h-11 rounded-md text-sm font-medium transition-all ${
                isLogin ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-400 shadow-sm' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              Connexion
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={!isLogin}
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-3 px-4 min-h-11 rounded-md text-sm font-medium transition-all ${
                !isLogin ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-400 shadow-sm' : 'text-gray-700 dark:text-gray-300'
              }`}
            >
              Inscription
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email
              </label>
              <input id="login-email"
                type="email"
                name="email"
                autoComplete="email"
                inputMode="email"
                autoCapitalize="none"
                spellCheck={false}
                value={formData.email}
                onChange={handleInputChange}
                placeholder="vous@exemple.com"
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            <div>
              <label htmlFor="login-password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Mot de passe
              </label>
              <div className="relative">
                <input id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  value={formData.password}
                  onChange={handleInputChange}
                  placeholder={isLogin ? '' : 'Minimum 8 caractères'}
                  minLength={isLogin ? undefined : 8}
                  className="w-full pl-4 pr-14 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                  aria-pressed={showPassword}
                  className="absolute inset-y-0 right-0 w-12 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24" aria-hidden="true">
                    {showPassword ? (
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.22A10.5 10.5 0 001.93 12c1.4 3.9 5.2 6.75 10.07 6.75 1.9 0 3.6-.45 5.1-1.2M6.2 6.2A10.7 10.7 0 0112 5.25c4.87 0 8.67 2.85 10.07 6.75a10.5 10.5 0 01-4.2 5.2M3 3l18 18M9.9 9.9a3 3 0 004.2 4.2" />
                    ) : (
                      <>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M1.93 12C3.33 8.1 7.13 5.25 12 5.25S20.67 8.1 22.07 12c-1.4 3.9-5.2 6.75-10.07 6.75S3.33 15.9 1.93 12z" />
                        <circle cx="12" cy="12" r="3" />
                      </>
                    )}
                  </svg>
                </button>
              </div>
            </div>

            {!isLogin && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                   Mot de passe minimum 8 caractères.
                </p>
              </div>
            )}

            {!isLogin && (
              <label className="flex items-start gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={acceptTerms}
                  onChange={(e) => setAcceptTerms(e.target.checked)}
                  className="mt-0.5 w-5 h-5 rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  J'ai lu et j'accepte les{' '}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      setShowTerms(true);
                    }}
                    className="text-green-600 dark:text-green-400 underline"
                  >
                    conditions générales d'utilisation
                  </button>
                  .
                </span>
              </label>
            )}

            {isLogin && (
              <label className="flex items-center gap-2 py-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-5 h-5 rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Rester connecté
                </span>
              </label>
            )}

            <button
              type="submit"
              disabled={loading || !formData.email || !formData.password || (!isLogin && !acceptTerms)}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'Créer un compte')}
            </button>

            {isLogin && (
              <button
                type="button"
                onClick={openForgotModal}
                className="w-full min-h-11 py-3 text-sm text-green-700 dark:text-green-300 hover:underline text-center mt-1"
              >
                Mot de passe oublié ?
              </button>
            )}
          </form>
        </div>

        {isLogin && (
          <p className="text-center text-sm text-gray-700 dark:text-gray-300">
            <button
              type="button"
              onClick={() => setShowTerms(true)}
              className="min-h-11 px-3 underline hover:text-gray-900 dark:hover:text-white"
            >
              Conditions générales d'utilisation
            </button>
          </p>
        )}
      </div>

      {showTerms && (
        <ModalOverlay
          onClose={() => setShowTerms(false)}
          zIndex={MODAL_Z.dialog}
          ariaLabel="Conditions générales d'utilisation"
          className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center p-0 sm:p-4"
        >
          <div className="bg-white dark:bg-gray-800 sm:rounded-2xl rounded-t-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] max-h-[90dvh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 dark:border-gray-700">
              <h3 className="text-base font-bold text-gray-900 dark:text-white">
                Conditions générales d'utilisation
              </h3>
              <button
                type="button"
                onClick={() => setShowTerms(false)}
                aria-label="Fermer"
                className="p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="overflow-y-auto px-5 py-4">
              <TermsContent />
            </div>
            <div className="px-5 py-3 border-t border-gray-100 dark:border-gray-700">
              {!isLogin && !acceptTerms ? (
                <button
                  type="button"
                  onClick={() => {
                    setAcceptTerms(true);
                    setShowTerms(false);
                  }}
                  className="w-full bg-green-600 hover:bg-green-700 text-white py-2.5 rounded-lg text-sm font-medium"
                >
                  J'accepte
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowTerms(false)}
                  className="w-full bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 py-2.5 rounded-lg text-sm font-medium"
                >
                  Fermer
                </button>
              )}
            </div>
          </div>
        </ModalOverlay>
      )}

      {/* Modal mot de passe oublié */}
      {showForgot && (
        <ModalOverlay
          onClose={() => setShowForgot(false)}
          zIndex={MODAL_Z.dialog}
          ariaLabel="Mot de passe oublié"
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4"
        >
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 w-full max-w-md">
            {forgotSent ? (
              <div className="text-center">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {forgotDelivery === 'email'
                    ? 'Email envoyé'
                    : forgotResetUrl
                      ? 'Lien prêt'
                      : 'Demande enregistrée'}
                </h3>
                {forgotDelivery === 'email' ? (
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Si <strong>{forgotEmail}</strong> est associé à un compte, tu recevras un lien sous peu (valable 1 heure).
                  </p>
                ) : forgotResetUrl ? (
                  <div className="text-left mb-6 space-y-3">
                    <p className="text-gray-600 dark:text-gray-400 text-sm">
                      Clique sur le lien ci-dessous pour choisir un nouveau mot de passe (valable 1 heure).
                    </p>
                    <a
                      href={forgotResetUrl}
                      className="block break-all text-sm text-green-700 dark:text-green-400 underline"
                    >
                      {forgotResetUrl}
                    </a>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <a
                        href={forgotResetUrl}
                        className="flex-1 text-center bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 font-medium"
                      >
                        Ouvrir le lien
                      </a>
                      <button
                        type="button"
                        onClick={copyResetLink}
                        className="flex-1 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 py-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 font-medium"
                      >
                        Copier
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Si <strong>{forgotEmail}</strong> est associé à un compte, un lien a été préparé.
                  </p>
                )}
                <button
                  type="button"
                  onClick={() => setShowForgot(false)}
                  className="w-full text-gray-500 dark:text-gray-400 py-2 text-sm hover:underline"
                >
                  Fermer
                </button>
              </div>
            ) : (
              <>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Mot de passe oublié</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6 text-sm">
                  Saisis ton adresse email. Tu obtiendras un lien pour réinitialiser ton mot de passe (valable 1 heure).
                </p>
                <form onSubmit={handleForgotPassword} className="space-y-4">
                  <input aria-label="Adresse e-mail" autoComplete="email" inputMode="email"
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
                    {forgotLoading ? 'Préparation…' : 'Obtenir le lien'}
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
        </ModalOverlay>
      )}
    </main>
  );
}

export default LoginPage;
