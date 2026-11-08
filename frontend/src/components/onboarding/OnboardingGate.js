import React, { useEffect, useRef, useState } from 'react';
import OnboardingLibraryPicker from './OnboardingLibraryPicker';
import {
  isOnboardingDone,
  markOnboardingDone,
  serverLibraryIsEmpty,
} from '../../services/onboardingService';

function WaitScreen() {
  return (
    <div className="flex min-h-screen min-h-dvh items-center justify-center bg-honeycomb px-6">
      <p role="status" className="text-center text-sm font-medium text-gray-800 dark:text-gray-200">
        Préparation de ta bibliothèque…
      </p>
    </div>
  );
}

/**
 * Page d'accueil d'un compte vide, affichée à la place de la bibliothèque
 * (pas de « livres populaires » en dessous).
 */
export default function OnboardingGate({ userKey, libraryEmpty, loading, onDone }) {
  const [phase, setPhase] = useState(() => {
    if (!userKey || isOnboardingDone(userKey)) return 'hidden';
    return 'wait';
  });
  const started = useRef(false);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  useEffect(() => {
    if (!userKey || isOnboardingDone(userKey)) {
      setPhase('hidden');
      return undefined;
    }
    if (loading) {
      setPhase('wait');
      return undefined;
    }
    if (!libraryEmpty) {
      setPhase('hidden');
      return undefined;
    }
    if (started.current) return undefined;
    started.current = true;
    setPhase('wait');
    let cancelled = false;
    serverLibraryIsEmpty().then((empty) => {
      if (cancelled) return;
      if (empty) {
        setPhase('show');
        return;
      }
      markOnboardingDone(userKey);
      setPhase('hidden');
      onDoneRef.current?.(0);
    });
    return () => {
      cancelled = true;
    };
  }, [userKey, libraryEmpty, loading]);

  if (phase === 'show') {
    return (
      <OnboardingLibraryPicker
        onFinish={(added) => {
          markOnboardingDone(userKey);
          setPhase('hidden');
          onDone?.(added);
        }}
      />
    );
  }

  if (phase === 'wait' || (loading && userKey && !isOnboardingDone(userKey))) {
    return <WaitScreen />;
  }

  return null;
}
