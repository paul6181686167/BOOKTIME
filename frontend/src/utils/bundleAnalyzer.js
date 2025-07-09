// Phase 2.3 - Analyseur de bundle pour optimiser la taille
import { useState, useEffect } from 'react';

/**
 * Utilitaire pour analyser et optimiser le bundle
 */
export class BundleAnalyzer {
  constructor() {
    this.performanceData = {
      loadTime: 0,
      domContentLoaded: 0,
      firstPaint: 0,
      firstContentfulPaint: 0,
      bundleSize: 0,
      componentCount: 0,
      renderCount: 0
    };
  }

  // Mesurer les performances de chargement
  measureLoadPerformance() {
    if (typeof window !== 'undefined' && 'performance' in window) {
      const navigation = performance.getEntriesByType('navigation')[0];
      const paint = performance.getEntriesByType('paint');
      
      this.performanceData.loadTime = navigation.loadEventEnd - navigation.loadEventStart;
      this.performanceData.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
      
      paint.forEach(entry => {
        if (entry.name === 'first-paint') {
          this.performanceData.firstPaint = entry.startTime;
        } else if (entry.name === 'first-contentful-paint') {
          this.performanceData.firstContentfulPaint = entry.startTime;
        }
      });
    }
  }

  // Analyser la taille du bundle
  analyzeBundleSize() {
    if (typeof window !== 'undefined') {
      const scripts = document.querySelectorAll('script[src]');
      let totalSize = 0;
      
      scripts.forEach(script => {
        // Estimation approximative basée sur les ressources
        if (script.src.includes('static/js/')) {
          totalSize += this.estimateScriptSize(script.src);
        }
      });
      
      this.performanceData.bundleSize = totalSize;
    }
  }

  // Estimer la taille d'un script (approximatif)
  estimateScriptSize(src) {
    // Estimation basée sur des patterns courants
    if (src.includes('main.')) return 200000; // ~200KB pour le bundle principal
    if (src.includes('vendor.')) return 500000; // ~500KB pour les vendors
    if (src.includes('chunk.')) return 50000; // ~50KB pour les chunks
    return 10000; // ~10KB par défaut
  }

  // Obtenir les recommandations d'optimisation
  getOptimizationRecommendations() {
    const recommendations = [];
    
    if (this.performanceData.firstContentfulPaint > 2000) {
      recommendations.push({
        type: 'performance',
        severity: 'high',
        message: 'First Contentful Paint trop lent (>2s)',
        solution: 'Implémenter le lazy loading et code splitting'
      });
    }
    
    if (this.performanceData.bundleSize > 1000000) {
      recommendations.push({
        type: 'bundle',
        severity: 'medium',
        message: 'Bundle trop volumineux (>1MB)',
        solution: 'Séparer les vendors et utiliser des chunks dynamiques'
      });
    }
    
    if (this.performanceData.renderCount > 100) {
      recommendations.push({
        type: 'react',
        severity: 'medium',
        message: 'Trop de re-rendus détectés',
        solution: 'Utiliser React.memo et useCallback'
      });
    }
    
    return recommendations;
  }

  // Générer un rapport complet
  generateReport() {
    this.measureLoadPerformance();
    this.analyzeBundleSize();
    
    return {
      performance: this.performanceData,
      recommendations: this.getOptimizationRecommendations(),
      score: this.calculatePerformanceScore(),
      timestamp: new Date().toISOString()
    };
  }

  // Calculer un score de performance
  calculatePerformanceScore() {
    let score = 100;
    
    // Pénalités basées sur les métriques
    if (this.performanceData.firstContentfulPaint > 1000) score -= 20;
    if (this.performanceData.firstContentfulPaint > 2000) score -= 30;
    if (this.performanceData.bundleSize > 500000) score -= 15;
    if (this.performanceData.bundleSize > 1000000) score -= 25;
    if (this.performanceData.loadTime > 3000) score -= 10;
    
    return Math.max(0, Math.min(100, score));
  }
}

/**
 * Hook pour utiliser l'analyseur de bundle
 */
export const useBundleAnalyzer = () => {
  const [analyzer] = useState(() => new BundleAnalyzer());
  const [report, setReport] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    
    // Attendre que la page soit complètement chargée
    await new Promise(resolve => {
      if (document.readyState === 'complete') {
        resolve();
      } else {
        window.addEventListener('load', resolve);
      }
    });
    
    const newReport = analyzer.generateReport();
    setReport(newReport);
    setIsAnalyzing(false);
  };

  useEffect(() => {
    // Lancer l'analyse après le montage du composant
    const timer = setTimeout(runAnalysis, 1000);
    return () => clearTimeout(timer);
  }, []);

  return {
    report,
    isAnalyzing,
    runAnalysis,
    analyzer
  };
};

/**
 * Composant pour afficher l'analyse du bundle (développement uniquement)
 */
export const BundleAnalyzerComponent = () => {
  const { report, isAnalyzing, runAnalysis } = useBundleAnalyzer();

  // Afficher seulement en développement
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  if (isAnalyzing) {
    return (
      <div className="fixed bottom-4 right-4 bg-blue-500 text-white p-3 rounded-lg shadow-lg">
        <div className="flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
          <span className="text-sm">Analyse en cours...</span>
        </div>
      </div>
    );
  }

  if (!report) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 max-w-sm">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-gray-900 dark:text-white">
          Performance Score: {report.score}
        </h3>
        <button
          onClick={runAnalysis}
          className="text-blue-500 hover:text-blue-600 text-sm"
        >
          Actualiser
        </button>
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">FCP:</span>
          <span className={report.performance.firstContentfulPaint > 2000 ? 'text-red-500' : 'text-green-500'}>
            {report.performance.firstContentfulPaint.toFixed(0)}ms
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Bundle:</span>
          <span className={report.performance.bundleSize > 1000000 ? 'text-red-500' : 'text-green-500'}>
            {(report.performance.bundleSize / 1000).toFixed(0)}KB
          </span>
        </div>
        
        {report.recommendations.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
            <p className="text-gray-600 dark:text-gray-400 mb-1">
              Recommandations ({report.recommendations.length})
            </p>
            {report.recommendations.slice(0, 2).map((rec, index) => (
              <div key={index} className="text-xs text-gray-500 dark:text-gray-500">
                • {rec.message}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BundleAnalyzer;