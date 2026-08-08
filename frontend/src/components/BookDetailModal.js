import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { XMarkIcon, StarIcon, TrashIcon, ArrowPathIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import LanguageSelector from './LanguageSelector';
import { API_BASE_URL } from '../config/environment';
import { displayBookTitleFrFirst } from '../utils/openLibraryBookDisplay';
import { displaySynopsis as formatSynopsis, isUsableSynopsis, sanitizeSynopsis } from '../utils/synopsisQuality';
import AddToCollectionMenu from './common/AddToCollectionMenu';
import CommunityReviews from './common/CommunityReviews';
import confetti from 'canvas-confetti';

// Déclenche les confettis de célébration
const launchConfetti = () => {
  const count = 180;
  const defaults = { origin: { y: 0.65 }, zIndex: 9999 };
  const fire = (particleRatio, opts) => {
    confetti({ ...defaults, ...opts, particleCount: Math.floor(count * particleRatio) });
  };
  fire(0.25, { spread: 26, startVelocity: 55 });
  fire(0.2,  { spread: 60 });
  fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
  fire(0.1,  { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
  fire(0.1,  { spread: 120, startVelocity: 45 });
};

const BookDetailModal = ({ book, onClose, onUpdate, onDelete, onAddFromOpenLibrary, onAuthorClick }) => {
  const navigate = useNavigate();
  const titleMain = useMemo(() => displayBookTitleFrFirst(book), [book]);
  const [isEditing, setIsEditing] = useState(false);
  const [bouncing, setBouncing] = useState(null); // id du bouton en train de bouncer
  const [olDetails, setOlDetails] = useState(null); // détails enrichis depuis OL
  const [olLoading, setOlLoading] = useState(false);
  const [editData, setEditData] = useState({
    status: book.status,
    current_page: book.current_page || 0,
    rating: book.rating || 0,
    review: book.review || '',
    original_language: book.original_language || 'français',
    available_translations: book.available_translations || [],
    reading_language: book.reading_language || 'français',
    saga: book.saga || '',
    volume_number: book.volume_number || '',
  });
  const [pageInput, setPageInput] = useState(book.current_page || 0);
  const [resolvedTotalPages, setResolvedTotalPages] = useState(
    book.total_pages > 0 ? book.total_pages : null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [addDone, setAddDone] = useState(false);
  const [publishingReview, setPublishingReview] = useState(false);
  const [communityRefreshKey, setCommunityRefreshKey] = useState(0);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [showCollectionMenu, setShowCollectionMenu] = useState(false);
  const pageInputRef = useRef(null);
  const pagesFetchDoneRef = useRef(null);
  const metaReqIdRef = useRef(0);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const totalPages = resolvedTotalPages || book.total_pages || 0;
  const displaySynopsis =
    formatSynopsis(olDetails?.description) || formatSynopsis(book.description) || '';

  useEffect(() => {
    setEditData({
      status: book.status,
      current_page: book.current_page || 0,
      rating: book.rating || 0,
      review: book.review || '',
      original_language: book.original_language || 'français',
      available_translations: book.available_translations || [],
      reading_language: book.reading_language || 'français',
      saga: book.saga || '',
      volume_number: book.volume_number || '',
    });
    setPageInput(book.current_page || 0);
    setResolvedTotalPages(book.total_pages > 0 ? book.total_pages : null);
    // Nouveau livre → reset résumé enrichi (sauf si déjà une vraie 4ᵉ en base)
    setOlDetails(
      isUsableSynopsis(book.description)
        ? { description: sanitizeSynopsis(book.description) }
        : null
    );
    pagesFetchDoneRef.current = null;
    metaReqIdRef.current += 1;
  }, [book]);

  // Charger résumé (rapide) + pages poche FR si manquants / faux résumés.
  // Important : ne PAS dépendre de book.description — la persistance du résumé
  // relançait l'effet, annulait le fetch et laissait « Aucun résumé » pour les
  // fiches series_library rétrogradées (ex-vignettes 0/0 tomes).
  useEffect(() => {
    const storedDesc = (book.description || '').trim();
    const needsDesc = !isUsableSynopsis(storedDesc);
    const needsPages = !(book.total_pages > 0);
    if (!needsDesc && !needsPages) {
      return;
    }

    const reqId = ++metaReqIdRef.current;
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const fetchKey = `${book.id}|${book.title}|p=${needsPages}|d=${needsDesc}`;
    if (pagesFetchDoneRef.current === fetchKey) return;

    const isLive = () => metaReqIdRef.current === reqId;

    const applyMeta = async ({ description, pages } = {}) => {
      const patch = {};
      if (needsDesc && isUsableSynopsis(description)) {
        const text = sanitizeSynopsis(description);
        // Afficher tout de suite même si une persistance concurrente tourne
        setOlDetails({ description: text });
        patch.description = text;
      }
      const n = parseInt(pages, 10);
      if (needsPages && n > 0) {
        setResolvedTotalPages(n);
        patch.total_pages = n;
      }
      if (
        Object.keys(patch).length &&
        book.id &&
        !book.isFromOpenLibrary &&
        onUpdateRef.current &&
        isLive()
      ) {
        try {
          await onUpdateRef.current(book.id, patch);
        } catch (_) {
          /* ignore */
        }
      }
    };

    const loadMeta = async () => {
      if (needsDesc) setOlLoading(true);
      let gotDesc = !needsDesc;
      let gotPages = !needsPages;
      const markDescDone = () => {
        if (isLive() && gotDesc) setOlLoading(false);
      };
      try {
        // 1) Livre réel en bibliothèque
        if (book.id && !book.isFromOpenLibrary && !book.isDemotedSeries) {
          const r = await fetch(
            `${API_BASE_URL}/api/books/${book.id}/synopsis?persist=true`,
            { headers }
          );
          if (r.ok && isLive()) {
            const data = await r.json();
            await applyMeta({
              description: data?.description,
              pages: data?.pages,
            });
            gotDesc = !needsDesc || isUsableSynopsis(data?.description);
            gotPages = !needsPages || !!data?.pages;
            markDescDone();
          }
        }

        // 2) Résumé : OL direct + resolve-synopsis en parallèle (premier résultat gagne)
        if (!gotDesc && isLive() && (book.title || book.ol_key)) {
          const olKey = book.ol_key || '';
          const isOlWork =
            olKey &&
            String(olKey).includes('works/') &&
            !String(olKey).startsWith('gbooks_');

          const fetchResolve = async () => {
            if (!(book.title || '').trim()) return null;
            const params = new URLSearchParams({
              title: book.title || '',
              author:
                book.author && book.author !== 'Auteur inconnu' ? book.author : '',
              include_pages: 'false',
            });
            if (book.isbn) params.set('isbn', book.isbn);
            if (olKey) params.set('ol_key', olKey);
            const r = await fetch(
              `${API_BASE_URL}/api/books/resolve-synopsis?${params}`,
              { headers, cache: 'no-store' }
            );
            if (!r.ok) return null;
            const data = await r.json();
            return isUsableSynopsis(data?.description) ? data.description : null;
          };

          const fetchOlDirect = async () => {
            if (!isOlWork) return null;
            const stripped = olKey.startsWith('/') ? olKey.slice(1) : olKey;
            const r = await fetch(`${API_BASE_URL}/api/openlibrary/book/${stripped}`, {
              headers,
              cache: 'no-store',
            });
            if (!r.ok) return null;
            const data = await r.json();
            return isUsableSynopsis(data?.description) ? data.description : null;
          };

          const results = await Promise.allSettled([fetchOlDirect(), fetchResolve()]);
          if (!isLive()) return;
          for (const res of results) {
            if (res.status === 'fulfilled' && res.value) {
              await applyMeta({ description: res.value });
              gotDesc = true;
              break;
            }
          }
          markDescDone();
        }

        // 3) Pages poche FR en arrière-plan (ne bloque plus l'UI du résumé)
        if (!gotPages && isLive() && (book.title || '').trim()) {
          const params = new URLSearchParams({
            title: book.title || '',
            author: book.author && book.author !== 'Auteur inconnu' ? book.author : '',
          });
          if (book.isbn) params.set('isbn', book.isbn);
          if (book.ol_key) params.set('ol_key', book.ol_key);
          const r = await fetch(
            `${API_BASE_URL}/api/books/resolve-pages?${params}`,
            { headers, cache: 'no-store' }
          );
          if (r.ok && isLive()) {
            const data = await r.json();
            if (data?.pages) {
              await applyMeta({ pages: data.pages });
              gotPages = true;
            }
          }
        }

        if (isLive()) {
          if ((!needsDesc || gotDesc) && (!needsPages || gotPages)) {
            pagesFetchDoneRef.current = fetchKey;
          } else {
            pagesFetchDoneRef.current = null;
          }
        }
      } catch (_) {
        if (isLive()) pagesFetchDoneRef.current = null;
      } finally {
        if (isLive()) setOlLoading(false);
      }
    };

    loadMeta();
    return () => {
      // Invalide seulement si un nouveau cycle n'a pas déjà pris le relais
      if (metaReqIdRef.current === reqId) {
        metaReqIdRef.current += 1;
      }
    };
  }, [
    book.id,
    book.title,
    book.author,
    book.isbn,
    book.ol_key,
    book.total_pages,
    book.isFromOpenLibrary,
    book.isDemotedSeries,
    // volontairement sans book.description (persistance ne doit pas annuler l'affichage)
  ]);

  // Micro-bounce sur un bouton
  const triggerBounce = useCallback((id) => {
    setBouncing(id);
    setTimeout(() => setBouncing(null), 380);
  }, []);

  const statusOptions = [
    { value: 'to_read',   label: 'À lire',   color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',    emoji: '📌' },
    { value: 'reading',   label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300',    emoji: '📖' },
    { value: 'completed', label: 'Terminé',  color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300', emoji: '✅' },
  ];

  const formatReadDate = (value) => {
    if (!value) return null;
    try {
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return null;
      return d.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      });
    } catch {
      return null;
    }
  };

  // Changer rapidement le statut
  const handleQuickStatusChange = async (newStatus) => {
    if (!book?.id || newStatus === book.status) return;
    triggerBounce(`status-${newStatus}`);
    const previousStatus = book.status;
    // Feedback immédiat dans le modal
    setEditData((prev) => ({ ...prev, status: newStatus }));
    try {
      // N'envoyer que le statut (évite champs hors BookUpdate / mauvais id série)
      await onUpdate(book.id, { status: newStatus });
      if (newStatus === 'completed') {
        setTimeout(launchConfetti, 200);
        toast.success('🎉 Bravo, livre terminé !', { duration: 3000, icon: '🏆' });
      }
    } catch (error) {
      setEditData((prev) => ({ ...prev, status: previousStatus }));
      toast.error('Erreur lors de la mise à jour du statut');
    }
  };

  // Relancer une lecture (conserve l'historique côté serveur)
  const handleReread = async () => {
    if (!book?.id || displayStatus !== 'completed') return;
    triggerBounce('reread');
    const previous = {
      status: book.status,
      current_page: book.current_page,
      date_completed: book.date_completed,
      date_started: book.date_started,
    };
    setEditData((prev) => ({ ...prev, status: 'reading', current_page: 0 }));
    setPageInput(0);
    try {
      await onUpdate(book.id, { status: 'reading', current_page: 0 });
      toast.success('Bonne relecture !', { icon: '📖' });
    } catch (error) {
      setEditData((prev) => ({
        ...prev,
        status: previous.status,
        current_page: previous.current_page || 0,
      }));
      setPageInput(previous.current_page || 0);
      toast.error('Impossible de relancer la lecture');
    }
  };

  // Sauvegarder la page courante rapidement (sans mode édition complet)
  const handlePageSave = async () => {
    const page = parseInt(pageInput) || 0;
    if (page === (book.current_page || 0)) return;
    triggerBounce('page-save');
    try {
      const updates = { current_page: page };
      // Comme les tomes de série : une page saisie ⇒ en cours de lecture
      if (page > 0 && book.status !== 'reading' && book.status !== 'completed') {
        updates.status = 'reading';
        setEditData((prev) => ({ ...prev, status: 'reading', current_page: page }));
      } else {
        setEditData((prev) => ({ ...prev, current_page: page }));
      }
      await onUpdate(book.id, updates);
    } catch (error) {
      toast.error('Erreur lors de la mise à jour de la page');
    }
  };


  const handleSave = async () => {
    setIsLoading(true);
    triggerBounce('save');
    try {
      const updates = {
        ...editData,
        current_page: parseInt(editData.current_page) || 0,
      };
      if (updates.status === 'completed' && book.status !== 'completed') {
        setTimeout(launchConfetti, 300);
      }
      await onUpdate(book.id, updates);
      setIsEditing(false);
      toast.success('Livre mis à jour !');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirmDelete) {
      setConfirmDelete(true);
      return;
    }
    setIsLoading(true);
    setConfirmDelete(false);
    try {
      await onDelete(book.id);
      // Le toast succès et la fermeture du modal sont gérés par BookActions.handleDeleteBook
    } catch (error) {
      toast.error('Erreur lors de la suppression. Vérifie ta connexion et réessaie.');
      setIsLoading(false);
      setConfirmDelete(false);
    }
  };

  // Fonction pour ajouter un livre depuis Open Library
  const handleAddFromOpenLibrary = async () => {
    if (!onAddFromOpenLibrary || !book.isFromOpenLibrary || isAdding) return;
    setIsAdding(true);
    try {
      await onAddFromOpenLibrary(book);
      setAddDone(true);
      setTimeout(() => onClose(), 800);
    } catch (error) {
      console.error('Erreur ajout livre:', error);
      toast.error(error.message || 'Erreur lors de l\'ajout du livre');
      setIsAdding(false);
    }
  };

  const displayStatus = editData.status || book.status;

  const handleRatingClick = async (rating) => {
    setEditData((prev) => ({ ...prev, rating }));
    // Note saisissable dès que le livre est terminé (sans mode édition complet)
    if ((editData.status || book.status) === 'completed' && book?.id && !book.isFromOpenLibrary) {
      try {
        await onUpdate(book.id, { rating });
        setCommunityRefreshKey((k) => k + 1);
      } catch (_) {
        toast.error('Erreur lors de la sauvegarde de la note');
      }
    }
  };

  const handleReviewPublish = async () => {
    if ((editData.status || book.status) !== 'completed' || !book?.id || book.isFromOpenLibrary) return;
    const review = (editData.review || '').trim();
    if (!review) {
      toast.error('Écris un avis avant de publier');
      return;
    }
    if (review === (book.review || '').trim()) {
      toast.success('Avis déjà publié');
      return;
    }
    setPublishingReview(true);
    try {
      await onUpdate(book.id, { review });
      setEditData((prev) => ({ ...prev, review }));
      setCommunityRefreshKey((k) => k + 1);
      toast.success('Avis publié');
    } catch (_) {
      toast.error("Erreur lors de la publication de l'avis");
    } finally {
      setPublishingReview(false);
    }
  };

  const getProgressPercentage = () => {
    if (!totalPages) return 0;
    const currentPage = isEditing ? editData.current_page : book.current_page;
    return Math.min(100, (currentPage / totalPages) * 100);
  };

  const getCurrentStatus = () => {
    return statusOptions.find(s => s.value === displayStatus) || statusOptions[0];
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-wide modal-animate w-full md:w-auto" onClick={(e) => e.stopPropagation()}>
        {/* Barre mobile sticky : fermeture toujours visible */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 md:hidden border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Détail</span>
          <button type="button" onClick={onClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        <div className="px-4 md:px-0 pt-2 md:pt-0">
        <div className="flex flex-col gap-4 mb-4 md:flex-row md:items-start md:justify-between md:gap-6">
          <div className="min-w-0 flex-1">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-2 break-words">{titleMain}</h2>
            <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 mb-4">
              par{' '}
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  if (onAuthorClick) onAuthorClick(book.author);
                }}
                className="text-lg text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
              >
                {book.author}
              </button>
            </p>
            
            {/* Catégorie */}
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-booktime-100 dark:bg-booktime-900/30 text-booktime-800 dark:text-booktime-300">
                {book.category === 'roman' && '📚'} 
                {book.category === 'bd' && '🎨'} 
                {book.category === 'manga' && '🇯🇵'} 
                {(book.category || 'roman').charAt(0).toUpperCase() + (book.category || 'roman').slice(1)}
              </span>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCurrentStatus().color}`}>
                {getCurrentStatus().label}
              </span>
              {titleMain ? (
                <button
                  type="button"
                  onClick={() => {
                    const params = new URLSearchParams({
                      tab: 'similaires',
                      title: titleMain,
                    });
                    if (book.author) params.set('author', book.author);
                    onClose?.();
                    navigate(`/recommendations?${params}`);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-900/60 transition-colors"
                >
                  <SparklesIcon className="h-4 w-4" />
                  Similaires
                </button>
              ) : null}
            </div>

            {/* Résumé / 4ᵉ de couverture — au-dessus du statut (comme les fiches séries) */}
            {displaySynopsis ? (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Résumé
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed whitespace-pre-line">
                  {displaySynopsis}
                </p>
              </div>
            ) : olLoading ? (
              <div className="mb-4 flex items-center gap-2 text-sm text-gray-400 py-2">
                <div className="h-4 w-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
                Chargement du résumé…
              </div>
            ) : (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Résumé
                </h3>
                <p className="text-gray-400 dark:text-gray-500 text-sm italic mb-2">
                  Aucun résumé disponible pour ce livre.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    pagesFetchDoneRef.current = null;
                    setOlLoading(true);
                    // Relancer l'effet en touchant une dépendance locale via re-fetch manuel
                    const token = localStorage.getItem('token');
                    const headers = token ? { Authorization: `Bearer ${token}` } : {};
                    const params = new URLSearchParams({
                      title: book.title || '',
                      author: book.author || '',
                      include_pages: 'false',
                    });
                    if (book.isbn) params.set('isbn', book.isbn);
                    if (book.ol_key) params.set('ol_key', book.ol_key);
                    fetch(`${API_BASE_URL}/api/books/resolve-synopsis?${params}`, { headers })
                      .then((r) => (r.ok ? r.json() : null))
                      .then(async (data) => {
                        if (isUsableSynopsis(data?.description)) {
                          const text = sanitizeSynopsis(data.description);
                          setOlDetails({ description: text });
                          if (book.id && !book.isFromOpenLibrary && onUpdateRef.current) {
                            try {
                              await onUpdateRef.current(book.id, {
                                description: text,
                              });
                            } catch (_) {
                              /* ignore */
                            }
                          }
                        }
                      })
                      .finally(() => setOlLoading(false));
                  }}
                  className="text-xs font-medium text-green-600 dark:text-green-400 hover:underline"
                >
                  Réessayer
                </button>
              </div>
            )}

            {/* Boutons rapides de changement de statut */}
            {(!book.isFromOpenLibrary || book.isOwned) && !isEditing && (
              <div className="mb-4">
                <div className="flex items-center mb-2">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Statut :</h3>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 w-fit">
                    {statusOptions.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => handleQuickStatusChange(option.value)}
                        className={`btn-ripple px-4 py-2 text-sm font-medium transition-all flex items-center space-x-2 ${
                          bouncing === `status-${option.value}` ? 'btn-bounce' : ''
                        } ${
                          displayStatus === option.value
                            ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md'
                            : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                        }`}
                        title={`Marquer comme ${option.label}`}
                      >
                        <span className="text-base">{option.emoji}</span>
                        <span>{option.label}</span>
                      </button>
                    ))}
                  </div>
                  {displayStatus === 'completed' && (
                    <button
                      type="button"
                      onClick={handleReread}
                      className={`inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors ${
                        bouncing === 'reread' ? 'btn-bounce' : ''
                      }`}
                      title="Relancer une lecture depuis le début"
                    >
                      <ArrowPathIcon className="h-4 w-4" />
                      Relire
                    </button>
                  )}
                </div>

                {displayStatus === 'completed' && formatReadDate(book.date_completed) && (
                  <p className="mt-2 text-sm text-green-700 dark:text-green-400">
                    Lu le {formatReadDate(book.date_completed)}
                    {formatReadDate(book.date_started) &&
                      formatReadDate(book.date_started) !== formatReadDate(book.date_completed) && (
                        <span className="text-gray-500 dark:text-gray-400">
                          {' '}· commencé le {formatReadDate(book.date_started)}
                        </span>
                      )}
                  </p>
                )}
                {displayStatus === 'reading' && formatReadDate(book.date_started) && (
                  <p className="mt-2 text-sm text-blue-700 dark:text-blue-400">
                    Lecture commencée le {formatReadDate(book.date_started)}
                  </p>
                )}
              </div>
            )}

            {/* Saisie rapide de la page (livres individuels + séries rétrogradées, comme les tomes) */}
            {(!book.isFromOpenLibrary || book.isOwned) && !isEditing && displayStatus === 'reading' && (
              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/40 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400">Progression de lecture</h3>
                  {totalPages > 0 && pageInput > 0 && (
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                      {Math.round(((pageInput || 0) / totalPages) * 100)}%
                    </span>
                  )}
                </div>
                {totalPages > 0 && pageInput > 0 && (
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-3">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full reading-progress-bar transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.round(((pageInput || 0) / totalPages) * 100))}%` }}
                    />
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Page</span>
                  <input
                    ref={pageInputRef}
                    type="number"
                    value={pageInput || ''}
                    placeholder="optionnel"
                    onChange={(e) => setPageInput(Math.max(0, Math.min(totalPages || 99999, parseInt(e.target.value) || 0)))}
                    onBlur={handlePageSave}
                    onKeyDown={(e) => e.key === 'Enter' && handlePageSave()}
                    min="0"
                    max={totalPages || undefined}
                    className="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-center"
                  />
                  {totalPages > 0 ? (
                    <span className="text-sm text-gray-500 dark:text-gray-400">/ {totalPages}</span>
                  ) : olLoading ? (
                    <span className="text-xs text-gray-400 dark:text-gray-500">recherche du total…</span>
                  ) : null}
                  {(parseInt(pageInput) || 0) !== (book.current_page || 0) && (
                    <button
                      onClick={handlePageSave}
                      className={`btn-ripple ml-auto px-3 py-1 text-sm font-medium bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white rounded-md transition-colors ${bouncing === 'page-save' ? 'btn-bounce' : ''}`}
                    >
                      ✓ Sauvegarder
                    </button>
                  )}
                </div>
              </div>
            )}


          </div>
          
          <div className="flex w-full flex-col gap-2 shrink-0 md:w-auto md:items-end">
            {/* Bouton Ajouter pour les livres Open Library — pleine largeur sur mobile */}
            {book.isFromOpenLibrary && !book.isOwned && onAddFromOpenLibrary && (
              <button
                onClick={handleAddFromOpenLibrary}
                disabled={isAdding || addDone}
                className={`btn-ripple w-full md:w-auto md:min-w-[180px] px-4 py-3 md:py-2 text-sm font-semibold text-white rounded-xl md:rounded-lg transition-all flex items-center justify-center gap-2 ${
                  addDone
                    ? 'bg-green-500 cursor-default'
                    : isAdding
                    ? 'bg-green-500 cursor-not-allowed opacity-80'
                    : 'bg-green-600 hover:bg-green-700 hover:shadow-md active:bg-green-800'
                }`}
              >
                {addDone ? (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Ajouté !</span>
                  </>
                ) : isAdding ? (
                  <>
                    <span className="btn-spinner" />
                    <span>Ajout en cours…</span>
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                    </svg>
                    <span>Ajouter à ma bibliothèque</span>
                  </>
                )}
              </button>
            )}
            
            <div className="flex flex-row flex-wrap items-center justify-end gap-1 md:gap-2">
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Fermer"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Image de couverture */}
          <div className="md:col-span-1">
            <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
              {book.cover_url ? (
                <img 
                  src={book.cover_url} 
                  alt={titleMain}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
                  <div className="text-center p-4">
                    <div className="text-6xl mb-2">
                      {book.category === 'roman' && '📚'}
                      {book.category === 'bd' && '🎨'}
                      {book.category === 'manga' && '🇯🇵'}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Pas de couverture</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Détails du livre */}
          <div className="md:col-span-2 space-y-6">
            {/* Édition des langues */}
            {isEditing && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">🌍 Modifier les langues</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Langue originale */}
                  <div>
                    <LanguageSelector
                      label="Langue originale"
                      selectedLanguages={[editData.original_language]}
                      onLanguagesChange={(languages) => setEditData(prev => ({ ...prev, original_language: languages[0] || 'français' }))}
                      single={true}
                      placeholder="Sélectionner la langue originale"
                    />
                  </div>

                  {/* Langue de lecture */}
                  <div>
                    <LanguageSelector
                      label="Langue de lecture"
                      selectedLanguages={[editData.reading_language]}
                      onLanguagesChange={(languages) => setEditData(prev => ({ ...prev, reading_language: languages[0] || 'français' }))}
                      single={true}
                      placeholder="Langue dans laquelle vous lisez"
                    />
                  </div>
                </div>

                {/* Traductions disponibles */}
                <div className="mt-4">
                  <LanguageSelector
                    label="Traductions disponibles"
                    selectedLanguages={editData.available_translations}
                    onLanguagesChange={(languages) => setEditData(prev => ({ ...prev, available_translations: languages }))}
                    maxSelections={10}
                    placeholder="Ajouter les langues de traduction disponibles"
                  />
                </div>
              </div>
            )}

            {/* Série / Saga */}
            {isEditing ? (
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Série (optionnel)
                  </label>
                  <input
                    type="text"
                    value={editData.saga}
                    onChange={(e) => setEditData(prev => ({ ...prev, saga: e.target.value }))}
                    placeholder="ex: Harry Potter, One Piece…"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tome n°
                  </label>
                  <input
                    type="number"
                    value={editData.volume_number}
                    onChange={(e) => setEditData(prev => ({ ...prev, volume_number: e.target.value }))}
                    placeholder="1"
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-sm"
                  />
                </div>
              </div>
            ) : book.saga ? (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Série</h3>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300 rounded-full text-sm font-medium">
                  📚 {book.saga}{book.volume_number ? ` — Tome ${book.volume_number}` : ''}
                </span>
              </div>
            ) : null}

            {/* Statut */}
            {isEditing ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Statut
                </label>
                <select
                  value={editData.status}
                  onChange={(e) => setEditData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                >
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Statut</h3>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCurrentStatus().color}`}>
                  {getCurrentStatus().label}
                </span>
              </div>
            )}

            {/* Progression */}
            {totalPages > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Progression</h3>
                {isEditing ? (
                  <div className="space-y-2">
                    <input
                      type="number"
                      value={editData.current_page}
                      onChange={(e) => setEditData(prev => ({ ...prev, current_page: e.target.value }))}
                      min="0"
                      max={totalPages}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>{editData.current_page} pages lues</span>
                      <span>{totalPages} pages total</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>{book.current_page || 0} pages lues</span>
                      <span>{totalPages} pages total</span>
                    </div>
                    <div className="progress-bar bg-gray-200 dark:bg-gray-700">
                      <div 
                        className="progress-fill"
                        style={{ width: `${getProgressPercentage()}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Note & avis — visibles uniquement une fois le livre terminé */}
            {displayStatus === 'completed' && (
              <>
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Note</h3>
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => handleRatingClick(star)}
                        className="h-6 w-6 cursor-pointer"
                      >
                        {star <= (editData.rating || book.rating || 0) ? (
                          <StarSolidIcon className="h-6 w-6 text-yellow-400" />
                        ) : (
                          <StarIcon className="h-6 w-6 text-gray-300 dark:text-gray-600" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Avis</h3>
                  <textarea
                    value={editData.review}
                    onChange={(e) => setEditData((prev) => ({ ...prev, review: e.target.value }))}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                    placeholder="Qu'avez-vous pensé de ce livre ?"
                  />
                  <button
                    type="button"
                    onClick={handleReviewPublish}
                    disabled={
                      publishingReview ||
                      !(editData.review || '').trim() ||
                      (editData.review || '').trim() === (book.review || '').trim()
                    }
                    className="mt-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {publishingReview ? 'Publication…' : 'Publier'}
                  </button>
                </div>
              </>
            )}

            <CommunityReviews
              book={book}
              refreshKey={communityRefreshKey}
            />

            {/* Sujets / Genres — depuis OL enrichi */}
            {(olDetails?.subjects?.length > 0 || book.subjects?.length > 0) && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Genres & Sujets</h3>
                <div className="flex flex-wrap gap-1">
                  {(olDetails?.subjects || book.subjects || [])
                    .map((s) => (typeof s === 'string' ? s : s?.name || ''))
                    .filter(Boolean)
                    // Préférer les sujets FR (accents / mots courants) ; sinon garder un échantillon
                    .sort((a, b) => {
                      const score = (t) =>
                        (/[àâäéèêëïîôùûç]/i.test(t) ? 2 : 0) +
                        (/\b(roman|policier|fantastique|aventure|jeunesse|bande|dessin)/i.test(t)
                          ? 1
                          : 0);
                      return score(b) - score(a);
                    })
                    .slice(0, 8)
                    .map((s, i) => (
                    <span key={i} className="px-2 py-0.5 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full border border-blue-100 dark:border-blue-800">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Lien Open Library */}
            {book.ol_key &&
              typeof book.ol_key === 'string' &&
              !book.ol_key.startsWith('gbooks_') && (
              <div className="pt-2">
                <a
                  href={`https://openlibrary.org${book.ol_key.startsWith('/') ? book.ol_key : '/' + book.ol_key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 underline"
                >
                  Voir sur Open Library →
                </a>
              </div>
            )}

            {/* Informations supplémentaires */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {book.original_title && book.original_title !== titleMain && (
                  <div className="col-span-2">
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">Titre original</h4>
                    <p className="text-gray-600 dark:text-gray-400 italic">{book.original_title}</p>
                  </div>
                )}
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">Date d'ajout</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    {book.date_added ? new Date(book.date_added).toLocaleDateString('fr-FR') : '—'}
                  </p>
                </div>
                {book.date_started && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">Début de lecture</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      {new Date(book.date_started).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                )}
                {book.date_completed && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">Terminé le</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      {new Date(book.date_completed).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                )}
                {book.isbn && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">ISBN</h4>
                    <p className="text-gray-600 dark:text-gray-400">{book.isbn}</p>
                  </div>
                )}
                {Array.isArray(book.reading_history) && book.reading_history.length > 0 && (
                  <div className="col-span-2">
                    <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">Lectures précédentes</h4>
                    <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                      {[...book.reading_history].reverse().map((entry, idx) => {
                        const done = formatReadDate(entry?.date_completed);
                        const started = formatReadDate(entry?.date_started);
                        if (!done && !started) return null;
                        return (
                          <li key={idx}>
                            {done ? `Lu le ${done}` : `Commencé le ${started}`}
                            {entry?.rating ? ` · ${entry.rating}/5` : ''}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Boutons d'action */}
        {isEditing ? (
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading}
              className={`btn-ripple px-4 py-2 text-sm font-semibold text-white bg-booktime-600 border border-transparent rounded-lg hover:bg-booktime-700 disabled:opacity-50 flex items-center gap-2 min-w-[120px] justify-center ${bouncing === 'save' ? 'btn-bounce' : ''}`}
            >
              {isLoading ? (
                <>
                  <span className="btn-spinner" />
                  <span>Sauvegarde…</span>
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Sauvegarder</span>
                </>
              )}
            </button>
          </div>
        ) : (
          /* Similaires + Collection + Retirer */
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
            {titleMain ? (
              <button
                type="button"
                onClick={() => {
                  const params = new URLSearchParams({
                    tab: 'similaires',
                    title: titleMain,
                  });
                  if (book.author) params.set('author', book.author);
                  onClose?.();
                  navigate(`/recommendations?${params}`);
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 active:bg-purple-800 rounded-xl transition-colors shadow-sm"
              >
                <SparklesIcon className="h-5 w-5" />
                Voir des livres similaires
              </button>
            ) : null}
          {!book.isFromOpenLibrary && (
            <>
              {book.id && (
                <div>
                  {showCollectionMenu ? (
                    <AddToCollectionMenu
                      item={{
                        type: book.isDemotedSeries ? 'series' : 'book',
                        id: book.id,
                        title: titleMain || book.title,
                        author: book.author || '',
                        cover_url: book.cover_url || null,
                      }}
                      onClose={() => setShowCollectionMenu(false)}
                    />
                  ) : (
                    <button
                      type="button"
                      onClick={() => setShowCollectionMenu(true)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                    >
                      Ajouter à une collection
                    </button>
                  )}
                </div>
              )}
              {onDelete && (confirmDelete ? (
                <div className="flex items-center justify-between bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                  <span className="text-sm text-red-700 dark:text-red-300 font-medium">
                    Retirer définitivement ce livre ?
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfirmDelete(false)}
                      className="px-3 py-1.5 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                    >
                      Annuler
                    </button>
                    <button
                      onClick={handleDelete}
                      disabled={isLoading}
                      className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
                    >
                      {isLoading ? 'Suppression…' : 'Confirmer'}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <TrashIcon className="h-4 w-4" />
                  Retirer de ma bibliothèque
                </button>
              ))}
            </>
          )}
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default BookDetailModal;
