import { useState, useEffect } from 'react';
import SeriesActions from '../components/series/SeriesActions';

// Hook personnalisé pour gérer l'état des séries
export const useSeries = () => {
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [showSeriesDetail, setShowSeriesDetail] = useState(false);
  const [showSeriesModal, setShowSeriesModal] = useState(false);
  const [userSeriesLibrary, setUserSeriesLibrary] = useState([]);
  const [seriesLibraryLoading, setSeriesLibraryLoading] = useState(false);

  // Charger les séries de la bibliothèque utilisateur
  const loadUserSeriesLibrary = async () => {
    await SeriesActions.loadUserSeriesLibrary(setSeriesLibraryLoading, setUserSeriesLibrary);
  };

  // Fonction pour ajouter une série à la bibliothèque
  const handleAddSeriesToLibrary = async (series) => {
    await SeriesActions.handleAddSeriesToLibrary(series, {
      setUserSeriesLibrary,
      loadUserSeriesLibrary
    });
  };

  // Fonction pour mettre à jour le statut d'un volume
  const handleUpdateVolumeStatus = async (seriesId, volumeNumber, newStatus) => {
    await SeriesActions.handleUpdateVolumeStatus(seriesId, volumeNumber, newStatus, {
      setUserSeriesLibrary,
      loadUserSeriesLibrary
    });
  };

  // Fonction pour mettre à jour le statut d'une série
  const handleUpdateSeriesStatus = async (seriesId, newStatus) => {
    await SeriesActions.handleUpdateSeriesStatus(seriesId, newStatus, {
      setUserSeriesLibrary,
      loadUserSeriesLibrary
    });
  };

  // Fonction pour supprimer une série de la bibliothèque
  const handleDeleteSeriesFromLibrary = async (seriesId) => {
    await SeriesActions.handleDeleteSeriesFromLibrary(seriesId, {
      setUserSeriesLibrary,
      loadUserSeriesLibrary
    });
  };

  // Fonction pour fermer le modal de série
  const closeSeriesModal = () => {
    setSelectedSeries(null);
    setShowSeriesModal(false);
  };

  // Fonction pour fermer le détail de série
  const closeSeriesDetail = () => {
    setShowSeriesDetail(false);
  };

  return {
    // États
    selectedSeries,
    showSeriesDetail,
    showSeriesModal,
    userSeriesLibrary,
    seriesLibraryLoading,
    
    // Actions
    loadUserSeriesLibrary,
    handleAddSeriesToLibrary,
    handleUpdateVolumeStatus,
    handleUpdateSeriesStatus,
    handleDeleteSeriesFromLibrary,
    closeSeriesModal,
    closeSeriesDetail,
    
    // Setters (pour compatibilité)
    setSelectedSeries,
    setShowSeriesDetail,
    setShowSeriesModal,
    setUserSeriesLibrary,
    setSeriesLibraryLoading
  };
};

export default useSeries;
