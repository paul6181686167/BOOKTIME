import React from 'react';
import { useUserLanguage } from '../contexts/UserLanguageContext';
import { getLanguageByCode } from '../constants/languages';
import { CheckCircleIcon, ExclamationTriangleIcon, NoSymbolIcon } from '@heroicons/react/24/outline';

const LanguageIndicator = ({ book, size = 'sm' }) => {
  const { getBookLanguageStatus } = useUserLanguage();
  const status = getBookLanguageStatus(book);
  
  const sizeClasses = {
    xs: 'text-xs px-1.5 py-0.5',
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-2.5 py-1.5',
    lg: 'text-base px-3 py-2'
  };

  const iconSizeClasses = {
    xs: 'h-3 w-3',
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  const getIndicatorConfig = () => {
    const preferredLang = getLanguageByCode(status.preferred_language);
    
    if (!status.available) {
      return {
        icon: NoSymbolIcon,
        color: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
        text: 'Non disponible',
        tooltip: `Pas disponible en ${preferredLang.name}`,
        flag: '⚪'
      };
    }

    switch (status.type) {
      case 'original':
        return {
          icon: CheckCircleIcon,
          color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
          text: 'Langue originale',
          tooltip: `Langue originale : ${preferredLang.name}`,
          flag: preferredLang.flag
        };
      case 'translation':
        return {
          icon: CheckCircleIcon,
          color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
          text: 'Traduit',
          tooltip: `Traduit en ${preferredLang.name}`,
          flag: preferredLang.flag
        };
      case 'reading':
        return {
          icon: ExclamationTriangleIcon,
          color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
          text: 'Langue de lecture',
          tooltip: `Vous lisez en ${preferredLang.name}`,
          flag: preferredLang.flag
        };
      default:
        return {
          icon: NoSymbolIcon,
          color: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
          text: 'Inconnu',
          tooltip: 'Statut linguistique inconnu',
          flag: '❓'
        };
    }
  };

  const config = getIndicatorConfig();
  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-1 rounded-full font-medium ${config.color} ${sizeClasses[size]}`}
      title={config.tooltip}
    >
      <span>{config.flag}</span>
      <Icon className={iconSizeClasses[size]} />
      <span className="hidden sm:inline">{config.text}</span>
    </div>
  );
};

export default LanguageIndicator;