// 🔄 DÉTECTION AUTOMATIQUE À L'AJOUT DE LIVRES
// Intégration dans le processus d'ajout pour détecter automatiquement les séries

export class AutoSeriesDetector {
  constructor() {
    this.apiBase = process.env.REACT_APP_BACKEND_URL || '';
    this.enabled = true;
    this.minConfidence = 120;
  }

  // 🎯 Détection automatique lors de l'ajout d'un livre
  async detectAndEnhanceBook(bookData) {
    if (!this.enabled) {
      return bookData;
    }

    console.log('🔍 Détection automatique série pour:', bookData.title);

    try {
      // 1. Vérifier si le livre a déjà une saga
      if (bookData.saga && bookData.saga.trim()) {
        console.log('📚 Saga déjà définie:', bookData.saga);
        return bookData;
      }

      // 2. Détecter la série
      const detection = await this.detectSeries(bookData);
      
      if (detection.found && detection.confidence >= this.minConfidence) {
        console.log(`✅ Série détectée: "${detection.series_name}" (confiance: ${detection.confidence})`);
        
        // 3. Enrichir les données du livre
        const enhancedBook = {
          ...bookData,
          saga: detection.series_name,
          volume_number: detection.series_info?.volume_number || null,
          auto_detected_series: true,
          detection_confidence: detection.confidence,
          detection_reasons: detection.match_reasons
        };

        // 4. Notification utilisateur
        this.notifySeriesDetected(enhancedBook, detection);
        
        return enhancedBook;
      } else {
        console.log(`📖 Livre standalone (confiance: ${detection.confidence})`);
        return bookData;
      }

    } catch (error) {
      console.error('❌ Erreur détection automatique:', error);
      return bookData; // Retour aux données originales en cas d'erreur
    }
  }

  // 🔍 Détection de série
  async detectSeries(bookData) {
    const token = localStorage.getItem('token');
    const query = encodeURIComponent(`${bookData.title} ${bookData.author}`);
    
    const response = await fetch(`${this.apiBase}/api/series/detect?q=${query}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erreur API détection: ${response.status}`);
    }
    
    return await response.json();
  }

  // 📢 Notification utilisateur
  notifySeriesDetected(book, detection) {
    // Toast notification
    if (window.toast) {
      window.toast.success(
        `📚 Série détectée: "${detection.series_name}" (confiance: ${detection.confidence})`,
        {
          duration: 4000,
          position: 'top-right'
        }
      );
    }

    // Console détaillée
    console.log('🎯 DÉTECTION AUTOMATIQUE RÉUSSIE:');
    console.log(`📚 Livre: "${book.title}"`);
    console.log(`🎯 Série: "${detection.series_name}"`);
    console.log(`📊 Confiance: ${detection.confidence}`);
    console.log(`🔍 Raisons: ${detection.match_reasons.join(', ')}`);
    if (book.volume_number) {
      console.log(`📖 Volume: ${book.volume_number}`);
    }
  }

  // ⚙️ Configuration
  configure(options = {}) {
    const {
      enabled = true,
      minConfidence = 120,
      notifyUser = true
    } = options;

    this.enabled = enabled;
    this.minConfidence = minConfidence;
    this.notifyUser = notifyUser;

    console.log('⚙️ Configuration détection automatique:', {
      enabled: this.enabled,
      minConfidence: this.minConfidence,
      notifyUser: this.notifyUser
    });
  }
}

// 🔄 Hook pour l'intégration dans les composants React
export const useAutoSeriesDetection = () => {
  const detector = new AutoSeriesDetector();

  const enhanceBookWithSeries = async (bookData) => {
    return await detector.detectAndEnhanceBook(bookData);
  };

  const configure = (options) => {
    detector.configure(options);
  };

  return {
    enhanceBookWithSeries,
    configure,
    detector
  };
};

// 🌍 Export global
window.AutoSeriesDetector = AutoSeriesDetector;

export default AutoSeriesDetector;