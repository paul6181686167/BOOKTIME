import React, { useLayoutEffect, useRef, useState } from 'react';
import { useLocation, useOutlet } from 'react-router-dom';
import { primaryTabIndex } from '../../utils/primaryTabs';
import useIsMobileLayout from '../../hooks/useIsMobileLayout';

const SLIDE_MS = 320;

/**
 * Outlet avec glissement horizontal selon l’ordre des onglets
 * (Biblio → À venir → Pour toi → Profil).
 */
export default function MobileSlideOutlet() {
  const location = useLocation();
  const outlet = useOutlet();
  const isMobile = useIsMobileLayout();
  const index = primaryTabIndex(location.pathname);

  const prevRef = useRef({
    path: location.pathname,
    index,
    outlet,
  });

  const [layers, setLayers] = useState(null);
  const clearTimerRef = useRef(null);

  useLayoutEffect(() => {
    const prev = prevRef.current;
    if (prev.path === location.pathname) {
      prevRef.current = { path: location.pathname, index, outlet };
      return undefined;
    }

    if (clearTimerRef.current) {
      clearTimeout(clearTimerRef.current);
      clearTimerRef.current = null;
    }

    const reduceMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const bothPrimary = index >= 0 && prev.index >= 0;
    const shouldSlide =
      isMobile && !reduceMotion && bothPrimary && index !== prev.index;

    if (shouldSlide) {
      const dir = index > prev.index ? 1 : -1;
      setLayers({
        dir,
        fromKey: prev.path,
        fromNode: prev.outlet,
        toKey: location.pathname,
        toNode: outlet,
      });
      clearTimerRef.current = setTimeout(() => {
        setLayers(null);
        clearTimerRef.current = null;
      }, SLIDE_MS);
    } else {
      setLayers(null);
    }

    prevRef.current = { path: location.pathname, index, outlet };

    return () => {
      if (clearTimerRef.current) {
        clearTimeout(clearTimerRef.current);
        clearTimerRef.current = null;
      }
    };
  }, [location.pathname, outlet, index, isMobile]);

  if (layers) {
    const exitCls =
      layers.dir > 0 ? 'mobile-page-exit-left' : 'mobile-page-exit-right';
    const enterCls =
      layers.dir > 0 ? 'mobile-page-enter-right' : 'mobile-page-enter-left';

    return (
      <div className="mobile-page-stage relative min-h-screen overflow-hidden">
        <div
          key={layers.fromKey}
          className={`mobile-page-layer absolute inset-0 ${exitCls}`}
          aria-hidden
        >
          {layers.fromNode}
        </div>
        <div key={layers.toKey} className={`mobile-page-layer relative z-10 ${enterCls}`}>
          {layers.toNode}
        </div>
      </div>
    );
  }

  return outlet;
}
