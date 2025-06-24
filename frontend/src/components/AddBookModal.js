import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import LanguageSelector from './LanguageSelector';

const AddBookModal = ({ onClose, onAdd, defaultCategory = 'roman' }) => {
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
    { value: 'bd', label: 'BD', icon: '🎨' },
    { value: 'manga', label: 'Manga', icon: '🇯🇵' },
  ];

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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Ajouter un livre</h2>
          <button
            onClick={onClose}
            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

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
      </div>
    </div>
  );
};

export default AddBookModal;