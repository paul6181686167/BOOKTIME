import React, { useState, useEffect } from 'react';
import { 
  RectangleStackIcon, 
  BookOpenIcon, 
  CheckCircleIcon, 
  PlusIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';
import MissingVolumesDetector from './MissingVolumesDetector';
import toast from 'react-hot-toast';

const SagasPanel = ({ onSagaSelect }) => {
  const [sagas, setSagas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSaga, setSelectedSaga] = useState(null);
  const [autoAddingFor, setAutoAddingFor] = useState(null);
  const [showMissingVolumes, setShowMissingVolumes] = useState(null);

  useEffect(() => {
    loadSagas();
  }, []);

  const loadSagas = async () => {
    try {
      setLoading(true);
      const data = await bookService.getSagas();
      setSagas(data);
    } catch (error) {
      console.error('Erreur lors du chargement des sagas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSagaClick = async (saga) => {
    setSelectedSaga(saga);
    if (onSagaSelect) {
      try {
        const books = await bookService.getBooksBySaga(saga.name);
        onSagaSelect(books, saga);
      } catch (error) {
        console.error('Erreur lors du chargement des livres de la saga:', error);
      }
    }
  };

  const handleAutoAdd = async (sagaName, event) => {
    event.stopPropagation(); // Empêche la sélection de la saga
    setAutoAddingFor(sagaName);
    
    try {
      await bookService.autoAddNextVolume(sagaName);
      toast.success(`Prochain tome de ${sagaName} ajouté automatiquement !`);
      await loadSagas(); // Recharger les sagas pour mettre à jour les stats
      
      // Recharger les livres si cette saga est sélectionnée
      if (selectedSaga?.name === sagaName && onSagaSelect) {
        const books = await bookService.getBooksBySaga(sagaName);
        onSagaSelect(books, selectedSaga);
      }
    } catch (error) {
      console.error('Erreur lors de l\'ajout automatique:', error);
      toast.error('Erreur lors de l\'ajout automatique du prochain tome');
    } finally {
      setAutoAddingFor(null);
    }
  };

  const handleAnalyzeMissingVolumes = (sagaName, event) => {
    event.stopPropagation();
    setShowMissingVolumes(sagaName);
  };

  const handleMissingVolumesImport = async (importedBook) => {
    await loadSagas(); // Recharger les sagas pour mettre à jour les stats
    
    // Recharger les livres si cette saga est sélectionnée
    if (selectedSaga && onSagaSelect) {
      try {
        const books = await bookService.getBooksBySaga(selectedSaga.name);
        onSagaSelect(books, selectedSaga);
      } catch (error) {
        console.error('Erreur lors du rechargement des livres de la saga:', error);
      }
    }
  };

  const getCompletionPercentage = (saga) => {
    if (saga.books_count === 0) return 0;
    return Math.round((saga.completed_books / saga.books_count) * 100);
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'roman': return '📚';
      case 'bd': return '🎨';
      case 'manga': return '🇯🇵';
      default: return '📖';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Sagas</h3>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-20 bg-gray-200 rounded loading-skeleton"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Sagas</h3>
        <span className="text-sm text-gray-500">{sagas.length} sagas</span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {sagas.map((saga) => (
          <div
            key={saga.name}
            onClick={() => handleSagaClick(saga)}
            className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
              selectedSaga?.name === saga.name
                ? 'border-booktime-500 bg-booktime-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{getCategoryIcon(saga.category)}</span>
                  <h4 className="font-medium text-gray-900 text-sm">{saga.name}</h4>
                </div>
                
                <div className="text-xs text-gray-600 mb-2">
                  par {saga.author}
                </div>
                
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-4 text-xs text-gray-600">
                    <div className="flex items-center space-x-1">
                      <BookOpenIcon className="h-3 w-3" />
                      <span>{saga.books_count} tome{saga.books_count > 1 ? 's' : ''}</span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <CheckCircleIcon className="h-3 w-3" />
                      <span>{saga.completed_books} terminé{saga.completed_books > 1 ? 's' : ''}</span>
                    </div>
                  </div>
                  
                  <span className="text-xs font-medium text-booktime-600">
                    {getCompletionPercentage(saga)}%
                  </span>
                </div>
                
                {/* Barre de progression */}
                <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                  <div 
                    className="bg-booktime-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${getCompletionPercentage(saga)}%` }}
                  />
                </div>
                
                {/* Prochain tome */}
                {saga.next_volume && (
                  <div className="text-xs text-gray-500">
                    Prochain tome : #{saga.next_volume}
                  </div>
                )}
              </div>
              
              {/* Boutons d'action */}
              <div className="flex space-x-2">
                {/* Bouton d'analyse des tomes manquants */}
                <button
                  onClick={(e) => handleAnalyzeMissingVolumes(saga.name, e)}
                  className="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-full transition-colors"
                  title="Analyser les tomes manquants"
                >
                  <MagnifyingGlassIcon className="h-4 w-4" />
                </button>
                
                {/* Bouton d'ajout automatique */}
                <button
                  onClick={(e) => handleAutoAdd(saga.name, e)}
                  disabled={autoAddingFor === saga.name}
                  className="p-2 text-gray-400 hover:text-booktime-600 hover:bg-booktime-50 rounded-full transition-colors disabled:opacity-50"
                  title="Ajouter automatiquement le prochain tome"
                >
                  {autoAddingFor === saga.name ? (
                    <div className="h-4 w-4 border-2 border-booktime-500 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <PlusIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SagasPanel;