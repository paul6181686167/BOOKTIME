import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ModalOverlay, { MODAL_Z } from './common/ModalOverlay';
import { useNavigate } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/environment';
import { displayBookTitleFrFirst } from '../utils/openLibraryBookDisplay';
import {
  isUsableSynopsis,
  looksEnglish,
  preferFrenchSynopsis,
  sanitizeSynopsis,
} from '../utils/synopsisQuality';
import { prefetchAuthor } from '../services/authorPrefetch';
import confetti from 'canvas-confetti';
import { useTheme } from '../contexts/ThemeContext';
import BookHeaderSection from './book-detail/BookHeaderSection';
import BookDetailsGrid from './book-detail/BookDetailsGrid';
import BookActionBar from './book-detail/BookActionBar';

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

// Livres dont le résumé a déjà été comparé à la 4ᵉ de couverture pendant cette session
const verifiedSynopsisBooks = new Set();

const BookDetailModal = ({ book, onClose, onUpdate, onDelete, onAddFromOpenLibrary, onAuthorClick }) => {
  const navigate = useNavigate();
  const { isVoid } = useTheme();
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
  const [coverProxy, setCoverProxy] = useState(false);
  const [isFavorite, setIsFavorite] = useState(!!book.is_favorite);
  const pageInputRef = useRef(null);
  const pagesFetchDoneRef = useRef(null);
  const metaReqIdRef = useRef(0);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const totalPages = resolvedTotalPages || book.total_pages || 0;
  // Afficher uniquement un résumé FR (jamais l'anglais en UI)
  const displaySynopsis =
    preferFrenchSynopsis(
      olDetails?.description,
      book.description,
      { rejectEnglish: true }
    ) || '';

  // Fiche auteur chargée d'avance : elle s'ouvre sans attente au clic sur le nom
  useEffect(() => {
    if (book.author && !book.isFromOpenLibrary) prefetchAuthor(book.author);
  }, [book.author, book.isFromOpenLibrary]);

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
    setIsFavorite(!!book.is_favorite);
    setResolvedTotalPages(book.total_pages > 0 ? book.total_pages : null);
    // Nouveau livre → reset résumé enrichi (sauf si déjà une vraie 4ᵉ en base)
    setOlDetails(
      isUsableSynopsis(book.description) && !looksEnglish(book.description)
        ? { description: sanitizeSynopsis(book.description) }
        : null
    );
    setOlLoading(false);
    setCoverProxy(false);
    pagesFetchDoneRef.current = null;
    metaReqIdRef.current += 1;
  }, [book]);

  // Charger résumé (rapide) + pages poche FR si manquants / faux résumés.
  // Important : ne PAS dépendre de book.description — la persistance du résumé
  // relançait l'effet, annulait le fetch et laissait « Aucun résumé » pour les
  // fiches series_library rétrogradées (ex-vignettes 0/0 tomes).
  useEffect(() => {
    const storedDesc = (book.description || '').trim();
    // Relancer la résolution si résumé anglais (préférer une version FR)
    const needsDesc = !isUsableSynopsis(storedDesc) || looksEnglish(storedDesc);
    const needsPages = !(book.total_pages > 0);
    // Résumé présent : on le compare une fois à la 4ᵉ de couverture réelle de l'édition
    const needsVerify =
      !needsDesc &&
      !!book.id &&
      !book.isFromOpenLibrary &&
      !book.isDemotedSeries &&
      !verifiedSynopsisBooks.has(book.id);
    if (!needsDesc && !needsPages && !needsVerify) {
      return;
    }

    const reqId = ++metaReqIdRef.current;
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const fetchKey = `${book.id}|${book.title}|p=${needsPages}|d=${needsDesc}|v=${needsVerify}`;
    if (pagesFetchDoneRef.current === fetchKey) {
      setOlLoading(false);
      return;
    }

    const isLive = () => metaReqIdRef.current === reqId;
    const abort = new AbortController();
    const fetchTimeoutMs = 22000;

    const fetchWithTimeout = async (url, opts = {}) => {
      if (abort.signal.aborted) {
        throw new DOMException('Aborted', 'AbortError');
      }
      const ctrl = new AbortController();
      const onParentAbort = () => ctrl.abort();
      abort.signal.addEventListener('abort', onParentAbort);
      const timer = setTimeout(() => ctrl.abort(), fetchTimeoutMs);
      try {
        return await fetch(url, {
          ...opts,
          signal: ctrl.signal,
          headers: { ...headers, ...(opts.headers || {}) },
        });
      } finally {
        clearTimeout(timer);
        abort.signal.removeEventListener('abort', onParentAbort);
      }
    };

    const applyMeta = async ({ description, pages } = {}) => {
      const patch = {};
      if (needsDesc && isUsableSynopsis(description)) {
        const best = preferFrenchSynopsis(
          storedDesc,
          description,
          { rejectEnglish: true }
        );
        if (best) {
          setOlDetails({ description: best });
          if (best !== sanitizeSynopsis(storedDesc)) {
            patch.description = best;
          }
        }
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
      // Toujours couper le spinner à la fin de la phase résumé (même sans FR trouvé)
      const markDescDone = () => {
        if (isLive()) setOlLoading(false);
      };
      try {
        // 1) Livre réel en bibliothèque
        if (book.id && !book.isFromOpenLibrary && !book.isDemotedSeries) {
          const r = await fetchWithTimeout(
            `${API_BASE_URL}/api/books/${book.id}/synopsis?persist=true`
          );
          if (r.ok && isLive()) {
            const data = await r.json();
            if (book.id) verifiedSynopsisBooks.add(book.id);
            // Le serveur a trouvé la 4ᵉ de couverture de l'édition : elle remplace l'ancien résumé
            if (
              data?.replaced &&
              isUsableSynopsis(data.description) &&
              !looksEnglish(data.description)
            ) {
              const backCover = sanitizeSynopsis(data.description);
              setOlDetails({ description: backCover });
              if (onUpdateRef.current) {
                try {
                  await onUpdateRef.current(book.id, { description: backCover });
                } catch (_) {
                  /* ignore */
                }
              }
            }
            await applyMeta({
              description: data?.description,
              pages: data?.pages,
            });
            let syn = data?.description || '';
            gotDesc =
              !needsDesc ||
              (isUsableSynopsis(syn) && !looksEnglish(syn));
            // Backend ancien / résumé encore EN → traduction dédiée
            if (!gotDesc && isUsableSynopsis(syn) && looksEnglish(syn)) {
              try {
                const tr = await fetchWithTimeout(
                  `${API_BASE_URL}/api/books/translate-synopsis`,
                  {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: syn }),
                  }
                );
                if (tr.ok) {
                  const td = await tr.json();
                  if (isUsableSynopsis(td?.description) && !looksEnglish(td.description)) {
                    syn = sanitizeSynopsis(td.description);
                    await applyMeta({ description: syn });
                    gotDesc = true;
                  }
                }
              } catch (_) {
                /* ignore */
              }
            }
            gotPages = !needsPages || !!data?.pages;
            if (gotDesc) markDescDone();
          }
        }

        // 2) resolve-synopsis (FR) prioritaire ; OL direct seulement s'il est FR
        if (!gotDesc && isLive() && (book.title || book.ol_key)) {
          const olKey = book.ol_key || '';
          const isOlWork =
            olKey &&
            String(olKey).includes('works/') &&
            !String(olKey).startsWith('gbooks_');

          const fetchResolve = async () => {
            if (!(book.title || '').trim()) return null;
            const params = new URLSearchParams({
              title: displayBookTitleFrFirst(book) || book.title || '',
              author:
                book.author && book.author !== 'Auteur inconnu' ? book.author : '',
              include_pages: 'false',
            });
            if (book.isbn) params.set('isbn', book.isbn);
            if (olKey) params.set('ol_key', olKey);
            const r = await fetchWithTimeout(
              `${API_BASE_URL}/api/books/resolve-synopsis?${params}`,
              { cache: 'no-store' }
            );
            if (!r.ok) return null;
            const data = await r.json();
            return isUsableSynopsis(data?.description) ? data.description : null;
          };

          const fetchOlDirect = async () => {
            if (!isOlWork) return null;
            const stripped = olKey.startsWith('/') ? olKey.slice(1) : olKey;
            const r = await fetchWithTimeout(
              `${API_BASE_URL}/api/openlibrary/book/${stripped}`,
              { cache: 'no-store' }
            );
            if (!r.ok) return null;
            const data = await r.json();
            const desc = data?.description;
            // Ignorer les 4ᵉ OL clairement anglaises
            if (!isUsableSynopsis(desc) || looksEnglish(desc)) return null;
            return desc;
          };

          const results = await Promise.allSettled([fetchResolve(), fetchOlDirect()]);
          if (!isLive()) return;
          const candidates = results
            .filter((res) => res.status === 'fulfilled' && res.value)
            .map((res) => res.value);
          let best = preferFrenchSynopsis(...candidates, { rejectEnglish: true });
          // Aucun FR natif → traduire le meilleur résumé anglais
          if (!best) {
            const enSource =
              preferFrenchSynopsis(...candidates) ||
              candidates.find((c) => looksEnglish(c)) ||
              candidates[0] ||
              (looksEnglish(storedDesc) ? storedDesc : '');
            if (enSource) {
              try {
                const tr = await fetchWithTimeout(
                  `${API_BASE_URL}/api/books/translate-synopsis`,
                  {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: enSource }),
                  }
                );
                if (tr.ok) {
                  const data = await tr.json();
                  if (isUsableSynopsis(data?.description) && !looksEnglish(data.description)) {
                    best = sanitizeSynopsis(data.description);
                  }
                }
              } catch (_) {
                /* ignore */
              }
            }
          }
          if (best) {
            await applyMeta({ description: best });
            gotDesc = true;
          }
        }
        // Fin de recherche résumé (FR trouvé ou non)
        markDescDone();

        // 3) Pages poche FR en arrière-plan (ne bloque plus l'UI du résumé)
        if (!gotPages && isLive() && (book.title || '').trim()) {
          const params = new URLSearchParams({
            title: book.title || '',
            author: book.author && book.author !== 'Auteur inconnu' ? book.author : '',
          });
          if (book.isbn) params.set('isbn', book.isbn);
          if (book.ol_key) params.set('ol_key', book.ol_key);
          const r = await fetchWithTimeout(
            `${API_BASE_URL}/api/books/resolve-pages?${params}`,
            { cache: 'no-store' }
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
          // Ne verrouiller que si le résumé FR est là (sinon nouvelle tentative à la réouverture)
          if (!needsDesc || gotDesc) {
            pagesFetchDoneRef.current = fetchKey;
          }
        }
      } catch (err) {
        // Ne pas verrouiller après un abort / échec résumé (réessai possible)
        if (isLive() && err?.name !== 'AbortError' && !needsDesc) {
          pagesFetchDoneRef.current = fetchKey;
        }
      } finally {
        if (isLive()) setOlLoading(false);
      }
    };

    loadMeta();
    return () => {
      abort.abort();
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
    { value: 'to_read',   label: 'À lire',   color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300' },
    { value: 'reading',   label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300' },
    { value: 'completed', label: 'Terminé',  color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' },
  ];
  const statusMeta = [
    ...statusOptions,
    {
      value: 'to_reread',
      label: 'À relire',
      color: 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-300',
    },
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
        toast.success('Bravo, livre terminé !', { duration: 3000 });
      }
    } catch (error) {
      setEditData((prev) => ({ ...prev, status: previousStatus }));
      toast.error('Erreur lors de la mise à jour du statut');
    }
  };

  // Marquer « À relire » depuis Terminé (section bibliothèque dédiée)
  const handleMarkToReread = async () => {
    if (!book?.id || displayStatus !== 'completed') return;
    triggerBounce('to-reread');
    const previousStatus = book.status;
    setEditData((prev) => ({ ...prev, status: 'to_reread' }));
    try {
      await onUpdate(book.id, { status: 'to_reread' });
      toast.success('Ajouté à « À relire »');
    } catch (error) {
      setEditData((prev) => ({ ...prev, status: previousStatus }));
      toast.error('Impossible de marquer à relire');
    }
  };

  // Démarrer la relecture depuis « À relire » (historique conservé côté serveur)
  const handleStartReread = async () => {
    if (!book?.id || displayStatus !== 'to_reread') return;
    triggerBounce('reread');
    const previous = {
      status: book.status,
      current_page: book.current_page,
    };
    setEditData((prev) => ({ ...prev, status: 'reading', current_page: 0 }));
    setPageInput(0);
    try {
      await onUpdate(book.id, { status: 'reading', current_page: 0 });
      toast.success('Bonne relecture !');
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

  // Ajout depuis catalogue externe (Open Library / Google Books / recommandations)
  const canAddFromCatalog =
    !!onAddFromOpenLibrary &&
    !book.isOwned &&
    (book.isFromOpenLibrary || book.isFromGoogleBooks);
  const inLibrary = !!book.isOwned || (!book.isFromOpenLibrary && !book.isFromGoogleBooks);

  const handleAddFromOpenLibrary = async () => {
    if (!canAddFromCatalog || isAdding) return;
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

  // Livre préféré : visible par les amis sur ton profil
  const handleToggleFavorite = async () => {
    if (!book?.id || !inLibrary) return;
    const next = !isFavorite;
    setIsFavorite(next);
    try {
      await onUpdate(book.id, { is_favorite: next });
      toast.success(next ? 'Ajouté à tes livres préférés' : 'Retiré de tes livres préférés');
    } catch (_) {
      setIsFavorite(!next);
      toast.error('Impossible de modifier les livres préférés');
    }
  };

  // Ouvre la messagerie des amis avec ce livre prêt à être envoyé
  const handleRecommendToFriend = () => {
    const payload = {
      title: titleMain || book.title,
      author: book.author,
      cover_url: book.cover_url || book.cover_image_url || '',
      category: book.category,
      ol_key: book.ol_key || '',
      isbn: book.isbn || '',
    };
    onClose?.();
    // La fiche se ferme d'abord : la fenêtre des amis s'ouvre ensuite par-dessus l'écran
    window.setTimeout(
      () => window.dispatchEvent(new CustomEvent('recommendToFriend', { detail: { book: payload } })),
      80
    );
  };

  const handleRatingClick = async (rating) => {
    setEditData((prev) => ({ ...prev, rating }));
    // Note saisissable dès que le livre est terminé (sans mode édition complet)
    if (
      ['completed', 'to_reread'].includes(editData.status || book.status) &&
      book?.id &&
      !book.isFromOpenLibrary
    ) {
      try {
        await onUpdate(book.id, { rating });
        setCommunityRefreshKey((k) => k + 1);
      } catch (_) {
        toast.error('Erreur lors de la sauvegarde de la note');
      }
    }
  };

  const handleReviewPublish = async () => {
    if (
      !['completed', 'to_reread'].includes(editData.status || book.status) ||
      !book?.id ||
      book.isFromOpenLibrary
    )
      return;
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
    return statusMeta.find((s) => s.value === displayStatus) || statusOptions[0];
  };

  // Rendu dans document.body : hors du carrousel mobile (transform, pointer-events,
  // empilement) qui pouvait bloquer les boutons et le défilement de la fiche.
  return (
    <ModalOverlay onClose={onClose} zIndex={MODAL_Z.sheet} ariaLabel="Fiche livre">
      <div
        className={`modal-content-wide modal-animate w-full md:w-auto${isVoid ? ' void-sheet' : ''}`}
        onClick={(e) => e.stopPropagation()}
        style={{
          overflowY: 'auto',
          WebkitOverflowScrolling: 'touch',
          overscrollBehavior: 'contain',
          touchAction: 'pan-y',
        }}
      >
        {/* Barre mobile sticky : fermeture toujours visible */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 md:hidden border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Détail</span>
          <button type="button" onClick={onClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        <div className="px-4 md:px-0 pt-2 md:pt-0">
        <BookHeaderSection
          book={book}
          onClose={onClose}
          onAuthorClick={onAuthorClick}
          navigate={navigate}
          titleMain={titleMain}
          isEditing={isEditing}
          bouncing={bouncing}
          olLoading={olLoading}
          pageInput={pageInput}
          setPageInput={setPageInput}
          isAdding={isAdding}
          addDone={addDone}
          coverProxy={coverProxy}
          setCoverProxy={setCoverProxy}
          isFavorite={isFavorite}
          pageInputRef={pageInputRef}
          totalPages={totalPages}
          displaySynopsis={displaySynopsis}
          statusOptions={statusOptions}
          formatReadDate={formatReadDate}
          handleQuickStatusChange={handleQuickStatusChange}
          handleMarkToReread={handleMarkToReread}
          handleStartReread={handleStartReread}
          handlePageSave={handlePageSave}
          canAddFromCatalog={canAddFromCatalog}
          inLibrary={inLibrary}
          handleAddFromOpenLibrary={handleAddFromOpenLibrary}
          displayStatus={displayStatus}
          handleToggleFavorite={handleToggleFavorite}
          handleRecommendToFriend={handleRecommendToFriend}
          getCurrentStatus={getCurrentStatus}
        />

        <BookDetailsGrid
          book={book}
          titleMain={titleMain}
          isEditing={isEditing}
          olDetails={olDetails}
          editData={editData}
          setEditData={setEditData}
          publishingReview={publishingReview}
          communityRefreshKey={communityRefreshKey}
          coverProxy={coverProxy}
          setCoverProxy={setCoverProxy}
          totalPages={totalPages}
          statusOptions={statusOptions}
          formatReadDate={formatReadDate}
          inLibrary={inLibrary}
          displayStatus={displayStatus}
          handleRatingClick={handleRatingClick}
          handleReviewPublish={handleReviewPublish}
          getProgressPercentage={getProgressPercentage}
          getCurrentStatus={getCurrentStatus}
        />

        <BookActionBar
          book={book}
          onClose={onClose}
          onDelete={onDelete}
          navigate={navigate}
          titleMain={titleMain}
          isEditing={isEditing}
          setIsEditing={setIsEditing}
          bouncing={bouncing}
          isLoading={isLoading}
          confirmDelete={confirmDelete}
          setConfirmDelete={setConfirmDelete}
          showCollectionMenu={showCollectionMenu}
          setShowCollectionMenu={setShowCollectionMenu}
          handleSave={handleSave}
          handleDelete={handleDelete}
        />
        </div>
      </div>
    </ModalOverlay>
  );
};

export default BookDetailModal;
