/**
 * 🚀 SCRIPT DE DÉMONSTRATION - ANALYSE AUTOMATIQUE DES SÉRIES
 * 
 * Ce script permet de tester toutes les fonctionnalités d'analyse automatique
 * Ouvrez la console F12 et tapez: runSeriesAnalysisDemo()
 */

// 🎯 FONCTION PRINCIPALE DE DÉMONSTRATION
window.runSeriesAnalysisDemo = async function() {
  console.log('🚀 DÉMONSTRATION ANALYSE AUTOMATIQUE DES SÉRIES');
  console.log('=' .repeat(60));
  
  try {
    // 1. Vérifier l'authentification
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('❌ Vous devez être connecté pour utiliser cette démonstration');
      return;
    }
    
    console.log('✅ Utilisateur connecté');
    
    // 2. Analyser tous les livres
    console.log('\n🔍 ÉTAPE 1: ANALYSE COMPLÈTE DE LA BIBLIOTHÈQUE');
    console.log('-'.repeat(50));
    
    const analysisResult = await analyzeAllSeries({
      minConfidence: 120,
      delayBetweenRequests: 300,
      onProgress: (current, total, percentage) => {
        console.log(`📊 Progression: ${current}/${total} (${percentage.toFixed(1)}%)`);
      }
    });
    
    // 3. Générer rapport détaillé
    console.log('\n📊 ÉTAPE 2: GÉNÉRATION RAPPORT DÉTAILLÉ');
    console.log('-'.repeat(50));
    
    const reportResult = await generateSeriesReport();
    
    // 4. Proposer actions
    console.log('\n💡 ÉTAPE 3: ACTIONS PROPOSÉES');
    console.log('-'.repeat(50));
    
    if (analysisResult.seriesDetected > 0) {
      console.log(`✅ ${analysisResult.seriesDetected} séries détectées !`);
      console.log('💡 Actions disponibles:');
      console.log('   - updateDetectedSeries() : Mettre à jour automatiquement');
      console.log('   - updateDetectedSeries({confirmEach: true}) : Confirmer chaque série');
      console.log('   - updateDetectedSeries({minConfidence: 150}) : Seuil confiance élevé');
      
      // Proposer mise à jour automatique
      const autoUpdate = confirm(`Voulez-vous mettre à jour automatiquement les ${analysisResult.seriesDetected} séries détectées ?`);
      if (autoUpdate) {
        console.log('\n🔄 MISE À JOUR AUTOMATIQUE...');
        await updateDetectedSeries({
          minConfidence: 120,
          confirmEach: false
        });
      }
    } else {
      console.log('📖 Aucune série détectée. Tous vos livres sont déjà bien catégorisés !');
    }
    
    // 5. Résumé final
    console.log('\n🎉 DÉMONSTRATION TERMINÉE !');
    console.log('=' .repeat(60));
    console.log('📊 Résumé:');
    console.log(`   - Livres analysés: ${analysisResult.booksAnalyzed}`);
    console.log(`   - Séries détectées: ${analysisResult.seriesDetected}`);
    console.log(`   - Livres standalone: ${analysisResult.standaloneBooks}`);
    console.log(`   - Erreurs: ${analysisResult.errors}`);
    
    console.log('\n💡 Fonctionnalités disponibles:');
    console.log('   🔍 analyzeAllSeries() - Analyse complète');
    console.log('   🔄 updateDetectedSeries() - Mise à jour série');
    console.log('   📊 generateSeriesReport() - Rapport détaillé');
    console.log('   🎯 runSeriesAnalysisDemo() - Cette démonstration');
    
  } catch (error) {
    console.error('❌ Erreur démonstration:', error);
  }
};

// 🎯 FONCTION D'ANALYSE RAPIDE
window.quickSeriesAnalysis = async function() {
  console.log('⚡ ANALYSE RAPIDE DES SÉRIES');
  console.log('=' .repeat(40));
  
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('❌ Vous devez être connecté');
      return;
    }
    
    // Récupérer les livres
    const response = await fetch('/api/books?limit=100', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!response.ok) {
      throw new Error('Erreur récupération livres');
    }
    
    const data = await response.json();
    const books = data.items || [];
    
    console.log(`📚 ${books.length} livres dans la bibliothèque`);
    
    // Analyser rapidement
    const withSeries = books.filter(book => book.saga && book.saga.trim());
    const withoutSeries = books.filter(book => !book.saga || !book.saga.trim());
    
    console.log(`📖 Livres avec série: ${withSeries.length}`);
    console.log(`📘 Livres sans série: ${withoutSeries.length}`);
    
    // Grouper par série
    const seriesMap = new Map();
    withSeries.forEach(book => {
      if (!seriesMap.has(book.saga)) {
        seriesMap.set(book.saga, []);
      }
      seriesMap.get(book.saga).push(book);
    });
    
    console.log(`🎭 ${seriesMap.size} séries différentes:`);
    Array.from(seriesMap.entries())
      .sort(([,a], [,b]) => b.length - a.length)
      .slice(0, 10)
      .forEach(([seriesName, books]) => {
        console.log(`   - ${seriesName}: ${books.length} livres`);
      });
    
    if (withoutSeries.length > 0) {
      console.log(`\n🔍 ${withoutSeries.length} livres à analyser pour détecter des séries:`);
      withoutSeries.slice(0, 10).forEach(book => {
        console.log(`   - "${book.title}" par ${book.author}`);
      });
      
      if (withoutSeries.length > 10) {
        console.log(`   ... et ${withoutSeries.length - 10} autres`);
      }
      
      console.log('\n💡 Lancez analyzeAllSeries() pour analyser ces livres !');
    }
    
  } catch (error) {
    console.error('❌ Erreur analyse rapide:', error);
  }
};

