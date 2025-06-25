import React from 'react';
import { 
  BookOpenIcon, 
  CheckCircleIcon, 
  ClockIcon, 
  QueueListIcon,
  UserIcon,
  RectangleStackIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';

const ExtendedStatsPanel = ({ stats }) => {
  const mainStatCards = [
    {
      title: 'Total',
      value: stats.total_books || 0,
      icon: BookOpenIcon,
      color: 'bg-blue-500',
      textColor: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-50 dark:bg-blue-900/30',
    },
    {
      title: 'Terminés',
      value: stats.completed_books || 0,
      icon: CheckCircleIcon,
      color: 'bg-green-500',
      textColor: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-50 dark:bg-green-900/30',
    },
    {
      title: 'En cours',
      value: stats.reading_books || 0,
      icon: ClockIcon,
      color: 'bg-yellow-500',
      textColor: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-50 dark:bg-yellow-900/30',
    },
    {
      title: 'À lire',
      value: stats.to_read_books || 0,
      icon: QueueListIcon,
      color: 'bg-gray-500',
      textColor: 'text-gray-600 dark:text-gray-400',
      bgColor: 'bg-gray-50 dark:bg-gray-700/50',
    },
  ];

  const extendedStatCards = [
    {
      title: 'Auteurs',
      value: stats.authors_count || 0,
      icon: UserIcon,
      color: 'bg-purple-500',
      textColor: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-50 dark:bg-purple-900/30',
      description: 'Auteurs uniques'
    },
    {
      title: 'Sagas',
      value: stats.sagas_count || 0,
      icon: RectangleStackIcon,
      color: 'bg-indigo-500',
      textColor: 'text-indigo-600 dark:text-indigo-400',
      bgColor: 'bg-indigo-50 dark:bg-indigo-900/30',
      description: 'Collections actives'
    },
    {
      title: 'Auto-ajoutés',
      value: stats.auto_added_count || 0,
      icon: CpuChipIcon,
      color: 'bg-emerald-500',
      textColor: 'text-emerald-600 dark:text-emerald-400',
      bgColor: 'bg-emerald-50 dark:bg-emerald-900/30',
      description: 'Ajouts automatiques'
    },
  ];

  const categoryStats = stats.categories || {};

  return (
    <div className="mb-8">
      {/* Statistiques principales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {mainStatCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md dark:hover:shadow-lg transition-all duration-200"
            >
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.bgColor} transition-colors`}>
                  <Icon className={`h-6 w-6 ${stat.textColor}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Statistiques étendues */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
        {extendedStatCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md dark:hover:shadow-lg transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${stat.bgColor} transition-colors`}>
                    <Icon className={`h-6 w-6 ${stat.textColor}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.title}</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">{stat.description}</p>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Statistiques par catégorie améliorées */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 transition-colors">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Répartition par catégorie</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg transition-colors">
            <div className="flex items-center space-x-3">
              <span className="text-3xl">📚</span>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Romans</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Littérature & Fiction</p>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-16 bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                    <div 
                      className="bg-blue-500 dark:bg-blue-400 h-2 rounded-full transition-colors"
                      style={{ 
                        width: `${stats.total_books ? (categoryStats.roman / stats.total_books) * 100 : 0}%` 
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {stats.total_books ? Math.round((categoryStats.roman / stats.total_books) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>
            <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {categoryStats.roman || 0}
            </span>
          </div>

          <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/30 rounded-lg transition-colors">
            <div className="flex items-center space-x-3">
              <span className="text-3xl">🎨</span>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Bande dessinée</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Bandes dessinées</p>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-16 bg-green-200 dark:bg-green-800 rounded-full h-2">
                    <div 
                      className="bg-green-500 dark:bg-green-400 h-2 rounded-full transition-colors"
                      style={{ 
                        width: `${stats.total_books ? (categoryStats.bd / stats.total_books) * 100 : 0}%` 
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {stats.total_books ? Math.round((categoryStats.bd / stats.total_books) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>
            <span className="text-3xl font-bold text-green-600 dark:text-green-400">
              {categoryStats.bd || 0}
            </span>
          </div>

          <div className="flex items-center justify-between p-4 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg transition-colors">
            <div className="flex items-center space-x-3">
              <span className="text-3xl">🇯🇵</span>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Mangas</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Comics japonais</p>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="w-16 bg-yellow-200 dark:bg-yellow-800 rounded-full h-2">
                    <div 
                      className="bg-yellow-500 dark:bg-yellow-400 h-2 rounded-full transition-colors"
                      style={{ 
                        width: `${stats.total_books ? (categoryStats.manga / stats.total_books) * 100 : 0}%` 
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {stats.total_books ? Math.round((categoryStats.manga / stats.total_books) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>
            <span className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
              {categoryStats.manga || 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExtendedStatsPanel;