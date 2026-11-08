import React from 'react';
import ReactDOM from 'react-dom/client';
import '@fontsource-variable/inter/index.css';
import './index.css';
import App from './App';
import ErrorBoundary from './components/monitoring/ErrorBoundary';
import { registerServiceWorker } from './utils/registerServiceWorker';
import { installUnauthorizedWatcher } from './services/apiClient';

// Les journaux sont gérés par utils/logger (silencieux en production, erreurs conservées)

// Repère les 401 du backend (session expirée) pour déconnecter proprement
installUnauthorizedWatcher();

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

registerServiceWorker();