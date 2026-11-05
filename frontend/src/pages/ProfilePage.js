import React, { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import ProfileModal from '../components/common/ProfileModal';
import useUnifiedContent from '../hooks/useUnifiedContent';
import BookActions from '../components/books/BookActions';

const BookDetailModal = lazy(() => import('../components/BookDetailModal'));
const SeriesDetailModal = lazy(() => import('../components/SeriesDetailModal'));
const AuthorModal = lazy(() => import('../components/AuthorModal'));

/** Page pleine Profil (mobile / route /profile). */
export default function ProfilePage() {
  const navigate = useNavigate();
  const unified = useUnifiedContent();
  const [selectedBook, setSelectedBook] = useState(null);
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [selectedAuthor, setSelectedAuthor] = useState(null);

  return (
    <>
      <ProfileModal
        variant="page"
        isOpen
        onClose={() => navigate('/')}
        onAuthorClick={(name) => setSelectedAuthor(name)}
        libraryBooks={unified.books || []}
        librarySeries={unified.userSeriesLibrary || []}
        onOpenBook={(bookId) => {
          const book = (unified.books || []).find((b) => b.id === bookId);
          if (book) setSelectedBook(book);
        }}
        onOpenSeries={(seriesId) => {
          const series = (unified.userSeriesLibrary || []).find((s) => s.id === seriesId);
          if (series) {
            setSelectedSeries({
              ...series,
              name: series.series_name || series.name,
              isOwnedSeries: true,
              isLibrarySeries: true,
            });
          }
        }}
        onAddFromOpenLibrary={async (book) => {
          try {
            await BookActions.addBook(book);
            await unified.refreshAfterAdd?.('books', {
              expectNewItem: true,
              maxRetries: 2,
              retryDelay: 800,
            });
            toast.success('Livre ajouté');
          } catch (err) {
            toast.error(err?.message || "Erreur lors de l'ajout");
          }
        }}
      />

      <Suspense fallback={null}>
        {selectedBook && (
          <BookDetailModal
            book={selectedBook}
            onClose={() => setSelectedBook(null)}
            onUpdate={() => unified.loadUnifiedContent?.({ forceRefresh: true, silent: true })}
            onDelete={async () => {
              setSelectedBook(null);
              await unified.loadUnifiedContent?.({ forceRefresh: true, silent: true });
            }}
            onAddFromOpenLibrary={async (book) => {
              await BookActions.addBook(book);
              await unified.refreshAfterAdd?.('books');
            }}
            onAuthorClick={(name) => setSelectedAuthor(name)}
          />
        )}
        {selectedSeries && (
          <SeriesDetailModal
            series={selectedSeries}
            isOpen
            onClose={() => setSelectedSeries(null)}
            onUpdate={() => unified.loadUnifiedContent?.({ forceRefresh: true })}
            onDelete={() => {
              setSelectedSeries(null);
              unified.loadUnifiedContent?.({ forceRefresh: true });
            }}
            onAuthorClick={(name) => setSelectedAuthor(name)}
            userSeriesLibrary={unified.userSeriesLibrary || []}
          />
        )}
        {selectedAuthor && (
          <AuthorModal
            author={selectedAuthor}
            isOpen
            onClose={() => setSelectedAuthor(null)}
            userBooks={unified.books || []}
            onAddBook={async (bookData) => {
              await BookActions.addBook(bookData);
              await unified.refreshAfterAdd?.('books');
            }}
            onOpenSeries={(series) => {
              setSelectedAuthor(null);
              setSelectedSeries(series);
            }}
          />
        )}
      </Suspense>
    </>
  );
}
