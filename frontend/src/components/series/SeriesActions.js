/**
 * SERIES ACTIONS - Module de gestion des actions sur les séries pour BOOKTIME
 * 
 * Fonctionnalités :
 * - Ajout de séries complètes à la bibliothèque
 * - Chargement des séries utilisateur
 * - Enrichissement automatique des métadonnées
 * - Gestion des statuts de séries et tomes
 * - Suppression de séries
 * 
 * Extrait d'App.js dans le cadre de la Phase 1.1 - Frontend Modularisation
 */

import { toast } from 'react-hot-toast';
import * as seriesLibraryService from '../../services/seriesLibraryService';
import { DEFAULT_SERIES_COVER } from '../../utils/constants';
import { seriesImageService } from '../../services/seriesImageService';
import {
  loadSeriesCache,
  saveSeriesCache,
} from '../../utils/offlineLibraryCache';

// CHARGEMENT DES SÉRIES UTILISATEUR
export const loadUserSeriesLibrary = async (setSeriesLibraryLoading, setUserSeriesLibrary) => {
  try {
    setSeriesLibraryLoading(true);
    const token = localStorage.getItem('token');
    const result = await seriesLibraryService.getUserSeriesLibrary(token);
    const series = result.series || [];
    setUserSeriesLibrary(series);
    saveSeriesCache(series);
  } catch (error) {
    console.error('Erreur chargement séries bibliothèque:', error);
    const cached = loadSeriesCache();
    if (cached?.series?.length) {
      setUserSeriesLibrary(cached.series);
    } else {
      toast.error('Erreur lors du chargement des séries');
    }
  } finally {
    setSeriesLibraryLoading(false);
  }
};

// ENRICHISSEMENT AUTOMATIQUE DES MÉTADONNÉES
export const enrichSeriesMetadata = async (seriesData) => {
  try {
    let cover_image_url = '';
    try {
      const openLibraryUrl = await seriesImageService.fetchCoverFromOpenLibrary(seriesData.name);
      cover_image_url = openLibraryUrl || DEFAULT_SERIES_COVER;
    } catch (error) {
      cover_image_url = DEFAULT_SERIES_COVER;
    }
    
    // 2. Générer une description française enrichie
    let description_fr = '';
    try {
      if (seriesData.description) {
        description_fr = seriesData.description;
      } else {
        // Générer une description basique
        const categoryText = {
          'roman': 'roman',
          'bd': 'bande dessinée', 
          'manga': 'manga'
        };
        
        const authorText = seriesData.authors?.length 
          ? ` par ${seriesData.authors.join(', ')}`
          : seriesData.author ? ` par ${seriesData.author}` : '';
        
        const volumeText = seriesData.volumes 
          ? ` Comprend ${seriesData.volumes} tome${seriesData.volumes > 1 ? 's' : ''}.`
          : '';
        
        description_fr = `Série de ${categoryText[seriesData.category] || 'livres'} populaire${authorText}.${volumeText}`;
      }
      
    } catch (error) {
      description_fr = `Série ${seriesData.category || 'populaire'}.`;
    }
    
    return {
      cover_image_url,
      description_fr,
      first_published: seriesData.first_published || '',
      last_published: '',
      publisher: ''
    };
    
  } catch (error) {
    console.error('❌ Erreur enrichissement métadonnées:', error);
    
    // Fallback sûr
    return {
      cover_image_url: DEFAULT_SERIES_COVER,
      description_fr: `Série ${seriesData.category || 'populaire'}.`,
      first_published: '',
      last_published: '',
      publisher: ''
    };
  }
};