// 🎯 FONCTION DE TEST DE DÉTECTION
window.testSeriesDetection = async function(bookTitle) {
  console.log(`🔍 TEST DÉTECTION SÉRIE POUR: "${bookTitle}"`);
  console.log('=' .repeat(50));
  
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('❌ Vous devez être connecté');
      return;
    }
    
    const query = encodeURIComponent(bookTitle);
    const response = await fetch(`/api/series/detect?q=${query}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!response.ok) {
      throw new Error('Erreur API détection');
    }
    
    const result = await response.json();
    
    console.log('📊 RÉSULTAT DÉTECTION:');
    console.log(`   ✅ Trouvé: ${result.found}`);
    console.log(`   📊 Confiance: ${result.confidence}`);
    
    if (result.found) {
      console.log(`   📚 Série: "${result.series_name}"`);
      console.log(`   🎯 Raisons: ${result.match_reasons.join(', ')}`);
      console.log(`   👤 Auteur: ${result.series_info.author}`);
      console.log(`   📖 Volumes: ${result.series_info.volumes}`);
      console.log(`   📂 Catégorie: ${result.series_info.category}`);
    } else {
      console.log('   📘 Livre standalone (pas de série détectée)');
    }
    
  } catch (error) {
    console.error('❌ Erreur test détection:', error);
  }
};

// 🎯 AIDE ET INSTRUCTIONS
window.showSeriesAnalysisHelp = function() {
  console.log('💡 AIDE - ANALYSE AUTOMATIQUE DES SÉRIES');
  console.log('=' .repeat(50));
  
  console.log('\n🚀 FONCTIONS PRINCIPALES:');
  console.log('   runSeriesAnalysisDemo() - Démonstration complète');
  console.log('   quickSeriesAnalysis() - Analyse rapide de la bibliothèque');
  console.log('   testSeriesDetection("titre du livre") - Test sur un livre');
  console.log('   showSeriesAnalysisHelp() - Cette aide');
  
  console.log('\n🔍 FONCTIONS D\'ANALYSE:');
  console.log('   analyzeAllSeries() - Analyse tous les livres sans série');
  console.log('   analyzeAllSeries({minConfidence: 150}) - Seuil confiance élevé');
  console.log('   analyzeAllSeries({delayBetweenRequests: 500}) - Délai personnalisé');
  
  console.log('\n🔄 FONCTIONS DE MISE À JOUR:');
  console.log('   updateDetectedSeries() - Met à jour automatiquement');
  console.log('   updateDetectedSeries({confirmEach: true}) - Confirmer chaque série');
  console.log('   updateDetectedSeries({minConfidence: 150}) - Seuil confiance');
  
  console.log('\n📊 FONCTIONS DE RAPPORT:');
  console.log('   generateSeriesReport() - Rapport complet exportable');
  
  console.log('\n🎯 EXEMPLES D\'UTILISATION:');
  console.log('   // Analyse complète avec rapport');
  console.log('   await runSeriesAnalysisDemo();');
  console.log('');
  console.log('   // Test sur un livre spécifique');
  console.log('   await testSeriesDetection("Harry Potter à l\'école des sorciers");');
  console.log('');
  console.log('   // Analyse avec seuil de confiance élevé');
  console.log('   await analyzeAllSeries({minConfidence: 150});');
  console.log('');
  console.log('   // Mise à jour avec confirmation');
  console.log('   await updateDetectedSeries({confirmEach: true});');
  
  console.log('\n📋 PARAMÈTRES DISPONIBLES:');
  console.log('   minConfidence: Seuil de confiance (défaut: 120)');
  console.log('   delayBetweenRequests: Délai entre requêtes ms (défaut: 200)');
  console.log('   confirmEach: Confirmer chaque série (défaut: false)');
  console.log('   onProgress: Callback de progression');
  
  console.log('\n💡 CONSEILS:');
  console.log('   - Commencez par quickSeriesAnalysis() pour un aperçu');
  console.log('   - Utilisez testSeriesDetection() pour tester un livre');
  console.log('   - Lancez runSeriesAnalysisDemo() pour tout automatiser');
  console.log('   - Augmentez minConfidence pour plus de précision');
  console.log('   - Utilisez confirmEach: true pour contrôler les mises à jour');
};

// 🎯 MESSAGE DE BIENVENUE
console.log('🔍 ANALYSEUR DE SÉRIES AUTOMATIQUE CHARGÉ !');
console.log('💡 Tapez showSeriesAnalysisHelp() pour voir l\'aide complète');
console.log('🚀 Tapez runSeriesAnalysisDemo() pour commencer !');

// Export des fonctions
window.seriesAnalysisFunctions = {
  runSeriesAnalysisDemo,
  quickSeriesAnalysis,
  testSeriesDetection,
  showSeriesAnalysisHelp
};