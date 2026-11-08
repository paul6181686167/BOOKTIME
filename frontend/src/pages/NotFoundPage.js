import React from 'react';
import { useNavigate } from 'react-router-dom';

/** Affichée quand l'adresse ne correspond à aucune page de l'application. */
export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <main
      className="min-h-screen min-h-dvh flex flex-col items-center justify-center gap-4 px-6 text-center bg-gray-50 dark:bg-gray-900"
      style={{ paddingTop: 'env(safe-area-inset-top)', paddingBottom: 'env(safe-area-inset-bottom)' }}
      data-testid="not-found"
    >
      <p className="text-5xl font-bold text-booktime-600 dark:text-booktime-400" aria-hidden="true">
        404
      </p>
      <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Page introuvable</h1>
      <p className="max-w-sm text-sm text-gray-600 dark:text-gray-300">
        Cette adresse n'existe pas ou a été déplacée.
      </p>
      <button
        type="button"
        onClick={() => navigate('/', { replace: true })}
        className="min-h-[44px] rounded-lg bg-booktime-600 px-5 font-semibold text-white hover:bg-booktime-700"
      >
        Retour à ma bibliothèque
      </button>
    </main>
  );
}
