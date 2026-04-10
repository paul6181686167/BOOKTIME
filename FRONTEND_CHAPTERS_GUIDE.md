# 🎨 **GUIDE DÉVELOPPEUR FRONTEND - COMPOSANTS CHAPITRES**

*Version 1.0 - React 18 + Hooks - Juillet 2025*

---

## 🎯 **APERÇU DES COMPOSANTS**

Le système chapitres frontend comprend **2 composants principaux** :

1. **`ChapterSection.js`** (352 lignes) : Interface utilisateur complète
2. **`useSeriesChapters.js`** (185 lignes) : Hook personnalisé pour logique métier

Ces composants s'intègrent parfaitement dans l'écosystème React existant avec support complet du **dark mode** et **responsive design**.

---

## 📦 **COMPOSANT PRINCIPAL : ChapterSection**

### **Import et Usage de Base**

```javascript
import ChapterSection from '../components/ChapterSection';

// Usage dans un modal ou page
const SeriesModal = ({ seriesInfo }) => {
  return (
    <div className="modal-content">
      {/* Contenu existant du modal */}
      
      {/* Section chapitres enrichie */}
      {seriesInfo && (
        <ChapterSection 
          seriesName={seriesInfo.name}
          onClose={() => setShowChapterSection(false)}
        />
      )}
    </div>
  );
};
```

### **Props Interface**

```typescript
interface ChapterSectionProps {
  seriesName: string;           // Nom de la série (requis)
  onClose?: () => void;         // Fonction fermeture (optionnel)
}
```

### **État Interne**

```javascript
const ChapterSection = ({ seriesName, onClose }) => {
  const [showAllChapters, setShowAllChapters] = useState(false);
  const [showAllVolumes, setShowAllVolumes] = useState(false);
  
  // Hook personnalisé pour données
  const {
    chaptersData,
    loading,
    error,
    refreshChapters,
    hasChapters,
    hasVolumes,
    hasPredictions
  } = useSeriesChapters(seriesName);
  
  // ...
};
```

### **Structure de Rendu**

```javascript
return (
  <div className="mt-6 border-t pt-6">
    {/* En-tête avec titre et contrôles */}
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold">
        📚 Chapitres et Prédictions
      </h3>
      <div className="flex items-center space-x-2">
        {/* Timestamp + bouton refresh */}
      </div>
    </div>

    {/* États de chargement/erreur */}
    {loading && <LoadingSpinner />}
    {error && <ErrorMessage />}

    {/* Contenu principal */}
    {chaptersData && !loading && (
      <div>
        {renderPredictions()}    {/* Prédictions en premier */}
        {renderChapters()}       {/* Chapitres récents */}  
        {renderVolumes()}        {/* Volumes/Tomes */}
      </div>
    )}
  </div>
);
```

---

## 🎛️ **HOOK PERSONNALISÉ : useSeriesChapters**

### **API Complète**

```javascript
const {
  // Données principales
  chaptersData,      // Object | null - Données complètes série
  loading,           // boolean - État chargement
  error,             // string | null - Message d'erreur
  lastUpdated,       // Date | null - Timestamp dernière MAJ
  
  // Actions
  fetchChapters,     // (forceFresh?: boolean) => Promise<void>
  refreshChapters,   // () => Promise<void>
  
  // Helpers booléens
  hasChapters,       // boolean - A des chapitres
  hasVolumes,        // boolean - A des volumes
  hasPredictions,    // boolean - A des prédictions
  
  // Métriques rapides
  totalChapters,     // number - Total chapitres
  latestChapter,     // Chapter | null - Dernier chapitre
  nextPrediction,    // ChapterPrediction | null - Prochaine prédiction
} = useSeriesChapters(seriesName);
```

### **Cache Intelligent**

```javascript
// Cache localStorage avec TTL de 1 heure
const getCacheKey = (name) => `chapters_${name.toLowerCase().replace(/\s+/g, '_')}`;

const getFromCache = (name) => {
  const cached = localStorage.getItem(getCacheKey(name));
  if (cached) {
    const parsed = JSON.parse(cached);
    const cacheAge = Date.now() - parsed.timestamp;
    
    // Valide pendant 1 heure
    if (cacheAge < 3600000) {
      return parsed.data;
    }
  }
  return null;
};
```

### **Gestion d'Erreurs**

