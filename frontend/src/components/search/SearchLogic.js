/**
 * SEARCH LOGIC - Module de logique de recherche pour BOOKTIME
 * 
 * Fonctionnalités :
 * - Recherche globale Open Library
 * - Détection automatique de propriété des livres
 * - Génération de badges catégorie automatiques
 * - Tri intelligent des résultats avec priorité séries
 * - Gestion ajout depuis Open Library avec placement intelligent
 * 
 * Extrait d'App.js dans le cadre de la Phase 1.1 - Frontend Modularisation
 */

import { toast } from 'react-hot-toast';
import SearchOptimizer from '../../utils/searchOptimizer';

// FONCTION PRINCIPALE DE RECHERCHE OPEN LIBRARY
export const searchOpenLibrary = async (query, {
  books, 
  setSearchLoading, 
  setIsSearchMode, 
  setLastSearchTerm, 
  setOpenLibraryResults,
  generateSeriesCardsForSearch,
  handleAddSeriesToLibrary,
  getCategoryBadgeFromBook
}) => {
  console.log('🚀 searchOpenLibrary GLOBALE appelée avec:', query);
  if (!query.trim()) {
    console.log('❌ Recherche annulée: query vide');
    return;
  }
  
  try {
    console.log('✅ Début de la recherche globale Open Library (toutes catégories)');
    setSearchLoading(true);
    setIsSearchMode(true);
    setLastSearchTerm(query);
    
    const token = localStorage.getItem('token');
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    
    // RECHERCHE GLOBALE : pas de filtre par catégorie, recherche dans TOUTES les catégories
    const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=40`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();
      
      // Générer automatiquement les cartes séries basées sur le terme de recherche
      const seriesCards = generateSeriesCardsForSearch(query, data.books).map(card => ({
        ...card,
        onAddToLibrary: handleAddSeriesToLibrary // Ajouter la callback pour le bouton
      }));
      
      // AJOUT DES BADGES CATÉGORIE : Marquer les livres avec leur catégorie et badge
      const resultsWithOwnership = data.books.map(book => {
        const isOwned = detectBookOwnership(book, books);
        
        // BADGES CATÉGORIE AUTOMATIQUES : Ajouter badge selon la catégorie détectée
        const categoryBadge = getCategoryBadgeFromBook(book);
        
        return {
          ...book,
          isFromOpenLibrary: true,
          isOwned: isOwned,
          id: `ol_${book.ol_key}`,
          // Badge catégorie pour affichage visuel
          categoryBadge: categoryBadge,
          // S'assurer que la catégorie est bien définie pour le placement intelligent
          category: book.category || categoryBadge.key || 'roman' // Défaut roman si non détecté
        };
      });
      
      // ALGORITHME DE TRI PRIORITAIRE OPTIMISÉ : Garantir fiches séries EN PREMIER avec scores 100000+
      const allResults = [...seriesCards, ...resultsWithOwnership];
      
      // TRI FINAL AVEC PRIORITÉ ABSOLUE DES SÉRIES selon les consignes du CHANGELOG
      // 1) Séries officielles (100000+) par pertinence
      // 2) Séries bibliothèque (90000+) par pertinence  
      // 3) Livres Open Library très pertinents (scores variables)
      // 4) Livres bibliothèque utilisateur (scores variables)
      const sortedResults = SearchOptimizer.applySuperiorSeriesPrioritySort(allResults);
      
      console.log('🎯 PRIORITÉ SÉRIES - Tri final appliqué:');
      sortedResults.slice(0, 5).forEach((item, index) => {
        console.log(`${index + 1}. ${item.isSeriesCard ? '📚 SÉRIE' : '📖 LIVRE'}: ${item.title || item.name} - Score: ${item.relevanceScore || item.confidence || 0}`);
      });
      
      // Stocker les résultats triés avec priorité absolue aux fiches séries
      setOpenLibraryResults(sortedResults);
      toast.success(`${data.books.length} livres trouvés${seriesCards.length > 0 ? ` + ${seriesCards.length} série(s) détectée(s) EN PREMIER` : ''}`);
    } else {
      toast.error('Erreur lors de la recherche Open Library');
    }
  } catch (error) {
    console.error('Erreur recherche Open Library:', error);
    toast.error('Erreur lors de la recherche Open Library');
  } finally {
    setSearchLoading(false);
  }
};

// DÉTECTION DE PROPRIÉTÉ D'UN LIVRE
const detectBookOwnership = (book, books) => {
  return books.some(localBook => {
    // Normaliser les titres et auteurs pour la comparaison
    const normalizeString = (str) => {
      if (!str) return '';
      return str.toLowerCase()
        .trim()
        .replace(/[^\w\s]/g, '') // Supprimer la ponctuation
        .replace(/\s+/g, ' '); // Normaliser les espaces
    };
    
    const localTitle = normalizeString(localBook.title);
    const localAuthor = normalizeString(localBook.author);
    const openLibTitle = normalizeString(book.title);
    const openLibAuthor = normalizeString(book.author);
    
    // Vérification par ol_key d'abord (plus précise)
    if (localBook.ol_key && book.ol_key && localBook.ol_key === book.ol_key) {
      return true;
    }
    
    // Vérification par ISBN si disponible
    if (localBook.isbn && book.isbn && 
        localBook.isbn.replace(/[-\s]/g, '') === book.isbn.replace(/[-\s]/g, '')) {
      return true;
    }
    
    // Vérification par titre et auteur (comparaison exacte)
    if (localTitle === openLibTitle && localAuthor === openLibAuthor) {
      return true;
    }
    
    // Vérification par titre et auteur (comparaison flexible)
    // Le titre de Open Library doit contenir le titre local OU vice versa
    const titleMatch = (localTitle.includes(openLibTitle) || openLibTitle.includes(localTitle)) && 
                      (localTitle.length > 3 && openLibTitle.length > 3); // Éviter les correspondances trop courtes
    
    // L'auteur doit correspondre exactement ou l'un doit contenir l'autre
    const authorMatch = localAuthor === openLibAuthor || 
                       (localAuthor.includes(openLibAuthor) && openLibAuthor.length > 3) ||
                       (openLibAuthor.includes(localAuthor) && localAuthor.length > 3);
    
    return titleMatch && authorMatch;
  });
};

// AJOUT INTELLIGENT : Placement automatique dans le bon onglet selon la catégorie
export const handleAddFromOpenLibrary = async (openLibraryBook, {
  books,
  addingBooks,
  setAddingBooks,
  activeTab,
  getCategoryBadgeFromBook,
  loadBooks,
  loadStats,
  setOpenLibraryResults
}) => {
  // Empêcher les clics multiples sur le même livre
  if (addingBooks.has(openLibraryBook.ol_key)) {
    return; // Si le livre est déjà en cours d'ajout, ne rien faire
  }

  try {
    // Marquer le livre comme en cours d'ajout
    setAddingBooks(prev => new Set([...prev, openLibraryBook.ol_key]));
    
    const token = localStorage.getItem('token');
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    
    // PLACEMENT INTELLIGENT : Déterminer la catégorie automatiquement via le badge
    const categoryBadge = openLibraryBook.categoryBadge || getCategoryBadgeFromBook(openLibraryBook);
    let targetCategory = categoryBadge.key; // Utiliser la catégorie détectée par le badge
    
    // Validation : s'assurer que la catégorie est valide
    if (!targetCategory || !['roman', 'bd', 'manga'].includes(targetCategory)) {
      // Si pas de catégorie ou catégorie invalide, utiliser l'onglet actuel par défaut
      targetCategory = activeTab;
    }
    
    const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ol_key: openLibraryBook.ol_key,
        category: targetCategory
      })
    });

    if (response.ok) {
      // 🔍 DIAGNOSTIC : Vérifier token avant loadBooks
      const currentToken = localStorage.getItem('token');
      console.log('🔐 PRE-LOADBOOKS TOKEN CHECK:', {
        hasToken: !!currentToken,
        tokenLength: currentToken?.length || 0,
        tokenPreview: currentToken?.substring(0, 30) + '...',
        timestamp: new Date().toISOString()
      });
      
      console.log('🔄 Starting loadBooks after successful book addition...');
      await loadBooks();
      
      console.log('🔄 Starting loadStats after successful book addition...');
      await loadStats();
      
      console.log('✅ loadBooks and loadStats completed successfully');
      
      // CORRECTION RCA : Retour automatique vers bibliothèque après ajout réussi
      // Solution au problème de synchronisation ajout/affichage
      setTimeout(() => {
        // Déclencher l'événement de retour à la bibliothèque
        const backToLibraryEvent = new CustomEvent('backToLibrary', {
          detail: { 
            reason: 'book_added_successfully',
            targetCategory: targetCategory,
            bookTitle: openLibraryBook.title
          }
        });
        window.dispatchEvent(backToLibraryEvent);
      }, 500); // Délai réduit pour une meilleure expérience utilisateur
      
      // Message de succès avec indication de l'onglet ET retour automatique
      const categoryLabels = {
        'roman': 'Roman',
        'bd': 'BD',
        'manga': 'Manga'
      };
      toast.success(`"${openLibraryBook.title}" ajouté à l'onglet ${categoryLabels[targetCategory]} ! 📚\nRetour automatique vers votre bibliothèque...`, {
        duration: 2000
      });
      
      // Mettre à jour le statut de possession dans les résultats
      setOpenLibraryResults(prev => 
        prev.map(book => 
          book.ol_key === openLibraryBook.ol_key 
            ? { ...book, isOwned: true }
            : book
        )
      );
    } else {
      const error = await response.json();
      if (response.status === 409) {
        toast.error('Ce livre est déjà dans votre collection');
        // Marquer le livre comme possédé même si l'ajout a échoué pour cause de doublon
        setOpenLibraryResults(prev => 
          prev.map(book => 
            book.ol_key === openLibraryBook.ol_key 
              ? { ...book, isOwned: true }
              : book
          )
        );
      } else {
        toast.error(error.detail || 'Erreur lors de l\'ajout du livre');
      }
    }
  } catch (error) {
    console.error('Erreur ajout livre:', error);
    toast.error('Erreur lors de l\'ajout du livre');
  } finally {
    // Retirer le livre de la liste des livres en cours d'ajout
    setAddingBooks(prev => {
      const newSet = new Set(prev);
      newSet.delete(openLibraryBook.ol_key);
      return newSet;
    });
  }
};

