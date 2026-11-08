import React from 'react';
import { useNavigate } from 'react-router-dom';
import TermsContent from '../components/legal/TermsContent';

/** Page publique des conditions générales d'utilisation (/cgu). */
export default function TermsPage() {
  const navigate = useNavigate();

  const goBack = () => {
    if (window.history.length > 1) navigate(-1);
    else navigate('/');
  };

  return (
    <div className="min-h-screen min-h-dvh bg-gray-50 dark:bg-gray-900">
      <div
        className="sticky top-0 z-10 bg-white/95 dark:bg-gray-900/95 backdrop-blur border-b border-gray-100 dark:border-gray-800"
        style={{ paddingTop: 'env(safe-area-inset-top)' }}
      >
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-3">
          <button
            type="button"
            onClick={goBack}
            aria-label="Retour"
            className="p-1.5 -ml-1.5 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-base font-bold text-gray-900 dark:text-white">Conditions générales d'utilisation</h1>
        </div>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-5 pb-12">
        <TermsContent />
      </div>
    </div>
  );
}
