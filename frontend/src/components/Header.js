import React from 'react';
import { MagnifyingGlassIcon, PlusIcon, BookOpenIcon, UserIcon, RectangleStackIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

const Header = ({ searchTerm, onSearchChange, onAddBook, viewMode, onViewModeChange, currentContext, onBackToAll }) => {
  const { isDarkMode, toggleTheme } = useTheme();

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo et titre */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="flex-shrink-0">
              <BookOpenIcon className="h-6 w-6 sm:h-8 sm:w-8 text-booktime-600 dark:text-booktime-400" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white truncate">BOOKTIME</h1>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 hidden sm:block">Votre tracker de livres personnel</p>
            </div>
          </div>

          {/* Navigation mobile - Vue mode */}
          <div className="flex md:hidden items-center space-x-1">
            <button
              onClick={() => onViewModeChange('books')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'books' 
                  ? 'bg-booktime-100 dark:bg-booktime-800 text-booktime-700 dark:text-booktime-300' 
                  : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              <BookOpenIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => onViewModeChange('authors')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'authors' 
                  ? 'bg-booktime-100 dark:bg-booktime-800 text-booktime-700 dark:text-booktime-300' 
                  : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              <UserIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => onViewModeChange('sagas')}
              className={`p-2 rounded-md transition-colors ${
                viewMode === 'sagas' 
                  ? 'bg-booktime-100 dark:bg-booktime-800 text-booktime-700 dark:text-booktime-300' 
                  : 'text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
            >
              <RectangleStackIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Barre de recherche desktop */}
          <div className="hidden md:block flex-1 max-w-lg mx-8">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 dark:focus:placeholder-gray-500 focus:ring-1 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
                placeholder="Rechercher un livre ou un auteur..."
              />
            </div>
          </div>

          {/* Navigation desktop */}
          <div className="hidden md:flex items-center space-x-4">
            <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1 transition-colors">
              <button
                onClick={() => onViewModeChange('books')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'books' 
                    ? 'bg-white dark:bg-gray-600 text-booktime-700 dark:text-booktime-300 shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <BookOpenIcon className="h-4 w-4" />
                <span>Livres</span>
              </button>
              <button
                onClick={() => onViewModeChange('authors')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'authors' 
                    ? 'bg-white dark:bg-gray-600 text-booktime-700 dark:text-booktime-300 shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <UserIcon className="h-4 w-4" />
                <span>Auteurs</span>
              </button>
              <button
                onClick={() => onViewModeChange('sagas')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'sagas' 
                    ? 'bg-white dark:bg-gray-600 text-booktime-700 dark:text-booktime-300 shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                <RectangleStackIcon className="h-4 w-4" />
                <span>Sagas</span>
              </button>
            </div>
          </div>

          {/* Toggle thème et bouton d'ajout */}
          <div className="flex items-center space-x-3">
            {/* Bouton toggle thème */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              title={isDarkMode ? 'Passer en mode clair' : 'Passer en mode sombre'}
            >
              {isDarkMode ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>

            {/* Bouton d'ajout */}
            <button
              onClick={onAddBook}
              className="inline-flex items-center px-3 sm:px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-booktime-600 hover:bg-booktime-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-booktime-500 dark:focus:ring-offset-gray-800 transition-colors"
            >
              <PlusIcon className="h-4 w-4 sm:h-5 sm:w-5 sm:mr-2" />
              <span className="hidden sm:inline">Ajouter un livre</span>
            </button>
          </div>
        </div>

        {/* Barre de recherche mobile */}
        <div className="md:hidden pb-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 dark:text-gray-500" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 dark:focus:placeholder-gray-500 focus:ring-1 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
              placeholder="Rechercher un livre ou un auteur..."
            />
          </div>
        </div>

        {/* Breadcrumb pour mobile */}
        {currentContext && (
          <div className="md:hidden pb-3">
            <button
              onClick={onBackToAll}
              className="flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <span>← Retour</span>
            </button>
            <div className="mt-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {currentContext.type === 'author' ? 'Auteur' : 'Saga'} : {currentContext.name}
              </p>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;