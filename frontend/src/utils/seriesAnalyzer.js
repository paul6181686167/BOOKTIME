// 🔍 ANALYSEUR AUTOMATIQUE DE SÉRIES - BOOKTIME
// Détection automatique des séries pour tous les livres de la bibliothèque

class SeriesAnalyzer {
  constructor() {
    this.apiBase = process.env.REACT_APP_BACKEND_URL || '';
    this.token = localStorage.getItem('token');
    this.analysisResults = [];
    this.reportData = {
      totalBooks: 0,
      booksAnalyzed: 0,
      seriesDetected: 0,
      standaloneBooks: 0,
      errors: 0,
      detectedSeries: [],
      errorBooks: []
    };
  }

  // 📊 Analyse complète de la bibliothèque
  async analyzeAllBooksForSeries(options = {}) {
    console.log('🔍 DÉMARRAGE ANALYSE AUTOMATIQUE DES SÉRIES');
    console.log('=' .repeat(50));
    
    const {
      minConfidence = 120,
      delayBetweenRequests = 200,
      onProgress = null
    } = options;

    try {
      // 1. Récupérer tous les livres
      const books = await this.fetchAllBooks();
      this.reportData.totalBooks = books.length;
      
      console.log(`📚 ${books.length} livres trouvés dans la bibliothèque`);
      
      // 2. Filtrer les livres sans saga
      const booksToAnalyze = books.filter(book => !book.saga || !book.saga.trim());
      this.reportData.booksAnalyzed = booksToAnalyze.length;
      
      console.log(`🔍 ${booksToAnalyze.length} livres à analyser (sans saga définie)`);
      
      if (booksToAnalyze.length === 0) {
        console.log('✅ Tous les livres ont déjà une saga définie !');
        return this.generateReport();
      }
      
      // 3. Analyser chaque livre
      for (let i = 0; i < booksToAnalyze.length; i++) {
        const book = booksToAnalyze[i];
        const progress = ((i + 1) / booksToAnalyze.length) * 100;
        
        console.log(`\n🔍 [${i + 1}/${booksToAnalyze.length}] Analyse: "${book.title}"`);
        console.log(`📖 Auteur: ${book.author}`);
        console.log(`📊 Progression: ${progress.toFixed(1)}%`);
        
        try {
          const detection = await this.detectSeriesForBook(book);
          
          if (detection.found && detection.confidence >= minConfidence) {
            // Série détectée avec confiance suffisante
            this.reportData.seriesDetected++;
            this.reportData.detectedSeries.push({
              book: book,
              seriesName: detection.series_name,
              confidence: detection.confidence,
              reasons: detection.match_reasons,
              volumeNumber: detection.series_info?.volume_number || null
            });
            
            console.log(`✅ SÉRIE DÉTECTÉE: "${detection.series_name}"`);
            console.log(`📊 Confiance: ${detection.confidence}`);
            console.log(`🎯 Raisons: ${detection.match_reasons.join(', ')}`);
            
          } else {
            // Livre standalone
            this.reportData.standaloneBooks++;
            console.log(`📖 LIVRE STANDALONE (confiance: ${detection.confidence})`);
          }
          
        } catch (error) {
          this.reportData.errors++;
          this.reportData.errorBooks.push({
            book: book,
            error: error.message
          });
          console.error(`❌ Erreur analyse "${book.title}":`, error.message);
        }
        
        // Callback progression
        if (onProgress) {
          onProgress(i + 1, booksToAnalyze.length, progress);
        }
        
        // Délai entre requêtes
        if (i < booksToAnalyze.length - 1) {
          await this.delay(delayBetweenRequests);
        }
      }
      
      console.log('\n🎉 ANALYSE TERMINÉE !');
      return this.generateReport();
      
    } catch (error) {
      console.error('❌ Erreur analyse globale:', error);
      throw error;
    }
  }

  // 🔍 Détection de série pour un livre spécifique
  async detectSeriesForBook(book) {
    const query = encodeURIComponent(`${book.title} ${book.author}`);
    
    const response = await fetch(`${this.apiBase}/api/series/detect?q=${query}`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erreur API: ${response.status}`);
    }
    
    return await response.json();
  }

  // 📚 Récupération de tous les livres
  async fetchAllBooks() {
    const response = await fetch(`${this.apiBase}/api/books?limit=1000`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erreur récupération livres: ${response.status}`);
    }
    
