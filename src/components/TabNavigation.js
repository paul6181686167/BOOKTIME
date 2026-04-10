import React from 'react';

const TabNavigation = ({ activeTab, onTabChange, activeStatus, onStatusChange }) => {
  const tabs = [
    { key: 'roman', label: 'Romans', icon: '📚', color: 'book-roman' },
    { key: 'bd', label: 'BD', icon: '🎨', color: 'book-bd' },
    { key: 'manga', label: 'Mangas', icon: '🇯🇵', color: 'book-manga' },
  ];

  const statusFilters = [
    { key: 'all', label: 'Tous' },
    { key: 'to_read', label: 'À lire' },
    { key: 'reading', label: 'En cours' },
    { key: 'completed', label: 'Terminés' },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6 transition-colors">
      {/* Onglets principaux */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        {/* Version desktop */}
        <nav className="hidden sm:flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.key
                  ? `border-${tab.color} text-${tab.color} dark:text-${tab.color}`
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <span className="flex items-center space-x-2">
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </span>
            </button>
          ))}
        </nav>

        {/* Version mobile - onglets horizontaux avec scroll */}
        <nav className="sm:hidden flex space-x-1 px-4 py-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => onTabChange(tab.key)}
              className={`flex-shrink-0 flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-booktime-100 dark:bg-booktime-900 text-booktime-800 dark:text-booktime-300 border border-booktime-200 dark:border-booktime-700'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Filtres de statut */}
      <div className="px-4 sm:px-6 py-4">
        <div className="flex flex-wrap gap-2">
          {statusFilters.map((filter) => (
            <button
              key={filter.key}
              onClick={() => onStatusChange(filter.key)}
              className={`px-3 py-1.5 sm:py-1 rounded-full text-xs sm:text-sm font-medium transition-colors ${
                activeStatus === filter.key
                  ? 'bg-booktime-100 dark:bg-booktime-900 text-booktime-800 dark:text-booktime-300 border border-booktime-200 dark:border-booktime-700'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 border border-transparent'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TabNavigation;