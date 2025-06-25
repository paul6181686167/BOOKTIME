import React, { useState } from 'react';
import { XMarkIcon, SparklesIcon, PlusIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import LanguageSelector from './LanguageSelector';

// Service Open Library (intégré temporairement)
const openLibraryService = {
  async searchBooks(query, limit = 10) {
    try {
      const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(
        `${API_BASE_URL}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=${limit}`
      );
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la recherche Open Library:', error);
      throw error;
    }
  },

  async importBook(olKey, category) {
    try {
      const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const response = await fetch(`${API_BASE_URL}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ol_key: olKey,
          category: category
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de l\'import Open Library:', error);
      throw error;
    }
  }
};

const AddBookModal = ({ onClose, onAdd, defaultCategory = 'roman' }) => {
  const [mode, setMode] = useState('search'); // 'search' ou 'manual'
  
  // États pour la recherche Open Library
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [importingBooks, setImportingBooks] = useState(new Set());

  // États pour le formulaire manuel
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    category: defaultCategory,
    description: '',
    cover_url: '',
    total_pages: '',
    isbn: '',
    saga: '',
    series: '',
    volume_number: '',
    publication_year: '',
    publisher: '',
    genre: [],
    original_language: 'français',
    available_translations: [],
    reading_language: 'français',
  });
  const [isLoading, setIsLoading] = useState(false);

  const categories = [
    { value: 'roman', label: 'Roman', icon: '📚' },
    { value: 'bd', label: 'Bande dessinée', icon: '🎨' },
    { value: 'manga', label: 'Manga', icon: '🇯🇵' },
  ];

  // Recherche Open Library
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    try {
      const results = await openLibraryService.searchBooks(searchQuery, 8);
      setSearchResults(results.books || []);
    } catch (error) {
      console.error('Erreur de recherche:', error);
      setSearchResults([]);
      toast.error('Erreur lors de la recherche');
    } finally {
      setSearchLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleImportBook = async (book) => {
    if (!book.ol_key) return;

    setImportingBooks(prev => new Set(prev).add(book.ol_key));
    try {
      const importedBook = await openLibraryService.importBook(book.ol_key, book.category);
      await onAdd(importedBook);
      toast.success('Livre importé avec succès !');
      onClose();
    } catch (error) {
      console.error('Erreur d\'import:', error);
      toast.error(`Erreur lors de l'import: ${error.message}`);
    } finally {
      setImportingBooks(prev => {
        const newSet = new Set(prev);
        newSet.delete(book.ol_key);
        return newSet;
      });
    }
  };

  // Formulaire manuel
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim() || !formData.author.trim()) {
      toast.error('Le titre et l\'auteur sont obligatoires');
      return;
    }

    setIsLoading(true);
    try {
      const bookData = {
        ...formData,
        total_pages: formData.total_pages ? parseInt(formData.total_pages) : null,
        volume_number: formData.volume_number ? parseInt(formData.volume_number) : null,
        publication_year: formData.publication_year ? parseInt(formData.publication_year) : null,
        saga: formData.saga || null,
        series: formData.series || null,
        publisher: formData.publisher || null,
        genre: formData.genre.length > 0 ? formData.genre : null,
      };
      
      await onAdd(bookData);
      toast.success('Livre ajouté avec succès !');
      onClose();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout du livre');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'roman': return 'bg-blue-100 text-blue-800';
      case 'bd': return 'bg-purple-100 text-purple-800';
      case 'manga': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-4xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Ajouter un livre</h2>
          <button
            onClick={onClose}
            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Onglets */}
        <div className="flex space-x-1 mb-6 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setMode('search')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${
              mode === 'search'
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
            }`}
          >
            <SparklesIcon className="h-4 w-4" />
            <span>Recherche Open Library</span>
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`flex-1 flex items-center justify-center space-x-2 px-4 py-2 rounded-md transition-colors ${
              mode === 'manual'
                ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
            }`}
          >
            <PlusIcon className="h-4 w-4" />
            <span>Ajout manuel</span>
          </button>
        </div>

        {/* Contenu selon le mode */}
        {mode === 'search' ? (
          <div className="space-y-6">
            {/* Barre de recherche */}
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Rechercher un titre, auteur, ISBN..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={searchLoading || !searchQuery.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {searchLoading ? (
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                ) : (
                  'Rechercher'
                )}
              </button>
            </div>

            {/* Résultats de recherche */}
            {searchResults.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Résultats ({searchResults.length})
                </h3>
                
                <div className="grid gap-4">
                  {searchResults.map((book, index) => (
                    <div
                      key={`${book.ol_key}-${index}`}
                      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex space-x-4">
                        {/* Couverture */}
                        <div className="flex-shrink-0">
                          {book.cover_url ? (
                            <img
                              src={book.cover_url}
                              alt={book.title}
                              className="w-16 h-20 object-cover rounded"
                              onError={(e) => {
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <div
                            className={`w-16 h-20 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center ${book.cover_url ? 'hidden' : 'flex'}`}
                          >
                            <span className="text-2xl">📚</span>
                          </div>
                        </div>

                        {/* Informations */}
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {book.title}
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {book.author}
                          </p>
                          
                          <div className="flex items-center space-x-2 mt-2">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(book.category)}`}>
                              {book.category}
                            </span>
                            {book.publication_year && (
                              <span className="text-xs text-gray-500">
                                {book.publication_year}
                              </span>
                            )}
                            {book.total_pages && (
                              <span className="text-xs text-gray-500">
                                {book.total_pages} pages
                              </span>
                            )}
                          </div>

                          {/* Bouton d'import */}
                          <button
                            onClick={() => handleImportBook(book)}
                            disabled={importingBooks.has(book.ol_key)}
                            className="mt-3 inline-flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-xs rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {importingBooks.has(book.ol_key) ? (
                              <>
                                <div className="animate-spin h-3 w-3 border border-white border-t-transparent rounded-full"></div>
                                <span>Import...</span>
                              </>
                            ) : (
                              <>
                                <PlusIcon className="h-3 w-3" />
                                <span>Importer</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* État vide */}
            {!searchLoading && searchResults.length === 0 && searchQuery && (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">
                  Aucun résultat trouvé pour "{searchQuery}"
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                  Essayez avec d'autres mots-clés ou utilisez l'ajout manuel
                </p>
              </div>
            )}
          </div>
        ) : (
          /* Formulaire manuel */
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Titre */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Titre *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                placeholder="Le nom du livre"
                required
              />
            </div>

            {/* Auteur */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Auteur *
              </label>
              <input
                type="text"
                name="author"
                value={formData.author}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                placeholder="Nom de l'auteur"
                required
              />
            </div>

            {/* Catégorie */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Catégorie
              </label>
              <div className="grid grid-cols-3 gap-2">
                {categories.map((category) => (
                  <button
                    key={category.value}
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, category: category.value }))}
                    className={`p-3 rounded-lg border-2 transition-colors ${
                      formData.category === category.value
                        ? 'border-booktime-500 bg-booktime-50 dark:bg-booktime-900/30 text-booktime-700 dark:text-booktime-300'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-xl mb-1">{category.icon}</div>
                      <div className="text-sm font-medium">{category.label}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Section Langues */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">🌍 Informations linguistiques</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Langue originale */}
                <div>
                  <LanguageSelector
                    label="Langue originale *"
                    selectedLanguages={[formData.original_language]}
                    onLanguagesChange={(languages) => setFormData(prev => ({ ...prev, original_language: languages[0] || 'français' }))}
                    single={true}
                    placeholder="Sélectionner la langue originale"
                  />
                </div>

                {/* Langue de lecture */}
                <div>
                  <LanguageSelector
                    label="Langue de lecture *"
                    selectedLanguages={[formData.reading_language]}
                    onLanguagesChange={(languages) => setFormData(prev => ({ ...prev, reading_language: languages[0] || 'français' }))}
                    single={true}
                    placeholder="Langue dans laquelle vous lisez"
                  />
                </div>
              </div>

              {/* Traductions disponibles */}
              <div className="mt-4">
                <LanguageSelector
                  label="Traductions disponibles"
                  selectedLanguages={formData.available_translations}
                  onLanguagesChange={(languages) => setFormData(prev => ({ ...prev, available_translations: languages }))}
                  maxSelections={10}
                  placeholder="Ajouter les langues de traduction disponibles"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Langues dans lesquelles cette œuvre a été traduite (optionnel)
                </p>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                placeholder="Résumé ou description du livre"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* URL de couverture */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  URL de la couverture
                </label>
                <input
                  type="url"
                  name="cover_url"
                  value={formData.cover_url}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                  placeholder="https://example.com/cover.jpg"
                />
              </div>

              {/* Nombre de pages */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nombre de pages
                </label>
                <input
                  type="number"
                  name="total_pages"
                  value={formData.total_pages}
                  onChange={handleChange}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                  placeholder="350"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* ISBN */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  ISBN
                </label>
                <input
                  type="text"
                  name="isbn"
                  value={formData.isbn}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                  placeholder="978-2-123456-78-9"
                />
              </div>

              {/* Saga */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Saga / Série
                </label>
                <input
                  type="text"
                  name="saga"
                  value={formData.saga}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                  placeholder="Nom de la saga"
                />
              </div>
            </div>

            {/* Boutons */}
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-booktime-500 dark:focus:ring-offset-gray-800 transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-booktime-600 border border-transparent rounded-md hover:bg-booktime-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-booktime-500 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Ajout...' : 'Ajouter'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default AddBookModal;