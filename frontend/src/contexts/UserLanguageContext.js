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
  const [language, setLanguage] = useState('français');

  useEffect(() => {
    // Charger la langue depuis localStorage
    const savedLanguage = localStorage.getItem('booktime-language');
    if (savedLanguage) {
      setLanguage(savedLanguage);
    }
  }, []);

  useEffect(() => {
    // Sauvegarder la langue
    localStorage.setItem('booktime-language', language);
  }, [language]);

  const changeLanguage = (newLanguage) => {
    setLanguage(newLanguage);
  };

  return (
    <UserLanguageContext.Provider value={{ language, changeLanguage }}>
      {children}
    </UserLanguageContext.Provider>
  );
};