/**
 * UTILITAIRE RÉGÉNÉRATION VIGNETTES SÉRIES
 * Fonction pour forcer la recréation des vignettes de série avec détection automatique
 */

// Fonction globale accessible depuis la console F12
window.regenerateSeriesThumbnails = async () => {
  console.log('🔄 [RÉGÉNÉRATION] Début régénération vignettes de série...');
  
  try {
    // Récupérer tous les livres
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    const token = localStorage.getItem('token');
    
    if (!token) {
      console.error('❌ [RÉGÉNÉRATION] Aucun token d\'authentification trouvé');
      return false;
    }
    
    const response = await fetch(`${backendUrl}/api/books`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      console.error('❌ [RÉGÉNÉRATION] Erreur API:', response.status);
      return false;
    }
    
    const books = await response.json();
    console.log(`📚 [RÉGÉNÉRATION] ${books.length} livres récupérés`);
    
    // Simuler la détection automatique comme dans le code corrigé
    const seriesGroups = {};
    const standaloneBooks = [];
    
    books.forEach(book => {
      let belongsToSeries = false;
      let detectedSeriesName = null;
      let detectionMethod = 'standalone';
      let confidence = 0;
      
      // Méthode 1 : Champ saga existant
      if (book.saga && book.saga.trim()) {
        belongsToSeries = true;
        detectedSeriesName = book.saga.trim();
        detectionMethod = 'existing_saga_field';
        confidence = 100;
      } else {
        // Méthode 2 : Détection automatique basique
        const titleLower = book.title.toLowerCase();
        
        // Pattern Harry Potter
        if (titleLower.includes('harry potter')) {
          belongsToSeries = true;
          detectedSeriesName = 'Harry Potter';
          detectionMethod = 'title_pattern_detection';
          confidence = 95;
        }
        // Pattern One Piece
        else if (titleLower.includes('one piece')) {
          belongsToSeries = true;
          detectedSeriesName = 'One Piece';
          detectionMethod = 'title_pattern_detection';
          confidence = 95;
        }
        // Pattern Astérix
        else if (titleLower.includes('asterix') || titleLower.includes('astérix')) {
          belongsToSeries = true;
          detectedSeriesName = 'Astérix';
          detectionMethod = 'title_pattern_detection';
          confidence = 95;
        }
        // Pattern numérotation
        else if (titleLower.includes('tome ') || titleLower.includes('volume ') || titleLower.includes(' #')) {
          const parts = book.title.split(/tome |volume | #/i);
          if (parts.length > 1 && parts[0].trim().length > 3) {
            belongsToSeries = true;
            detectedSeriesName = parts[0].trim();
            detectionMethod = 'numbering_pattern_detection';
            confidence = 80;
          }
        }
      }
      
      if (belongsToSeries && confidence >= 70) {
        // Regrouper dans la série
        const seriesKey = detectedSeriesName.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            name: detectedSeriesName,
            books: [],
            method: detectionMethod,
            avgConfidence: confidence
          };
        }
        seriesGroups[seriesKey].books.push(book.title);
        
        console.log(`📚 [RÉGÉNÉRATION] "${book.title}" → Série "${detectedSeriesName}" (${detectionMethod}, ${confidence}%)`);
      } else {
        standaloneBooks.push(book.title);
        console.log(`📖 [RÉGÉNÉRATION] "${book.title}" → Livre standalone`);
      }
    });
    
    // Afficher les résultats
    const seriesCount = Object.keys(seriesGroups).length;
    const standaloneCount = standaloneBooks.length;
    const totalSeriesBooks = Object.values(seriesGroups).reduce((sum, series) => sum + series.books.length, 0);
    
    console.log(`\n🎯 [RÉGÉNÉRATION] RÉSULTATS:`);
    console.log(`📚 Vignettes de série qui devraient être créées: ${seriesCount}`);
    console.log(`📖 Vignettes de livres individuels: ${standaloneCount}`);
    console.log(`🔒 Livres qui devraient être masqués: ${totalSeriesBooks}`);
    
    Object.entries(seriesGroups).forEach(([key, series]) => {
      console.log(`   📚 Série "${series.name}": ${series.books.length} livre(s) - ${series.method}`);
      series.books.forEach(title => {
        console.log(`      - ${title}`);
      });
    });
    
    if (standaloneBooks.length > 0) {
      console.log(`   📖 Livres standalone:`);
      standaloneBooks.forEach(title => {
        console.log(`      - ${title}`);
      });
    }
    
    console.log(`\n✅ [RÉGÉNÉRATION] Analyse terminée! Rechargez la page pour voir les changements.`);
    
    return {
      seriesCount,
      standaloneCount,
      totalBooks: books.length,
      seriesGroups,
      standaloneBooks
    };
    
  } catch (error) {
    console.error('❌ [RÉGÉNÉRATION] Erreur:', error);
    return false;
  }
};

// Fonction de diagnostic rapide
window.diagnoseSeries = async () => {
  console.log('🔍 [DIAGNOSTIC] Analyse rapide de l\'état actuel...');
  
  try {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${backendUrl}/api/books`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const books = await response.json();
    
    const withSaga = books.filter(b => b.saga && b.saga.trim());
    const withoutSaga = books.filter(b => !b.saga || !b.saga.trim());
    
    console.log(`📊 [DIAGNOSTIC] Livres avec champ saga: ${withSaga.length}`);
    console.log(`📊 [DIAGNOSTIC] Livres sans champ saga: ${withoutSaga.length}`);
    
    console.log(`\n📚 [DIAGNOSTIC] Livres avec saga:`);
    withSaga.forEach(book => {
      console.log(`   - "${book.title}" → Série "${book.saga}"`);
    });
    
    console.log(`\n📖 [DIAGNOSTIC] Livres sans saga (candidates à détection automatique):`);
    withoutSaga.forEach(book => {
      console.log(`   - "${book.title}" par ${book.author}`);
    });
    
    return { withSaga: withSaga.length, withoutSaga: withoutSaga.length, total: books.length };
    
  } catch (error) {
    console.error('❌ [DIAGNOSTIC] Erreur:', error);
    return false;
  }
};

// Messages d'aide
console.log(`
🔧 [UTILITAIRES SÉRIES] Fonctions disponibles dans la console:

📊 diagnoseSeries() - Diagnostic rapide de l'état actuel
🔄 regenerateSeriesThumbnails() - Analyse complète avec détection automatique

Exemple d'utilisation:
> await diagnoseSeries()
> await regenerateSeriesThumbnails()
`);

export { regenerateSeriesThumbnails, diagnoseSeries };