```javascript
const fetchChapters = async (forceFresh = false) => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('Token d\'authentification requis');
    }

    const response = await fetch(`${API_BASE_URL}/api/chapters/series/${encodeURIComponent(seriesName)}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Session expirée, veuillez vous reconnecter');
      } else if (response.status === 404) {
        throw new Error('Aucune donnée chapitre disponible pour cette série');
      } else {
        throw new Error(`Erreur serveur (${response.status})`);
      }
    }

    const data = await response.json();
    setChaptersData(data);
    saveToCache(seriesName, data);
    
  } catch (err) {
    setError(err.message);
    setChaptersData(null);
  }
};
```

---

## 🎨 **COMPOSANTS UI DÉTAILLÉS**

### **Rendu des Chapitres**

```javascript
const renderChapters = () => {
  if (!hasChapters) return null;

  const chapters = chaptersData.current_chapters || [];
  const displayChapters = showAllChapters ? chapters : chapters.slice(-8);

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-md font-semibold flex items-center">
          <ChapterIcon />
          <span className="ml-2">Chapitres Récents</span>
          {totalChapters > 0 && (
            <span className="ml-2 text-sm text-gray-500">({totalChapters} total)</span>
          )}
        </h4>
        
        {/* Bouton expand/collapse */}
        {chapters.length > 8 && (
          <button onClick={() => setShowAllChapters(!showAllChapters)}>
            {showAllChapters ? 'Voir moins' : `Voir tous (${chapters.length})`}
          </button>
        )}
      </div>

      {/* Grille responsive des chapitres */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {displayChapters.map((chapter, index) => (
          <ChapterCard key={chapter.chapter_number} chapter={chapter} />
        ))}
      </div>
    </div>
  );
};
```

### **Carte Chapitre avec Statuts**

```javascript
const ChapterCard = ({ chapter }) => {
  const getStatusStyles = (status) => {
    switch (status) {
      case 'released':
        return 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-700 dark:text-green-300';
      case 'upcoming':
        return 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-300';
      case 'predicted':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-300';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800 dark:bg-gray-900/20 dark:border-gray-700 dark:text-gray-300';
    }
  };

  return (
    <div className={`p-2 rounded-lg border text-xs ${getStatusStyles(chapter.status)}`}>
      <div className="font-semibold">Ch. {chapter.chapter_number}</div>
      {chapter.title && (
        <div className="text-xs opacity-75 truncate">{chapter.title}</div>
      )}
      <div className="text-xs opacity-60 mt-1">
        {formatDate(chapter.release_date)}
      </div>
    </div>
  );
};
```

### **Rendu des Prédictions**

```javascript
const renderPredictions = () => {
  if (!hasPredictions) return null;

  const predictions = chaptersData.predictions || {};

  return (
    <div className="mb-4">
      <h4 className="text-md font-semibold flex items-center mb-3">
        <CalendarIcon />
        <span className="ml-2">Prédictions Sorties</span>
      </h4>

      <div className="space-y-2">
        {/* Prédiction prochain chapitre */}
        {predictions.next_chapter && (
          <PredictionCard 
            type="chapter"
            prediction={predictions.next_chapter}
            colorScheme="blue"
          />
        )}

        {/* Prédiction prochain volume */}
        {predictions.next_volume && (
          <PredictionCard 
            type="volume"
            prediction={predictions.next_volume}
            colorScheme="purple"
          />
        )}
      </div>
    </div>
  );
};
```

### **Carte Prédiction avec Confiance**

```javascript
const PredictionCard = ({ type, prediction, colorScheme }) => {
  const formatConfidence = (confidence) => {
    if (!confidence) return '';
    const percent = Math.round(confidence * 100);
    if (percent >= 80) return '🟢';
    if (percent >= 60) return '🟡';
    return '🔴';
  };

  const colorClasses = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700 text-blue-900 dark:text-blue-100',
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-700 text-purple-900 dark:text-purple-100'
  };

  return (
    <div className={`p-3 rounded-lg border ${colorClasses[colorScheme]}`}>
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium">
          Prochain {type === 'chapter' ? 'Chapitre' : 'Volume'} {prediction.estimated_number}
        </div>
        <div className="text-xs">
          {formatConfidence(prediction.confidence)}
        </div>
      </div>
      <div className="text-xs mt-1">
        Prévu le {formatDate(prediction.estimated_date)}
      </div>
      {prediction.estimated_chapters_range && (
        <div className="text-xs mt-1">
          Chapitres {prediction.estimated_chapters_range}
        </div>
      )}
    </div>
  );
};
```

---

## 🔄 **GESTION D'ÉTAT ET LIFECYCLE**

### **Cycle de Vie Composant**

```javascript
const ChapterSection = ({ seriesName, onClose }) => {
  const hook = useSeriesChapters(seriesName);

  // Auto-actualisation toutes les 30 minutes
  useEffect(() => {
    if (!seriesName) return;

    const interval = setInterval(() => {
      hook.fetchChapters(false); // Depuis cache si disponible
    }, 30 * 60 * 1000); // 30 minutes

    return () => clearInterval(interval);
  }, [seriesName, hook.fetchChapters]);

  // Nettoyage au démontage
  useEffect(() => {
    return () => {
      // Nettoyage optionnel
      console.log('ChapterSection unmounted for', seriesName);
    };
  }, [seriesName]);
};
```

### **État de Chargement**

```javascript
const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-8">
    <div className="flex items-center text-sm text-gray-500">
      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
      Récupération des données chapitres...
    </div>
  </div>
);
```

### **Gestion d'Erreurs UI**

```javascript
const ErrorMessage = ({ error, onRetry }) => (
  <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 mb-4">
    <div className="text-sm text-red-800 dark:text-red-200">
      <strong>Erreur :</strong> {error}
    </div>
    <button
      onClick={onRetry}
      className="mt-2 text-xs text-red-600 hover:text-red-800 dark:text-red-400 underline"
    >
      Réessayer
    </button>
  </div>
);
```

---

## 🎯 **INTÉGRATION DANS L'APPLICATION**

### **SeriesDetailModal.js**

```javascript
import ChapterSection from './ChapterSection';

