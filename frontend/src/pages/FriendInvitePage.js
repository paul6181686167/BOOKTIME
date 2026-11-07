import React from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { PENDING_FRIEND_CODE_KEY, normalizeFriendCode } from '../utils/friendLink';

/**
 * Lien de partage /ami/CODE : mémorise le code puis ouvre l'accueil, où la fenêtre
 * Amis s'ouvre sur la fiche du lecteur. Hors connexion, l'écran de connexion s'affiche
 * d'abord (cette page n'est atteinte qu'une fois connecté).
 */
export default function FriendInvitePage() {
  const { code } = useParams();
  const clean = normalizeFriendCode(code);
  if (clean) {
    try {
      localStorage.setItem(PENDING_FRIEND_CODE_KEY, clean);
    } catch (_) {
      /* stockage indisponible : on ouvre simplement l'accueil */
    }
  }
  return <Navigate to="/" replace />;
}
