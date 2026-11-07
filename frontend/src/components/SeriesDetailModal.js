import React, { useState, useEffect, useRef, useMemo } from 'react';
import ModalOverlay, { MODAL_Z } from './common/ModalOverlay';
import { useNavigate } from 'react-router-dom';
import {
  BookOpenIcon,
  CheckCircleIcon,
  ClockIcon,
  PlusIcon,
  XMarkIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';
import { deleteSeriesFromLibrary } from '../services/seriesLibraryService';
import { EXTENDED_SERIES_DATABASE } from '../utils/seriesDatabaseExtended';
import ChapterSection from './ChapterSection'; // ← NOUVEAU : Import du composant chapitres
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/environment';
import { displayBookTitleFrFirst, mergeOpenLibraryBooksByVolume } from '../utils/openLibraryBookDisplay';
import {
  mergeStaticWdWorksWithOpenLibrary,
  enrichVolumeRowsGoogleBooksIsbnThenIntitle,
  mapLiveWikidataVolumesToWorks,
} from '../utils/sourceMerge';
import { DEFAULT_SERIES_MODAL_GOOGLE_BOOKS } from '../utils/searchSourcePipeline';
import { isVolumeUnreleased, countReleasedVolumes } from '../utils/volumeRelease';
import { prefetchAuthor } from '../services/authorPrefetch';
import { preferFrenchSynopsis } from '../utils/synopsisQuality';
import { useTheme } from '../contexts/ThemeContext';
import SeriesHeader from './series-detail/SeriesHeader';
import SeriesStatusBar from './series-detail/SeriesStatusBar';
import SeriesTomeList from './series-detail/SeriesTomeList';
import PreviousTomesDialog from './series-detail/PreviousTomesDialog';
import SeriesLibraryActions from './series-detail/SeriesLibraryActions';
import SeriesRatingReview from './series-detail/SeriesRatingReview';
import {
  isPersistedLibraryId,
  resolveVolumesCount,
  normalizeSeriesVolumesField,
  mapStaticWikidataWorksToOlBooks,
} from '../utils/seriesDetailHelpers';
import logger from '../utils/logger';

const SeriesDetailModal = ({ 
  series, 
  isOpen, 
  onClose, 
  onUpdate,
  onDelete,
  onAddSeries,
  onAuthorClick,
  userSeriesLibrary = []
}) => {
  const navigate = useNavigate();
  const { isVoid } = useTheme();
  const seriesDisplayName = series?.name || series?.series_name || series?.title || '';
  const goToSimilar = () => {
    const name = seriesDisplayName;
    if (!name) return;
    const params = new URLSearchParams({ tab: 'similaires', series: name });
    const author = series?.author || series?.authors?.[0] || '';
    if (author) params.set('author', author);
    onClose?.();
    navigate(`/recommendations?${params}`);
  };
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTomes, setSelectedTomes] = useState(new Set());
  const [isSeriesOwned, setIsSeriesOwned] = useState(false);
  const [seriesStatus, setSeriesStatus] = useState('to_read');
  const [seriesRating, setSeriesRating] = useState(0);
  const [seriesReview, setSeriesReview] = useState('');
  const [savedSeriesReview, setSavedSeriesReview] = useState('');
  const [publishingSeriesReview, setPublishingSeriesReview] = useState(false);
  const [communityRefreshKey, setCommunityRefreshKey] = useState(0);
  // tomeStatuses : { "1": { status: "non_lu"|"en_cours"|"lu", currentPage: null|number }, ... }
  const [tomeStatuses, setTomeStatuses] = useState({});
  // Rétrocompatibilité : readTomes dérivé de tomeStatuses
  const readTomes = new Set(
    Object.entries(tomeStatuses)
      .filter(([, v]) => v.status === 'lu')
      .map(([k]) => Number(k))
  );
  const [missingPreviousWarning, setMissingPreviousWarning] = useState(null);
  const [showWdRaw, setShowWdRaw] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [showCollectionMenu, setShowCollectionMenu] = useState(false);
  const [coverProxy, setCoverProxy] = useState(false);
  // États du bouton "Ajouter à ma bibliothèque" (alignés sur ceux des livres individuels)
  const [isAdding, setIsAdding] = useState(false);
  const [addDone, setAddDone] = useState(false);
  // Vérification croisée multi-sources (Référence + Wikidata + Open Library + Google Books).
  const [verification, setVerification] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const onUpdateDebounceRef = useRef(null);

  const handleDeleteSeries = async () => {
    setDeleting(true);
    setConfirmDelete(false);
    try {
      const token = localStorage.getItem('token');
      let deleted = false;

      // Cas 1 : série possédée → retirer de la bibliothèque de séries
      if (isSeriesOwned || series.isOwnedSeries || series.isLibrarySeries) {
        const seriesId = series.id || series._id;
        if (seriesId) {
          try {
            await deleteSeriesFromLibrary(seriesId, token);
            deleted = true;
          } catch (e) {
            // continue pour essayer de supprimer les livres
          }
        }
      }

      // Cas 2 : supprimer les livres individuels (série auto-détectée ou livres associés)
      // Priorité : books[] sur l'objet série, puis books[] chargés dans le modal
      const directBooks = [
        ...(series.books || []),
        ...books  // état interne du modal (chargé par loadBooksForSeries)
      ];
      const uniqueBooks = directBooks.filter(
        (b, i, arr) => b && (b.id || b._id) && arr.findIndex(x => (x.id || x._id) === (b.id || b._id)) === i
      );

      if (uniqueBooks.length > 0) {
        await Promise.allSettled(uniqueBooks.map(b => bookService.deleteBook(b.id || b._id)));
        deleted = true;
      }

      // Cas 3 : fallback — chercher par champ saga
      if (!deleted) {
        const resp = await fetch(
          `${API_BASE_URL}/api/books/all?saga=${encodeURIComponent(series.name)}&limit=100`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (resp.ok) {
          const data = await resp.json();
          const sagaBooks = (data.items || []).filter(b =>
            (b.saga || '').toLowerCase().trim() === (series.name || '').toLowerCase().trim()
          );
          if (sagaBooks.length > 0) {
            await Promise.allSettled(sagaBooks.map(b => bookService.deleteBook(b.id || b._id)));
            deleted = true;
          }
        }
      }

      if (!deleted) throw new Error('Aucun contenu trouvé à supprimer');

      toast.success('Série retirée de ta bibliothèque !');
      onClose();
      if (onDelete) onDelete();
    } catch (error) {
      toast.error('Erreur lors du retrait de la série');
    } finally {
      setDeleting(false);
    }
  };

  const normalizeTomeStatuses = (raw) => {
    const out = {};
    Object.entries(raw || {}).forEach(([k, v]) => {
      if (!v || typeof v !== 'object') return;
      out[String(k)] = {
        status: v.status || 'non_lu',
        currentPage: v.currentPage ?? v.current_page ?? null,
        rating: v.rating ?? 0,
        review: v.review || '',
      };
    });
    return out;
  };

  //  NOUVELLE FONCTION : Charger les préférences de lecture depuis la base de données
  const loadReadingPreferences = async (seriesName) => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = API_BASE_URL
      
      const response = await fetch(`${backendUrl}/api/series/reading-preferences/${encodeURIComponent(seriesName)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Reconstituer tomeStatuses depuis tome_statuses (nouveau) ou read_tomes (legacy)
        if (data.tome_statuses && Object.keys(data.tome_statuses).length > 0) {
          return normalizeTomeStatuses(data.tome_statuses);
        }
        // Fallback legacy : read_tomes → statut "lu"
        const legacy = {};
        (data.read_tomes || []).forEach(n => { legacy[String(n)] = { status: 'lu', currentPage: null, rating: 0, review: '' }; });
        return legacy;
      } else {
        return {};
      }
    } catch (error) {
      logger.error(' Erreur lors du chargement des préférences:', error);
      return {};
    }
  };

  //  NOUVELLE FONCTION : Sauvegarder les préférences de lecture en base de données
  const saveReadingPreferences = async (seriesName, currentTomeStatuses) => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = API_BASE_URL
      
      const response = await fetch(`${backendUrl}/api/series/reading-preferences`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          series_name: seriesName,
          read_tomes: Object.entries(currentTomeStatuses)
            .filter(([, v]) => v.status === 'lu')
            .map(([k]) => Number(k)),
          tome_statuses: currentTomeStatuses
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        logger.debug(' Préférences sauvegardées:', data);
        return true;
      } else {
        logger.error(' Erreur lors de la sauvegarde:', response.status);
        return false;
      }
    } catch (error) {
      logger.error(' Erreur lors de la sauvegarde des préférences:', error);
      return false;
    }
  };

  //  NOUVELLE FONCTION : Charger les préférences pour la série courante
  const loadReadingPreferencesForSeries = async () => {
    if (!enrichedSeries?.name) return;
    try {
      const statuses = await loadReadingPreferences(enrichedSeries.name);
      setTomeStatuses(statuses || {});

      // Calculer le statut à afficher depuis les données chargées, sans déclencher de toast
      const entries = Object.values(statuses || {});
      const hasRead = entries.some(v => v.status === 'lu');
      const hasInProgress = entries.some(v => v.status === 'en_cours');
      const readCount = entries.filter(v => v.status === 'lu').length;
      const totalTomes = resolveVolumesCount(
        enrichedSeries?.volumes,
        series?.books?.length || 0
      );

      let derivedStatus = 'to_read';
      if (hasInProgress || (hasRead && (totalTomes === 0 || readCount < totalTomes))) {
        derivedStatus = 'reading';
      } else if (hasRead && totalTomes > 0 && readCount >= totalTomes) {
        derivedStatus = 'completed';
      }
      // Ne pas écraser le statut série explicite (ex. « Terminé » sans tous les tomes cochés)
      const explicit = series?.status || series?.series_status;
      if (explicit === 'completed' && derivedStatus !== 'completed') {
        setSeriesStatus('completed');
      } else if (hasRead || hasInProgress) {
        setSeriesStatus(derivedStatus);
      } else if (explicit) {
        setSeriesStatus(explicit);
      }
    } catch (error) {
      logger.error(' Erreur chargement préférences:', error);
      setTomeStatuses({});
    }
  };

  // Fonction pour enrichir les données de série avec les métadonnées de référence
  const enrichSeriesData = (series) => {
    if (!series?.name && !series?.fromStaticWikidata) {
      return normalizeSeriesVolumesField(series);
    }

    if (series.fromStaticWikidata && series.staticWikidataDetail) {
      const works = series.staticWikidataDetail.works || [];
      const nVol = works.length || series.staticWikidataDetail.work_count || 0;
      return {
        ...series,
        volumes: nVol,
        volume_titles: {},
        referenceFound: false,
        fromFallbackBooks: true,
      };
    }

    if (!series?.name) return normalizeSeriesVolumesField(series);
    
    // Rechercher dans la base de données de référence
    const seriesName = series.name.toLowerCase();
    let referenceData = null;
    
    // Parcourir toutes les catégories de la base de données de référence
    for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
      for (const seriesData of Object.values(category)) {
        if (seriesData.name.toLowerCase() === seriesName || 
            seriesData.variations?.some(variation => variation.toLowerCase() === seriesName)) {
          referenceData = seriesData;
          break;
        }
      }
      if (referenceData) break;
    }
    
    if (referenceData) {
      return {
        ...series,
        volumes: referenceData.volumes,
        volume_titles: referenceData.volume_titles,
        volume_details: referenceData.volume_details,
        description: referenceData.description,
        first_published: referenceData.first_published,
        status: referenceData.status,
        referenceFound: true
      };
    }

    // Série bibliothèque : volumes = [{ volume_number, volume_title, is_read, date_read }, ...]
    if (Array.isArray(series.volumes) && series.volumes.length > 0) {
      return {
        ...normalizeSeriesVolumesField(series),
        referenceFound: false,
        fromFallbackBooks: true,
      };
    }
    
    // Fallback : utiliser series.books (résultats OL ou Wikidata) pour déduire les volumes
    const fallbackBooks = series.books || [];
    if (fallbackBooks.length > 0) {
      const volumeTitles = {};
      fallbackBooks.forEach((b, i) => {
        const num = b.volume_number || (i + 1);
        volumeTitles[num] = b.title || `${series.name} - Tome ${num}`;
      });
      return {
        ...series,
        volumes: fallbackBooks.length,
        volume_titles: volumeTitles,
        referenceFound: false,
        fromFallbackBooks: true,
      };
    }
    
    return normalizeSeriesVolumesField(series);
  };

  //  NOUVELLE FONCTION : Calculer et mettre à jour automatiquement le statut de la série
  const calculateAndUpdateSeriesStatus = async (newReadTomes) => {
    if (!enrichedSeries?.name || !enrichedSeries?.volumes) {
      logger.debug(' Calcul statut ignoré - série non valide ou données manquantes');
      return;
    }

    //  CORRECTION : Permettre le calcul même si la série n'est pas encore "officiellement" possédée
    // L'utilisateur peut marquer des tomes comme lus avant d'ajouter la série à sa bibliothèque
    const totalTomes = resolveVolumesCount(enrichedSeries.volumes);
    const readTomesCount = newReadTomes.size;
    

    // Déterminer le nouveau statut selon les règles
    let newStatus = 'to_read'; // Par défaut
    
    if (readTomesCount === 0) {
      return;
    } else if (readTomesCount === totalTomes && totalTomes > 0) {
      newStatus = 'completed'; // Tous les tomes lus = Terminé
    } else {
      newStatus = 'reading'; // Quelques tomes lus = En cours
    }

    if (isSeriesOwned && newStatus !== seriesStatus) {
      
      try {
        // Utiliser la fonction existante pour changer le statut
        await handleQuickStatusChange(newStatus);
        
        // Notification utilisateur pour série possédée
        const statusLabels = {
          'to_read': 'À lire',
          'reading': 'En cours',
          'completed': 'Terminé'
        };
        
        toast.success(`Statut de la série mis à jour automatiquement : ${statusLabels[newStatus]}`, {
          icon: '',
          duration: 3000
        });
        
      } catch (error) {
        logger.error(' Erreur lors de la mise à jour automatique du statut:', error);
      }
    } else if (!isSeriesOwned && newStatus !== seriesStatus) {
      
      // Mettre à jour l'état local pour l'affichage même si série non possédée
      setSeriesStatus(newStatus);
      
      // Notification utilisateur pour série non possédée
      const statusLabels = {
        'to_read': 'À lire',
        'reading': 'En cours',
        'completed': 'Terminé'
      };
      
      toast.success(`Progression mise à jour : ${statusLabels[newStatus]}`, {
        icon: '',
        duration: 2000
      });
    }
  };

  // Note / avis d'un tome lu
  const handleTomeFeedbackChange = async (tomeNumber, { rating, review }) => {
    const prev = tomeStatuses[String(tomeNumber)] || { status: 'lu', currentPage: null };
    const newStatuses = {
      ...tomeStatuses,
      [String(tomeNumber)]: {
        ...prev,
        status: prev.status || 'lu',
        rating: rating ?? prev.rating ?? 0,
        review: review ?? prev.review ?? '',
      },
    };
    setTomeStatuses(newStatuses);

    if (enrichedSeries?.name) {
      await saveReadingPreferences(enrichedSeries.name, newStatuses);

      const token = localStorage.getItem('token');
      const booksInSeries = series?.books || [];
      const matchingBook = booksInSeries.find(
        (b) =>
          (b.volume_number || 0) === tomeNumber ||
          booksInSeries.indexOf(b) + 1 === tomeNumber
      );
      if (matchingBook?.id) {
        await fetch(`${API_BASE_URL}/api/books/${matchingBook.id}`, {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            rating: rating ?? prev.rating ?? 0,
            review: review ?? prev.review ?? '',
          }),
        }).catch(() => {});
      }
    }
  };

  // Changer le statut d'un tome (non_lu | en_cours | lu) + page optionnelle
  const handleTomeStatusChange = async (tomeNumber, newStatus, currentPage = null) => {
    if (isVolumeUnreleased(enrichedSeries, tomeNumber)) {
      toast.error('Ce volume n’est pas encore sorti');
      return;
    }
    const prev = tomeStatuses[String(tomeNumber)] || {};
    const newStatuses = {
      ...tomeStatuses,
      [String(tomeNumber)]: {
        status: newStatus,
        currentPage,
        rating: prev.rating || 0,
        review: prev.review || '',
      },
    };
    setTomeStatuses(newStatuses);

    // Suggestion tomes précédents si on marque "lu" (ignorer les non sortis)
    if (newStatus === 'lu' && tomeNumber > 1) {
      const missingPrevious = [];
      for (let i = 1; i < tomeNumber; i++) {
        if (isVolumeUnreleased(enrichedSeries, i)) continue;
        if ((newStatuses[String(i)]?.status || 'non_lu') === 'non_lu') missingPrevious.push(i);
      }
      if (missingPrevious.length > 0) {
        setMissingPreviousWarning({ currentTome: tomeNumber, missingTomes: missingPrevious });
      } else {
        setMissingPreviousWarning(null);
      }
    } else {
      setMissingPreviousWarning(null);
    }

    // Calculer et mettre à jour le statut de la série
    const newReadSet = new Set(
      Object.entries(newStatuses)
        .filter(([k, v]) => v.status === 'lu' && !isVolumeUnreleased(enrichedSeries, Number(k)))
        .map(([k]) => Number(k))
    );
    // Statut : en_cours si au moins 1 tome lu ou en cours
    const hasInProgress = Object.entries(newStatuses).some(
      ([k, v]) => v.status === 'en_cours' && !isVolumeUnreleased(enrichedSeries, Number(k))
    );
    const hasRead = newReadSet.size > 0;
    const catalogTotal = resolveVolumesCount(
      enrichedSeries?.volumes,
      olBooks.length || (series?.books?.length) || 0
    );
    // Ne compter que les tomes déjà parus pour « terminé »
    const totalTomes =
      countReleasedVolumes(enrichedSeries, catalogTotal) || catalogTotal;
    let autoStatus = 'to_read';
    if (hasInProgress || (hasRead && newReadSet.size < totalTomes)) autoStatus = 'reading';
    else if (hasRead && totalTomes > 0 && newReadSet.size >= totalTomes) autoStatus = 'completed';
    setSeriesStatus(autoStatus);

    if (enrichedSeries?.name) {
      await saveReadingPreferences(enrichedSeries.name, newStatuses);

      // Mapping statut tome → statut livre (pour mettre à jour la BDD et bouger la carte)
      const tomeToBookStatus = { non_lu: 'to_read', en_cours: 'reading', lu: 'completed' };
      const bookStatus = tomeToBookStatus[newStatus] || 'to_read';
      const token = localStorage.getItem('token');
      const backendUrl = API_BASE_URL;

      // 1. Mettre à jour le livre correspondant dans series.books (séries auto-détectées)
      const booksInSeries = series?.books || [];
      const matchingBook = booksInSeries.find(b =>
        (b.volume_number || 0) === tomeNumber || booksInSeries.indexOf(b) + 1 === tomeNumber
      );
      if (matchingBook?.id) {
        await fetch(`${backendUrl}/api/books/${matchingBook.id}`, {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: bookStatus })
        }).catch(() => {});
      }

      // 2. Mettre à jour le statut agrégé de la série dans la library (séries possédées)
      if (autoStatus !== (series?.status || 'to_read')) {
        const libEntry = (userSeriesLibrary || []).find(
          s => (s.series_name || s.name || '').toLowerCase().trim() === (series.name || '').toLowerCase().trim()
        );
        const seriesId = libEntry?.id || series?.id;
        if (seriesId && autoStatus) {
          await fetch(`${backendUrl}/api/series/library/${seriesId}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ series_status: autoStatus })
          }).catch(() => {});
        }
      }

      // Debounce onUpdate pour éviter N rechargements si l'utilisateur clique vite sur plusieurs tomes
      if (onUpdate) {
        if (onUpdateDebounceRef.current) clearTimeout(onUpdateDebounceRef.current);
        onUpdateDebounceRef.current = setTimeout(() => { onUpdate(); }, 800);
      }
    }
  };

  // Rétrocompatibilité pour handleTomeReadToggle (utilisé dans handleCheckPreviousTomes)
  const handleTomeReadToggle = async (tomeNumber) => {
    const current = tomeStatuses[String(tomeNumber)]?.status || 'non_lu';
    await handleTomeStatusChange(tomeNumber, current === 'lu' ? 'non_lu' : 'lu');
  };

  // Fonction pour cocher automatiquement tous les tomes précédents avec sauvegarde
  const handleCheckPreviousTomes = async () => {
    if (!missingPreviousWarning) return;
    
    const newStatuses = { ...tomeStatuses };
    missingPreviousWarning.missingTomes.forEach(tomeNumber => {
      const prev = newStatuses[String(tomeNumber)] || {};
      newStatuses[String(tomeNumber)] = {
        status: 'lu',
        currentPage: null,
        rating: prev.rating || 0,
        review: prev.review || '',
      };
    });
    setTomeStatuses(newStatuses);
    
    // Recalcul du statut agrégé
    const readCount = Object.values(newStatuses).filter(v => v.status === 'lu').length;
    const hasInProgress = Object.values(newStatuses).some(v => v.status === 'en_cours');
    const totalTomes = resolveVolumesCount(
      enrichedSeries?.volumes,
      series?.books?.length || 0
    );
    let bulkStatus = 'to_read';
    if (hasInProgress || (readCount > 0 && readCount < totalTomes)) bulkStatus = 'reading';
    else if (readCount > 0 && totalTomes > 0 && readCount >= totalTomes) bulkStatus = 'completed';
    setSeriesStatus(bulkStatus);

    if (enrichedSeries?.name) {
      await saveReadingPreferences(enrichedSeries.name, newStatuses);

      // Mettre à jour chaque livre coché "lu" en BDD
      const token = localStorage.getItem('token');
      const backendUrl = API_BASE_URL;
      const booksInSeries = series?.books || [];
      await Promise.all(
        missingPreviousWarning.missingTomes.map(tomeNum => {
          const book = booksInSeries.find(b =>
            (b.volume_number || 0) === tomeNum || booksInSeries.indexOf(b) + 1 === tomeNum
          );
          if (!book?.id) return Promise.resolve();
          return fetch(`${backendUrl}/api/books/${book.id}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'completed' })
          }).catch(() => {});
        })
      );

      if (onUpdate) onUpdate();
    }
    setMissingPreviousWarning(null);
  };

  // Enrichir les données de série au chargement.
  // Mémoïsé car la résolution parcourt tout le référentiel curé : sans cela le scan
  // était refait à chaque rendu de la modale (frappe, changement de statut, etc.).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const enrichedSeries = useMemo(() => enrichSeriesData(series), [series]);

  const seriesCoverUrl = useMemo(() => {
    const candidates = [
      series?.cover_url,
      series?.cover_image_url,
      enrichedSeries?.cover_url,
      enrichedSeries?.cover_image_url,
      series?.books?.[0]?.cover_url,
      books?.[0]?.cover_url,
      Array.isArray(enrichedSeries?.volumes) ? enrichedSeries.volumes[0]?.cover_url : null,
    ];
    return candidates.map((u) => String(u || '').trim()).find(Boolean) || '';
  }, [series, enrichedSeries, books]);

  const seriesSynopsis = useMemo(() => {
    return (
      preferFrenchSynopsis(
        enrichedSeries?.description_fr,
        enrichedSeries?.description,
        series?.description_fr,
        series?.description,
        { rejectEnglish: true }
      ) || ''
    );
  }, [enrichedSeries, series]);

  // Options de statut pour les boutons rapides
  const statusOptions = [
    { value: 'to_read', label: 'À lire', color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300' },
    { value: 'reading', label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300' },
    { value: 'completed', label: 'Terminé', color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' },
  ];

  const resolveSeriesLibraryId = () => {
    const name = (series?.name || series?.title || series?.series_name || '').toLowerCase().trim();
    const libEntry = (userSeriesLibrary || []).find(
      (s) => (s.series_name || s.name || '').toLowerCase().trim() === name
    );
    const candidate =
      libEntry?.id ||
      ((series?.isOwnedSeries || series?.isLibrarySeries) ? series?.id : null);
    return isPersistedLibraryId(candidate) ? candidate : null;
  };

  const persistSeriesFeedback = async (payload) => {
    const seriesId = resolveSeriesLibraryId();
    if (!seriesId) {
      toast.error('Ajoutez d’abord la série à votre bibliothèque');
      return false;
    }
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/api/series/library/${seriesId}`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      logger.error('PUT series feedback failed', res.status, await res.text());
      return false;
    }
    return true;
  };

  const handleSeriesRatingClick = async (rating) => {
    setSeriesRating(rating);
    if (!isSeriesOwned) return;
    const ok = await persistSeriesFeedback({ rating });
    if (ok) {
      setCommunityRefreshKey((k) => k + 1);
      if (onUpdate) {
        if (onUpdateDebounceRef.current) clearTimeout(onUpdateDebounceRef.current);
        onUpdateDebounceRef.current = setTimeout(() => onUpdate(), 400);
      }
    } else {
      toast.error('Impossible d’enregistrer la note');
    }
  };

  const handleSeriesReviewPublish = async () => {
    const review = (seriesReview || '').trim();
    if (!review) {
      toast.error('Écrivez un avis avant de publier');
      return;
    }
    if (review === (savedSeriesReview || '').trim()) {
      toast.success('Avis déjà publié');
      return;
    }
    setPublishingSeriesReview(true);
    try {
      const ok = await persistSeriesFeedback({
        review,
        rating: seriesRating || undefined,
      });
      if (!ok) {
        toast.error('Impossible de publier l’avis');
        return;
      }
      setSavedSeriesReview(review);
      setCommunityRefreshKey((k) => k + 1);
      toast.success('Avis publié');
      if (onUpdate) {
        if (onUpdateDebounceRef.current) clearTimeout(onUpdateDebounceRef.current);
        onUpdateDebounceRef.current = setTimeout(() => onUpdate(), 400);
      }
    } finally {
      setPublishingSeriesReview(false);
    }
  };

  // Fonction pour changer rapidement le statut de la série
  const handleQuickStatusChange = async (newStatus) => {
    const hasDetectedBooks = (series?.books || []).length > 0;
    if (!isSeriesOwned && !hasDetectedBooks) {
      toast.error('Vous devez d\'abord ajouter cette série à votre bibliothèque');
      return;
    }

    const token = localStorage.getItem('token');
    const backendUrl = API_BASE_URL;
    const statusLabel = statusOptions.find(s => s.value === newStatus)?.label || newStatus;
    const previousStatus = seriesStatus;
    const previousTomeStatuses = tomeStatuses;

    // Mise à jour optimiste de l'UI
    setSeriesStatus(newStatus);

    // Propager Terminé / À lire sur les tomes déjà parus (sinon l'UI reste « non lu »)
    const catalogTotal = resolveVolumesCount(
      enrichedSeries?.volumes,
      olBooks.length || (series?.books?.length) || Object.keys(tomeStatuses).length || 0
    );
    const volumeTotal =
      countReleasedVolumes(enrichedSeries, catalogTotal) || catalogTotal;
    let nextTomeStatuses = tomeStatuses;
    if (newStatus === 'completed' || newStatus === 'to_read') {
      const targetTomeStatus = newStatus === 'completed' ? 'lu' : 'non_lu';
      nextTomeStatuses = { ...tomeStatuses };
      const maxTome = Math.max(volumeTotal, Object.keys(tomeStatuses).length, 0);
      for (let i = 1; i <= maxTome; i += 1) {
        if (isVolumeUnreleased(enrichedSeries, i)) continue;
        const prev = nextTomeStatuses[String(i)] || {};
        nextTomeStatuses[String(i)] = {
          status: targetTomeStatus,
          currentPage: targetTomeStatus === 'lu' ? null : (prev.currentPage ?? null),
          rating: prev.rating || 0,
          review: prev.review || '',
        };
      }
      setTomeStatuses(nextTomeStatuses);
      setMissingPreviousWarning(null);
    }

    try {
      let anyOk = false;
      const seriesName = series.name || series.title || '';
      const jobs = [];

      // 1. series_library (carte série)
      const seriesId = resolveSeriesLibraryId();
      if (seriesId) {
        jobs.push(
          fetch(`${backendUrl}/api/series/library/${seriesId}`, {
            method: 'PUT',
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ series_status: newStatus }),
          }).then(async (res) => {
            if (res.ok) anyOk = true;
            else logger.error('PUT series_status failed', res.status, await res.text());
          })
        );
      }

      // 2. Préférences de tomes (lu / non_lu) — source de vérité de la grille de volumes
      if (
        seriesName &&
        (newStatus === 'completed' || newStatus === 'to_read') &&
        Object.keys(nextTomeStatuses).length > 0
      ) {
        jobs.push(
          saveReadingPreferences(seriesName, nextTomeStatuses).then((ok) => {
            if (ok) anyOk = true;
          })
        );
      }

      // 3. Livres individuels de la saga — 1 seul appel bulk (évite N PUT + fetch lent)
      if (seriesName) {
        jobs.push(
          fetch(`${backendUrl}/api/sagas/${encodeURIComponent(seriesName)}/bulk-status`, {
            method: 'PUT',
            headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus }),
          })
            .then(async (res) => {
              if (res.ok) {
                anyOk = true;
                return;
              }
              // Fallback : PUT livre par livre si bulk indisponible
              const candidateBooks = (series.books || []).filter((b) => isPersistedLibraryId(b.id));
              if (candidateBooks.length === 0) return;
              const results = await Promise.all(
                candidateBooks.map((book) =>
                  fetch(`${backendUrl}/api/books/${book.id}`, {
                    method: 'PUT',
                    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
                    body: JSON.stringify({ status: newStatus }),
                  }).then((r) => r.ok)
                )
              );
              if (results.some(Boolean)) anyOk = true;
            })
            .catch(() => {})
        );
      }

      await Promise.all(jobs);

      if (!anyOk) {
        setSeriesStatus(previousStatus);
        setTomeStatuses(previousTomeStatuses);
        toast.error('Impossible de mettre à jour le statut de la série');
        return;
      }

      toast.success(`Statut de la série "${seriesName}" : ${statusLabel}`);
      // Rafraîchir la biblio en arrière-plan (ne pas bloquer l’UI)
      if (onUpdate) {
        if (onUpdateDebounceRef.current) clearTimeout(onUpdateDebounceRef.current);
        onUpdateDebounceRef.current = setTimeout(() => {
          onUpdate();
        }, 400);
      }
    } catch (error) {
      logger.error(' Erreur changement statut:', error);
      setSeriesStatus(previousStatus);
      setTomeStatuses(previousTomeStatuses);
      toast.error('Erreur lors du changement de statut');
    }
  };

  // Vérification allégée : limit=1. Accepte un AbortSignal pour éviter les races.
  const checkIfSeriesOwned = async (signal) => {
    if (!series?.name) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${API_BASE_URL}/api/books/all?saga=${encodeURIComponent(series.name)}&limit=1`,
        { headers: { 'Authorization': `Bearer ${token}` }, signal }
      );
      if (signal?.aborted) return;
      if (response.ok) {
        const data = await response.json();
        if (signal?.aborted) return;
        const seriesNameLower = series.name.toLowerCase().trim();
        const match = (data.items || []).find(book => {
          const bookSaga = (book.saga || '').toLowerCase().trim();
          return bookSaga === seriesNameLower;
        });
        setIsSeriesOwned(!!match);
        // Ne pas écraser le statut série (series_library) avec le statut d'un tome isolé
        const explicit = series.status || series.series_status;
        if (!explicit && match?.status) setSeriesStatus(match.status);
      } else {
        setIsSeriesOwned(false);
      }
    } catch (e) {
      if (e?.name !== 'AbortError') setIsSeriesOwned(false);
    }
  };

  // Fiche auteur chargée d'avance : elle s'ouvre sans attente au clic sur le nom
  useEffect(() => {
    if (!isOpen) return;
    const seriesAuthor = series?.author || series?.authors?.[0];
    if (seriesAuthor) prefetchAuthor(seriesAuthor);
  }, [isOpen, series?.author, series?.authors]);

  useEffect(() => {
    if (!isOpen || !series) return;

    let cancelled = false;
    const abortController = new AbortController();

    setTomeStatuses({});
    setOlBooks([]);
    setMissingPreviousWarning(null);
    setShowWdRaw(false);
    setVerification(null);
    setCoverProxy(false);
    // Statut lecture depuis la carte / series_library (pas toujours 'to_read')
    setSeriesStatus(series.status || series.series_status || 'to_read');
    const nameKey = (series.name || series.title || series.series_name || '').toLowerCase().trim();
    const libEntry = (userSeriesLibrary || []).find(
      (s) => (s.series_name || s.name || '').toLowerCase().trim() === nameKey
    );
    const initialRating = Number(series.rating ?? libEntry?.rating ?? 0) || 0;
    const initialReview = series.review || libEntry?.review || '';
    setSeriesRating(initialRating);
    setSeriesReview(initialReview);
    setSavedSeriesReview(initialReview);
    setPublishingSeriesReview(false);
    // Réinitialiser : on ne considère une série comme possédée qu'après vérification réelle.
    setIsSeriesOwned(false);

    if (series.isOwnedSeries || series.isLibrarySeries) {
      setIsSeriesOwned(true);
    } else {
      // NB : on ne se fie PAS à series.books — pour une carte issue de la recherche,
      // ce champ contient les tomes du CATALOGUE (Wikidata/OpenLibrary), pas les livres
      // que l'utilisateur possède. La possession se vérifie via la bibliothèque de séries
      // puis, à défaut, via l'API (livres de l'utilisateur filtrés par saga).
      const inLibrary = (userSeriesLibrary || []).some(
        s => (s.series_name || s.name || '').toLowerCase().trim() === (series.name || '').toLowerCase().trim()
      );
      if (inLibrary) {
        setIsSeriesOwned(true);
      } else {
        // Passer le signal pour annuler si le modal est fermé avant la réponse
        checkIfSeriesOwned(abortController.signal);
      }
    }

    const loadAll = async () => {
      await loadSeriesBooks();
      if (cancelled) return;
      await loadReadingPreferencesForSeries();
      if (cancelled) return;
      if (!enrichedSeries?.referenceFound) {
        await loadOLSeriesBooks();
      }
      if (cancelled) return;
      // Vérification croisée en arrière-plan (n'empêche pas l'affichage du modal).
      loadVolumeVerification(abortController.signal);
    };
    loadAll();

    return () => {
      cancelled = true;
      abortController.abort(); // annule checkIfSeriesOwned en vol
      if (onUpdateDebounceRef.current) clearTimeout(onUpdateDebounceRef.current);
    };
  // userSeriesLibrary retiré des dépendances pour éviter la rafale API à chaque refresh global.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, series]);

  const loadSeriesBooks = async () => {
    if (!series?.name) return;

    // Données déjà présentes (série en bibliothèque) : affichage immédiat
    const localVolumes =
      series.volumes ||
      series.mergedLibraryVolumes ||
      series.books ||
      [];
    if (Array.isArray(localVolumes) && localVolumes.length > 0) {
      const asBooks = localVolumes.map((v, i) =>
        typeof v === 'object'
          ? v
          : { title: String(v), volume_number: i + 1 }
      );
      setBooks(
        [...asBooks].sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0))
      );
      setLoading(false);
      // Refresh réseau en fond, non bloquant
      bookService
        .getBooksBySaga(series.name)
        .then((booksData) => {
          if (Array.isArray(booksData) && booksData.length > 0) {
            setBooks(
              [...booksData].sort(
                (a, b) => (a.volume_number || 0) - (b.volume_number || 0)
              )
            );
          }
        })
        .catch(() => {});
      return;
    }

    try {
      setLoading(true);
      const booksData = await bookService.getBooksBySaga(series.name);
      setBooks(
        (booksData || []).sort(
          (a, b) => (a.volume_number || 0) - (b.volume_number || 0)
        )
      );
    } catch (error) {
      logger.warn('Livres de saga indisponibles (timeout/réseau):', error?.message || error);
      setBooks([]);
    } finally {
      setLoading(false);
    }
  };

  // Vérification croisée du nombre de tomes / titres sur plusieurs sources.
  const loadVolumeVerification = async (signal) => {
    if (!series?.name) return;
    try {
      setVerifying(true);
      const token = localStorage.getItem('token');
      const qid = series.wikidata_qid || series.staticWikidataDetail?.qid || '';
      const params = new URLSearchParams({ name: series.name });
      if (series.author) params.set('author', series.author);
      if (qid) params.set('qid', qid);
      const res = await fetch(`${API_BASE_URL}/api/series/verify-volumes?${params.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal,
      });
      if (!res.ok) return;
      const data = await res.json();
      if (!signal?.aborted) setVerification(data);
    } catch (error) {
      if (error?.name !== 'AbortError') {
        logger.warn('Vérification des tomes indisponible:', error);
      }
    } finally {
      if (!signal?.aborted) setVerifying(false);
    }
  };

  // Charger les tomes depuis Wikidata (priorité) puis OL (fallback)
  const [olBooks, setOlBooks] = useState([]);
  const loadOLSeriesBooks = async () => {
    if (series?.fromStaticWikidata && series.staticWikidataDetail) {
      const works = series.staticWikidataDetail.works || [];
      const baseMapped = works.length > 0 ? mapStaticWikidataWorksToOlBooks(works) : [];
      if (!series?.name) {
        setOlBooks(baseMapped);
        return;
      }
      try {
        const token = localStorage.getItem('token');
        const olParams = new URLSearchParams({ name: series.name, limit: '30' });
        if (series.author) olParams.append('author', series.author);
        const olRes = await fetch(`${API_BASE_URL}/api/openlibrary/series-books?${olParams}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        let olClean = [];
        if (olRes.ok) {
          const olData = await olRes.json();
          olClean = (olData.books || []).filter((b) => {
            const t = (b.title || '').toLowerCase();
            return (
              !t.includes('box set') &&
              !t.includes('collection') &&
              !t.includes('omnibus') &&
              !t.includes('vol. 1-') &&
              t.length < 80
            );
          });
        }
        const merged = mergeStaticWdWorksWithOpenLibrary(works, mergeOpenLibraryBooksByVolume(olClean));
        const gbAuthor =
          series.author || (works[0] && (works[0].authors_en || [])[0]) || '';
        const withGb = await enrichVolumeRowsGoogleBooksIsbnThenIntitle(merged, {
          maxIsbn: DEFAULT_SERIES_MODAL_GOOGLE_BOOKS.maxIsbn,
          maxIntitle: DEFAULT_SERIES_MODAL_GOOGLE_BOOKS.maxIntitle,
          authorName: gbAuthor,
          fetchBook: (path) =>
            fetch(`${API_BASE_URL}${path}`, {
              headers: { Authorization: `Bearer ${token}` },
            }),
        });
        setOlBooks(
          withGb.map((b) => ({
            ...b,
            display_title: displayBookTitleFrFirst(b),
          }))
        );
      } catch (e) {
        logger.warn('Series OL merge (static WD) failed:', e);
        setOlBooks(baseMapped);
      }
      return;
    }
    if (!series?.name) return;
    try {
      const token = localStorage.getItem('token');

      const olParams = new URLSearchParams({ name: series.name, limit: '20' });
      if (series.author) olParams.append('author', series.author);
      const olRes = await fetch(`${API_BASE_URL}/api/openlibrary/series-books?${olParams}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      let olClean = [];
      if (olRes.ok) {
        const olData = await olRes.json();
        olClean = (olData.books || []).filter((b) => {
          const t = (b.title || '').toLowerCase();
          return (
            !t.includes('box set') &&
            !t.includes('collection') &&
            !t.includes('omnibus') &&
            !t.includes('vol. 1-') &&
            t.length < 80
          );
        });
      }
      const olMerged = mergeOpenLibraryBooksByVolume(olClean);

      const wdParams = new URLSearchParams({ name: series.name });
      if (series.author) wdParams.append('author', series.author);
      const wdRes = await fetch(`${API_BASE_URL}/api/wikidata/series/by-name/volumes?${wdParams}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      let merged;
      if (wdRes.ok) {
        const wdData = await wdRes.json();
        if (wdData.found && wdData.volumes?.length > 0) {
          merged = mergeStaticWdWorksWithOpenLibrary(
            mapLiveWikidataVolumesToWorks(wdData.volumes),
            olMerged
          );
        } else {
          merged = mergeStaticWdWorksWithOpenLibrary([], olMerged);
        }
      } else {
        merged = mergeStaticWdWorksWithOpenLibrary([], olMerged);
      }

      const withGb = await enrichVolumeRowsGoogleBooksIsbnThenIntitle(merged, {
        maxIsbn: DEFAULT_SERIES_MODAL_GOOGLE_BOOKS.maxIsbn,
        maxIntitle: DEFAULT_SERIES_MODAL_GOOGLE_BOOKS.maxIntitle,
        authorName: series.author || '',
        fetchBook: (path) =>
          fetch(`${API_BASE_URL}${path}`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
      });
      setOlBooks(
        withGb.map((b) => ({
          ...b,
          display_title: displayBookTitleFrFirst(b),
        }))
      );
    } catch (e) {
      logger.warn('Series books fetch failed:', e);
    }
  };

  const handleTomeToggle = async (book, isRead) => {
    try {
      await bookService.toggleTomeStatus(series.name, book.volume_number, isRead);
      await loadSeriesBooks();
      if (onUpdate) onUpdate();
      toast.success(`Tome ${book.volume_number} marqué comme ${isRead ? 'lu' : 'non lu'}`);
    } catch (error) {
      logger.error('Erreur lors de la mise à jour du tome:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  if (!isOpen) return null;

  // Rendu dans document.body : hors du carrousel mobile (transform, pointer-events).
  return (
    <ModalOverlay
      onClose={onClose}
      zIndex={MODAL_Z.sheet}
      ariaLabel="Fiche série"
      closeOnBackdrop={false}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-end md:items-center justify-center md:p-4"
    >
      <div className={`modal-content-wide shadow-2xl overflow-hidden w-full md:w-auto${isVoid ? ' void-sheet' : ''}`}>
        
        {/* Barre mobile sticky : fermeture toujours visible */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 md:hidden border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          <span className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Série</span>
          <button aria-label="Fermer" type="button" onClick={onClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* En-tête de la fiche (et JSON Wikidata) */}
        <SeriesHeader
          series={series}
          seriesCoverUrl={seriesCoverUrl}
          coverProxy={coverProxy}
          setCoverProxy={setCoverProxy}
          onAuthorClick={onAuthorClick}
          seriesStatus={seriesStatus}
          enrichedSeries={enrichedSeries}
          olBooks={olBooks}
          books={books}
          seriesDisplayName={seriesDisplayName}
          goToSimilar={goToSimilar}
          showWdRaw={showWdRaw}
          setShowWdRaw={setShowWdRaw}
          onAddSeries={onAddSeries}
          isSeriesOwned={isSeriesOwned}
          isAdding={isAdding}
          setIsAdding={setIsAdding}
          addDone={addDone}
          setAddDone={setAddDone}
          checkIfSeriesOwned={checkIfSeriesOwned}
          onClose={onClose}
        />

        {/* Section Résumé de la série — compact + FR prioritaire */}
        {seriesSynopsis ? (
          <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6">
            <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center">
              <BookOpenIcon className="w-3.5 h-3.5 mr-1 text-purple-600 dark:text-purple-400" />
              Résumé
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-xs sm:text-sm leading-relaxed whitespace-pre-line">
              {seriesSynopsis}
            </p>
          </div>
        ) : null}

        <SeriesStatusBar
          statusOptions={statusOptions}
          handleQuickStatusChange={handleQuickStatusChange}
          seriesStatus={seriesStatus}
          isSeriesOwned={isSeriesOwned}
        />

        {/* Actions Bar — affichée uniquement lorsqu'il y a une sélection de tomes */}
        {selectedTomes.size > 0 && (
          <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6 sm:py-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {selectedTomes.size} sélectionné(s)
              </span>
              <button
                onClick={() => setSelectedTomes(new Set())}
                className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
              >
                Désélectionner
              </button>
            </div>
          </div>
        )}

        <SeriesTomeList
          onClose={onClose}
          enrichedSeries={enrichedSeries}
          olBooks={olBooks}
          series={series}
          readTomes={readTomes}
          tomeStatuses={tomeStatuses}
          handleTomeStatusChange={handleTomeStatusChange}
          handleTomeFeedbackChange={handleTomeFeedbackChange}
          handleTomeReadToggle={handleTomeReadToggle}
        />

        <PreviousTomesDialog
          missingPreviousWarning={missingPreviousWarning}
          handleCheckPreviousTomes={handleCheckPreviousTomes}
          setMissingPreviousWarning={setMissingPreviousWarning}
        />

        {/* Books List (Section détaillée existante) - SUPPRIMÉE SUR DEMANDE UTILISATEUR */}

        {/* Chapitres sortis : mangas et BD (romans graphiques) */}
        {series && series.name && ['manga', 'bd', 'graphic_novel', 'graphic_novels'].includes(series.category) && (
          <ChapterSection 
            seriesName={series.name} 
            onClose={() => {/* Optionnel: logique fermeture section */}} 
          />
        )}

        {/* Similaires — CTA bien visible */}
        {seriesDisplayName ? (
          <div className="px-4 sm:px-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={goToSimilar}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 active:bg-purple-800 rounded-xl transition-colors shadow-sm"
            >
              <SparklesIcon className="h-5 w-5" />
              Voir des séries / livres similaires
            </button>
          </div>
        ) : null}

        <SeriesLibraryActions
          isSeriesOwned={isSeriesOwned}
          series={series}
          books={books}
          showCollectionMenu={showCollectionMenu}
          setShowCollectionMenu={setShowCollectionMenu}
          confirmDelete={confirmDelete}
          setConfirmDelete={setConfirmDelete}
          handleDeleteSeries={handleDeleteSeries}
          deleting={deleting}
        />

        <SeriesRatingReview
          isSeriesOwned={isSeriesOwned}
          seriesRating={seriesRating}
          handleSeriesRatingClick={handleSeriesRatingClick}
          seriesReview={seriesReview}
          setSeriesReview={setSeriesReview}
          handleSeriesReviewPublish={handleSeriesReviewPublish}
          publishingSeriesReview={publishingSeriesReview}
          savedSeriesReview={savedSeriesReview}
          seriesDisplayName={seriesDisplayName}
          series={series}
          communityRefreshKey={communityRefreshKey}
        />

      </div>
    </ModalOverlay>
  );
};

export default SeriesDetailModal;