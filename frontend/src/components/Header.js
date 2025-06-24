import React, { useState } from 'react';
import { 
  MagnifyingGlassIcon, 
  PlusIcon, 
  SunIcon, 
  MoonIcon,
  UserGroupIcon,
  BookOpenIcon,
  LanguageIcon,
  ArrowLeftIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import { useUserLanguage } from '../contexts/UserLanguageContext';
import LanguageSelector from './LanguageSelector';
import { getLanguageByCode } from '../constants/languages';

const Header = ({ 
  searchTerm, 
  onSearchChange, 
  onAddBook, 
  onOpenLibrarySearch,
  viewMode, 
  onViewModeChange, 
  currentContext, 
  onBackToAll 
}) => {
  const { theme, toggleTheme } = useTheme();
  const { preferredLanguage, updatePreferredLanguage } = useUserLanguage();
  const [showLanguageSelector, setShowLanguageSelector] = useState(false);

  const viewModes = [
    { value: 'books', label: 'Livres', icon: BookOpenIcon },
    { value: 'authors', label: 'Auteurs', icon: UserGroupIcon },
    { value: 'sagas', label: 'Sagas', icon: BookOpenIcon },
  ];

  const handleLanguageChange = (languages) => {
    if (languages.length > 0) {
      updatePreferredLanguage(languages[0]);
      setShowLanguageSelector(false);
    }
  };

  const preferredLangInfo = getLanguageByCode(preferredLanguage);

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo et titre */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-booktime-600 dark:text-booktime-400">
                📚 BOOKTIME
              </h1>
            </div>
            
            {/* Contexte actuel */}
            {currentContext && (
              <div className="flex items-center space-x-2">
                <ArrowLeftIcon className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {currentContext.type === 'author' ? 'Auteur' : 'Saga'}: {currentContext.name}
                </span>
              </div>
            )}
          </div>

          {/* Barre de recherche */}
          <div className="flex-1 max-w-lg mx-8">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 sm:text-sm transition-colors"
                placeholder="Rechercher un livre, un auteur..."
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-4">
            {/* Sélecteur de langue préférée */}
            <div className="relative">
              <button
                onClick={() => setShowLanguageSelector(!showLanguageSelector)}
                className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                title={`Langue préférée: ${preferredLangInfo.name}`}
              >
                <LanguageIcon className="h-4 w-4" />
                <span className="hidden sm:inline">{preferredLangInfo.flag}</span>
                <span className="hidden md:inline">{preferredLangInfo.name}</span>
              </button>

              {showLanguageSelector && (
                <div className="absolute right-0 mt-2 w-64 z-50">
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                      Ma langue préférée
                    </h3>
                    <LanguageSelector
                      selectedLanguages={[preferredLanguage]}
                      onLanguagesChange={handleLanguageChange}
                      single={true}
                      placeholder="Choisir ma langue préférée"
                    />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Affiche les indicateurs de traduction selon votre langue
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Navigation des vues */}
            <div className="hidden sm:flex items-center space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
              {viewModes.map((mode) => {
                const Icon = mode.icon;
                return (
                  <button
                    key={mode.value}
                    onClick={() => onViewModeChange(mode.value)}
                    className={`flex items-center space-x-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      viewMode === mode.value
                        ? 'bg-white dark:bg-gray-600 text-booktime-600 dark:text-booktime-400 shadow-sm'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden lg:inline">{mode.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Bouton d'ajout */}
            <button
              onClick={onAddBook}
              className="flex items-center space-x-1 px-4 py-2 text-sm font-medium text-white bg-booktime-600 border border-transparent rounded-md hover:bg-booktime-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-booktime-500 dark:focus:ring-offset-gray-800 transition-colors"
            >
              <PlusIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Ajouter</span>
            </button>

            {/* Toggle thème */}
            <button
              onClick={toggleTheme}
              className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              title={theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
            >
              {theme === 'dark' ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Fermer le sélecteur de langue en cliquant ailleurs */}
      {showLanguageSelector && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setShowLanguageSelector(false)}
        />
      )}
    </header>
  );
};

export default Header;