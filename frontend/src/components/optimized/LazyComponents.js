// Phase 2.3 - Composants lazy loading pour optimiser le bundle
import React, { lazy, Suspense } from 'react';

// Composant de loading générique
const LoadingSpinner = ({ message = "Chargement..." }) => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-green-500 mr-3"></div>
    <span className="text-gray-600 dark:text-gray-400">{message}</span>
  </div>
);

// Lazy loading des composants lourds
export const LazyBookDetailModal = lazy(() => import('../BookDetailModal'));
export const LazySeriesDetailModal = lazy(() => import('../SeriesDetailModal'));
export const LazySeriesDetailPage = lazy(() => import('../../pages/SeriesDetailPage'));
export const LazyProfileModal = lazy(() => import('../common/ProfileModal'));
export const LazyPaginatedBookGrid = lazy(() => import('../books/PaginatedBookGrid'));

// Composants wrapper avec Suspense
export const BookDetailModal = (props) => (
  <Suspense fallback={<LoadingSpinner message="Chargement des détails du livre..." />}>
    <LazyBookDetailModal {...props} />
  </Suspense>
);

export const SeriesDetailModal = (props) => (
  <Suspense fallback={<LoadingSpinner message="Chargement des détails de la série..." />}>
    <LazySeriesDetailModal {...props} />
  </Suspense>
);

export const SeriesDetailPage = (props) => (
  <Suspense fallback={<LoadingSpinner message="Chargement de la page série..." />}>
    <LazySeriesDetailPage {...props} />
  </Suspense>
);

export const ProfileModal = (props) => (
  <Suspense fallback={<LoadingSpinner message="Chargement du profil..." />}>
    <LazyProfileModal {...props} />
  </Suspense>
);

export const PaginatedBookGrid = (props) => (
  <Suspense fallback={<LoadingSpinner message="Chargement de la grille..." />}>
    <LazyPaginatedBookGrid {...props} />
  </Suspense>
);

// Hook pour précharger les composants
export const usePreloadComponents = () => {
  const preloadBookDetail = () => {
    import('../BookDetailModal');
  };

  const preloadSeriesDetail = () => {
    import('../SeriesDetailModal');
  };

  const preloadProfile = () => {
    import('../common/ProfileModal');
  };

  const preloadPaginatedGrid = () => {
    import('../books/PaginatedBookGrid');
  };

  return {
    preloadBookDetail,
    preloadSeriesDetail,
    preloadProfile,
    preloadPaginatedGrid
  };
};

// Composant pour précharger les ressources critiques
export const ResourcePreloader = () => {
  const { preloadBookDetail, preloadSeriesDetail, preloadProfile } = usePreloadComponents();

  React.useEffect(() => {
    // Précharger les composants critiques après un délai
    const timer = setTimeout(() => {
      preloadBookDetail();
      preloadSeriesDetail();
      preloadProfile();
    }, 2000);

    return () => clearTimeout(timer);
  }, [preloadBookDetail, preloadSeriesDetail, preloadProfile]);

  return null;
};

export default {
  BookDetailModal,
  SeriesDetailModal,
  SeriesDetailPage,
  ProfileModal,
  PaginatedBookGrid,
  ResourcePreloader
};