import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import ModalOverlay, { MODAL_Z } from '../common/ModalOverlay';

/** Confirmation « cocher aussi les tomes précédents ? ». */
const PreviousTomesDialog = ({
  missingPreviousWarning,
  handleCheckPreviousTomes,
  setMissingPreviousWarning,
}) => (
  <>
        {/* Modal de confirmation pour cocher les tomes précédents */}
        {missingPreviousWarning && (
          <ModalOverlay
            onClose={() => setMissingPreviousWarning(null)}
            zIndex={MODAL_Z.dialog}
            ariaLabel="Cocher aussi les tomes précédents ?"
            className="fixed inset-0 bg-black/50 flex items-center justify-center"
          >
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-full">
                  <ExclamationTriangleIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Suggestion de lecture
                </h3>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-700 dark:text-gray-300 mb-3">
                  Vous avez marqué comme lu le <strong>tome {missingPreviousWarning.currentTome}</strong>.
                </p>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  Souhaitez-vous également marquer comme lus les tomes précédents ?
                </p>
                <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  <strong>Tomes concernés :</strong> {missingPreviousWarning.missingTomes.join(', ')}
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={handleCheckPreviousTomes}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 text-sm font-medium"
                >
                  Oui, cocher les précédents
                </button>
                <button
                  onClick={() => setMissingPreviousWarning(null)}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg transition-colors duration-200 text-sm font-medium"
                >
                  Non, juste ce tome
                </button>
              </div>
            </div>
          </ModalOverlay>
        )}
  </>
);

export default PreviousTomesDialog;
