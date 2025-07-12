import React, { useState, useEffect } from 'react';
import {
  BookOpenIcon,
  CheckCircleIcon,
  ClockIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';
import { EXTENDED_SERIES_DATABASE } from '../utils/seriesDatabaseExtended';
import TomeDropdown from './TomeDropdown'; // ← AJOUT : Import du nouveau composant
import toast from 'react-hot-toast';

const SeriesDetailModal = ({ 
  series, 
  isOpen, 
  onClose, 
  onUpdate,
  onAddSeries
}) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTomes, setSelectedTomes] = useState(new Set());
  const [autoCompleting, setAutoCompleting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [missingAnalysis, setMissingAnalysis] = useState(null);
  const [isSeriesOwned, setIsSeriesOwned] = useState(false);
  const [seriesStatus, setSeriesStatus] = useState('to_read');
  const [readTomes, setReadTomes] = useState(new Set()); // ← AJOUT: État des tomes lus/non lus
  const [missingPreviousWarning, setMissingPreviousWarning] = useState(null); // ← AJOUT: Avertissement tomes précédents manquants

  // ✅ NOUVELLE FONCTION : Charger les préférences de lecture depuis la base de données
  const loadReadingPreferences = async (seriesName) => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/series/reading-preferences/${encodeURIComponent(seriesName)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📚 Préférences de lecture chargées:', data);
        return new Set(data.read_tomes || []);
      } else {
        console.log('ℹ️ Aucune préférence trouvée, initialisation vide');
        return new Set();
      }
    } catch (error) {
      console.error('❌ Erreur lors du chargement des préférences:', error);
      return new Set();
    }
  };

  // ✅ NOUVELLE FONCTION : Sauvegarder les préférences de lecture en base de données
  const saveReadingPreferences = async (seriesName, readTomes) => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/series/reading-preferences`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          series_name: seriesName,
          read_tomes: [...readTomes]
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
      const preferences = await loadReadingPreferences(enrichedSeries.name);
      setReadTomes(preferences);
      console.log('📚 Préférences chargées pour', enrichedSeries.name, ':', preferences.size, 'tomes');
      
      // ✅ NOUVEAU : Calculer et mettre à jour le statut de la série au chargement
      await calculateAndUpdateSeriesStatus(preferences);
      
    } catch (error) {
      console.error('❌ Erreur chargement préférences:', error);
      // Fallback : initialiser vide en cas d'erreur
      setReadTomes(new Set());
    }
  };

  // Fonction pour enrichir les données de série avec les métadonnées de référence
  const enrichSeriesData = (series) => {
    if (!series?.name) return series;
    
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
    
    // Enrichir avec les données de référence si trouvées
    if (referenceData) {
      return {
        ...series,
        volumes: referenceData.volumes,
        volume_titles: referenceData.volume_titles, // ← AJOUT: Inclure les vrais noms des tomes
        volume_details: referenceData.volume_details, // ← AJOUT: Détails par tome pour mini-fiches
        description: referenceData.description,
        first_published: referenceData.first_published,
        status: referenceData.status,
        referenceFound: true
      };
    }
    
    return series;
  };

  // ✅ NOUVELLE FONCTION : Calculer et mettre à jour automatiquement le statut de la série
  const calculateAndUpdateSeriesStatus = async (newReadTomes) => {
    if (!enrichedSeries?.name || !enrichedSeries?.volumes) {
      console.log('🔄 Calcul statut ignoré - série non valide ou données manquantes');
      return;
    }

    // ✅ CORRECTION : Permettre le calcul même si la série n'est pas encore "officiellement" possédée
    // L'utilisateur peut marquer des tomes comme lus avant d'ajouter la série à sa bibliothèque
    const totalTomes = enrichedSeries.volumes;
    const readTomesCount = newReadTomes.size;
    
    console.log('📊 Calcul statut série:', {
      seriesName: enrichedSeries.name,
      totalTomes,
      readTomesCount,
      readTomes: Array.from(newReadTomes),
      isSeriesOwned
    });

    // Déterminer le nouveau statut selon les règles
    let newStatus = 'to_read'; // Par défaut
    
    if (readTomesCount === 0) {
      newStatus = 'to_read'; // Aucun tome lu = À lire
    } else if (readTomesCount === totalTomes) {
      newStatus = 'completed'; // Tous les tomes lus = Terminé
    } else {
      newStatus = 'reading'; // Quelques tomes lus = En cours
    }

    console.log('🎯 Nouveau statut calculé:', newStatus, 'depuis', seriesStatus);

    // ✅ CORRECTION : Seulement tenter la mise à jour API si la série est possédée
    // Sinon, juste mettre à jour l'état local pour l'affichage
    if (isSeriesOwned && newStatus !== seriesStatus) {
      console.log('🔄 Mise à jour statut série automatique (série possédée):', seriesStatus, '→', newStatus);
      
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
      console.log('📝 Mise à jour statut série local (série non possédée):', seriesStatus, '→', newStatus);
      
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
    } else {
      console.log('ℹ️ Statut série inchangé, pas de mise à jour nécessaire');
    }
  };

  // Fonction pour basculer l'état lu/non lu d'un tome avec sauvegarde en base de données
  const handleTomeReadToggle = async (tomeNumber) => {
    const newReadTomes = new Set(readTomes);
    
    if (newReadTomes.has(tomeNumber)) {
      // Décocher le tome
      newReadTomes.delete(tomeNumber);
      setMissingPreviousWarning(null); // Effacer l'avertissement si on décoche
    } else {
      // Cocher le tome
      newReadTomes.add(tomeNumber);
      
      // ✅ LOGIQUE SUGGESTION : Vérifier si des tomes précédents manquent
      if (tomeNumber > 1) {
        const missingPrevious = [];
        for (let i = 1; i < tomeNumber; i++) {
          if (!newReadTomes.has(i)) {
            missingPrevious.push(i);
          }
        }
        
        if (missingPrevious.length > 0) {
          setMissingPreviousWarning({
            currentTome: tomeNumber,
            missingTomes: missingPrevious
          });
        } else {
          setMissingPreviousWarning(null);
        }
      } else {
        setMissingPreviousWarning(null);
      }
    }
    
    // Mettre à jour l'état local immédiatement
    setReadTomes(newReadTomes);
    
    // ✅ PERSISTANCE : Sauvegarder en base de données
    if (enrichedSeries?.name) {
      const saved = await saveReadingPreferences(enrichedSeries.name, newReadTomes);
      if (saved) {
        console.log('✅ Préférences sauvegardées automatiquement');
      } else {
        console.warn('⚠️ Échec de la sauvegarde, état local maintenu');
        // Note: On garde l'état local même si la sauvegarde échoue
        // L'utilisateur peut réessayer et ça sera sauvegardé
      }
    }

    // ✅ NOUVEAU : Calculer et mettre à jour automatiquement le statut de la série
    await calculateAndUpdateSeriesStatus(newReadTomes);
  };

  // Fonction pour cocher automatiquement tous les tomes précédents avec sauvegarde
  const handleCheckPreviousTomes = async () => {
    if (!missingPreviousWarning) return;
    
    const newReadTomes = new Set(readTomes);
    // Ajouter tous les tomes manquants
    missingPreviousWarning.missingTomes.forEach(tomeNumber => {
      newReadTomes.add(tomeNumber);
    });
    
    // Mettre à jour l'état local
    setReadTomes(newReadTomes);
    
    // ✅ PERSISTANCE : Sauvegarder en base de données
    if (enrichedSeries?.name) {
      const saved = await saveReadingPreferences(enrichedSeries.name, newReadTomes);
      if (saved) {
        console.log('✅ Préférences sauvegardées après cochage automatique');
      } else {
        console.warn('⚠️ Échec de la sauvegarde, état local maintenu');
      }
    }
    
    // Effacer l'avertissement
    setMissingPreviousWarning(null);

    // ✅ NOUVEAU : Calculer et mettre à jour automatiquement le statut de la série
    await calculateAndUpdateSeriesStatus(newReadTomes);
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
    console.log('🎯 DÉBUT handleQuickStatusChange:', { newStatus, isSeriesOwned, series });
    
    if (!isSeriesOwned) {
      console.log('❌ Série non possédée, affichage erreur');
      toast.error('Vous devez d\'abord ajouter cette série à votre bibliothèque');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      console.log('🔑 Token trouvé:', !!token);
      console.log('🔄 Changement statut série:', series.name, 'vers', newStatus);
      
      // Rechercher le livre série dans la bibliothèque
      const response = await fetch(`${backendUrl}/api/books/all?saga=${encodeURIComponent(series.name)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('📡 Réponse recherche série:', { status: response.status, ok: response.ok });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📚 Données reçues:', data);
        
        // CORRECTION RCA: Même logique case-insensitive pour chercher le livre série
        const seriesBook = data.items?.find(book => 
          book.saga?.toLowerCase().includes(series.name.toLowerCase()) && 
          (book.is_series === true || book.title?.toLowerCase().includes('collection'))
        );
        
        if (seriesBook) {
          console.log('📖 Livre série trouvé:', seriesBook);
          // Mettre à jour le statut du livre série
          const updateResponse = await fetch(`${backendUrl}/api/books/${seriesBook.id}`, {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
          });
          
          console.log('🔄 Réponse mise à jour:', { status: updateResponse.status, ok: updateResponse.ok });
          
          if (updateResponse.ok) {
            const updatedBook = await updateResponse.json();
            console.log('✅ Livre mis à jour:', updatedBook);
            setSeriesStatus(newStatus);
            toast.success(`Statut de la série "${series.name}" changé vers "${statusOptions.find(s => s.value === newStatus)?.label}"`);
            
            // Actualiser la bibliothèque
            if (onUpdate) {
              console.log('🔄 Actualisation bibliothèque');
              onUpdate();
            }
          } else {
            const errorData = await updateResponse.json();
            console.error('❌ Erreur mise à jour:', errorData);
            toast.error('Erreur lors de la mise à jour du statut');
          }
        } else {
          console.error('❌ Livre série non trouvé dans les résultats');
          console.log('📋 Livres disponibles:', data.items?.map(b => ({ title: b.title, saga: b.saga, is_series: b.is_series })));
          toast.error('Livre série non trouvé dans la bibliothèque');
        }
      } else {
        const errorData = await response.json();
        console.error('❌ Erreur recherche série:', errorData);
        toast.error('Erreur lors de la recherche de la série');
      }
    } catch (error) {
      console.error('❌ Erreur générale changement statut:', error);
      toast.error('Erreur lors du changement de statut');
    }
  };

  // Fonction pour vérifier si la série est déjà dans la bibliothèque
  const checkIfSeriesOwned = async () => {
    if (!series?.name) {
      console.log('⚠️ Pas de nom de série fourni');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      console.log('🔍 Vérification série possédée:', series.name);
      console.log('🔑 Token disponible:', !!token);
      console.log('🌐 Backend URL:', backendUrl);
      
      // Rechercher les livres de cette saga
      const response = await fetch(`${backendUrl}/api/books/all?saga=${encodeURIComponent(series.name)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('📡 Réponse vérification:', { 
        status: response.status, 
        ok: response.ok,
        statusText: response.statusText 
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📚 Livres trouvés pour saga:', data);
        
        // CORRECTION RCA: Utiliser case-insensitive substring match pour compatibilité avec regex backend
        const hasSeriesBook = data.items && data.items.some(book => 
          book.saga?.toLowerCase().includes(series.name.toLowerCase()) && 
          (book.is_series === true || book.title?.toLowerCase().includes('collection'))
        );
        
        console.log('📖 Série déjà possédée:', hasSeriesBook);
        setIsSeriesOwned(hasSeriesBook);
        
        // Récupérer le statut de la série si elle existe
        if (hasSeriesBook) {
          // CORRECTION RCA: Même logique case-insensitive pour récupérer le statut
          const seriesBook = data.items.find(book => 
            book.saga?.toLowerCase().includes(series.name.toLowerCase()) && 
            (book.is_series === true || book.title?.toLowerCase().includes('collection'))
          );
          if (seriesBook) {
            setSeriesStatus(seriesBook.status || 'to_read');
            console.log('📊 Statut série récupéré:', seriesBook.status);
          }
        }
        
        console.log('✅ Série déjà possédée:', hasSeriesBook);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        console.error('❌ Erreur API vérification série:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });
        // Ne pas bloquer l'interface si l'API échoue
        setIsSeriesOwned(false);
      }
    } catch (error) {
      console.error('❌ Erreur lors de la vérification de la série:', error);
      // Ne pas bloquer l'interface si la vérification échoue
      setIsSeriesOwned(false);
    }
  };

  useEffect(() => {
    if (isOpen && series) {
      loadSeriesBooks();
      checkIfSeriesOwned();
      // ✅ PERSISTANCE : Charger les préférences depuis la base de données au lieu de réinitialiser
      loadReadingPreferencesForSeries();
      setMissingPreviousWarning(null); // ← AJOUT: Réinitialiser l'avertissement à chaque ouverture
    }
  }, [isOpen, series]);

  const loadSeriesBooks = async () => {
    if (!series?.name) return;
    
    try {
      setLoading(true);
      const booksData = await bookService.getBooksBySaga(series.name);
      setBooks(booksData.sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0)));
    } catch (error) {
      console.error('Erreur lors du chargement des livres de la série:', error);
      toast.error('Erreur lors du chargement des livres');
    } finally {
      setLoading(false);
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

  const handleAutoComplete = async () => {
    try {
      setAutoCompleting(true);
      const maxVolume = Math.max(...books.map(b => b.volume_number || 0));
      const targetVolume = Math.max(maxVolume + 10, 20);

      const result = await bookService.autoCompleteSaga(series.name, targetVolume);
      await loadSeriesBooks();
      if (onUpdate) onUpdate();
      toast.success(`${result.created_books?.length || 0} nouveaux tomes ajoutés !`);
    } catch (error) {
      console.error('Erreur lors de l\'auto-complétion:', error);
      toast.error('Erreur lors de l\'auto-complétion');
    } finally {
      setAutoCompleting(false);
    }
  };

  const handleAnalyzeMissing = async () => {
    try {
      setAnalyzing(true);
      const analysis = await bookService.analyzeMissingVolumes(series.name);
      setMissingAnalysis(analysis);
      
      if (analysis.missing_volumes.length > 0) {
        toast.success(`${analysis.missing_volumes.length} tome(s) manquant(s) détecté(s)`);
      } else {
        toast.success('Aucun tome manquant détecté');
      }
    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error);
      toast.error('Erreur lors de l\'analyse');
    } finally {
      setAnalyzing(false);
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="modal-content-wide shadow-2xl overflow-hidden">>
        
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              {/* Image de couverture ou icône de série */}
              <div className="w-16 h-20 rounded-lg flex items-center justify-center shadow-md overflow-hidden">
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
              
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                  {series?.name}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  par {series?.author}
                </p>
                <div className="flex items-center space-x-4 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(series?.status)}`}>
                    {getStatusLabel(series?.status)}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">
                    📚 {books.length} tome(s)
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">
                    🏆 {series?.completion_percentage || 0}% complété
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Bouton Ajouter fonctionnel (même style que BookDetailModal) */}
              {!isSeriesOwned && onAddSeries && (
                <button
                  onClick={async () => {
                    try {
                      console.log('🟢 Clic sur ajouter série:', series);
                      await onAddSeries(series);
                      // CORRECTION: Attendre un peu puis re-vérifier si la série est possédée
                      setTimeout(() => {
                        checkIfSeriesOwned();
                      }, 1000);
                    } catch (error) {
                      console.error('❌ Erreur lors de l\'ajout de la série:', error);
                    }
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors flex items-center space-x-2"
                >
                  <span>+</span>
                  <span>Ajouter à ma bibliothèque</span>
                </button>
              )}
              
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xl"
              >
                ✕
              </button>
            </div>
          </div>
        </div>

        {/* Section Résumé de la série */}
        {enrichedSeries?.description && (
          <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
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
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center mb-2">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Changer le statut rapidement :</h3>
            {/* Indicateur de debug */}
            <span className="ml-2 text-xs text-gray-500">
              (Série possédée: {isSeriesOwned ? '✅' : '❌'})
            </span>
          </div>
          <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 w-fit">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  console.log('🖱️ CLIC BOUTON STATUT:', {
                    option: option.value,
                    isSeriesOwned,
                    seriesName: series?.name
                  });
                  handleQuickStatusChange(option.value);
                }}
                className={`px-4 py-2 text-sm font-medium transition-all flex items-center space-x-2 ${
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

        {/* Actions Bar */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {selectedTomes.size > 0 && (
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
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleAnalyzeMissing}
                disabled={analyzing}
                className="p-2 text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-full transition-colors"
                title="Analyser les tomes manquants"
              >
                {analyzing ? (
                  <div className="w-5 h-5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <MagnifyingGlassIcon className="w-5 h-5" />
                )}
              </button>
              
              <button
                onClick={handleAutoComplete}
                disabled={autoCompleting}
                className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-full transition-colors"
                title="Auto-compléter la série"
              >
                {autoCompleting ? (
                  <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <SparklesIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Missing Volumes Analysis */}
        {missingAnalysis && missingAnalysis.missing_volumes.length > 0 && (
          <div className="bg-orange-50 dark:bg-orange-900/20 border-b border-orange-200 dark:border-orange-800 px-6 py-3">
            <div className="flex items-center space-x-2 text-orange-800 dark:text-orange-300">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span className="text-sm font-medium">
                {missingAnalysis.missing_volumes.length} tome(s) manquant(s) : 
                {missingAnalysis.missing_volumes.slice(0, 10).join(', ')}
                {missingAnalysis.missing_volumes.length > 10 && '...'}
              </span>
            </div>
          </div>
        )}

        {/* Liste des tomes avec mini-fiches dropdown */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Liste des tomes</h3>
          
          {enrichedSeries?.volumes && enrichedSeries.volumes > 0 ? (
            <div className="space-y-1">
              {Array.from({ length: enrichedSeries.volumes }, (_, index) => {
                const tomeNumber = index + 1;
                // Utiliser le titre spécifique s'il existe, sinon titre générique
                const tomeTitle = enrichedSeries.volume_titles?.[tomeNumber] || `${enrichedSeries.name} - Tome ${tomeNumber}`;
                const isRead = readTomes.has(tomeNumber);
                
                return (
                  <TomeDropdown
                    key={tomeNumber}
                    tomeNumber={tomeNumber}
                    tomeTitle={tomeTitle}
                    seriesData={enrichedSeries}
                    isRead={isRead}
                    onToggleRead={handleTomeReadToggle}
                  />
                );
              })}
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

      </div>
    </div>
  );
};

export default SeriesDetailModal;