const SeriesDetailModal = ({ series, isOpen, onClose }) => {
  const [showChapterSection, setShowChapterSection] = useState(true);

  return (
    <div className={`modal ${isOpen ? 'modal-open' : ''}`}>
      <div className="modal-content max-w-4xl">
        {/* En-tête modal existant */}
        <div className="modal-header">
          <h2>{series?.name}</h2>
          <button onClick={onClose}>×</button>
        </div>

        {/* Contenu existant (infos série, livres) */}
        <div className="modal-body">
          {/* Section informations générales */}
          <SeriesInfoSection series={series} />
          
          {/* Section livres de la série */}
          <SeriesBooksSection books={series?.books} />
          
          {/* 🆕 NOUVELLE SECTION CHAPITRES */}
          {showChapterSection && series?.name && (
            <ChapterSection 
              seriesName={series.name}
              onClose={() => setShowChapterSection(false)}
            />
          )}
        </div>

        {/* Actions modal existantes */}
        <div className="modal-footer">
          <button onClick={onClose}>Fermer</button>
        </div>
      </div>
    </div>
  );
};
```

### **Feature Flag (Optionnel)**

```javascript
// Activation progressive avec feature flag
const ENABLE_CHAPTERS_FEATURE = process.env.REACT_APP_ENABLE_CHAPTERS === 'true';

// Dans le composant
{ENABLE_CHAPTERS_FEATURE && (
  <ChapterSection seriesName={seriesName} />
)}
```

---

## 🎨 **STYLING ET THEMES**

### **Classes Tailwind Utilisées**

```css
/* Layout */
.mt-6.border-t.pt-6          /* Séparation section */
.grid.grid-cols-2.sm:grid-cols-3.md:grid-cols-4.gap-2  /* Grille responsive */

/* États chapitres */
.bg-green-50.border-green-200.text-green-800    /* Released */
.bg-blue-50.border-blue-200.text-blue-800       /* Upcoming */
.bg-yellow-50.border-yellow-200.text-yellow-800 /* Predicted */

/* Dark mode */
.dark:bg-green-900/20.dark:border-green-700.dark:text-green-300
.dark:bg-blue-900/20.dark:border-blue-700.dark:text-blue-300
.dark:bg-yellow-900/20.dark:border-yellow-700.dark:text-yellow-300

/* Interactivité */
.hover:bg-gray-50.hover:text-gray-900
.cursor-pointer.transition-colors
```

### **Variables CSS Personnalisées**

```css
:root {
  --chapters-cache-duration: 3600000; /* 1 heure en ms */
  --chapters-refresh-interval: 1800000; /* 30 min en ms */
  --chapters-animation-duration: 200ms;
}

/* Animation des cartes */
.chapter-card {
  transition: transform var(--chapters-animation-duration) ease-in-out;
}

.chapter-card:hover {
  transform: translateY(-2px);
}
```

---

## 📱 **RESPONSIVE DESIGN**

### **Breakpoints Utilisés**

```css
/* Mobile first approach */
.grid-cols-2           /* Mobile : 2 colonnes */
.sm:grid-cols-3        /* Tablet : 3 colonnes */
.md:grid-cols-4        /* Desktop : 4 colonnes */

