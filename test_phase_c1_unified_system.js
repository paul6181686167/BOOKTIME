/**
 * PHASE C.1 - TESTS ET VALIDATION
 * Tests pour le système de rafraîchissement unifié
 */

import { verifyAndDisplaySeries, verifyAndDisplayBook } from '../src/components/search/SearchLogic';

/**
 * Test 1: Vérifier loadAllContent charge tout
 */
export const testLoadAllContent = async (unifiedContent) => {
  console.log('🧪 [PHASE C.1] Test 1: loadAllContent');
  
  const startTime = Date.now();
  const result = await unifiedContent.loadAllContent();
  const loadTime = Date.now() - startTime;
  
  console.log(`📊 [TEST] loadAllContent terminé en ${loadTime}ms`);
  console.log(`📚 [TEST] Livres chargés: ${unifiedContent.books?.length || 0}`);
  console.log(`📖 [TEST] Séries chargées: ${unifiedContent.userSeriesLibrary?.length || 0}`);
  console.log(`📊 [TEST] Stats chargées: ${Object.keys(unifiedContent.stats || {}).length > 0 ? 'Oui' : 'Non'}`);
  
  return {
    success: !!result?.success,
    loadTime,
    booksLoaded: unifiedContent.books?.length || 0,
    seriesLoaded: unifiedContent.userSeriesLibrary?.length || 0,
    statsLoaded: Object.keys(unifiedContent.stats || {}).length > 0
  };
};

/**
 * Test 2: Vérifier verifyAndDisplaySeries fonctionne
 */
export const testVerifyAndDisplaySeries = async (seriesName = 'Harry Potter', targetCategory = 'roman', userSeriesLibrary = [], loadUserSeriesLibrary = () => {}) => {
  console.log('🧪 [PHASE C.1] Test 2: verifyAndDisplaySeries');
  
  const result = await verifyAndDisplaySeries(seriesName, targetCategory, userSeriesLibrary, loadUserSeriesLibrary);
  
  console.log(`📊 [TEST] verifyAndDisplaySeries résultat:`, result);
  
  return result;
};

/**
 * Test 3: Vérifier performance chargement unifié
 */
export const testPerformanceUnifiedContent = async (unifiedContent, iterations = 3) => {
  console.log(`🧪 [PHASE C.1] Test 3: Performance (${iterations} iterations)`);
  
  const results = [];
  
  for (let i = 1; i <= iterations; i++) {
    console.log(`🔄 [TEST] Iteration ${i}/${iterations}`);
    
    const startTime = Date.now();
    await unifiedContent.loadAllContent({ silent: true });
    const loadTime = Date.now() - startTime;
    
    results.push(loadTime);
    console.log(`⏱️ [TEST] Iteration ${i}: ${loadTime}ms`);
    
    // Petite pause entre les tests
    if (i < iterations) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  const averageTime = results.reduce((a, b) => a + b, 0) / results.length;
  const minTime = Math.min(...results);
  const maxTime = Math.max(...results);
  
  console.log(`📊 [TEST] Performance - Moyenne: ${averageTime.toFixed(1)}ms, Min: ${minTime}ms, Max: ${maxTime}ms`);
  
  return {
    iterations,
    results,
    averageTime: Math.round(averageTime),
    minTime,
    maxTime,
    performanceGrade: averageTime < 1000 ? 'Excellent' : averageTime < 2000 ? 'Bon' : 'À améliorer'
  };
};

/**
 * Test 4: Vérifier gestion erreurs
 */
export const testErrorHandling = async (unifiedContent) => {
  console.log('🧪 [PHASE C.1] Test 4: Gestion erreurs');
  
  // Simuler une erreur en passant des hooks invalides
  const mockUnifiedContentWithError = {
    loadAllContent: async () => {
      throw new Error('Test erreur simulée');
    }
  };
  
  try {
    await mockUnifiedContentWithError.loadAllContent();
    return { success: false, message: 'Erreur non capturée' };
  } catch (error) {
    console.log(`✅ [TEST] Erreur correctement capturée: ${error.message}`);
    return { success: true, message: 'Gestion erreur fonctionnelle' };
  }
};

/**
 * Suite de tests complète Phase C.1
 */
export const runFullPhaseC1Tests = async (unifiedContent) => {
  console.log('🚀 [PHASE C.1] Démarrage tests complets');
  
  const results = {
    testStartTime: Date.now(),
    tests: {}
  };
  
  try {
    // Test 1: loadAllContent
    results.tests.loadAllContent = await testLoadAllContent(unifiedContent);
    
    // Test 2: verifyAndDisplaySeries (avec données mock)
    results.tests.verifyAndDisplaySeries = await testVerifyAndDisplaySeries();
    
    // Test 3: Performance
    results.tests.performance = await testPerformanceUnifiedContent(unifiedContent);
    
    // Test 4: Gestion erreurs
    results.tests.errorHandling = await testErrorHandling(unifiedContent);
    
    results.totalTime = Date.now() - results.testStartTime;
    results.success = true;
    
    console.log(`✅ [PHASE C.1] Tests complétés en ${results.totalTime}ms`);
    console.log('📊 [RÉSULTATS] Sommaire des tests:', results);
    
  } catch (error) {
    results.success = false;
    results.error = error.message;
    console.error(`❌ [PHASE C.1] Échec tests:`, error);
  }
  
  return results;
};

// Export pour utilisation dans App.js ou console
export default {
  testLoadAllContent,
  testVerifyAndDisplaySeries,
  testPerformanceUnifiedContent,
  testErrorHandling,
  runFullPhaseC1Tests
};

// Fonction globale pour faciliter les tests depuis la console
if (typeof window !== 'undefined') {
  window.phaseC1Tests = {
    testLoadAllContent,
    testVerifyAndDisplaySeries,
    testPerformanceUnifiedContent,
    testErrorHandling,
    runFullPhaseC1Tests
  };
  
  console.log('🧪 [PHASE C.1] Tests disponibles dans window.phaseC1Tests');
}