// NAVIGATION ET UTILITAIRES DE RECHERCHE

// Fonction pour revenir à la bibliothèque locale
export const backToLibrary = (setIsSearchMode, setOpenLibraryResults, setLastSearchTerm, clearSearch) => {
  setIsSearchMode(false);
  setOpenLibraryResults([]);
  setLastSearchTerm('');
  clearSearch();
};

// Gestionnaires de clics sur éléments

// Gestionnaire de clic sur série pour afficher la fiche dédiée
export const handleSeriesClick = (series, setSelectedSeries, setShowSeriesModal) => {
  if (series.isLibrarySeries) {
    // Série de bibliothèque : créer une fiche dédiée locale
    // Pour l'instant, on peut montrer une modal avec les livres de la série
    setSelectedSeries(series);
    setShowSeriesModal(true);
  } else {
    // Série Open Library : naviguer vers la page dédiée
    const navigate = window.location.pathname !== '/' ? 
      (path) => window.location.href = path : 
      (path) => window.history.pushState({}, '', path);
    navigate(`/series/${encodeURIComponent(series.name)}`);
  }
};

// Gestionnaire de clic sur livre
export const handleBookClick = (book, setSelectedBook, setShowBookModal) => {
  setSelectedBook(book);
  setShowBookModal(true);
};

// Gestionnaire de clic conditionnel (livre ou série)
export const handleItemClick = (item, setSelectedSeries, setShowSeriesModal, setSelectedBook, setShowBookModal) => {
  if (item.isSeriesCard) {
    handleSeriesClick(item, setSelectedSeries, setShowSeriesModal);
  } else {
    handleBookClick(item, setSelectedBook, setShowBookModal);
  }
};

export default {
  searchOpenLibrary,
  handleAddFromOpenLibrary,
  backToLibrary,
  handleSeriesClick,
  handleBookClick,
  handleItemClick
};