    const data = await response.json();
    return data.items || [];
  }

  // ⏰ Utilitaire délai
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 📊 Génération du rapport détaillé
  generateReport() {
    const report = {
      ...this.reportData,
      analysisDate: new Date().toISOString(),
      summary: this.generateSummary()
    };
    
    this.displayReport(report);
    return report;
  }

  // 📋 Génération du résumé
  generateSummary() {
    const { totalBooks, booksAnalyzed, seriesDetected, standaloneBooks, errors } = this.reportData;
    
    return {
      totalBooks,
      booksAnalyzed,
      seriesDetected,
      standaloneBooks,
      errors,
      detectionRate: booksAnalyzed > 0 ? ((seriesDetected / booksAnalyzed) * 100).toFixed(1) : 0,
      seriesNames: [...new Set(this.reportData.detectedSeries.map(d => d.seriesName))],
      topSeries: this.getTopDetectedSeries()
    };
  }

  // 🏆 Séries les plus détectées
  getTopDetectedSeries() {
    const seriesCount = {};
    
    this.reportData.detectedSeries.forEach(detection => {
      seriesCount[detection.seriesName] = (seriesCount[detection.seriesName] || 0) + 1;
    });
    
    return Object.entries(seriesCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }));
  }

  // 📊 Affichage du rapport
  displayReport(report) {
    console.log('\n🎯 RAPPORT D\'ANALYSE DÉTAILLÉ');
    console.log('=' .repeat(50));
    
    // Statistiques générales
    console.log('\n📊 STATISTIQUES GÉNÉRALES:');
    console.log(`📚 Livres total: ${report.summary.totalBooks}`);
    console.log(`🔍 Livres analysés: ${report.summary.booksAnalyzed}`);
    console.log(`✅ Séries détectées: ${report.summary.seriesDetected}`);
    console.log(`📖 Livres standalone: ${report.summary.standaloneBooks}`);
    console.log(`❌ Erreurs: ${report.summary.errors}`);
    console.log(`📊 Taux de détection: ${report.summary.detectionRate}%`);
    
    // Séries détectées
    if (report.detectedSeries.length > 0) {
      console.log('\n✅ SÉRIES DÉTECTÉES:');
      report.detectedSeries.forEach((detection, index) => {
        console.log(`${index + 1}. "${detection.book.title}"`);
        console.log(`   → Série: "${detection.seriesName}"`);
        console.log(`   → Confiance: ${detection.confidence}`);
        console.log(`   → Raisons: ${detection.reasons.join(', ')}`);
        if (detection.volumeNumber) {
          console.log(`   → Volume: ${detection.volumeNumber}`);
        }
        console.log('');
      });
    }
    
    // Top séries
    if (report.summary.topSeries.length > 0) {
      console.log('\n🏆 SÉRIES LES PLUS DÉTECTÉES:');
      report.summary.topSeries.forEach((series, index) => {
        console.log(`${index + 1}. "${series.name}" (${series.count} livres)`);
      });
    }
    
    // Erreurs
    if (report.errorBooks.length > 0) {
      console.log('\n❌ ERREURS:');
      report.errorBooks.forEach((error, index) => {
        console.log(`${index + 1}. "${error.book.title}": ${error.error}`);
      });
    }
    
    console.log('\n🎉 Rapport terminé !');
    console.log('💡 Utilisez updateDetectedSeries() pour appliquer les changements.');
  }

  // 🔄 Mise à jour des livres avec séries détectées
  async updateDetectedSeries(options = {}) {
    const { confirmEach = false, minConfidence = 120 } = options;
    
    const seriesToUpdate = this.reportData.detectedSeries.filter(
      detection => detection.confidence >= minConfidence
    );
    
    if (seriesToUpdate.length === 0) {
      console.log('❌ Aucune série à mettre à jour');
      return;
    }
    
    console.log(`\n🔄 MISE À JOUR DE ${seriesToUpdate.length} LIVRES`);
    console.log('=' .repeat(50));
    
    let updated = 0;
    let errors = 0;
    
    for (const detection of seriesToUpdate) {
      try {
        // Confirmation individuelle si demandée
        if (confirmEach) {
          const confirm = window.confirm(
            `Mettre à jour "${detection.book.title}" → série "${detection.seriesName}" ?`
          );
          if (!confirm) {
            console.log(`⏭️ Ignoré: "${detection.book.title}"`);
            continue;
          }
        }
        
        // Mise à jour du livre
        const updateResponse = await fetch(`${this.apiBase}/api/books/${detection.book.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            ...detection.book,
            saga: detection.seriesName,
            volume_number: detection.volumeNumber
          })
        });
        
        if (updateResponse.ok) {
          updated++;
          console.log(`✅ Mis à jour: "${detection.book.title}" → "${detection.seriesName}"`);
        } else {
          errors++;
          console.error(`❌ Erreur mise à jour: "${detection.book.title}"`);
        }
        
      } catch (error) {
        errors++;
        console.error(`❌ Erreur: "${detection.book.title}":`, error.message);
      }
      
      // Délai entre mises à jour
      await this.delay(300);
    }
    
    console.log(`\n🎉 MISE À JOUR TERMINÉE:`);
    console.log(`✅ Livres mis à jour: ${updated}`);
    console.log(`❌ Erreurs: ${errors}`);
    console.log('💡 Rechargez la page pour voir les changements !');
  }
}

// 🌍 Export et utilisation globale
window.SeriesAnalyzer = SeriesAnalyzer;

// 🚀 Fonctions utilitaires globales
window.analyzeAllSeries = async (options = {}) => {
  const analyzer = new SeriesAnalyzer();
  return await analyzer.analyzeAllBooksForSeries(options);
};

window.updateDetectedSeries = async (options = {}) => {
  if (window.lastAnalyzer) {
    return await window.lastAnalyzer.updateDetectedSeries(options);
  } else {
    console.error('❌ Aucune analyse précédente trouvée. Lancez d\'abord analyzeAllSeries()');
  }
};

console.log('🔍 SeriesAnalyzer chargé !');
console.log('💡 Utilisez: analyzeAllSeries() pour démarrer l\'analyse');

export default SeriesAnalyzer;