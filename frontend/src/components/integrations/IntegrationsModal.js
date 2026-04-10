/**
 * PHASE 3.5 - Modal d'Intégrations Externes
 * Interface pour les intégrations tierces et services externes
 */
import React, { useState, useEffect } from 'react';
import integrationsService from '../../services/integrationsService';

const IntegrationsModal = ({ isOpen, onClose, onAddBooks }) => {
  const [activeTab, setActiveTab] = useState('goodreads');
  const [loading, setLoading] = useState(false);
  const [goodreadsFile, setGoodreadsFile] = useState(null);
  const [googleResults, setGoogleResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [combinedResults, setCombinedResults] = useState([]);
  const [stats, setStats] = useState(null);
  const [importResults, setImportResults] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadIntegrationsData();
    }
  }, [isOpen]);

  const loadIntegrationsData = async () => {
    try {
      const statsResponse = await integrationsService.getIntegrationsStats();
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Erreur lors du chargement des données d\'intégration:', error);
    }
  };

  // === GOODREADS INTEGRATION ===

  const handleGoodreadsFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && integrationsService.validateGoodreadsCSV(file)) {
      setGoodreadsFile(file);
    } else {
      alert('Veuillez sélectionner un fichier CSV valide de Goodreads');
      event.target.value = '';
    }
  };

  const handleGoodreadsImport = async () => {
    if (!goodreadsFile) {
      alert('Veuillez sélectionner un fichier CSV');
      return;
    }

    setLoading(true);
    try {
      const response = await integrationsService.importGoodreadsCSV(goodreadsFile);
      const formattedStats = integrationsService.formatImportStats(response.data.statistics);
      
      setImportResults({
        ...response,
        formattedStats
      });

      // Ajouter les livres à la bibliothèque
      if (response.data.books && response.data.books.length > 0) {
        await onAddBooks(response.data.books);
      }

      alert(`Import terminé ! ${formattedStats.convertedBooks} livres ajoutés.`);
    } catch (error) {
      console.error('Erreur lors de l\'import Goodreads:', error);
      alert('Erreur lors de l\'import. Vérifiez le format du fichier.');
    } finally {
      setLoading(false);
    }
  };

  // === GOOGLE BOOKS INTEGRATION ===

  const handleGoogleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await integrationsService.searchGoogleBooks(searchQuery, 20);
      setGoogleResults(response.data.books || []);
    } catch (error) {
      console.error('Erreur lors de la recherche Google Books:', error);
      setGoogleResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddGoogleBook = async (book) => {
    try {
      await onAddBooks([book]);
      alert('Livre ajouté avec succès !');
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre:', error);
      alert('Erreur lors de l\'ajout du livre');
    }
  };

  // === RECHERCHE COMBINÉE ===

  const handleCombinedSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await integrationsService.combinedSearch(
        searchQuery, 
        ['google_books'], 
        15
      );
      setCombinedResults(response.data.books || []);
    } catch (error) {
      console.error('Erreur lors de la recherche combinée:', error);
      setCombinedResults([]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              🔗 Intégrations Externes
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Importez et recherchez depuis des services externes
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation onglets */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          {[
            { id: 'goodreads', label: '📚 Goodreads', description: 'Import CSV' },
            { id: 'google', label: '📖 Google Books', description: 'Recherche' },
            { id: 'combined', label: '🔍 Recherche combinée', description: 'Multi-sources' },
            { id: 'stats', label: '📊 Statistiques', description: 'État intégrations' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-medium text-sm text-left ${
                activeTab === tab.id
                  ? 'border-b-2 border-green-500 text-green-600 dark:text-green-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <div>{tab.label}</div>
              <div className="text-xs text-gray-500">{tab.description}</div>
            </button>
          ))}
        </div>

        {/* Contenu */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Onglet Goodreads */}
          {activeTab === 'goodreads' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Import Goodreads CSV</h3>
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mb-4">
                  <h4 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                    Comment exporter depuis Goodreads :
                  </h4>
                  <ol className="list-decimal list-inside text-sm text-blue-800 dark:text-blue-300 space-y-1">
                    <li>Connectez-vous à votre compte Goodreads</li>
                    <li>Allez dans "My Books" → "Import and export"</li>
                    <li>Cliquez sur "Export Library"</li>
                    <li>Téléchargez le fichier CSV</li>
                    <li>Sélectionnez ce fichier ci-dessous</li>
                  </ol>
                </div>

                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6">
                  <div className="text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <div className="mt-4">
                      <label htmlFor="goodreads-file" className="cursor-pointer">
                        <span className="mt-2 block text-sm font-medium text-gray-900 dark:text-white">
                          Sélectionnez votre fichier CSV Goodreads
                        </span>
                        <input
                          id="goodreads-file"
                          name="goodreads-file"
                          type="file"
                          accept=".csv"
                          className="sr-only"
                          onChange={handleGoodreadsFileSelect}
                        />
                        <span className="mt-2 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700">
                          Choisir un fichier
                        </span>
                      </label>
                    </div>
                    {goodreadsFile && (
                      <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                        Fichier sélectionné : {goodreadsFile.name}
                      </div>
                    )}
                  </div>
                </div>

                {goodreadsFile && (
                  <div className="flex justify-center">
                    <button
                      onClick={handleGoodreadsImport}
                      disabled={loading}
                      className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {loading ? 'Import en cours...' : 'Importer les livres'}
                    </button>
                  </div>
                )}

                {importResults && (
                  <div className="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <h4 className="font-semibold text-green-900 dark:text-green-200 mb-2">
                      Import terminé !
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <strong>Total :</strong> {importResults.formattedStats.totalBooks}
                      </div>
                      <div>
                        <strong>Convertis :</strong> {importResults.formattedStats.convertedBooks}
                      </div>
                      <div>
                        <strong>Taux :</strong> {importResults.formattedStats.conversionRate}%
                      </div>
                      <div>
                        <strong>Erreurs :</strong> {importResults.formattedStats.hasErrors ? 'Oui' : 'Non'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Onglet Google Books */}
          {activeTab === 'google' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Recherche Google Books</h3>
                
                <div className="flex gap-4 mb-6">
                  <input
                    type="text"
                    placeholder="Titre, auteur, ISBN..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleGoogleSearch()}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                  <button
                    onClick={handleGoogleSearch}
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Recherche...' : 'Rechercher'}
                  </button>
                </div>

                {googleResults.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {googleResults.map((book, index) => (
                      <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                        <div className="flex gap-4">
                          {book.cover_url && (
                            <img
                              src={book.cover_url}
                              alt={book.title}
                              className="w-16 h-24 object-cover rounded"
                            />
                          )}
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
                              {book.title}
                            </h4>
                            <p className="text-gray-600 dark:text-gray-400 text-sm">
                              {book.author}
                            </p>
                            <div className="mt-2">
                              <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                                {book.category}
                              </span>
                              {book.total_pages > 0 && (
                                <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 px-2 py-1 rounded ml-2">
                                  {book.total_pages} pages
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => handleAddGoogleBook(book)}
                          className="mt-3 w-full px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                        >
                          Ajouter à ma bibliothèque
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Onglet Recherche Combinée */}
          {activeTab === 'combined' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Recherche Multi-Sources</h3>
                
                <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg mb-4">
                  <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                    🔍 Cette recherche combine plusieurs sources externes pour vous offrir un maximum de résultats.
                    Les doublons sont automatiquement supprimés.
                  </p>
                </div>

                <div className="flex gap-4 mb-6">
                  <input
                    type="text"
                    placeholder="Recherche sur toutes les sources..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleCombinedSearch()}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                  <button
                    onClick={handleCombinedSearch}
                    disabled={loading}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    {loading ? 'Recherche...' : 'Recherche combinée'}
                  </button>
                </div>

                {combinedResults.length > 0 && (
                  <div>
                    <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
                      {combinedResults.length} résultats trouvés
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {combinedResults.map((book, index) => (
                        <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="flex gap-4">
                            {book.cover_url && (
                              <img
                                src={book.cover_url}
                                alt={book.title}
                                className="w-16 h-24 object-cover rounded"
                              />
                            )}
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
                                {book.title}
                              </h4>
                              <p className="text-gray-600 dark:text-gray-400 text-sm">
                                {book.author}
                              </p>
                              <div className="mt-2">
                                <span className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded">
                                  {book.source}
                                </span>
                                <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded ml-2">
                                  {book.category}
                                </span>
                              </div>
                            </div>
                          </div>
                          <button
                            onClick={() => handleAddGoogleBook(book)}
                            className="mt-3 w-full px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                          >
                            Ajouter à ma bibliothèque
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Onglet Statistiques */}
          {activeTab === 'stats' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold mb-4">Statistiques des Intégrations</h3>
              
              {stats ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="font-semibold mb-4">Intégrations Supportées</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {stats.supported_integrations.map((integration, index) => (
                        <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <h5 className="font-semibold text-gray-900 dark:text-white">
                            {integration.name}
                          </h5>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            {integration.description}
                          </p>
                          <div className="mt-3 flex items-center gap-2">
                            <span className={`px-2 py-1 rounded text-xs ${
                              integration.status === 'active'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            }`}>
                              {integration.status}
                            </span>
                            <span className="text-xs text-gray-500">
                              Type: {integration.type}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold mb-4">Statistiques d'Utilisation</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {Object.entries(stats.usage_stats).map(([key, value]) => (
                        <div key={key} className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                          <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {value}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {key.replace('_', ' ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-gray-600 dark:text-gray-400">
                  Chargement des statistiques...
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntegrationsModal;