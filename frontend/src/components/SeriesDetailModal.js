import React, { useState, useEffect, useRef } from 'react';
import {
  BookOpenIcon,
  CheckCircleIcon,
  ClockIcon,
  PlusIcon,
  ExclamationTriangleIcon,
  XMarkIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';
import { deleteSeriesFromLibrary } from '../services/seriesLibraryService';
import { EXTENDED_SERIES_DATABASE } from '../utils/seriesDatabaseExtended';
import TomeDropdown from './TomeDropdown'; // ← AJOUT : Import du nouveau composant
import ChapterSection from './ChapterSection'; // ← NOUVEAU : Import du composant chapitres
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/environment';
import { displayBookTitleFrFirst, mergeOpenLibraryBooksByVolume, sortOpenLibraryBooksByVolume } from '../utils/openLibraryBookDisplay';
import {
  mergeStaticWdWorksWithOpenLibrary,
  enrichVolumeRowsGoogleBooksIsbnThenIntitle,
  mapLiveWikidataVolumesToWorks,
} from '../utils/sourceMerge';
import { DEFAULT_SERIES_MODAL_GOOGLE_BOOKS } from '../utils/searchSourcePipeline';

function parseVolumeFromWork(vol) {
  if (vol == null || vol === '') return null;
  const m = String(vol).match(/\d+/);
  if (!m) return null;
  const n = parseInt(m[0], 10);
  return Number.isNaN(n) ? null : n;
}

/** volumes peut être un nombre (référentiel) ou un tableau (série bibliothèque). */
function resolveVolumesCount(volumes, fallback = 0) {
  if (typeof volumes === 'number' && Number.isFinite(volumes)) return volumes;
  if (Array.isArray(volumes)) return volumes.length;
  return fallback;
}

function volumeTitlesFromLibraryVolumes(volumes) {
  if (!Array.isArray(volumes)) return null;
  const map = {};
  volumes.forEach((v, i) => {
    const num = v?.volume_number ?? i + 1;
    map[num] = v?.volume_title || v?.title || `Tome ${num}`;
  });
  return Object.keys(map).length ? map : null;
}

function normalizeSeriesVolumesField(seriesData) {
  if (!seriesData || !Array.isArray(seriesData.volumes)) return seriesData;
  return {
    ...seriesData,
    volumes: seriesData.volumes.length,
    volume_titles:
      seriesData.volume_titles || volumeTitlesFromLibraryVolumes(seriesData.volumes) || {},
  };
}

function mapStaticWikidataWorksToOlBooks(works) {
  return (works || []).map((w, i) => {
    const titleFr = w.title_fr || '';
    const titleEn = w.title_en || '';
    const primary = titleFr || titleEn || 'Œuvre';
    const vn = parseVolumeFromWork(w.volume);
    return {
      title: primary,
      display_title: displayBookTitleFrFirst({
        title: primary,
        original_title: titleFr && titleEn && titleFr !== titleEn ? titleEn : undefined,
      }),
      volume_number: vn != null ? vn : i + 1,
      first_publish_year: w.publication_date ? parseInt(String(w.publication_date).slice(0, 4), 10) : null,
      cover_url: null,
      ol_key: null,
      work_qid: w.work_qid,
      isFromStaticWikidata: true,
    };
  });
}

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
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTomes, setSelectedTomes] = useState(new Set());
  const [isSeriesOwned, setIsSeriesOwned] = useState(false);
  const [seriesStatus, setSeriesStatus] = useState('to_read');
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

  // ✅ NOUVELLE FONCTION : Charger les préférences de lecture depuis la base de données
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
          return data.tome_statuses;
        }
        // Fallback legacy : read_tomes → statut "lu"
        const legacy = {};
        (data.read_tomes || []).forEach(n => { legacy[String(n)] = { status: 'lu', currentPage: null }; });
        return legacy;
      } else {
        return {};
      }
    } catch (error) {
      console.error('❌ Erreur lors du chargement des préférences:', error);
      return {};
    }
  };

  // ✅ NOUVELLE FONCTION : Sauvegarder les préférences de lecture en base de données
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
        console.log('✅ Préférences sauvegardées:', data);
        return true;
      } else {
        console.error('❌ Erreur lors de la sauvegarde:', response.status);
        return false;
      }
    } catch (error) {
      console.error('❌ Erreur lors de la sauvegarde des préférences:', error);
      return false;
    }
  };

  // ✅ NOUVELLE FONCTION : Charger les préférences pour la série courante
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
      // Ne mettre à jour que si on a des données significatives
      if (hasRead || hasInProgress) {
        setSeriesStatus(derivedStatus);
      }
    } catch (error) {
      console.error('❌ Erreur chargement préférences:', error);
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

  // ✅ NOUVELLE FONCTION : Calculer et mettre à jour automatiquement le statut de la série
  const calculateAndUpdateSeriesStatus = async (newReadTomes) => {
    if (!enrichedSeries?.name || !enrichedSeries?.volumes) {
      console.log('🔄 Calcul statut ignoré - série non valide ou données manquantes');
      return;
    }

    // ✅ CORRECTION : Permettre le calcul même si la série n'est pas encore "officiellement" possédée
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
          icon: '🎯',
          duration: 3000
        });
        
      } catch (error) {
        console.error('❌ Erreur lors de la mise à jour automatique du statut:', error);
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
        icon: '📈',
        duration: 2000
      });
    }
  };

  // Changer le statut d'un tome (non_lu | en_cours | lu) + page optionnelle
  const handleTomeStatusChange = async (tomeNumber, newStatus, currentPage = null) => {
    const newStatuses = {
      ...tomeStatuses,
      [String(tomeNumber)]: { status: newStatus, currentPage }
    };
    setTomeStatuses(newStatuses);

    // Suggestion tomes précédents si on marque "lu"
    if (newStatus === 'lu' && tomeNumber > 1) {
      const missingPrevious = [];
      for (let i = 1; i < tomeNumber; i++) {
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
      Object.entries(newStatuses).filter(([,v]) => v.status === 'lu').map(([k]) => Number(k))
    );
    // Statut : en_cours si au moins 1 tome lu ou en cours
    const hasInProgress = Object.values(newStatuses).some(v => v.status === 'en_cours');
    const hasRead = newReadSet.size > 0;
    const totalTomes = resolveVolumesCount(
      enrichedSeries?.volumes,
      olBooks.length || (series?.books?.length) || 0
    );
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
      newStatuses[String(tomeNumber)] = { status: 'lu', currentPage: null };
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

  // Enrichir les données de série au chargement
  const enrichedSeries = enrichSeriesData(series);

  // Options de statut pour les boutons rapides
  const statusOptions = [
    { value: 'to_read', label: 'À lire', color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300', emoji: '' },
    { value: 'reading', label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300', emoji: '' },
    { value: 'completed', label: 'Terminé', color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300', emoji: '' },
  ];

  // Fonction pour changer rapidement le statut de la série
  const handleQuickStatusChange = async (newStatus) => {
    // Autoriser si la série est possédée OU si elle contient des livres détectés
    const hasDetectedBooks = (series?.books || []).length > 0;
    if (!isSeriesOwned && !hasDetectedBooks) {
      toast.error('Vous devez d\'abord ajouter cette série à votre bibliothèque');
      return;
    }

    const token = localStorage.getItem('token');
    const backendUrl = API_BASE_URL;
    const statusLabel = statusOptions.find(s => s.value === newStatus)?.label || newStatus;

    // Mise à jour optimiste de l'UI
    setSeriesStatus(newStatus);

    try {
      let updatedViaBooks = false;

      // 1a. Livres déjà présents dans l'objet série (détection automatique ou série possédée)
      const booksInSeries = series.books || [];

      if (booksInSeries.length > 0) {
        const results = await Promise.all(
          booksInSeries.map(book =>
            fetch(`${backendUrl}/api/books/${book.id}`, {
              method: 'PUT',
              headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({ status: newStatus })
            }).then(r => r.ok)
          )
        );
        if (results.some(r => r)) updatedViaBooks = true;
      }

      // 1b. Fallback saga : chercher les livres par champ saga si series.books vide
      if (!updatedViaBooks) {
        const response = await fetch(
          `${backendUrl}/api/books/all?saga=${encodeURIComponent(series.name)}&limit=100`,
          { headers: { 'Authorization': `Bearer ${token}` } }
        );
        if (response.ok) {
          const data = await response.json();
          const seriesBooks = (data.items || []).filter(book =>
            (book.saga || '').toLowerCase().trim() === (series.name || '').toLowerCase().trim()
          );
          if (seriesBooks.length > 0) {
            const results = await Promise.all(
              seriesBooks.map(book =>
                fetch(`${backendUrl}/api/books/${book.id}`, {
                  method: 'PUT',
                  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                  body: JSON.stringify({ status: newStatus })
                }).then(r => r.ok)
              )
            );
            if (results.some(r => r)) updatedViaBooks = true;
          }
        }
      }

      // 2. Fallback series_library : série ajoutée via le panneau séries (sans livres individuels)
      if (!updatedViaBooks) {
        const libEntry = (userSeriesLibrary || []).find(
          s => (s.series_name || s.name || '').toLowerCase().trim() === (series.name || '').toLowerCase().trim()
        );
        const seriesId = libEntry?.id || series.id;
        if (seriesId) {
          await fetch(`${backendUrl}/api/series/library/${seriesId}`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ series_status: newStatus })
          });
        }
      }

      toast.success(`Statut de la série "${series.name}" : ${statusLabel}`);
      if (onUpdate) {
        await onUpdate();
        setSeriesStatus(newStatus);
      }
    } catch (error) {
      console.error('❌ Erreur changement statut:', error);
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
        if (match) setSeriesStatus(match.status || 'to_read');
      } else {
        setIsSeriesOwned(false);
      }
    } catch (e) {
      if (e?.name !== 'AbortError') setIsSeriesOwned(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !series) return;

    let cancelled = false;
    const abortController = new AbortController();

    setTomeStatuses({});
    setOlBooks([]);
    setMissingPreviousWarning(null);
    setShowWdRaw(false);
    setVerification(null);
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
    
    try {
      setLoading(true);
      // Charger les livres depuis la bibliothèque perso
      const booksData = await bookService.getBooksBySaga(series.name);
      setBooks(booksData.sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0)));
    } catch (error) {
      console.error('Erreur lors du chargement des livres de la série:', error);
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
        console.warn('Vérification des tomes indisponible:', error);
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
        console.warn('Series OL merge (static WD) failed:', e);
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
      console.warn('Series books fetch failed:', e);
    }
  };

  const handleTomeToggle = async (book, isRead) => {
    try {
      await bookService.toggleTomeStatus(series.name, book.volume_number, isRead);
      await loadSeriesBooks();
      if (onUpdate) onUpdate();
      toast.success(`Tome ${book.volume_number} marqué comme ${isRead ? 'lu' : 'non lu'}`);
    } catch (error) {
      console.error('Erreur lors de la mise à jour du tome:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'reading':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return 'Lu';
      case 'reading': return 'En cours';
      default: return 'Non lu';
    }
  };

  const getCategoryEmoji = (category) => {
    switch (category) {
      case 'bd': return '🎨';
      case 'manga': return '🇯🇵';
      case 'roman': return '📚';
      default: return '📖';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-end md:items-center justify-center z-50 md:p-4">
      <div className="modal-content-wide shadow-2xl overflow-hidden w-full md:w-auto">
        
        {/* Barre mobile sticky : fermeture toujours visible */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 md:hidden border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Série</span>
          <button type="button" onClick={onClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-4 sm:p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between md:gap-4">
            <div className="flex min-w-0 flex-1 items-start gap-3 sm:gap-4">
              {/* Image de couverture ou icône de série */}
              <div className="h-20 w-14 shrink-0 rounded-lg shadow-md overflow-hidden sm:w-16">
                {series.cover_url ? (
                  <img 
                    src={series.cover_url} 
                    alt={`Couverture de ${series.name}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Fallback vers le dégradé si l'image ne charge pas
                      e.target.style.display = 'none';
                      e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div 
                  className={`w-full h-full bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center text-white text-2xl ${series.cover_url ? 'hidden' : 'flex'}`}
                >
                  {getCategoryEmoji(series?.category)}
                </div>
              </div>
              
              <div className="min-w-0 flex-1">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-1 break-words">
                  {series?.name}
                </h2>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-2">
                  {series?.author ? (
                    <>
                      par{' '}
                      <button 
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onAuthorClick) onAuthorClick(series?.author);
                        }}
                        className="text-left text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
                      >
                        {series?.author}
                      </button>
                    </>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Référentiel Wikidata statique</span>
                  )}
                </p>
                <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm">
                  <span className={`px-2 py-1 rounded-full font-medium ${getStatusBadge(seriesStatus)}`}>
                    {getStatusLabel(seriesStatus)}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    📚 {resolveVolumesCount(
                      enrichedSeries?.volumes,
                      olBooks.length || books.length || (series?.books?.length) || 0
                    )} tome(s)
                  </span>
                  {series.fromStaticWikidata && series.staticWikidataDetail && (
                    <>
                      <a
                        href={`https://www.wikidata.org/wiki/${series.wikidata_qid || series.staticWikidataDetail.qid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 dark:text-indigo-400 hover:underline"
                      >
                        Wikidata ↗
                      </a>
                      <button
                        type="button"
                        onClick={() => setShowWdRaw((v) => !v)}
                        className="text-gray-600 dark:text-gray-400 hover:underline"
                      >
                        {showWdRaw ? 'Masquer JSON' : 'JSON brut'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex w-full flex-col gap-2 md:w-auto md:shrink-0 md:items-end">
              {/* Bouton Ajouter — identique à celui des livres individuels (pleine largeur sur mobile) */}
              {onAddSeries && !isSeriesOwned && (
                <button
                  type="button"
                  onClick={async () => {
                    if (isAdding || addDone) return;
                    setIsAdding(true);
                    try {
                      await onAddSeries({ ...series, mergedLibraryVolumes: olBooks });
                      setAddDone(true);
                      setTimeout(() => {
                        checkIfSeriesOwned();
                        setIsAdding(false);
                        setAddDone(false);
                      }, 1000);
                    } catch (error) {
                      console.error('Erreur lors de l\'ajout de la série:', error);
                      toast.error(error.message || 'Erreur lors de l\'ajout de la série');
                      setIsAdding(false);
                    }
                  }}
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

              <button
                type="button"
                onClick={onClose}
                className="hidden md:block p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                aria-label="Fermer"
              >
                <span className="text-xl leading-none">✕</span>
              </button>
            </div>
          </div>
        </div>

        {showWdRaw && series.staticWikidataDetail && (
          <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6">
            <pre className="max-h-56 overflow-auto rounded bg-gray-50 p-3 text-left text-[10px] leading-snug text-gray-800 dark:bg-gray-900 dark:text-gray-200 sm:text-xs">
              {JSON.stringify(series.staticWikidataDetail, null, 2)}
            </pre>
          </div>
        )}

        {/* Section Résumé de la série */}
        {enrichedSeries?.description && (
          <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-4 sm:px-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              <BookOpenIcon className="w-5 h-5 mr-2 text-purple-600 dark:text-purple-400" />
              Résumé de la série
            </h3>
            <div className="prose prose-gray dark:prose-invert max-w-none">
              <p className="text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                {enrichedSeries.description}
              </p>
            </div>
          </div>
        )}

        {/* Boutons rapides de changement de statut - MÊME EMPLACEMENT QUE DANS BookDetailModal */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-4 sm:px-6">
          <div className="mb-2 flex flex-col gap-1 sm:flex-row sm:items-center sm:flex-wrap">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Changer le statut rapidement :</h3>
            <span className="text-xs text-gray-500 sm:ml-2">
              (Série possédée: {isSeriesOwned ? '✅' : '❌'})
            </span>
          </div>
          <div className="flex w-full max-w-md overflow-hidden rounded-lg border border-gray-200 dark:border-gray-600 sm:w-fit">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  handleQuickStatusChange(option.value);
                }}
                className={`flex flex-1 items-center justify-center gap-1 px-2 py-2.5 text-xs font-medium transition-all sm:space-x-2 sm:px-4 sm:py-2 sm:text-sm ${
                  seriesStatus === option.value
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
                title={`Marquer comme ${option.label}`}
                disabled={!isSeriesOwned}
              >
                <span className="text-base">{option.emoji}</span>
                <span>{option.label}</span>
              </button>
            ))}
          </div>
          {!isSeriesOwned && (
            <p className="text-xs text-gray-500 mt-2">
              Ajoutez d'abord cette série à votre bibliothèque pour changer son statut
            </p>
          )}
        </div>

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

        {/* Liste des tomes avec mini-fiches dropdown */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-4 sm:px-6">
          <div className="sticky top-0 z-10 -mx-4 mb-3 flex items-center justify-between border-b border-gray-100 bg-white px-4 py-2 dark:border-gray-800 dark:bg-gray-800 sm:static sm:mx-0 sm:mb-3 sm:border-0 sm:bg-transparent sm:p-0 dark:sm:bg-transparent">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white sm:text-lg">Liste des tomes</h3>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300 sm:hidden"
            >
              Fermer
            </button>
          </div>
          
          {(resolveVolumesCount(enrichedSeries?.volumes) > 0) || olBooks.length > 0 ? (
            <div className="space-y-1">
              {(() => {
                const volumeCount = resolveVolumesCount(enrichedSeries?.volumes);
                // Construire la liste finale : préférence enrichedSeries (base statique) > olBooks (Wikidata/OL)
                if (volumeCount > 0 && !enrichedSeries.fromFallbackBooks) {
                  // Source : EXTENDED_SERIES_DATABASE → style TomeDropdown exact comme Harry Potter
                  return Array.from({ length: volumeCount }, (_, index) => {
                    const tomeNumber = index + 1;
                    const tomeTitle = enrichedSeries.volume_titles?.[tomeNumber] || `${enrichedSeries.name} - Tome ${tomeNumber}`;
                    const isRead = readTomes.has(tomeNumber);
                    return (
                      <TomeDropdown
                        key={tomeNumber}
                        tomeNumber={tomeNumber}
                        tomeTitle={tomeTitle}
                        seriesData={enrichedSeries}
                        tomeStatus={tomeStatuses[String(tomeNumber)]?.status || 'non_lu'}
                        currentPage={tomeStatuses[String(tomeNumber)]?.currentPage || null}
                        onStatusChange={handleTomeStatusChange}
                        onToggleRead={handleTomeReadToggle}
                      />
                    );
                  });
                }

                // Source : Wikidata ou OL → construire un enrichedSeries synthétique
                const booksToShowRaw = olBooks.length > 0 ? olBooks : (series.books || []);
                const booksToShow = mergeOpenLibraryBooksByVolume([...booksToShowRaw]).sort(sortOpenLibraryBooksByVolume);
                const syntheticVolumeTitles = {};
                booksToShow.forEach((b, i) => {
                  const num = b.volume_number || (i + 1);
                  syntheticVolumeTitles[num] = displayBookTitleFrFirst(b) || `${series.name} - Tome ${num}`;
                });
                const syntheticSeries = {
                  ...enrichedSeries,
                  volumes: booksToShow.length,
                  volume_titles: syntheticVolumeTitles,
                };
                return booksToShow.map((book, index) => {
                  const tomeNumber = book.volume_number || (index + 1);
                  const tomeTitle = syntheticVolumeTitles[tomeNumber] || displayBookTitleFrFirst(book);
                  return (
                    <TomeDropdown
                      key={book.ol_key || book.id || `tome-${tomeNumber}-${index}`}
                      tomeNumber={tomeNumber}
                      tomeTitle={tomeTitle}
                      seriesData={syntheticSeries}
                      tomeStatus={tomeStatuses[String(tomeNumber)]?.status || 'non_lu'}
                      currentPage={tomeStatuses[String(tomeNumber)]?.currentPage || null}
                      onStatusChange={handleTomeStatusChange}
                      onToggleRead={handleTomeReadToggle}
                    />
                  );
                });
              })()}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              Informations sur les tomes non disponibles pour cette série
            </p>
          )}
        </div>

        {/* Modal de confirmation pour cocher les tomes précédents */}
        {missingPreviousWarning && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-full">
                  <ExclamationTriangleIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Suggestion de lecture
                </h3>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-700 dark:text-gray-300 mb-3">
                  Vous avez marqué comme lu le <strong>tome {missingPreviousWarning.currentTome}</strong>.
                </p>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  Souhaitez-vous également marquer comme lus les tomes précédents ?
                </p>
                <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  <strong>Tomes concernés :</strong> {missingPreviousWarning.missingTomes.join(', ')}
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={handleCheckPreviousTomes}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 text-sm font-medium"
                >
                  Oui, cocher les précédents
                </button>
                <button
                  onClick={() => setMissingPreviousWarning(null)}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg transition-colors duration-200 text-sm font-medium"
                >
                  Non, juste ce tome
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Books List (Section détaillée existante) - SUPPRIMÉE SUR DEMANDE UTILISATEUR */}

        {/* ✅ NOUVEAU : Section Chapitres Individuels et Prédictions - UNIQUEMENT POUR LES MANGAS */}
        {series && series.name && series.category === 'manga' && (
          <ChapterSection 
            seriesName={series.name} 
            onClose={() => {/* Optionnel: logique fermeture section */}} 
          />
        )}

        {/* Bouton Retirer — identique à celui du modal livre individuel, placé en bas */}
        {(isSeriesOwned || series.isOwnedSeries || series.isLibrarySeries || series.isSeriesCard || (series.books && series.books.length > 0) || books.length > 0) && (
          <div className="px-4 sm:px-6 py-4 border-t border-gray-200 dark:border-gray-700">
            {confirmDelete ? (
              <div className="flex items-center justify-between bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                <span className="text-sm text-red-700 dark:text-red-300 font-medium">
                  Retirer définitivement cette série ?
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="px-3 py-1.5 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleDeleteSeries}
                    disabled={deleting}
                    className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
                  >
                    {deleting ? 'Suppression…' : 'Confirmer'}
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
            )}
          </div>
        )}

      </div>
    </div>
  );
};

export default SeriesDetailModal;