// AJOUT DE SÉRIE COMPLÈTE À LA BIBLIOTHÈQUE
export const handleAddSeriesToLibrary = async (seriesData, {
  setSeriesLibraryLoading,
  loadUserSeriesLibrary
}) => {
  try {
    setSeriesLibraryLoading(true);
    const token = localStorage.getItem('token');
    
    // Importer le référentiel étendu
    const { EXTENDED_SERIES_DATABASE } = await import('../../utils/seriesDatabaseExtended.js');
    
    // Générer les volumes avec titres depuis le référentiel
    const volumes = seriesLibraryService.generateVolumesList(seriesData, EXTENDED_SERIES_DATABASE);

    let authors = seriesData.authors || (seriesData.author ? [seriesData.author] : []);
    if (
      (!authors || authors.length === 0) &&
      seriesData.staticWikidataDetail?.works?.length
    ) {
      const set = new Set();
      seriesData.staticWikidataDetail.works.forEach((w) => {
        (w.authors_en || []).forEach((a) => {
          if (a) set.add(a);
        });
      });
      authors = [...set];
    }

    const enrichedMetadata = await enrichSeriesMetadata({ ...seriesData, authors });

    let coverFromMerge = '';
    if (Array.isArray(seriesData.mergedLibraryVolumes)) {
      const hit = seriesData.mergedLibraryVolumes.find((r) => r.cover_url);
      if (hit?.cover_url) coverFromMerge = hit.cover_url;
    }

    // Préparer les données de la série avec toutes les métadonnées
    const seriesPayload = {
      series_name: seriesData.name,
      author: seriesData.author || authors[0] || '',
      authors,
      category: seriesData.category || 'roman',
      total_volumes: volumes.length,
      volumes: volumes,
      description_fr: enrichedMetadata.description_fr,
      cover_image_url: coverFromMerge || enrichedMetadata.cover_image_url,
      first_published: enrichedMetadata.first_published || seriesData.first_published || '',
      last_published: enrichedMetadata.last_published || '',
      publisher: enrichedMetadata.publisher || '',
      series_status: 'to_read'
    };
    
    // Appel API pour ajouter la série
    const result = await seriesLibraryService.addSeriesToLibrary(seriesPayload, token);
    
    if (result.success) {
      await loadUserSeriesLibrary();
      
      // Message de succès détaillé
      toast.success(
        `✅ Série "${seriesData.name}" ajoutée avec ${volumes.length} tome${volumes.length > 1 ? 's' : ''} !`,
        { duration: 4000 }
      );
      
    }
  } catch (error) {
    console.error('❌ Erreur ajout série:', error);
    
    // Gestion des erreurs spécifiques
    if (error.message.includes('409')) {
      toast.error('Cette série est déjà dans votre bibliothèque');
    } else if (error.message.includes('400')) {
      toast.error('Données de série invalides');
    } else {
      toast.error('❌ Erreur lors de l\'ajout de la série');
    }
  } finally {
    setSeriesLibraryLoading(false);
  }
};

// MISE À JOUR DU STATUT D'UN TOME
export const handleUpdateVolumeStatus = async (seriesId, volumeNumber, isRead, setUserSeriesLibrary) => {
  try {
    const token = localStorage.getItem('token');
    const result = await seriesLibraryService.toggleVolumeStatus(seriesId, volumeNumber, isRead, token);
    
    if (result.success) {
      // Mettre à jour l'état local
      setUserSeriesLibrary(prev => 
        prev.map(series => 
          series.id === seriesId 
            ? {
                ...series,
                volumes: series.volumes.map(vol => 
                  vol.volume_number === volumeNumber 
                    ? { ...vol, is_read: isRead, date_read: isRead ? new Date().toISOString() : null }
                    : vol
                ),
                completion_percentage: result.completion_percentage,
                series_status: result.series_status
              }
            : series
        )
      );
      
      toast.success(`Tome ${volumeNumber} marqué comme ${isRead ? 'lu' : 'non lu'}`);
    }
  } catch (error) {
    console.error('Erreur mise à jour tome:', error);
    toast.error('Erreur lors de la mise à jour du tome');
  }
};

// MISE À JOUR DU STATUT GLOBAL D'UNE SÉRIE
export const handleUpdateSeriesStatus = async (seriesId, newStatus, setUserSeriesLibrary) => {
  try {
    const token = localStorage.getItem('token');
    const result = await seriesLibraryService.updateSeriesStatus(seriesId, newStatus, token);
    
    if (result.success) {
      // Mettre à jour l'état local
      setUserSeriesLibrary(prev => 
        prev.map(series => 
          series.id === seriesId 
            ? { ...series, series_status: newStatus }
            : series
        )
      );
      
      const statusLabels = {
        'to_read': 'À lire',
        'reading': 'En cours',
        'completed': 'Terminé'
      };
      toast.success(`Statut mis à jour : ${statusLabels[newStatus]}`);
    }
  } catch (error) {
    console.error('Erreur mise à jour statut série:', error);
    toast.error('Erreur lors de la mise à jour du statut');
  }
};

// SUPPRESSION D'UNE SÉRIE DE LA BIBLIOTHÈQUE
export const handleDeleteSeriesFromLibrary = async (seriesId, setUserSeriesLibrary) => {
  if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette série de votre bibliothèque ?')) {
    return;
  }
  
  try {
    const token = localStorage.getItem('token');
    const result = await seriesLibraryService.deleteSeriesFromLibrary(seriesId, token);
    
    if (result.success) {
      setUserSeriesLibrary(prev => prev.filter(series => series.id !== seriesId));
      toast.success('Série supprimée de votre bibliothèque');
    }
  } catch (error) {
    console.error('Erreur suppression série:', error);
    toast.error('Erreur lors de la suppression de la série');
  }
};

export default {
  loadUserSeriesLibrary,
  enrichSeriesMetadata,
  handleAddSeriesToLibrary,
  handleUpdateVolumeStatus,
  handleUpdateSeriesStatus,
  handleDeleteSeriesFromLibrary
};