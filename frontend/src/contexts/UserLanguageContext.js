import React, { createContext, useContext, useState, useEffect } from 'react';

const UserLanguageContext = createContext();

export const useUserLanguage = () => {
  const context = useContext(UserLanguageContext);
  if (!context) {
    throw new Error('useUserLanguage must be used within a UserLanguageProvider');
  }
  return context;
};

export const UserLanguageProvider = ({ children }) => {
  const [preferredLanguage, setPreferredLanguage] = useState('français');

  // Charger la langue préférée depuis localStorage au démarrage
  useEffect(() => {
    const savedLanguage = localStorage.getItem('booktime_preferred_language');
    if (savedLanguage) {
      setPreferredLanguage(savedLanguage);
    }
  }, []);

  // Sauvegarder la langue préférée dans localStorage quand elle change
  const updatePreferredLanguage = (language) => {
    setPreferredLanguage(language);
    localStorage.setItem('booktime_preferred_language', language);
  };

  // Fonction pour vérifier si un livre est disponible dans la langue préférée
  const isBookAvailableInPreferredLanguage = (book) => {
    if (!book) return false;
    
    // Si la langue originale correspond
    if (book.original_language === preferredLanguage) {
      return { available: true, type: 'original' };
    }
    
    // Si une traduction est disponible
    if (book.available_translations && book.available_translations.includes(preferredLanguage)) {
      return { available: true, type: 'translation' };
    }
    
    // Si l'utilisateur lit déjà dans cette langue
    if (book.reading_language === preferredLanguage) {
      return { available: true, type: 'reading' };
    }
    
    return { available: false, type: 'unavailable' };
  };

  // Fonction pour obtenir le statut linguistique d'un livre
  const getBookLanguageStatus = (book) => {
    const availability = isBookAvailableInPreferredLanguage(book);
    
    return {
      ...availability,
      original_language: book.original_language || 'français',
      reading_language: book.reading_language || 'français',
      available_translations: book.available_translations || [],
      preferred_language: preferredLanguage
    };
  };

  const value = {
    preferredLanguage,
    updatePreferredLanguage,
    isBookAvailableInPreferredLanguage,
    getBookLanguageStatus
  };

  return (
    <UserLanguageContext.Provider value={value}>
      {children}
    </UserLanguageContext.Provider>
  );
};