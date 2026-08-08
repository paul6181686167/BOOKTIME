import React, { useEffect, useRef } from 'react';
import { XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const MobileSearchOverlay = ({ isOpen, onClose, searchTerm, onSearchChange, onSearch }) => {
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm?.trim()) {
      onSearch(searchTerm);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="md:hidden fixed inset-0 z-50 bg-honeycomb flex flex-col">
      {/* Barre de recherche */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 px-4 py-3 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl border-b border-booktime-mist/55 dark:border-booktime-800/50 safe-area-top"
      >
        <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
        <input
          ref={inputRef}
          type="search"
          value={searchTerm || ''}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Titre, auteur, série…"
          className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-400 text-base outline-none"
          enterKeyHint="search"
        />
        <button
          type="button"
          onClick={onClose}
          className="p-1 text-gray-500 dark:text-gray-400"
        >
          <XMarkIcon className="w-6 h-6" />
        </button>
      </form>

      {/* Suggestions ou état vide */}
      <div className="flex-1 overflow-auto px-4 py-6">
        {!searchTerm && (
          <div className="text-center text-gray-400 dark:text-gray-500 mt-12">
            <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Tape le titre d'un livre, un auteur ou une série</p>
          </div>
        )}
        {searchTerm && (
          <button
            onClick={handleSubmit}
            className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium text-base transition-colors"
          >
            Rechercher « {searchTerm} »
          </button>
        )}
      </div>
    </div>
  );
};

export default MobileSearchOverlay;
