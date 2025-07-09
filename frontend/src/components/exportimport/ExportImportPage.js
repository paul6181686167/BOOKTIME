import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { toast } from 'react-hot-toast';
import { 
  ArrowDownTrayIcon, 
  ArrowUpTrayIcon, 
  DocumentTextIcon,
  TableCellsIcon,
  DocumentChartBarIcon,
  ArchiveBoxIcon,
  CloudArrowUpIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const ExportImportPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('export');
  const [loading, setLoading] = useState(false);
  const [formats, setFormats] = useState([]);
  const [importFormats, setImportFormats] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [importPreview, setImportPreview] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [exportOptions, setExportOptions] = useState({
    format: 'json',
    include_metadata: true,
    include_stats: true,
    include_reading_progress: true,
    include_reviews: true,
    include_covers: false
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadFormats();
  }, []);

  const loadFormats = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Charger les formats d'export
      const exportResponse = await fetch(`${backendUrl}/api/export-import/export/formats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (exportResponse.ok) {
        const exportData = await exportResponse.json();
        setFormats(exportData.formats_details || {});
      }
      
      // Charger les formats d'import
      const importResponse = await fetch(`${backendUrl}/api/export-import/import/formats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (importResponse.ok) {
        const importData = await importResponse.json();
        setImportFormats(importData.supported_formats || {});
      }
      
    } catch (error) {
      console.error('Erreur lors du chargement des formats:', error);
    }
  };

  const handleExport = async () => {
    if (!user) return;
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      
      Object.entries(exportOptions).forEach(([key, value]) => {
        if (key === 'format') {
          params.append('format_type', value);
        } else {
          params.append(key, value);
        }
      });
      
      const response = await fetch(`${backendUrl}/api/export-import/export?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const contentDisposition = response.headers.get('Content-Disposition');
        const filename = contentDisposition 
          ? contentDisposition.split('filename=')[1].replace(/"/g, '')
          : `booktime_export_${exportOptions.format}`;
        
        // Télécharger le fichier
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success('Export terminé avec succès !');
      } else {
        throw new Error('Erreur lors de l\'export');
      }
      
    } catch (error) {
      console.error('Erreur export:', error);
      toast.error('Erreur lors de l\'export');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setImportPreview(null);
      setImportResult(null);
    }
  };

  const handlePreview = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      const response = await fetch(`${backendUrl}/api/export-import/import/preview`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setImportPreview(data);
        setShowPreview(true);
      } else {
        throw new Error('Erreur lors de la prévisualisation');
      }
      
    } catch (error) {
      console.error('Erreur preview:', error);
      toast.error('Erreur lors de la prévisualisation');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (skipDuplicates = true, updateExisting = false) => {
    if (!selectedFile) return;
    
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('skip_duplicates', skipDuplicates);
      formData.append('update_existing', updateExisting);
      formData.append('dry_run', false);
      
      const response = await fetch(`${backendUrl}/api/export-import/import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setImportResult(data);
        setShowPreview(false);
        
        if (data.success) {
          toast.success(`Import terminé ! ${data.summary.imported_count} livres importés.`);
        } else {
          toast.error('Import terminé avec des erreurs');
        }
      } else {
        throw new Error('Erreur lors de l\'import');
      }
      
    } catch (error) {
      console.error('Erreur import:', error);
      toast.error('Erreur lors de l\'import');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/export-import/templates/generate?format_type=csv`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'booktime_import_template.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        toast.success('Template téléchargé !');
      }
    } catch (error) {
      console.error('Erreur template:', error);
      toast.error('Erreur lors du téléchargement du template');
    }
  };

  const getFormatIcon = (format) => {
    switch (format) {
      case 'json': return <DocumentTextIcon className="w-5 h-5" />;
      case 'csv': return <TableCellsIcon className="w-5 h-5" />;
      case 'excel': return <DocumentChartBarIcon className="w-5 h-5" />;
      case 'full_backup': return <ArchiveBoxIcon className="w-5 h-5" />;
      default: return <DocumentTextIcon className="w-5 h-5" />;
    }
  };

  const renderExportSection = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          📤 Export de votre bibliothèque
        </h3>
        <p className="text-blue-800 dark:text-blue-200 text-sm">
          Sauvegardez votre bibliothèque dans différents formats pour analyse ou sauvegarde.
        </p>
      </div>

      {/* Choix du format */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Format d'export
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(formats).map(([key, format]) => (
            <label key={key} className="relative">
              <input
                type="radio"
                name="format"
                value={key}
                checked={exportOptions.format === key}
                onChange={(e) => setExportOptions({...exportOptions, format: e.target.value})}
                className="sr-only"
              />
              <div className={`p-4 border rounded-lg cursor-pointer transition-all ${
                exportOptions.format === key
                  ? 'border-green-500 bg-green-50 dark:bg-green-900/30'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              }`}>
                <div className="flex items-center space-x-3">
                  {getFormatIcon(key)}
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      {format.name}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {format.description}
                    </div>
                    <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      {format.best_for}
                    </div>
                  </div>
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Options d'export */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Options d'export
        </label>
        <div className="space-y-2">
          {[
            { key: 'include_metadata', label: 'Métadonnées utilisateur', desc: 'Informations de profil' },
            { key: 'include_stats', label: 'Statistiques', desc: 'Compteurs et analytics' },
            { key: 'include_reading_progress', label: 'Progression', desc: 'Pages lues et avancement' },
            { key: 'include_reviews', label: 'Avis et notes', desc: 'Commentaires et évaluations' },
            { key: 'include_covers', label: 'Couvertures', desc: 'Images en base64 (augmente la taille)' }
          ].map((option) => (
            <label key={option.key} className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={exportOptions[option.key]}
                onChange={(e) => setExportOptions({
                  ...exportOptions,
                  [option.key]: e.target.checked
                })}
                className="rounded border-gray-300 text-green-600 focus:ring-green-500"
              />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  {option.label}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {option.desc}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Bouton d'export */}
      <button
        onClick={handleExport}
        disabled={loading}
        className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
            <span>Export en cours...</span>
          </>
        ) : (
          <>
            <ArrowDownTrayIcon className="w-5 h-5" />
            <span>Exporter ma bibliothèque</span>
          </>
        )}
      </button>
    </div>
  );

  const renderImportSection = () => (
    <div className="space-y-6">
      <div className="bg-purple-50 dark:bg-purple-900/30 p-4 rounded-lg">
        <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">
          📥 Import de données
        </h3>
        <p className="text-purple-800 dark:text-purple-200 text-sm">
          Importez des livres depuis un fichier CSV, JSON ou un export Goodreads.
        </p>
      </div>

      {/* Formats supportés */}
      <div>
        <h4 className="font-medium text-gray-900 dark:text-white mb-3">
          Formats supportés
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(importFormats).map(([key, format]) => (
            <div key={key} className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div className="font-medium text-gray-900 dark:text-white">
                {format.name}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {format.description}
              </div>
              <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                Compatibilité: {format.compatibility}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Template */}
      <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
        <h4 className="font-medium text-gray-900 dark:text-white mb-2">
          Template d'import
        </h4>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Téléchargez un template CSV pour voir le format attendu.
        </p>
        <button
          onClick={downloadTemplate}
          className="text-green-600 hover:text-green-700 text-sm font-medium"
        >
          📋 Télécharger le template CSV
        </button>
      </div>

      {/* Sélection fichier */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Sélectionner un fichier
        </label>
        <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
          <input
            type="file"
            accept=".json,.csv,.xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
            id="import-file"
          />
          <label htmlFor="import-file" className="cursor-pointer">
            <CloudArrowUpIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Cliquez pour sélectionner un fichier ou glissez-déposez
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              JSON, CSV, Excel acceptés (max 50MB)
            </div>
          </label>
        </div>
        
        {selectedFile && (
          <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
            <div className="flex items-center space-x-2">
              <DocumentTextIcon className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-blue-900 dark:text-blue-100">
                {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Boutons d'action */}
      {selectedFile && (
        <div className="flex space-x-3">
          <button
            onClick={handlePreview}
            disabled={loading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <EyeIcon className="w-5 h-5" />
            <span>Prévisualiser</span>
          </button>
          
          <button
            onClick={() => handleImport(true, false)}
            disabled={loading}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2"
          >
            <ArrowUpTrayIcon className="w-5 h-5" />
            <span>Importer</span>
          </button>
        </div>
      )}
    </div>
  );

  const renderPreview = () => {
    if (!showPreview || !importPreview) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Prévisualisation de l'import
              </h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Résumé */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{importPreview.preview.total_books_found}</div>
                <div className="text-sm text-blue-800 dark:text-blue-200">Livres trouvés</div>
              </div>
              <div className="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{importPreview.preview.would_import}</div>
                <div className="text-sm text-green-800 dark:text-green-200">Seront importés</div>
              </div>
              <div className="bg-yellow-50 dark:bg-yellow-900/30 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">{importPreview.preview.would_skip}</div>
                <div className="text-sm text-yellow-800 dark:text-yellow-200">Seront ignorés</div>
              </div>
              <div className="bg-red-50 dark:bg-red-900/30 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{importPreview.preview.duplicates_detected}</div>
                <div className="text-sm text-red-800 dark:text-red-200">Doublons détectés</div>
              </div>
            </div>

            {/* Exemples de livres */}
            {importPreview.sample_books && importPreview.sample_books.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  Exemples de livres à importer
                </h4>
                <div className="space-y-2">
                  {importPreview.sample_books.slice(0, 5).map((book, index) => (
                    <div key={index} className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="font-medium text-gray-900 dark:text-white">{book.title}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {book.author} • {book.category} • {book.status}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Doublons */}
            {importPreview.duplicates_sample && importPreview.duplicates_sample.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  Doublons détectés
                </h4>
                <div className="space-y-2">
                  {importPreview.duplicates_sample.map((dup, index) => (
                    <div key={index} className="p-3 border border-yellow-200 dark:border-yellow-700 rounded-lg bg-yellow-50 dark:bg-yellow-900/30">
                      <div className="font-medium text-yellow-900 dark:text-yellow-100">{dup.title}</div>
                      <div className="text-sm text-yellow-800 dark:text-yellow-200">
                        {dup.author} • {dup.match_reason}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Erreurs */}
            {importPreview.errors_sample && importPreview.errors_sample.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  Erreurs détectées
                </h4>
                <div className="space-y-2">
                  {importPreview.errors_sample.map((error, index) => (
                    <div key={index} className="p-3 border border-red-200 dark:border-red-700 rounded-lg bg-red-50 dark:bg-red-900/30">
                      <div className="text-sm text-red-800 dark:text-red-200">{error}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              >
                Annuler
              </button>
              <button
                onClick={() => handleImport(true, false)}
                disabled={loading}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg"
              >
                Confirmer l'import
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderResult = () => {
    if (!importResult) return null;

    return (
      <div className="mt-6 p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
        <h4 className="font-medium text-gray-900 dark:text-white mb-3">
          Résultat de l'import
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{importResult.summary.imported_count}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Importés</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{importResult.summary.skipped_count}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Ignorés</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{importResult.summary.error_count}</div>
            <div className="text-sm text-gray-600 dark:text-gray-400">Erreurs</div>
          </div>
        </div>

        {importResult.success ? (
          <div className="flex items-center space-x-2 text-green-600">
            <CheckCircleIcon className="w-5 h-5" />
            <span className="text-sm">Import terminé avec succès</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 text-red-600">
            <ExclamationTriangleIcon className="w-5 h-5" />
            <span className="text-sm">Import terminé avec des erreurs</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.history.back()}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                ← Retour
              </button>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Export / Import
              </h1>
            </div>
          </div>
        </div>
      </div>

      {/* Contenu */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Onglets */}
        <div className="flex space-x-1 mb-8">
          {[
            { key: 'export', label: 'Export', icon: ArrowDownTrayIcon },
            { key: 'import', label: 'Import', icon: ArrowUpTrayIcon }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                activeTab === tab.key
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Contenu des onglets */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
          {activeTab === 'export' ? renderExportSection() : renderImportSection()}
        </div>

        {/* Résultat d'import */}
        {renderResult()}
      </div>

      {/* Preview modal */}
      {renderPreview()}
    </div>
  );
};

export default ExportImportPage;