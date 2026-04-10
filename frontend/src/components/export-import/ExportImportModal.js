/**
 * PHASE 3.2 - Modal Export/Import de Données
 * Interface utilisateur complète pour export/import
 */
import React, { useState } from 'react';
import { X, Download, Upload, FileText, FileSpreadsheet, Archive, Eye, CheckCircle, AlertCircle } from 'lucide-react';

const ExportImportModal = ({ isOpen, onClose, backendUrl, token }) => {
  const [activeTab, setActiveTab] = useState('export');
  const [exportFormat, setExportFormat] = useState('json');
  const [exportOptions, setExportOptions] = useState({
    include_metadata: true,
    include_stats: true,
    include_reading_progress: true,
    include_reviews: true,
    include_covers: false
  });
  const [importFile, setImportFile] = useState(null);
  const [importOptions, setImportOptions] = useState({
    skip_duplicates: true,
    update_existing: false,
    dry_run: false
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');
  const [previewData, setPreviewData] = useState(null);

  const formatIcons = {
    json: <FileText className="w-5 h-5" />,
    csv: <FileSpreadsheet className="w-5 h-5" />,
    excel: <FileSpreadsheet className="w-5 h-5" />,
    full_backup: <Archive className="w-5 h-5" />
  };

  const formatDescriptions = {
    json: "Format JSON complet avec toutes les données",
    csv: "Format CSV pour tableurs (Excel, LibreOffice)",
    excel: "Fichier Excel avec feuilles multiples",
    full_backup: "Archive ZIP avec tous les formats"
  };

  const showMessage = (msg, type = 'info') => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => setMessage(''), 5000);
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams({
        format_type: exportFormat,
        ...exportOptions
      });

      const response = await fetch(`${backendUrl}/api/export-import/export?${params}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      // Télécharger le fichier
      const blob = await response.blob();
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition 
        ? contentDisposition.split('filename=')[1].replace(/"/g, '')
        : `booktime_export_${new Date().toISOString().split('T')[0]}.${exportFormat}`;

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      window.URL.revokeObjectURL(url);

      showMessage('Export terminé avec succès !', 'success');
    } catch (error) {
      console.error('Erreur export:', error);
      showMessage(`Erreur lors de l'export: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!importFile) return;

    try {
      setLoading(true);
      
      const formData = new FormData();
      formData.append('file', importFile);

      const response = await fetch(`${backendUrl}/api/export-import/import/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setPreviewData(data);
      showMessage('Aperçu généré avec succès !', 'success');
    } catch (error) {
      console.error('Erreur preview:', error);
      showMessage(`Erreur lors de l'aperçu: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!importFile) return;

    try {
      setLoading(true);
      
      const formData = new FormData();
      formData.append('file', importFile);
      formData.append('skip_duplicates', importOptions.skip_duplicates);
      formData.append('update_existing', importOptions.update_existing);
      formData.append('dry_run', importOptions.dry_run);

      const response = await fetch(`${backendUrl}/api/export-import/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        showMessage(`Import terminé ! ${data.summary.imported_count} livres importés, ${data.summary.skipped_count} ignorés.`, 'success');
        setImportFile(null);
        setPreviewData(null);
        
        // Actualiser la page après import réussi
        setTimeout(() => {
          window.location.reload();
        }, 2000);
      } else {
        showMessage('Import échoué. Vérifiez les erreurs.', 'error');
      }
    } catch (error) {
      console.error('Erreur import:', error);
      showMessage(`Erreur lors de l'import: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/export-import/templates/generate?format_type=csv`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'booktime_import_template.csv';
      a.click();
      window.URL.revokeObjectURL(url);

      showMessage('Template téléchargé avec succès !', 'success');
    } catch (error) {
      console.error('Erreur template:', error);
      showMessage(`Erreur lors du téléchargement: ${error.message}`, 'error');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Export/Import de Données
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Message */}
        {message && (
          <div className={`mx-6 mt-4 p-4 rounded-md ${
            messageType === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400' :
            messageType === 'error' ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400' :
            'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
          }`}>
            <div className="flex items-center">
              {messageType === 'success' && <CheckCircle className="w-5 h-5 mr-2" />}
              {messageType === 'error' && <AlertCircle className="w-5 h-5 mr-2" />}
              {message}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('export')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'export'
                ? 'text-green-600 dark:text-green-400 border-b-2 border-green-600'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            <Download className="w-5 h-5 inline mr-2" />
            Exporter
          </button>
          <button
            onClick={() => setActiveTab('import')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'import'
                ? 'text-green-600 dark:text-green-400 border-b-2 border-green-600'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
            }`}
          >
            <Upload className="w-5 h-5 inline mr-2" />
            Importer
          </button>
        </div>

        <div className="p-6">
          {activeTab === 'export' && (
            <div className="space-y-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Format d'export
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(formatDescriptions).map(([format, description]) => (
                    <div
                      key={format}
                      onClick={() => setExportFormat(format)}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        exportFormat === format
                          ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }`}
                    >
                      <div className="flex items-center mb-2">
                        {formatIcons[format]}
                        <span className="ml-2 font-medium text-gray-900 dark:text-white">
                          {format.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Export Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Options d'export
                </label>
                <div className="space-y-3">
                  {Object.entries({
                    include_metadata: "Inclure métadonnées utilisateur",
                    include_stats: "Inclure statistiques de lecture",
                    include_reading_progress: "Inclure progression détaillée",
                    include_reviews: "Inclure avis et notes",
                    include_covers: "Inclure couvertures (augmente la taille)"
                  }).map(([key, label]) => (
                    <label key={key} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={exportOptions[key]}
                        onChange={(e) => setExportOptions({
                          ...exportOptions,
                          [key]: e.target.checked
                        })}
                        className="h-4 w-4 text-green-600 rounded border-gray-300 dark:border-gray-600"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                        {label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Export Button */}
              <button
                onClick={handleExport}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-colors"
              >
                {loading ? 'Export en cours...' : 'Exporter mes données'}
              </button>
            </div>
          )}

          {activeTab === 'import' && (
            <div className="space-y-6">
              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Fichier à importer
                </label>
                <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    accept=".json,.csv,.xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files[0])}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="cursor-pointer inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    <Upload className="w-5 h-5 mr-2" />
                    Choisir un fichier
                  </label>
                  {importFile && (
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      Fichier sélectionné: {importFile.name}
                    </p>
                  )}
                </div>
                
                {/* Template Download */}
                <div className="mt-4 text-center">
                  <button
                    onClick={handleDownloadTemplate}
                    className="text-green-600 hover:text-green-700 text-sm font-medium"
                  >
                    Télécharger un template CSV
                  </button>
                </div>
              </div>

              {/* Import Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Options d'import
                </label>
                <div className="space-y-3">
                  {Object.entries({
                    skip_duplicates: "Ignorer les doublons",
                    update_existing: "Mettre à jour les livres existants",
                    dry_run: "Mode simulation (ne pas importer réellement)"
                  }).map(([key, label]) => (
                    <label key={key} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={importOptions[key]}
                        onChange={(e) => setImportOptions({
                          ...importOptions,
                          [key]: e.target.checked
                        })}
                        className="h-4 w-4 text-green-600 rounded border-gray-300 dark:border-gray-600"
                      />
                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                        {label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Preview Button */}
              {importFile && (
                <button
                  onClick={handlePreview}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-colors"
                >
                  <Eye className="w-5 h-5 inline mr-2" />
                  {loading ? 'Génération aperçu...' : 'Aperçu de l\'import'}
                </button>
              )}

              {/* Preview Data */}
              {previewData && (
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                    Aperçu de l'import
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{previewData.preview?.total_books_found || 0}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Livres trouvés</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{previewData.preview?.would_import || 0}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Seront importés</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">{previewData.preview?.would_skip || 0}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Seront ignorés</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{previewData.preview?.duplicates_detected || 0}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400">Doublons détectés</div>
                    </div>
                  </div>
                  
                  {previewData.sample_books && previewData.sample_books.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        Exemples de livres ({previewData.sample_books.length} premiers):
                      </h4>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {previewData.sample_books.map((book, index) => (
                          <div key={index} className="text-sm bg-white dark:bg-gray-800 p-2 rounded">
                            <span className="font-medium">{book.title}</span>
                            <span className="text-gray-600 dark:text-gray-400"> par {book.author}</span>
                            <span className="ml-2 inline-block px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded">
                              {book.category}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Import Button */}
              {importFile && (
                <button
                  onClick={handleImport}
                  disabled={loading}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg transition-colors"
                >
                  {loading ? 'Import en cours...' : 'Importer les données'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExportImportModal;