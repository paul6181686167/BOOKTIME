import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * Fenêtre modale commune (fiches, profil, amis, réglages…).
 *
 * - Rendue dans `document.body` : hors du carrousel mobile (transform, pointer-events,
 *   empilement) qui bloquait boutons et défilement des fiches.
 * - Fond cliquable, touche Échap (seule la fenêtre du dessus se ferme).
 * - Sémantique d'accessibilité : role="dialog", aria-modal, libellé, focus rendu à la fermeture.
 */

/** Niveaux d'empilement des fenêtres. */
export const MODAL_Z = {
  panel: 1100, // profil, amis, réglages…
  sheet: 1200, // fiches livre / série
  nested: 1300, // fiche auteur, scanners (au-dessus d'une fiche)
  dialog: 1400, // confirmations
};

// Pile des fenêtres ouvertes : Échap ne ferme que celle du dessus
const stack = [];

export default function ModalOverlay({
  onClose,
  children,
  zIndex = MODAL_Z.panel,
  className = 'modal-overlay',
  ariaLabel,
  closeOnBackdrop = true,
  style,
}) {
  const token = useRef({});
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const entry = token.current;
    const previouslyFocused =
      typeof document !== 'undefined' ? document.activeElement : null;
    stack.push(entry);

    const onKeyDown = (e) => {
      if (e.key !== 'Escape') return;
      if (stack[stack.length - 1] !== entry) return;
      e.stopPropagation();
      onCloseRef.current?.();
    };
    document.addEventListener('keydown', onKeyDown);

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      const i = stack.indexOf(entry);
      if (i >= 0) stack.splice(i, 1);
      try {
        if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
          previouslyFocused.focus({ preventScroll: true });
        }
      } catch {
        /* ignore */
      }
    };
  }, []);

  if (typeof document === 'undefined') return null;

  return createPortal(
    <div
      className={className}
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      style={{ zIndex, ...style }}
      onClick={(e) => {
        if (closeOnBackdrop && e.target === e.currentTarget) onCloseRef.current?.(e);
      }}
    >
      {children}
    </div>,
    document.body
  );
}
