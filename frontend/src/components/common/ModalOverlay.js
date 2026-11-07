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

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex=\"-1\"])';

function isVisible(el) {
  if (el.closest('[hidden]')) return false;
  const s = window.getComputedStyle(el);
  return s.display !== 'none' && s.visibility !== 'hidden';
}

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
  const dialogRef = useRef(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const entry = token.current;
    const previouslyFocused =
      typeof document !== 'undefined' ? document.activeElement : null;
    stack.push(entry);

    // Le focus entre dans la fenêtre (lecteurs d'écran, clavier) s'il n'y est pas déjà
    const dialog = dialogRef.current;
    if (dialog && !dialog.contains(document.activeElement)) {
      try {
        dialog.focus({ preventScroll: true });
      } catch {
        /* ignore */
      }
    }

    const onKeyDown = (e) => {
      if (stack[stack.length - 1] !== entry) return;
      if (e.key === 'Escape') {
        e.stopPropagation();
        onCloseRef.current?.();
        return;
      }
      // Piège à focus : Tab / Maj+Tab restent dans la fenêtre du dessus
      if (e.key === 'Tab' && dialog) {
        const focusable = [...dialog.querySelectorAll(FOCUSABLE)].filter(isVisible);
        if (focusable.length === 0) {
          e.preventDefault();
          dialog.focus({ preventScroll: true });
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement;
        if (e.shiftKey && (active === first || active === dialog)) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && active === last) {
          e.preventDefault();
          first.focus();
        } else if (!dialog.contains(active)) {
          e.preventDefault();
          first.focus();
        }
      }
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
      ref={dialogRef}
      tabIndex={-1}
      className={className}
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      style={{ zIndex, outline: 'none', ...style }}
      onClick={(e) => {
        if (closeOnBackdrop && e.target === e.currentTarget) onCloseRef.current?.(e);
      }}
    >
      {children}
    </div>,
    document.body
  );
}
