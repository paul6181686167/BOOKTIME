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
import toast from 'react-hot-toast';

const SeriesDetailModal = ({ 
  series, 
  isOpen, 
  onClose, 
  onUpdate
}) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTomes, setSelectedTomes] = useState(new Set());
  const [autoCompleting, setAutoCompleting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (isOpen && series) {
      loadSeriesBooks();
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
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl">
        
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-20 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center text-white text-2xl">
                {getCategoryEmoji(series?.category)}
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
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xl"
              >
                ✕
              </button>
            </div>
          </div>
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

        {/* Books List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {books.map((book) => (
                <div
                  key={book.id}
                  className={`flex items-center justify-between p-4 rounded-lg border transition-all ${
                    selectedTomes.has(book.volume_number)
                      ? 'border-blue-300 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedTomes.has(book.volume_number)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedTomes);
                        if (e.target.checked) {
                          newSelected.add(book.volume_number);
                        } else {
                          newSelected.delete(book.volume_number);
                        }
                        setSelectedTomes(newSelected);
                      }}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    
                    <div className="w-8 h-10 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                      {book.cover_url ? (
                        <img 
                          src={book.cover_url} 
                          alt={book.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <BookOpenIcon className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                          Tome {book.volume_number || '?'}
                        </span>
                        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusBadge(book.status)}`}>
                          {getStatusLabel(book.status)}
                        </span>
                        {book.auto_added && (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">
                            Auto-ajouté
                          </span>
                        )}
                      </div>
                      
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                        {book.title}
                      </h4>
                      
                      {book.description && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                          {book.description.substring(0, 100)}...
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleTomeToggle(book, book.status !== 'completed')}
                      className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                        book.status === 'completed'
                          ? 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/20 dark:text-green-300'
                          : 'bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {book.status === 'completed' ? '✓ Lu' : 'Marquer comme lu'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SeriesDetailModal;