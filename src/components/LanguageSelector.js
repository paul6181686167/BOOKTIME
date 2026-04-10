import React, { useState } from 'react';
import { ChevronDownIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { LANGUAGES, COMMON_LANGUAGES, getLanguageByCode } from '../constants/languages';

const LanguageSelector = ({ 
  selectedLanguages = [], 
  onLanguagesChange, 
  maxSelections = 10,
  placeholder = "Sélectionner des langues",
  label,
  single = false 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredLanguages = LANGUAGES.filter(lang => 
    lang.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lang.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Ordonner par langues communes d'abord
  const orderedLanguages = [
    ...filteredLanguages.filter(lang => COMMON_LANGUAGES.includes(lang.code)),
    ...filteredLanguages.filter(lang => !COMMON_LANGUAGES.includes(lang.code))
  ];

  const handleLanguageSelect = (languageCode) => {
    if (single) {
      onLanguagesChange([languageCode]);
      setIsOpen(false);
      return;
    }

    if (selectedLanguages.includes(languageCode)) {
      onLanguagesChange(selectedLanguages.filter(code => code !== languageCode));
    } else if (selectedLanguages.length < maxSelections) {
      onLanguagesChange([...selectedLanguages, languageCode]);
    }
  };

  const removeLanguage = (languageCode, e) => {
    e.stopPropagation();
    onLanguagesChange(selectedLanguages.filter(code => code !== languageCode));
  };

  return (
    <div className="relative">
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          {label}
        </label>
      )}
      
      <div 
        className="w-full min-h-[2.5rem] px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white cursor-pointer focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex flex-wrap gap-1 items-center">
          {selectedLanguages.length > 0 ? (
            selectedLanguages.map(code => {
              const lang = getLanguageByCode(code);
              return (
                <span 
                  key={code}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-booktime-100 dark:bg-booktime-900/30 text-booktime-800 dark:text-booktime-300 text-xs rounded-md"
                >
                  <span>{lang.flag}</span>
                  <span>{lang.name}</span>
                  {!single && (
                    <button
                      onClick={(e) => removeLanguage(code, e)}
                      className="ml-1 hover:text-booktime-600 dark:hover:text-booktime-400"
                    >
                      <XMarkIcon className="h-3 w-3" />
                    </button>
                  )}
                </span>
              );
            })
          ) : (
            <span className="text-gray-500 dark:text-gray-400">{placeholder}</span>
          )}
          
          <ChevronDownIcon 
            className={`h-4 w-4 text-gray-400 ml-auto transition-transform ${isOpen ? 'rotate-180' : ''}`} 
          />
        </div>
      </div>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-60 overflow-hidden">
          <div className="p-2 border-b border-gray-200 dark:border-gray-600">
            <input
              type="text"
              placeholder="Rechercher une langue..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-booktime-500"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          
          <div className="overflow-y-auto max-h-48">
            {orderedLanguages.map(lang => (
              <button
                key={lang.code}
                onClick={() => handleLanguageSelect(lang.code)}
                className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2 transition-colors ${
                  selectedLanguages.includes(lang.code) 
                    ? 'bg-booktime-50 dark:bg-booktime-900/30 text-booktime-700 dark:text-booktime-300' 
                    : 'text-gray-900 dark:text-white'
                }`}
              >
                <span>{lang.flag}</span>
                <span>{lang.name}</span>
                {selectedLanguages.includes(lang.code) && (
                  <span className="ml-auto text-booktime-600 dark:text-booktime-400">✓</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;