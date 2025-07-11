// 📊 GÉNÉRATEUR DE RAPPORTS DÉTAILLÉS
// Rapports avancés d'analyse des séries et statistiques

export class SeriesReportGenerator {
  constructor() {
    this.apiBase = process.env.REACT_APP_BACKEND_URL || '';
    this.token = localStorage.getItem('token');
  }

  // 📊 Génération de rapport complet
  async generateCompleteReport() {
    console.log('📊 GÉNÉRATION RAPPORT COMPLET DES SÉRIES');
    console.log('=' .repeat(60));

    try {
      const [books, stats, series] = await Promise.all([
        this.fetchAllBooks(),
        this.fetchStats(),
        this.fetchAllSeries()
      ]);

      const report = {
        metadata: {
          generatedAt: new Date().toISOString(),
          generatedBy: 'SeriesReportGenerator',
          version: '1.0.0'
        },
        overview: this.generateOverview(books, stats, series),
        seriesAnalysis: this.analyzeSeriesDistribution(books),
        completionAnalysis: this.analyzeCompletionStatus(books, series),
        authorAnalysis: this.analyzeAuthors(books),
        categoryAnalysis: this.analyzeCategories(books),
        trendsAnalysis: this.analyzeTrends(books),
        recommendations: this.generateRecommendations(books, series),
        detailedBreakdown: this.generateDetailedBreakdown(books, series)
      };

      this.displayCompleteReport(report);
      this.exportReport(report);

      return report;

    } catch (error) {
      console.error('❌ Erreur génération rapport:', error);
      throw error;
    }
  }

  // 📋 Vue d'ensemble
  generateOverview(books, stats, series) {
    const seriesBooks = books.filter(book => book.saga && book.saga.trim());
    const standaloneBooks = books.filter(book => !book.saga || !book.saga.trim());
    
    return {
      totalBooks: books.length,
      seriesBooks: seriesBooks.length,
      standaloneBooks: standaloneBooks.length,
      totalSeries: series.length,
      seriesPercentage: books.length > 0 ? ((seriesBooks.length / books.length) * 100).toFixed(1) : 0,
      categories: stats.categories || {},
      readingStatus: {
        completed: books.filter(book => book.status === 'completed').length,
        reading: books.filter(book => book.status === 'reading').length,
        toRead: books.filter(book => book.status === 'to_read').length
      }
    };
  }

  // 📚 Analyse distribution des séries
  analyzeSeriesDistribution(books) {
    const seriesMap = new Map();
    
    books.forEach(book => {
      if (book.saga && book.saga.trim()) {
        if (!seriesMap.has(book.saga)) {
          seriesMap.set(book.saga, {
            name: book.saga,
            books: [],
            author: book.author,
            category: book.category,
            totalBooks: 0,
            completedBooks: 0,
            readingBooks: 0,
            toReadBooks: 0,
            completionPercentage: 0
          });
        }
        
        const series = seriesMap.get(book.saga);
        series.books.push(book);
        series.totalBooks++;
        
        switch (book.status) {
          case 'completed':
            series.completedBooks++;
            break;
          case 'reading':
            series.readingBooks++;
            break;
          case 'to_read':
            series.toReadBooks++;
            break;
        }
        
        series.completionPercentage = series.totalBooks > 0 ? 
          ((series.completedBooks / series.totalBooks) * 100).toFixed(1) : 0;
      }
    });

    const seriesArray = Array.from(seriesMap.values());
    
    return {
      totalSeries: seriesArray.length,
      seriesData: seriesArray.sort((a, b) => b.totalBooks - a.totalBooks),
      averageBooksPerSeries: seriesArray.length > 0 ? 
        (seriesArray.reduce((sum, s) => sum + s.totalBooks, 0) / seriesArray.length).toFixed(1) : 0,
      largestSeries: seriesArray.length > 0 ? seriesArray[0] : null,
      completedSeries: seriesArray.filter(s => s.completionPercentage === 100),
      inProgressSeries: seriesArray.filter(s => s.completionPercentage > 0 && s.completionPercentage < 100),
      notStartedSeries: seriesArray.filter(s => s.completionPercentage === 0)
    };
  }

  // 🎯 Analyse statut de completion
  analyzeCompletionStatus(books, series) {
    const seriesBooks = books.filter(book => book.saga && book.saga.trim());
    
    return {
      totalSeriesBooks: seriesBooks.length,
      completedSeriesBooks: seriesBooks.filter(book => book.status === 'completed').length,
      readingSeriesBooks: seriesBooks.filter(book => book.status === 'reading').length,
      toReadSeriesBooks: seriesBooks.filter(book => book.status === 'to_read').length,
      completionRate: seriesBooks.length > 0 ? 
        ((seriesBooks.filter(book => book.status === 'completed').length / seriesBooks.length) * 100).toFixed(1) : 0,
      seriesStatus: {
        completed: series.filter(s => s.status === 'completed').length,
        reading: series.filter(s => s.status === 'reading').length,
        toRead: series.filter(s => s.status === 'to_read').length
      }
    };
  }