/* Adaptations mobiles */
@media (max-width: 640px) {
  .chapter-card {
    font-size: 0.75rem;  /* Plus petit sur mobile */
  }
}
```

### **Composant Responsive**

```javascript
const useResponsive = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return { isMobile };
};

// Usage dans ChapterSection
const { isMobile } = useResponsive();
const chaptersToShow = isMobile ? 4 : 8; // Moins sur mobile
```

---

## 🧪 **TESTS COMPOSANTS**

### **Tests Unit Hook**

```javascript
import { renderHook, act } from '@testing-library/react';
import { useSeriesChapters } from '../hooks/useSeriesChapters';

describe('useSeriesChapters Hook', () => {
  beforeEach(() => {
    localStorage.clear();
    fetch.resetMocks();
  });

  test('should fetch chapters data', async () => {
    const mockData = {
      series_name: 'One Piece',
      current_chapters: [
        { chapter_number: 1101, status: 'released' }
      ]
    };

    fetch.mockResponseOnce(JSON.stringify(mockData));

    const { result, waitForNextUpdate } = renderHook(() => 
      useSeriesChapters('One Piece')
    );

    expect(result.current.loading).toBe(true);

    await waitForNextUpdate();

    expect(result.current.loading).toBe(false);
    expect(result.current.chaptersData).toEqual(mockData);
    expect(result.current.hasChapters).toBe(true);
  });

  test('should handle cache correctly', () => {
    const cachedData = { series_name: 'Cached Series' };
    localStorage.setItem(
      'chapters_cached_series', 
      JSON.stringify({
        data: cachedData,
        timestamp: Date.now()
      })
    );

    const { result } = renderHook(() => 
      useSeriesChapters('Cached Series')
    );

    expect(result.current.chaptersData).toEqual(cachedData);
  });
});
```

### **Tests Composant**

```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChapterSection from '../components/ChapterSection';

const mockChaptersData = {
  current_chapters: [
    {
      chapter_number: 1101,
      title: 'Test Chapter',
      status: 'released',
      release_date: '2024-01-15T00:00:00Z'
    }
  ],
  predictions: {
    next_chapter: {
      estimated_number: 1102,
      confidence: 0.95
    }
  }
};

jest.mock('../hooks/useSeriesChapters', () => ({
  useSeriesChapters: () => ({
    chaptersData: mockChaptersData,
    loading: false,
    error: null,
    hasChapters: true,
    hasPredictions: true,
    refreshChapters: jest.fn()
  })
}));

describe('ChapterSection Component', () => {
  test('renders chapters section correctly', () => {
    render(<ChapterSection seriesName="One Piece" />);
    
    expect(screen.getByText('📚 Chapitres et Prédictions')).toBeInTheDocument();
    expect(screen.getByText('Ch. 1101')).toBeInTheDocument();
    expect(screen.getByText('Test Chapter')).toBeInTheDocument();
  });

  test('shows loading state', () => {
    jest.mocked(useSeriesChapters).mockReturnValue({
      loading: true,
      chaptersData: null,
      error: null
    });

    render(<ChapterSection seriesName="Loading Series" />);
    
    expect(screen.getByText(/récupération des données/i)).toBeInTheDocument();
  });

  test('handles refresh button click', async () => {
    const mockRefresh = jest.fn();
    jest.mocked(useSeriesChapters).mockReturnValue({
      chaptersData: mockChaptersData,
      refreshChapters: mockRefresh,
      loading: false
    });

    render(<ChapterSection seriesName="One Piece" />);
    
    const refreshButton = screen.getByTitle('Actualiser les données');
    fireEvent.click(refreshButton);

    expect(mockRefresh).toHaveBeenCalled();
  });
});
```

---

## ⚡ **OPTIMISATIONS PERFORMANCE**

### **Memoization Composants**

```javascript
import { memo, useMemo } from 'react';

const ChapterCard = memo(({ chapter }) => {
  const statusStyles = useMemo(() => getStatusStyles(chapter.status), [chapter.status]);
  const formattedDate = useMemo(() => formatDate(chapter.release_date), [chapter.release_date]);

  return (
    <div className={`p-2 rounded-lg border text-xs ${statusStyles}`}>
      <div className="font-semibold">Ch. {chapter.chapter_number}</div>
      {chapter.title && (
        <div className="text-xs opacity-75 truncate">{chapter.title}</div>
      )}
      <div className="text-xs opacity-60 mt-1">{formattedDate}</div>
    </div>
  );
});
```

### **Lazy Loading**

```javascript
import { lazy, Suspense } from 'react';

const ChapterSection = lazy(() => import('./ChapterSection'));

