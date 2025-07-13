// Service pour gérer les séries en bibliothèque

const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

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

  return response.json();
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

// Mettre à jour le statut global d'une série
export const updateSeriesStatus = async (seriesId, newStatus, token) => {
  const response = await fetch(`${API_BASE}/api/series/library/${seriesId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ series_status: newStatus })
  });

  if (!response.ok) {
    throw new Error(`Erreur ${response.status}: ${await response.text()}`);
  }

  return response.json();
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
    
    // Fallback amélioré : Utiliser total_volumes ou volumes du seriesData
    const volumeCount = seriesData.total_volumes || seriesData.volumes || 1;
    console.log('⚠️ [DEBUG] Fallback génération:', volumeCount, 'volumes');
    
    return Array.from({ length: volumeCount }, (_, i) => ({
      volume_number: i + 1,
      volume_title: `${seriesData.name} - Tome ${i + 1}`,
      is_read: false,
      date_read: null
    }));
  } catch (error) {
    console.error('Erreur génération volumes:', error);
    // Fallback en cas d'erreur
    return Array.from({ length: seriesData.volumes || 1 }, (_, i) => ({
      volume_number: i + 1,
      volume_title: `${seriesData.name} - Tome ${i + 1}`,
      is_read: false,
      date_read: null
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

// Récupération d'image par défaut (peut être enrichie avec vision_expert_agent)
const getSeriesImage = async (seriesName) => {
  // Pour le moment, retourner une image par défaut
  // Plus tard, intégrer vision_expert_agent
  return '/default-series-cover.jpg';
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
