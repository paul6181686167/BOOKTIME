/**
 * 🎯 GUIDE TESTS RAPIDES - SYSTÈME UNIFIÉ BOOKTIME
 * Session 85.4 - Tests de validation pour développeurs
 */

console.log('🚀 BOOKTIME - Guide Tests Rapides chargé');

// ============================================================================
// 🧪 TESTS CONSOLE DISPONIBLES
// ============================================================================

if (typeof window !== 'undefined') {
  
  // Tests Phase C.1 (disponibles si importés)
  if (window.phaseC1Tests) {
    console.log('✅ Phase C.1 Tests disponibles dans window.phaseC1Tests');
    console.log('   - testLoadAllContent()');
    console.log('   - testVerifyAndDisplaySeries()');
    console.log('   - testPerformanceUnifiedContent()');
    console.log('   - runFullPhaseC1Tests()');
  }
  
  // Tests Phase C.3 (disponibles si importés)
  if (window.phaseC3Tests) {
    console.log('✅ Phase C.3 Tests disponibles dans window.phaseC3Tests');
    console.log('   - testEndToEndWorkflow()');
    console.log('   - testAdvancedPerformance()');
    console.log('   - testStressAndEdgeCases()');
    console.log('   - runCompletePhaseC3Tests()');
  }
  
  // Tests Phase D (disponibles si importés)
  if (window.phaseDTests) {
    console.log('✅ Phase D Tests disponibles dans window.phaseDTests');
    console.log('   - scenario1() à scenario5()');
    console.log('   - performance()');
    console.log('   - runComplete()');
  }

  // ============================================================================
  // 🔧 FONCTIONS UTILITAIRES RAPIDES
  // ============================================================================

  window.quickTests = {
    
    // Test sanité basique
    healthCheck: async () => {
      console.log('🏥 [QUICK TEST] Health Check');
      try {
        const response = await fetch('/health');
        const data = await response.json();
        console.log('✅ Backend:', data);
        return data.status === 'ok';
      } catch (error) {
        console.error('❌ Backend inaccessible:', error);
        return false;
      }
    },

    // Test authentification
    testAuth: () => {
      console.log('🔐 [QUICK TEST] Authentification');
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      
      if (token && user) {
        console.log('✅ Utilisateur connecté:', JSON.parse(user));
        return true;
      } else {
        console.log('❌ Aucun utilisateur connecté');
        return false;
      }
    },

    // Test données chargées
    testDataLoaded: () => {
      console.log('📚 [QUICK TEST] Données chargées');
      
      // Vérifier si on a accès au state global de l'app
      const hasBooks = window.appState?.books?.length > 0;
      const hasSeries = window.appState?.userSeriesLibrary?.length > 0;
      const hasStats = window.appState?.stats && Object.keys(window.appState.stats).length > 0;
      
      console.log(`📖 Livres: ${hasBooks ? '✅' : '❌'} (${window.appState?.books?.length || 0})`);
      console.log(`📚 Séries: ${hasSeries ? '✅' : '❌'} (${window.appState?.userSeriesLibrary?.length || 0})`);
      console.log(`📊 Stats: ${hasStats ? '✅' : '❌'}`);
      
      return hasBooks || hasSeries || hasStats;
    },

    // Test système unifié
    testUnifiedSystem: async () => {
      console.log('🔄 [QUICK TEST] Système Unifié');
      
      // Simuler un chargement unifié si hook disponible
      if (window.unifiedContentHook && typeof window.unifiedContentHook.loadAllContent === 'function') {
        try {
          const startTime = Date.now();
          const result = await window.unifiedContentHook.loadAllContent({ silent: true });
          const loadTime = Date.now() - startTime;
          
          console.log(`✅ Chargement unifié: ${loadTime}ms`);
          console.log('📊 Résultat:', result);
          return true;
        } catch (error) {
          console.error('❌ Échec chargement unifié:', error);
          return false;
        }
      } else {
        console.log('⚠️ Hook unifié non disponible');
        return false;
      }
    },

    // Test masquage intelligent
    testIntelligentMasking: () => {
      console.log('🎭 [QUICK TEST] Masquage Intelligent');
      
      // Test détection série si SeriesDetector disponible
      if (window.SeriesDetector) {
        const testBooks = [
          { title: 'Harry Potter à l\'école des sorciers', author: 'J.K. Rowling' },
          { title: 'Dune', author: 'Frank Herbert' },
          { title: 'One Piece - Romance Dawn', author: 'Eiichiro Oda' }
        ];
        
        testBooks.forEach(book => {
          const detection = window.SeriesDetector.detectBookSeries(book);
          console.log(`📘 "${book.title}": ${detection.belongsToSeries ? '🎭 Masqué' : '👁️ Visible'} (${detection.confidence}%)`);
        });
        
        return true;
      } else {
        console.log('⚠️ SeriesDetector non disponible');
        return false;
      }
    },

    // Suite de tests rapides complète
    runQuickValidation: async () => {
      console.log('🚀 [QUICK VALIDATION] Suite de tests rapides');
      
      const results = {
        startTime: Date.now(),
        tests: {}
      };
      
      results.tests.healthCheck = await window.quickTests.healthCheck();
      results.tests.auth = window.quickTests.testAuth();
      results.tests.dataLoaded = window.quickTests.testDataLoaded();
      results.tests.unifiedSystem = await window.quickTests.testUnifiedSystem();
      results.tests.intelligentMasking = window.quickTests.testIntelligentMasking();
      
      results.totalTime = Date.now() - results.startTime;
      results.successCount = Object.values(results.tests).filter(Boolean).length;
      results.totalTests = Object.keys(results.tests).length;
      results.successRate = Math.round((results.successCount / results.totalTests) * 100);
      
      console.log(`🏁 [VALIDATION] ${results.successCount}/${results.totalTests} tests réussis (${results.successRate}%) en ${results.totalTime}ms`);
      
      if (results.successRate >= 80) {
        console.log('✅ [VALIDATION] Système fonctionnel');
      } else {
        console.log('⚠️ [VALIDATION] Problèmes détectés');
      }
      
      return results;
    }
  };

  // ============================================================================
  // 📋 COMMANDES UTILES
  // ============================================================================

  console.log('\n📋 COMMANDES DISPONIBLES:');
  console.log('🔧 window.quickTests.runQuickValidation() - Validation rapide complète');
  console.log('🏥 window.quickTests.healthCheck() - Test sanité backend');
  console.log('🔐 window.quickTests.testAuth() - Vérifier authentification');
  console.log('📚 window.quickTests.testDataLoaded() - Vérifier données chargées');
  console.log('🔄 window.quickTests.testUnifiedSystem() - Test système unifié');
  console.log('🎭 window.quickTests.testIntelligentMasking() - Test masquage intelligent');
  
  console.log('\n🧪 TESTS AVANCÉS (si disponibles):');
  console.log('📖 window.phaseC1Tests.runFullPhaseC1Tests() - Tests Phase C.1');
  console.log('⚡ window.phaseC3Tests.runCompletePhaseC3Tests() - Tests Phase C.3');
  console.log('🏆 window.phaseDTests.runComplete() - Tests Phase D finaux');
  
  console.log('\n💡 USAGE RAPIDE:');
  console.log('await window.quickTests.runQuickValidation()');

} else {
  console.log('⚠️ Environment non-browser détecté');
}

// ============================================================================
// 🎯 EXPORT POUR UTILISATION EXTERNE
// ============================================================================

export const quickValidationGuide = {
  description: 'Guide tests rapides BOOKTIME Session 85.4',
  commands: [
    'window.quickTests.runQuickValidation()',
    'window.phaseC1Tests?.runFullPhaseC1Tests()',
    'window.phaseC3Tests?.runCompletePhaseC3Tests()',
    'window.phaseDTests?.runComplete()'
  ],
  documentation: '/app/RAPPORT_FINAL_SYSTEME_UNIFIE.md'
};

export default quickValidationGuide;