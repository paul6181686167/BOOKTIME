import React from 'react';
import { BookOpenIcon, CheckCircleIcon, ClockIcon, QueueListIcon } from '@heroicons/react/24/outline';

const StatsPanel = ({ stats }) => {
  const statCards = [
    {
      title: 'Total',
      value: stats.total_books || 0,
      icon: BookOpenIcon,
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Terminés',
      value: stats.completed_books || 0,
      icon: CheckCircleIcon,
      color: 'bg-green-500',
      textColor: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'En cours',
      value: stats.reading_books || 0,
      icon: ClockIcon,
      color: 'bg-yellow-500',
      textColor: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      title: 'À lire',
      value: stats.to_read_books || 0,
      icon: QueueListIcon,
      color: 'bg-gray-500',
      textColor: 'text-gray-600',
      bgColor: 'bg-gray-50',
    },
  ];

  const categoryStats = stats.categories || {};

  return (
    <div className="mb-8">
      {/* Statistiques principales */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-6 w-6 ${stat.textColor}`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Statistiques par catégorie */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Répartition par catégorie</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">📚</span>
              <div>
                <p className="font-medium text-gray-900">Romans</p>
                <p className="text-sm text-gray-600">Littérature classique et moderne</p>
              </div>
            </div>
            <span className="text-2xl font-bold text-blue-600">
              {categoryStats.roman || 0}
            </span>
          </div>

          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🎨</span>
              <div>
                <p className="font-medium text-gray-900">Bande dessinée</p>
                <p className="text-sm text-gray-600">Bandes dessinées</p>
              </div>
            </div>
            <span className="text-2xl font-bold text-green-600">
              {categoryStats.bd || 0}
            </span>
          </div>

          <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🇯🇵</span>
              <div>
                <p className="font-medium text-gray-900">Mangas</p>
                <p className="text-sm text-gray-600">Comics japonais</p>
              </div>
            </div>
            <span className="text-2xl font-bold text-yellow-600">
              {categoryStats.manga || 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;