  // 👤 Analyse des auteurs
  analyzeAuthors(books) {
    const authorMap = new Map();
    
    books.forEach(book => {
      if (!authorMap.has(book.author)) {
        authorMap.set(book.author, {
          name: book.author,
          totalBooks: 0,
          series: new Set(),
          categories: new Set(),
          completedBooks: 0
        });
      }
      
      const author = authorMap.get(book.author);
      author.totalBooks++;
      author.categories.add(book.category);
      
      if (book.saga && book.saga.trim()) {
        author.series.add(book.saga);
      }
      
      if (book.status === 'completed') {
        author.completedBooks++;
      }
    });

    const authorsArray = Array.from(authorMap.values()).map(author => ({
      ...author,
      series: Array.from(author.series),
      categories: Array.from(author.categories),
      seriesCount: author.series.size,
      completionRate: author.totalBooks > 0 ? 
        ((author.completedBooks / author.totalBooks) * 100).toFixed(1) : 0
    }));

    return {
      totalAuthors: authorsArray.length,
      authorsData: authorsArray.sort((a, b) => b.totalBooks - a.totalBooks),
      mostProductiveAuthor: authorsArray.length > 0 ? authorsArray[0] : null,
      authorsWithSeries: authorsArray.filter(a => a.seriesCount > 0),
      averageBooksPerAuthor: authorsArray.length > 0 ? 
        (authorsArray.reduce((sum, a) => sum + a.totalBooks, 0) / authorsArray.length).toFixed(1) : 0
    };
  }

  // 📂 Analyse par catégorie
  analyzeCategories(books) {
    const categories = ['roman', 'bd', 'manga'];
    const categoryData = {};

    categories.forEach(category => {
      const categoryBooks = books.filter(book => book.category === category);
      const categorySeriesBooks = categoryBooks.filter(book => book.saga && book.saga.trim());
      
      categoryData[category] = {
        totalBooks: categoryBooks.length,
        seriesBooks: categorySeriesBooks.length,
        standaloneBooks: categoryBooks.length - categorySeriesBooks.length,
        seriesPercentage: categoryBooks.length > 0 ? 
          ((categorySeriesBooks.length / categoryBooks.length) * 100).toFixed(1) : 0,
        completed: categoryBooks.filter(book => book.status === 'completed').length,
        reading: categoryBooks.filter(book => book.status === 'reading').length,
        toRead: categoryBooks.filter(book => book.status === 'to_read').length,
        uniqueSeries: new Set(categorySeriesBooks.map(book => book.saga)).size
      };
    });

    return categoryData;
  }

  // 📈 Analyse des tendances
  analyzeTrends(books) {
    const booksWithDates = books.filter(book => book.date_added);
    const monthlyData = new Map();

    booksWithDates.forEach(book => {
      const date = new Date(book.date_added);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!monthlyData.has(monthKey)) {
        monthlyData.set(monthKey, {
          month: monthKey,
          totalBooks: 0,
          seriesBooks: 0,
          categories: { roman: 0, bd: 0, manga: 0 }
        });
      }
      
      const monthData = monthlyData.get(monthKey);
      monthData.totalBooks++;
      
      if (book.saga && book.saga.trim()) {
        monthData.seriesBooks++;
      }
      
      if (monthData.categories[book.category] !== undefined) {
        monthData.categories[book.category]++;
      }
    });