// Usage avec fallback
<Suspense fallback={<div>Chargement section chapitres...</div>}>
  <ChapterSection seriesName={seriesName} />
</Suspense>
```

### **Debounce Refresh**

```javascript
import { useDebouncedCallback } from 'use-debounce';

const useSeriesChapters = (seriesName) => {
  const debouncedRefresh = useDebouncedCallback(
    async () => {
      await fetchChapters(true);
    },
    1000  // 1 seconde de debounce
  );

  return {
    // ...autres propriétés
    refreshChapters: debouncedRefresh
  };
};
```

---

## 🛠️ **UTILITAIRES ET HELPERS**

### **Formatage Dates**

```javascript
const formatDate = (dateString) => {
  if (!dateString) return 'Date inconnue';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

    // Formatage relatif pour dates récentes
    if (diffDays === 0) return "Aujourd'hui";
    if (diffDays === 1) return "Hier";
    if (diffDays < 7) return `Il y a ${diffDays} jours`;

    // Formatage standard pour dates plus anciennes
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  } catch (e) {
    return 'Date invalide';
  }
};
```

### **Calcul Confiance Visuelle**

```javascript
const getConfidenceIcon = (confidence) => {
  if (!confidence || confidence === 0) return '';
  
  const percent = Math.round(confidence * 100);
  
  if (percent >= 90) return '🟢';      // Très fiable
  if (percent >= 80) return '🔵';      // Fiable
  if (percent >= 60) return '🟡';      // Moyennement fiable
  if (percent >= 40) return '🟠';      // Peu fiable
  return '🔴';                         // Très peu fiable
};

const getConfidenceText = (confidence) => {
  const percent = Math.round(confidence * 100);
  
  if (percent >= 90) return 'Très fiable';
  if (percent >= 80) return 'Fiable';
  if (percent >= 60) return 'Modéré';
  if (percent >= 40) return 'Incertain';
  return 'Très incertain';
};
```

### **Validation Props**

```javascript
import PropTypes from 'prop-types';

ChapterSection.propTypes = {
  seriesName: PropTypes.string.isRequired,
  onClose: PropTypes.func
};

ChapterSection.defaultProps = {
  onClose: null
};
```

---

## 🔧 **CONFIGURATION ET VARIABLES**

### **Variables d'Environnement**

```javascript
// Frontend .env
REACT_APP_ENABLE_CHAPTERS_FEATURE=true
REACT_APP_CHAPTERS_CACHE_DURATION=3600000
REACT_APP_CHAPTERS_REFRESH_INTERVAL=1800000
REACT_APP_BACKEND_URL=http://localhost:8001
```

### **Configuration Hook**

```javascript
const CONFIG = {
  CACHE_DURATION: parseInt(process.env.REACT_APP_CHAPTERS_CACHE_DURATION) || 3600000,
  REFRESH_INTERVAL: parseInt(process.env.REACT_APP_CHAPTERS_REFRESH_INTERVAL) || 1800000,
  MAX_CHAPTERS_DISPLAY: 8,
  MAX_VOLUMES_DISPLAY: 4,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000
};
```

---

## 📚 **EXEMPLES D'USAGE AVANCÉS**

### **Composant avec Animation**

```javascript
import { motion } from 'framer-motion';

const AnimatedChapterCard = ({ chapter, index }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.1 }}
    className="chapter-card"
  >
    <ChapterCard chapter={chapter} />
  </motion.div>
);
```

### **Hook avec Context**

```javascript
import { createContext, useContext } from 'react';

const ChaptersContext = createContext();

export const ChaptersProvider = ({ children }) => {
  const [globalConfig, setGlobalConfig] = useState({
    enablePredictions: true,
    confidenceThreshold: 0.8
  });

  return (
    <ChaptersContext.Provider value={{ globalConfig, setGlobalConfig }}>
      {children}
    </ChaptersContext.Provider>
  );
};

export const useChaptersConfig = () => {
  const context = useContext(ChaptersContext);
  if (!context) {
    throw new Error('useChaptersConfig must be used within ChaptersProvider');
  }
  return context;
};
```

### **Intégration avec React Query**

```javascript
import { useQuery } from 'react-query';

const useSeriesChaptersQuery = (seriesName) => {
  return useQuery(
    ['seriesChapters', seriesName],
    () => fetchSeriesChapters(seriesName),
    {
      staleTime: 30 * 60 * 1000,  // 30 minutes
      cacheTime: 60 * 60 * 1000,  // 1 heure
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
    }
  );
};
```

---

*Guide Développeur Frontend - Version 1.0 - Juillet 2025*  
*Composants Chapitres BookTime - React 18 + Hooks Personnalisés*