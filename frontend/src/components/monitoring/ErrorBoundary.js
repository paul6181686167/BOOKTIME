import React from 'react';
import { toast } from 'react-hot-toast';

/**
 * PHASE 2.4 - MONITORING ET ANALYTICS
 * Composant Error Boundary pour gestion d'erreurs robuste
 * Capture les erreurs JavaScript et affiche une interface de secours
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Met à jour l'état pour afficher l'UI de secours au prochain rendu
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Génère un ID unique pour l'erreur
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    console.group('🚨 ERROR BOUNDARY - Erreur capturée');
    console.error('Error ID:', errorId);
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.groupEnd();

    // Sauvegarde l'erreur dans l'état
    this.setState({
      error: error,
      errorInfo: errorInfo,
      errorId: errorId
    });

    // Log l'erreur pour monitoring
    this.logError(error, errorInfo, errorId);

    // Notification utilisateur
    toast.error(`Une erreur est survenue (ID: ${errorId})`, {
      duration: 5000,
      style: {
        background: '#ef4444',
        color: 'white',
      },
    });
  }

  logError = (error, errorInfo, errorId) => {
    // Prépare les données d'erreur pour envoi au backend
    const errorData = {
      errorId: errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: localStorage.getItem('userId') || 'anonymous'
    };

    // En production, envoyer au service de monitoring
    if (process.env.NODE_ENV === 'production') {
      // Exemple : Sentry, LogRocket, ou service custom
      fetch('/api/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(errorData)
      }).catch(err => console.error('Failed to log error:', err));
    }

    // Log local pour développement
    localStorage.setItem(`error_${errorId}`, JSON.stringify(errorData));
  };

  handleReload = () => {
    window.location.reload();
  };

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null 
    });
  };

  render() {
    if (this.state.hasError) {
      const { error, errorId } = this.state;
      
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            {/* Icône d'erreur */}
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
            </div>

            {/* Titre */}
            <h1 className="text-xl font-bold text-gray-900 dark:text-white text-center mb-2">
              Oups ! Une erreur est survenue
            </h1>

            {/* Description */}
            <p className="text-gray-600 dark:text-gray-400 text-center mb-4">
              BookTime a rencontré un problème inattendu. Nos équipes ont été notifiées.
            </p>

            {/* Détails de l'erreur (mode développement) */}
            {process.env.NODE_ENV === 'development' && error && (
              <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 mb-4">
                <p className="text-xs font-mono text-red-600 dark:text-red-400 break-all">
                  {error.message}
                </p>
                {errorId && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    ID: {errorId}
                  </p>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3">
              <button
                onClick={this.handleRetry}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                Réessayer
              </button>
              <button
                onClick={this.handleReload}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
              >
                Recharger
              </button>
            </div>

            {/* Contact support */}
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-4">
              Problème persistant ? Contactez-nous avec l'ID : {errorId}
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;