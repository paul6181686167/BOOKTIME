import { API_BASE_URL } from '../config/environment';
import { mapMergedVolumeRowsToLibraryVolumes } from '../utils/sourceMerge';
// Service pour gérer les séries en bibliothèque

const API_BASE = API_BASE_URL

// Ajouter une série complète à la bibliothèque
export const addSeriesToLibrary = async (seriesData, token) => {
  const response = await fetch(`${API_BASE}/api/series/library`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(seriesData)
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${await response.text()}`);
  }

  return response.json();
};

// Récupérer toutes les séries de la bibliothèque
export const getUserSeriesLibrary = async (token, filters = {}) => {
  const params = new URLSearchParams();
  if (filters.category) params.append('category', filters.category);
  if (filters.status) params.append('status', filters.status);

  const response = await fetch(`${API_BASE}/api/series/library?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${await response.text()}`);
  }

  const result = await response.json();

  // API peut renvoyer un tableau ou { series: [...] }
  const series = Array.isArray(result)
    ? result
    : Array.isArray(result?.series)
      ? result.series
      : [];

  return {
    series,
    total_count: series.length,
  };
};

// Toggle statut lu/non lu d'un tome
export const toggleVolumeStatus = async (seriesId, volumeNumber, isRead, token) => {
  const response = await fetch(`${API_BASE}/api/series/library/${seriesId}/volume/${volumeNumber}?is_read=${isRead}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${await response.text()}`);
  }

  return response.json();
};

// Mettre à jour une entrée series_library (statut et/ou page courante)
export const updateSeriesLibraryEntry = async (seriesId, data, token) => {
  const response = await fetch(`${API_BASE}/api/series/library/${seriesId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${await response.text()}`);
  }

  return response.json();
};

// Mettre à jour le statut global d'une série
export const updateSeriesStatus = async (seriesId, newStatus, token) => {
  return updateSeriesLibraryEntry(seriesId, { series_status: newStatus }, token);
};

// Supprimer une série de la bibliothèque
export const deleteSeriesFromLibrary = async (seriesId, token) => {
  const response = await fetch(`${API_BASE}/api/series/library/${seriesId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${await response.text()}`);
  }

  return response.json();
};

// Générer la liste des tomes avec titres depuis le référentiel
export const generateVolumesList = (seriesData, extendedSeriesDatabase) => {
  const parseVol = (vol, fallbackIndex) => {
    if (vol == null || vol === '') return fallbackIndex;
    const m = String(vol).match(/\d+/);
    if (!m) return fallbackIndex;
    const n = parseInt(m[0], 10);
    return Number.isNaN(n) ? fallbackIndex : n;
  };

  if (
    Array.isArray(seriesData.mergedLibraryVolumes) &&
    seriesData.mergedLibraryVolumes.length > 0
  ) {
    return mapMergedVolumeRowsToLibraryVolumes(seriesData.name || '', seriesData.mergedLibraryVolumes);
  }

  if (
    seriesData.fromStaticWikidata &&
    Array.isArray(seriesData.staticWikidataDetail?.works) &&
    seriesData.staticWikidataDetail.works.length > 0
  ) {
    const sorted = [...seriesData.staticWikidataDetail.works].sort((a, b) => {
      const na = parseVol(a.volume, 9999);
      const nb = parseVol(b.volume, 9999);
      return na - nb;
    });
    return sorted.map((w, i) => {
      const title = w.title_fr || w.title_en || `${seriesData.name} - Tome ${i + 1}`;
      const volume_number = parseVol(w.volume, i + 1);
      return {
        volume_number,
        volume_title: title,
        is_read: false,
        date_read: null,
        wikidata_work_qid: w.work_qid || null,
      };
    });
  }

  try {
    const seriesKey = normalizeString(seriesData.name);
    
    // CORRECTION : Essayer différentes variantes de catégorie pour correspondre à la base
    const categoryMappings = {
      'roman': 'romans',
      'romans': 'romans',
      'bd': 'bd',
      'manga': 'mangas',
      'mangas': 'mangas'
    };
    
    const categoryKey = categoryMappings[seriesData.category] || seriesData.category;
    const seriesInfo = extendedSeriesDatabase[categoryKey]?.[seriesKey];
    
    console.log('🔍 [DEBUG] Recherche série:', { 
      originalName: seriesData.name, 
      normalizedKey: seriesKey, 
      originalCategory: seriesData.category,
      mappedCategory: categoryKey,
      seriesFound: !!seriesInfo 
    });
    
    if (seriesInfo) {
      // CORRECTION : Chercher d'abord volume_titles, puis tomes_officiels
      const volumes = seriesInfo.volume_titles || seriesInfo.tomes_officiels;
      
      if (volumes) {
        console.log('✅ [DEBUG] Volumes trouvés:', volumes);
        
        // Si c'est un objet (volume_titles), convertir en array
        const volumeArray = Array.isArray(volumes) ? volumes : Object.values(volumes);
        
        return volumeArray.map((title, index) => ({
          volume_number: index + 1,
          volume_title: title,
          is_read: false,
          date_read: null
        }));
      }
    }
    
    // Fallback : total_volumes / totalBooks / work_count (PAS un array volumes vide)
    const volumeCount = Number(
      seriesData.total_volumes ||
        seriesData.totalBooks ||
        seriesData.work_count ||
        (typeof seriesData.volumes === 'number' ? seriesData.volumes : 0) ||
        0
    );
    if (!volumeCount || volumeCount < 1) {
      // Pas de tomes connus → une seule entrée générique (sera rétrogradée en livre à l'affichage)
      return [
        {
          volume_number: 1,
          volume_title: seriesData.name || 'Tome 1',
          is_read: false,
          date_read: null,
        },
      ];
    }
    console.log('⚠️ [DEBUG] Fallback génération:', volumeCount, 'volumes');

    return Array.from({ length: volumeCount }, (_, i) => ({
      volume_number: i + 1,
      volume_title: `${seriesData.name} - Tome ${i + 1}`,
      is_read: false,
      date_read: null,
    }));
  } catch (error) {
    console.error('Erreur génération volumes:', error);
    const n = Number(
      (typeof seriesData.volumes === 'number' && seriesData.volumes) ||
        seriesData.total_volumes ||
        1
    );
    return Array.from({ length: Math.max(1, n) }, (_, i) => ({
      volume_number: i + 1,
      volume_title: `${seriesData.name} - Tome ${i + 1}`,
      is_read: false,
      date_read: null,
    }));
  }
};

// Fonction utilitaire pour normaliser les chaînes
const normalizeString = (str) => {
  return str?.toLowerCase()
    .replace(/[àáâãäå]/g, 'a')
    .replace(/[èéêë]/g, 'e')
    .replace(/[ìíîï]/g, 'i')
    .replace(/[òóôõö]/g, 'o')
    .replace(/[ùúûü]/g, 'u')
    .replace(/[ñ]/g, 'n')
    .replace(/[ç]/g, 'c')
    .replace(/\s+/g, '_')  // CORRECTION : Remplacer espaces par underscores
    .replace(/[^a-z0-9_]/g, '')  // CORRECTION : Garder les underscores
    || '';
};

// Enrichissement automatique des métadonnées
export const enrichSeriesMetadata = async (seriesData) => {
  try {
    // Récupérer une image représentative
    const cover_image_url = await getSeriesImage(seriesData.name);
    
    // Générer une description basique (peut être enrichie plus tard)
    const description_fr = generateBasicDescription(seriesData);
    
    return {
      cover_image_url,
      description_fr,
      first_published: seriesData.first_published || '',
      last_published: seriesData.last_published || '',
      publisher: seriesData.publisher || ''
    };
  } catch (error) {
    console.error('Erreur enrichissement métadonnées:', error);
    return {
      cover_image_url: '',
      description_fr: `Série ${seriesData.category} populaire.`,
      first_published: '',
      last_published: '',
      publisher: ''
    };
  }
};

// Image par défaut série (SVG inline pour éviter 404)
export const DEFAULT_SERIES_COVER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='300' viewBox='0 0 200 300'%3E%3Crect fill='%23e5e7eb' width='200' height='300'/%3E%3Ctext fill='%239ca3af' x='50%25' y='50%25' text-anchor='middle' dy='.3em' font-family='sans-serif' font-size='48'%3E📚%3C/text%3E%3C/svg%3E";

const getSeriesImage = async (seriesName) => {
  return DEFAULT_SERIES_COVER;
};

// Génération description basique
const generateBasicDescription = (seriesData) => {
  const categoryText = {
    'roman': 'roman',
    'bd': 'bande dessinée',
    'manga': 'manga'
  };
  
  return `Série de ${categoryText[seriesData.category] || 'livres'} populaire ${seriesData.authors?.length ? `par ${seriesData.authors.join(', ')}` : ''}.${seriesData.volumes ? ` Comprend ${seriesData.volumes} tome${seriesData.volumes > 1 ? 's' : ''}.` : ''}`;
};
