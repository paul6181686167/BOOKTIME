import React, { useCallback, useEffect, useState } from 'react';
import ModalOverlay, { MODAL_Z } from './ModalOverlay';
import { registerConfirmHost } from '../../utils/confirmDialog';

/** Fenêtre de confirmation commune. À monter une seule fois, tout en haut de l'application. */
export default function ConfirmHost() {
  const [request, setRequest] = useState(null);

  useEffect(() => registerConfirmHost(setRequest), []);

  const answer = useCallback(
    (value) => {
      if (request) request.resolve(value);
      setRequest(null);
    },
    [request]
  );

  if (!request) return null;

  return (
    <ModalOverlay
      onClose={() => answer(false)}
      zIndex={MODAL_Z.dialog}
      ariaLabel="Confirmation"
      className="fixed inset-0 flex items-center justify-center bg-black/60 p-4"
    >
      <div
        data-testid="confirm-dialog"
        className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-xl dark:bg-gray-800"
      >
        <p className="text-base text-gray-900 dark:text-white">{request.message}</p>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={() => answer(false)}
            className="min-h-[44px] rounded-lg border border-gray-300 px-4 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
          >
            {request.cancelLabel}
          </button>
          <button
            type="button"
            onClick={() => answer(true)}
            className={`min-h-[44px] rounded-lg px-4 text-sm font-semibold text-white ${
              request.danger ? 'bg-red-600 hover:bg-red-700' : 'bg-booktime-600 hover:bg-booktime-700'
            }`}
          >
            {request.confirmLabel}
          </button>
        </div>
      </div>
    </ModalOverlay>
  );
}
