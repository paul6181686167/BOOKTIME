import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import AuthService from '../../services/authService';

const CONFIRM_WORD = 'SUPPRIMER';

/**
 * Suppression définitive du compte et de toutes les données associées.
 * Parcours exigé par Google Play pour les applications à comptes utilisateurs.
 */
const DeleteAccountDialog = ({ isOpen, onClose, onDeleted }) => {
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const canSubmit = password.length > 0 && confirmation.trim().toUpperCase() === CONFIRM_WORD;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!canSubmit || submitting) return;

    setSubmitting(true);
    const result = await new AuthService().deleteAccount(password);
    setSubmitting(false);

    if (!result.success) {
      toast.error(result.error);
      return;
    }

    toast.success('Compte supprimé. Au revoir !');
    if (onDeleted) onDeleted();
    window.location.reload();
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-md rounded-xl bg-white dark:bg-gray-800 shadow-xl">
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Supprimer définitivement mon compte
            </h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              Ton compte, ta bibliothèque, tes notes, tes avis et ta progression de lecture seront
              effacés immédiatement et sans possibilité de récupération.
            </p>
          </div>

          <label className="block">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
              Mot de passe
            </span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white"
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
              Tape {CONFIRM_WORD} pour confirmer
            </span>
            <input
              type="text"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
              autoComplete="off"
              className="mt-1 w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-2 text-sm text-gray-900 dark:text-white"
            />
          </label>

          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 py-2 text-sm font-medium text-gray-700 dark:text-gray-200"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={!canSubmit || submitting}
              className="flex-1 rounded-lg bg-red-600 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-red-700"
            >
              {submitting ? 'Suppression…' : 'Supprimer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DeleteAccountDialog;
