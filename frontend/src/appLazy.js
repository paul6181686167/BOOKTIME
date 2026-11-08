import { lazy } from 'react';

// Pages de routes et modales : chargées à la demande pour ne pas alourdir le
// premier rendu. Les deux modales les plus ouvertes sont préchargées en temps mort
// (voir hooks/useIdlePreload) afin que leur ouverture reste instantanée.
export const BookDetailModal = lazy(() => import('./components/BookDetailModal'));
export const AuthorModal = lazy(() => import('./components/AuthorModal'));
export const SeriesDetailModal = lazy(() => import('./components/SeriesDetailModal'));
export const SeriesDetailPage = lazy(() => import('./pages/SeriesDetailPage'));
export const RecommendationPage = lazy(() => import('./components/recommendations/RecommendationPage'));
export const OpenLibraryBookPage = lazy(() => import('./pages/OpenLibraryBookPage'));
export const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
export const ExportImportPage = lazy(() => import('./components/exportimport/ExportImportPage'));
export const UpcomingPage = lazy(() => import('./pages/UpcomingPage'));
export const ProfilePage = lazy(() => import('./pages/ProfilePage'));
export const AdminPage = lazy(() => import('./pages/AdminPage'));
export const TermsPage = lazy(() => import('./pages/TermsPage'));
export const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));
export const ProfileModal = lazy(() => import('./components/common/ProfileModal'));
export const ExportImportModal = lazy(() => import('./components/export-import/ExportImportModal'));
export const UpcomingPanel = lazy(() => import('./components/UpcomingPanel'));
export const SocialModal = lazy(() => import('./components/social/SocialModal'));
export const FriendsModal = lazy(() => import('./components/friends/FriendsModal'));
export const AdvancedRecommendationsModal = lazy(() =>
  import('./components/advanced-recommendations/AdvancedRecommendationsModal')
);
export const IntegrationsModal = lazy(() => import('./components/integrations/IntegrationsModal'));
export const IsbnScannerModal = lazy(() => import('./components/common/IsbnScannerModal'));
