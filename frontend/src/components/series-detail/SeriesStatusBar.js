import React from 'react';

/** Boutons rapides de statut de la série (à lire / en cours / terminée…). */
const SeriesStatusBar = ({
  statusOptions,
  handleQuickStatusChange,
  seriesStatus,
  isSeriesOwned,
}) => (
  <>
        {/* Boutons rapides de statut — une seule ligne compacte */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6">
          <div className="mb-1.5 flex items-center gap-2">
            <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300">Statut</h3>
            {!isSeriesOwned && (
              <span className="text-[10px] text-gray-500">ajoutez la série pour modifier</span>
            )}
          </div>
          <div className="flex w-full max-w-md overflow-hidden rounded-lg border border-gray-200 dark:border-gray-600">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  handleQuickStatusChange(option.value);
                }}
                className={`flex flex-1 items-center justify-center whitespace-nowrap px-2 py-1.5 text-[11px] sm:text-xs font-medium transition-all sm:px-3 sm:py-2 ${
                  seriesStatus === option.value
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
                title={`Marquer comme ${option.label}`}
                disabled={!isSeriesOwned}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
  </>
);

export default SeriesStatusBar;
