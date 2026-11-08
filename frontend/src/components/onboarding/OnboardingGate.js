import React, { useEffect, useRef, useState } from 'react';
import OnboardingLibraryPicker from './OnboardingLibraryPicker';
import {
  isOnboardingDone,
  markOnboardingDone,
  serverLibraryIsEmpty,
} from '../../services/onboardingService';

/**
 * Affiche l'écran « Qu'as-tu déjà lu ? » une seule fois, quand la bibliothèque
 * est vide, avant que l'utilisateur n'y accède.
 *
 * `libraryEmpty` vient de l'état local ; le serveur le confirme avant d'afficher
 * l'écran (réseau coupé ou serveur qui se réveille : on n'affiche rien).
 */
export default function OnboardingGate({ userKey, libraryEmpty, onDone }) {
  const [phase, setPhase] = useState('idle'); // idle | show | hidden
  const started = useRef(false);

  // La vérification serveur n'est lancée qu'une fois par session d'écran.
  useEffect(() => {
    if (started.current || !userKey || !libraryEmpty || isOnboardingDone(userKey)) return undefined;
    started.current = true;
    let cancelled = false;
    serverLibraryIsEmpty().then((empty) => {
      if (!cancelled) setPhase(empty ? 'show' : 'hidden');
    });
    return () => {
      cancelled = true;
    };
  }, [userKey, libraryEmpty]);

  if (phase !== 'show') return null;

  return (
    <OnboardingLibraryPicker
      onFinish={(added) => {
        markOnboardingDone(userKey);
        setPhase('hidden');
        if (added > 0) onDone?.(added);
      }}
    />
  );
}
