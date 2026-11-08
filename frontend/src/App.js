// Imports
import React, { useMemo, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Context imports
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './hooks/useAuth';

// Component imports
import LoginPage from './components/user/LoginPage';
import NativeAppShell from './components/native/NativeAppShell';


// PHASE 2.4 - Monitoring et Analytics
import ErrorBoundary from './components/monitoring/ErrorBoundary';
// Service imports
// Hook imports
// PHASE C.1 - Hook unifié pour rafraîchissement optimisé


// Utils imports
import { pathToPrimaryTab } from './utils/primaryTabs';


// Search components imports (Phase 1.1 - Step 3)

// Series components imports (Phase 1.1 - Step 4)

// Books components imports (Phase 1.1 - Step 5 & 6)
import UpdateBanner from './components/UpdateBanner';
import ConfirmHost from './components/common/ConfirmHost';
import PrimaryTabsLayout from './components/navigation/PrimaryTabsLayout';
import FriendInvitePage from './pages/FriendInvitePage';
import useCollectionsSync from './hooks/useCollectionsSync';
import useOfflineWriteQueue from './hooks/useOfflineWriteQueue';
import OfflineBanner from './components/OfflineBanner';
import SlowBackendBanner from './components/common/SlowBackendBanner';

import './App.css';
import './styles/optimized.css';
import RouteFallback from './components/common/RouteFallback';
import { SeriesDetailPage, RecommendationPage, OpenLibraryBookPage, ResetPasswordPage, ExportImportPage, UpcomingPage, ProfilePage, AdminPage, TermsPage, NotFoundPage } from './appLazy';
import MainApp from './pages/MainApp';

// Main App Content — onglets primaires = carrousel de diapositives (mobile)
function AppContent() {
  const { pathname } = useLocation();
  const primarySlides = useMemo(
    () => ({
      home: <MainApp />,
      upcoming: (
        <Suspense fallback={<RouteFallback />}>
          <UpcomingPage />
        </Suspense>
      ),
      recommendations: (
        <Suspense fallback={<RouteFallback />}>
          <RecommendationPage />
        </Suspense>
      ),
      profile: (
        <Suspense fallback={<RouteFallback />}>
          <ProfilePage />
        </Suspense>
      ),
    }),
    []
  );

  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/series/:seriesName" element={<SeriesDetailPage />} />
        <Route path="/export-import" element={<ExportImportPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/ami/:code" element={<FriendInvitePage />} />
        <Route path="/catalogue/*" element={<OpenLibraryBookPage />} />
        <Route
          path="/*"
          element={
            // Adresse inconnue : page 404 plutôt que l'accueil affiché sans explication
            pathToPrimaryTab(pathname) === null ? (
              <NotFoundPage />
            ) : (
              <PrimaryTabsLayout slides={primarySlides} />
            )
          }
        />
      </Routes>
    </Suspense>
  );
}

// Main App Component
function App() {
  return (
    <Router future={{ 
      v7_startTransition: true,
      v7_relativeSplatPath: true 
    }}>
      <ThemeProvider>
        <AuthProvider>
          <ErrorBoundary>
            <NativeAppShell />
            <UpdateBanner />
            <OfflineBanner />
            <SlowBackendBanner />
            <ConfirmHost />
            <Suspense fallback={<RouteFallback />}>
              <Routes>
                {/* Route publique */}
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/cgu" element={<TermsPage />} />
                {/* Toutes les autres routes passent par AppWithAuth (vérification login) */}
                <Route path="/*" element={<AppWithAuth />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

// App with Auth Wrapper
function AppWithAuth() {
  const { user, loading } = useAuth();
  useCollectionsSync(user?.id);
  useOfflineWriteQueue(user?.id);

  if (loading) {
    return (
      <div className="min-h-screen min-h-dvh flex items-center justify-center bg-honeycomb">
        <div role="status" aria-label="Chargement en cours" className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-700 dark:border-green-400"></div>
      </div>
    );
  }

  if (user) return <AppContent />;
  // LoginPage hors de AppContent : on monte ici un Toaster dédié, sinon les
  // messages (erreur de connexion, etc.) ne s'afficheraient jamais.
  return (
    <>
      <LoginPage />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { marginBottom: 'calc(5.5rem + env(safe-area-inset-bottom))' },
        }}
        containerStyle={{ bottom: 0 }}
      />
    </>
  );
}

export default App;
