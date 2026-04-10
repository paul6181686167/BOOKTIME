import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import ExportImportModal from '../export-import/ExportImportModal';
import { API_BASE_URL } from '../../config/environment';

/**
 * Page principale Export/Import pour la bibliothèque BOOKTIME
 * Sessions 86.3-86.7 - Architecture modulaire complète
 * Gestion export (JSON, CSV, Excel, backup) et import (CSV, JSON, Goodreads, Excel)
 */

const ExportImportPage = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Configuration backend unifiée
  const backendUrl = API_BASE_URL;

  // Test de connectivité backend
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await fetch(`${backendUrl}/health`);
        if (!response.ok) {
          toast.error('Backend indisponible');
        }
      } catch (error) {
        console.error('Backend connection test failed:', error);
        toast.error('Erreur de connexion backend');
      }
    };
    
    testConnection();
  }, [backendUrl]);

  const openModal = useCallback(() => setIsModalOpen(true), []);
  const closeModal = useCallback(() => setIsModalOpen(false), []);

  return (
    <div className="export-import-page">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Export & Import
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Sauvegardez et restaurez votre bibliothèque en toute simplicité
            </p>
          </div>

          {/* Bouton principal */}
          <div className="text-center">
            <button
              onClick={openModal}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              Ouvrir Export/Import
            </button>
          </div>

          {/* Informations */}
          <div className="mt-12 grid md:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                📤 Export
              </h3>
              <ul className="text-gray-600 dark:text-gray-300 space-y-2">
                <li>• Format JSON (complet)</li>
                <li>• Format CSV (tableur)</li>
                <li>• Format Excel (avancé)</li>
                <li>• Sauvegarde complète (ZIP)</li>
              </ul>
            </div>

            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                📥 Import
              </h3>
              <ul className="text-gray-600 dark:text-gray-300 space-y-2">
                <li>• Format CSV (personnalisé)</li>
                <li>• Format JSON (BOOKTIME)</li>
                <li>• Format Goodreads (CSV)</li>
                <li>• Format Excel (XLS/XLSX)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Modal Export/Import */}
      {isModalOpen && (
        <ExportImportModal 
          isOpen={isModalOpen}
          onClose={closeModal}
        />
      )}
    </div>
  );
};

export default ExportImportPage;