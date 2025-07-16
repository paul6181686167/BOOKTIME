import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const AuthorModal = ({ author, isOpen, onClose }) => {
  if (!isOpen || !author) return null;

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div className="modal-content-wide" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {author}
            </h2>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="text-center py-8">
          <div className="text-6xl mb-4">👤</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Informations à venir
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Plus d'informations sur cet auteur seront ajoutées prochainement !
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthorModal;