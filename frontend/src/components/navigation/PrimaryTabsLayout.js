import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import MobileBottomNav from '../MobileBottomNav';
import useIsMobileLayout from '../../hooks/useIsMobileLayout';
import {
  PRIMARY_TABS,
  pathToPrimaryTab,
  primaryTabIndex,
  primaryTabToPath,
} from '../../utils/primaryTabs';

const SLIDE_EASE = 'cubic-bezier(0.32, 0.72, 0, 1)';
const SLIDE_MS = 380;
const SWIPE_MIN_DX = 72;

/**
 * Coquille des 4 destinations : carrousel horizontal sur mobile.
 */
export default function PrimaryTabsLayout({ slides }) {
  const location = useLocation();
  const navigate = useNavigate();
  const isMobile = useIsMobileLayout();
  const activeTab = pathToPrimaryTab(location.pathname) || 'home';
  const activeIndex = Math.max(0, primaryTabIndex(location.pathname));

  const [mounted, setMounted] = useState(() => ({ [activeIndex]: true }));
  const touchRef = useRef(null);
  const reduceMotion =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    setMounted((prev) => (prev[activeIndex] ? prev : { ...prev, [activeIndex]: true }));
  }, [activeIndex]);

  // Verrouille le scroll document sur mobile (le scroll vit dans chaque diapositive)
  useEffect(() => {
    if (!isMobile) return undefined;
    document.documentElement.classList.add('mobile-tabs-scroll');
    return () => document.documentElement.classList.remove('mobile-tabs-scroll');
  }, [isMobile]);

  // Remonter en haut de la diapo active au changement d’onglet
  useEffect(() => {
    if (!isMobile) return;
    const slides = document.querySelectorAll('.mobile-slideshow-slide');
    const el = slides[activeIndex];
    if (el) el.scrollTop = 0;
  }, [activeIndex, isMobile]);

  const handleTabChange = (tabId) => {
    const path = primaryTabToPath(tabId);
    if (path !== location.pathname) navigate(path);
  };

  const order = useMemo(() => PRIMARY_TABS.map((t) => t.id), []);

  // Swipe horizontal uniquement si le geste est clairement latéral (ne bloque pas le scroll)
  const onTouchStart = (e) => {
    if (!isMobile || e.touches.length !== 1) return;
    touchRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    };
  };

  const onTouchEnd = (e) => {
    const start = touchRef.current;
    touchRef.current = null;
    if (!start) return;
    const dx = e.changedTouches[0].clientX - start.x;
    const dy = e.changedTouches[0].clientY - start.y;
    if (Math.abs(dx) < SWIPE_MIN_DX) return;
    if (Math.abs(dx) < Math.abs(dy) * 1.4) return; // prioriser le scroll vertical
    if (dx < 0 && activeIndex < PRIMARY_TABS.length - 1) {
      navigate(PRIMARY_TABS[activeIndex + 1].path);
    } else if (dx > 0 && activeIndex > 0) {
      navigate(PRIMARY_TABS[activeIndex - 1].path);
    }
  };

  const toaster = (
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: { marginBottom: 'calc(5.5rem + env(safe-area-inset-bottom))' },
      }}
      containerStyle={{ bottom: 0 }}
    />
  );

  if (!isMobile) {
    const id = order[activeIndex] || 'home';
    return (
      <>
        {slides[id]}
        {toaster}
      </>
    );
  }

  return (
    <>
      <div
        className="mobile-slideshow"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        <div
          className="mobile-slideshow-track"
          style={{
            transform: `translate3d(-${activeIndex * 100}%, 0, 0)`,
            transition: reduceMotion
              ? 'none'
              : `transform ${SLIDE_MS}ms ${SLIDE_EASE}`,
          }}
        >
          {order.map((id, i) => (
            <section
              key={id}
              className="mobile-slideshow-slide"
              aria-hidden={i !== activeIndex}
              // `inert` : les panneaux hors écran ne reçoivent ni focus clavier ni lecteur d'écran
              // (React 18 ne gère pas le booléen : on passe une chaîne vide).
              inert={i !== activeIndex ? '' : undefined}
              style={{ pointerEvents: i === activeIndex ? 'auto' : 'none' }}
            >
              {mounted[i] ? slides[id] : null}
            </section>
          ))}
        </div>
      </div>
      <MobileBottomNav activeTab={activeTab} onTabChange={handleTabChange} />
      {toaster}
    </>
  );
}
