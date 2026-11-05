import React, { useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

const MobileSearchOverlay = ({ isOpen, onClose, searchTerm, onSearchChange, onSearch }) => {
  const inputRef = useRef(null);
  const { isVoid } = useTheme();

  useEffect(() => {
    if (isOpen && inputRef.current) {
      const t = setTimeout(() => inputRef.current?.focus(), 50);
      return () => clearTimeout(t);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (searchTerm?.trim()) onSearch(searchTerm.trim());
  };

  return (
    <div className="md:hidden fixed inset-0 z-50 flex flex-col bg-honeycomb">
      <form
        onSubmit={handleSubmit}
        className={`flex items-center gap-3 px-4 py-3 backdrop-blur-xl border-b safe-area-top ${
          isVoid
            ? 'bg-[#050505]/90 border-white/[0.06]'
            : 'bg-booktime-mistSoft/75 dark:bg-gray-900/70 border-booktime-mist/55 dark:border-booktime-800/50'
        }`}
      >
        <MagnifyingGlassIcon
          className={`w-5 h-5 flex-shrink-0 ${isVoid ? 'text-white/35' : 'text-gray-400'}`}
        />
        <input
          ref={inputRef}
          type="search"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Titre, auteur, série…"
          className={`flex-1 bg-transparent text-base outline-none ${
            isVoid
              ? 'text-white placeholder-white/30'
              : 'text-gray-900 dark:text-white placeholder-gray-400'
          }`}
          enterKeyHint="search"
        />
        <button
          type="button"
          onClick={onClose}
          className={`p-1 ${isVoid ? 'text-white/40 hover:text-white/80' : 'text-gray-500 dark:text-gray-400'}`}
        >
          <XMarkIcon className="w-6 h-6" />
        </button>
      </form>

      <div className="flex-1 overflow-auto px-4 py-6">
        {!searchTerm?.trim() ? (
          <div className={`text-center mt-12 ${isVoid ? 'text-white/35' : 'text-gray-400 dark:text-gray-500'}`}>
            <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">Tape le titre d'un livre, un auteur ou une série</p>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => onSearch(searchTerm.trim())}
            className={`w-full py-3 rounded-xl font-medium text-base transition-colors ${
              isVoid
                ? 'bg-[#f0d060] hover:bg-[#e4c24a] text-black'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            Rechercher « {searchTerm.trim()} »
          </button>
        )}
      </div>
    </div>
  );
};

export default MobileSearchOverlay;