    return {
      monthlyData: Array.from(monthlyData.values()).sort((a, b) => a.month.localeCompare(b.month)),
      totalMonths: monthlyData.size,
      averageBooksPerMonth: monthlyData.size > 0 ? 
        (booksWithDates.length / monthlyData.size).toFixed(1) : 0
    };
  }

  // 💡 Génération de recommandations
  generateRecommendations(books, series) {
    const recommendations = [];
    
    // Séries incomplètes
    const incompleteSeries = series.filter(s => s.status !== 'completed');
    if (incompleteSeries.length > 0) {
      recommendations.push({
        type: 'incomplete_series',
        title: 'Séries à terminer',
        description: `Vous avez ${incompleteSeries.length} séries en cours`,
        items: incompleteSeries.slice(0, 5).map(s => s.name),
        priority: 'high'
      });
    }

    // Auteurs avec plusieurs séries
    const authorsMap = new Map();
    books.forEach(book => {
      if (book.saga && book.saga.trim()) {
        if (!authorsMap.has(book.author)) {
          authorsMap.set(book.author, new Set());
        }
        authorsMap.get(book.author).add(book.saga);
      }
    });

    const prolificAuthors = Array.from(authorsMap.entries())
      .filter(([author, series]) => series.size > 1)
      .map(([author, series]) => ({ author, seriesCount: series.size }));

    if (prolificAuthors.length > 0) {
      recommendations.push({
        type: 'prolific_authors',
        title: 'Auteurs prolifiques',
        description: 'Auteurs avec plusieurs séries dans votre bibliothèque',
        items: prolificAuthors.slice(0, 3).map(a => `${a.author} (${a.seriesCount} séries)`),
        priority: 'medium'
      });
    }

    // Catégories déséquilibrées
    const categoryStats = this.analyzeCategories(books);
    const totalBooks = books.length;
    const imbalancedCategories = Object.entries(categoryStats)
      .filter(([category, data]) => data.totalBooks / totalBooks < 0.2)
      .map(([category, data]) => ({ category, percentage: ((data.totalBooks / totalBooks) * 100).toFixed(1) }));

    if (imbalancedCategories.length > 0) {
      recommendations.push({
        type: 'category_balance',
        title: 'Diversification des catégories',
        description: 'Certaines catégories sont sous-représentées',
        items: imbalancedCategories.map(c => `${c.category}: ${c.percentage}%`),
        priority: 'low'
      });
    }

    return recommendations;
  }

  // 🔍 Détail complet
  generateDetailedBreakdown(books, series) {
    return {
      seriesDetails: series.map(s => ({
        name: s.name,
        totalBooks: s.books ? s.books.length : 0,
        completedBooks: s.books ? s.books.filter(b => b.status === 'completed').length : 0,
        author: s.author,
        category: s.category,
        status: s.status,
        progress: s.completion_percentage || 0
      })),
      standaloneBooks: books.filter(book => !book.saga || !book.saga.trim()).map(book => ({
        title: book.title,
        author: book.author,
        category: book.category,
        status: book.status,
        dateAdded: book.date_added
      }))
    };
  }

  // 📊 Affichage du rapport
  displayCompleteReport(report) {
    console.log('\n📊 RAPPORT COMPLET DES SÉRIES');
    console.log('=' .repeat(80));

    // Vue d'ensemble
    console.log('\n📋 VUE D\'ENSEMBLE:');
    console.log(`📚 Total livres: ${report.overview.totalBooks}`);
    console.log(`📖 Livres en série: ${report.overview.seriesBooks} (${report.overview.seriesPercentage}%)`);
    console.log(`📘 Livres standalone: ${report.overview.standaloneBooks}`);
    console.log(`🎭 Total séries: ${report.overview.totalSeries}`);

    // Statut de lecture
    console.log('\n📊 STATUT DE LECTURE:');
    console.log(`✅ Terminés: ${report.overview.readingStatus.completed}`);
    console.log(`📖 En cours: ${report.overview.readingStatus.reading}`);
    console.log(`📚 À lire: ${report.overview.readingStatus.toRead}`);

    // Top séries
    console.log('\n🏆 TOP SÉRIES (par nombre de livres):');
    report.seriesAnalysis.seriesData.slice(0, 10).forEach((series, index) => {
      console.log(`${index + 1}. ${series.name} (${series.totalBooks} livres, ${series.completionPercentage}% complété)`);
    });

    // Auteurs productifs
    console.log('\n👤 AUTEURS LES PLUS PRODUCTIFS:');
    report.authorAnalysis.authorsData.slice(0, 10).forEach((author, index) => {
      console.log(`${index + 1}. ${author.name} (${author.totalBooks} livres, ${author.seriesCount} séries)`);
    });

    // Catégories
    console.log('\n📂 RÉPARTITION PAR CATÉGORIE:');
    Object.entries(report.categoryAnalysis).forEach(([category, data]) => {
      console.log(`${category.toUpperCase()}: ${data.totalBooks} livres (${data.seriesPercentage}% en série)`);
    });

    // Recommandations
    if (report.recommendations.length > 0) {
      console.log('\n💡 RECOMMANDATIONS:');
      report.recommendations.forEach((rec, index) => {
        console.log(`${index + 1}. ${rec.title} (${rec.priority})`);
        console.log(`   ${rec.description}`);
        if (rec.items.length > 0) {
          rec.items.forEach(item => console.log(`   - ${item}`));
        }
        console.log('');
      });
    }

    console.log('\n🎉 Rapport terminé !');
  }

  // 💾 Export du rapport
  exportReport(report) {
    const reportText = JSON.stringify(report, null, 2);
    const blob = new Blob([reportText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `series-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('💾 Rapport exporté en JSON');
  }

  // 🔗 Méthodes utilitaires
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

  async fetchStats() {
    const response = await fetch(`${this.apiBase}/api/stats`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erreur récupération stats: ${response.status}`);
    }
    
    return await response.json();
  }

  async fetchAllSeries() {
    const response = await fetch(`${this.apiBase}/api/series/library`, {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erreur récupération séries: ${response.status}`);
    }
    
    const data = await response.json();
    return data.series || [];
  }
}

// 🌍 Export global
window.SeriesReportGenerator = SeriesReportGenerator;

// 🚀 Fonction utilitaire globale
window.generateSeriesReport = async () => {
  const generator = new SeriesReportGenerator();
  return await generator.generateCompleteReport();
};

console.log('📊 SeriesReportGenerator chargé !');
console.log('💡 Utilisez: generateSeriesReport() pour générer le rapport');

export default SeriesReportGenerator;