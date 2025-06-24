import React from 'react';
import { MagnifyingGlassIcon, PlusIcon, BookOpenIcon } from '@heroicons/react/24/outline';

const Header = ({ searchTerm, onSearchChange, onAddBook }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo et titre */}
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <BookOpenIcon className="h-8 w-8 text-booktime-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">BOOKTIME</h1>
              <p className="text-sm text-gray-500">Votre tracker de livres personnel</p>
            </div>
          </div>

          {/* Barre de recherche */}
          <div className="hidden md:block flex-1 max-w-lg mx-8">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-booktime-500 focus:border-booktime-500"
                placeholder="Rechercher un livre ou un auteur..."
              />
            </div>
          </div>

          {/* Bouton d'ajout */}
          <div className="flex items-center space-x-4">
            <button
              onClick={onAddBook}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-booktime-600 hover:bg-booktime-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-booktime-500 transition-colors"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Ajouter un livre
            </button>
          </div>
        </div>

        {/* Barre de recherche mobile */}
        <div className="md:hidden pb-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-booktime-500 focus:border-booktime-500"
              placeholder="Rechercher un livre ou un auteur..."
            />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;