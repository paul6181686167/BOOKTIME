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
import { EXTENDED_SERIES_DATABASE } from '../../utils/seriesDatabaseExtended.js';
import {
  loadSeriesCache,
  saveSeriesCache,
} from '../../utils/offlineLibraryCache';

/** Couverture déjà connue sur la carte / les tomes — sans rappeler Open Library. */
const resolveSeriesCover = (seriesData) => {
  if (seriesData?.cover_url) return seriesData.cover_url;
  if (seriesData?.cover_image_url) return seriesData.cover_image_url;
  if (Array.isArray(seriesData?.mergedLibraryVolumes)) {
    const hit = seriesData.mergedLibraryVolumes.find((r) => r.cover_url);
    if (hit?.cover_url) return hit.cover_url;
  }
  if (Array.isArray(seriesData?.books)) {
    const hit = seriesData.books.find((b) => b.cover_url);
    if (hit?.cover_url) return hit.cover_url;
  }
  return '';
};

// CHARGEMENT DES SÉRIES UTILISATEUR
export const loadUserSeriesLibrary = async (setSeriesLibraryLoading, setUserSeriesLibrary) => {
  try {
    setSeriesLibraryLoading(true);
    const token = localStorage.getItem('token');
    const result = await seriesLibraryService.getUserSeriesLibrary(token);
    const series = Array.isArray(result?.series)
      ? result.series
      : Array.isArray(result)
        ? result
        : [];
    setUserSeriesLibrary((prev) => {
      if (series.length === 0 && Array.isArray(prev) && prev.length > 0) {
        console.warn('[loadSeries] Réponse vide ignorée, conservation de l’état local');
        return prev;
      }
      return series;
    });
    if (series.length > 0) saveSeriesCache(series);
  } catch (error) {
    console.error('Erreur chargement séries bibliothèque:', error);
    const cached = loadSeriesCache();
    if (cached?.series?.length) {
      setUserSeriesLibrary(cached.series);
      toast.error('Erreur réseau — séries locales conservées');
    } else {
      toast.error('Erreur lors du chargement des séries');
    }
  } finally {
    setSeriesLibraryLoading(false);
  }
};

// Métadonnées locales uniquement — plus d'appel Open Library ici (il timeoutait
// 3× avant chaque ajout et faisait paraître l'action bloquée 10–30 s).
export const enrichSeriesMetadata = (seriesData) => {
  const categoryText = {
    roman: 'roman',
    bd: 'bande dessinée',
    manga: 'manga',
  };
  const authorText = seriesData.authors?.length
    ? ` par ${seriesData.authors.join(', ')}`
    : seriesData.author
      ? ` par ${seriesData.author}`
      : '';
  const volumeCount =
    seriesData.total_volumes ||
    seriesData.totalBooks ||
    (typeof seriesData.volumes === 'number' ? seriesData.volumes : 0) ||
    0;
  const volumeText = volumeCount
    ? ` Comprend ${volumeCount} tome${volumeCount > 1 ? 's' : ''}.`
    : '';

  return {
    // Vide si inconnue : l'enrichissement arrière-plan cherchera + mémorisera
    cover_image_url: resolveSeriesCover(seriesData) || '',
    description_fr:
      seriesData.description ||
      seriesData.description_fr ||
      `Série de ${categoryText[seriesData.category] || 'livres'}${authorText}.${volumeText}`,
    first_published: seriesData.first_published || '',
    last_published: seriesData.last_published || '',
    publisher: seriesData.publisher || '',
  };
};

// AJOUT DE SÉRIE COMPLÈTE À LA BIBLIOTHÈQUE
export const handleAddSeriesToLibrary = async (seriesData, {
  setSeriesLibraryLoading,
  loadUserSeriesLibrary
}) => {
  try {
    setSeriesLibraryLoading?.(true);
    const token = localStorage.getItem('token');

    const volumes = seriesLibraryService.generateVolumesList(
      seriesData,
      EXTENDED_SERIES_DATABASE
    );

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

    const enrichedMetadata = enrichSeriesMetadata({ ...seriesData, authors });

    const seriesPayload = {
      series_name: seriesData.name,
      author: seriesData.author || authors[0] || '',
      authors,
      category: seriesData.category || 'roman',
      total_volumes: volumes.length,
      volumes,
      description_fr: enrichedMetadata.description_fr,
      cover_image_url: enrichedMetadata.cover_image_url,
      first_published: enrichedMetadata.first_published || '',
      last_published: enrichedMetadata.last_published || '',
      publisher: enrichedMetadata.publisher || '',
      series_status: 'to_read',
    };

    const result = await seriesLibraryService.addSeriesToLibrary(seriesPayload, token);

    if (result.success) {
      toast.success(
        `Série « ${seriesData.name} » ajoutée (${volumes.length} tome${volumes.length > 1 ? 's' : ''})`,
        { duration: 3000 }
      );

      // Refresh hors chemin critique : l'UI peut fermer la modale tout de suite
      if (typeof loadUserSeriesLibrary === 'function') {
        Promise.resolve(loadUserSeriesLibrary()).catch((err) =>
          console.warn('Refresh séries après ajout:', err)
        );
      }
    }
    return result;
  } catch (error) {
    console.error('❌ Erreur ajout série:', error);
    const msg = error?.message || '';
    if (msg.includes('409')) {
      toast.error('Cette série est déjà dans votre bibliothèque');
    } else if (msg.includes('400')) {
      toast.error('Données de série invalides');
    } else {
      toast.error("Erreur lors de l'ajout de la série");
    }
    throw error;
  } finally {
    setSeriesLibraryLoading?.(false);
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