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
const SWIPE_MIN_DX = 56;

/**
 * Coquille des 4 destinations : sur mobile, vrai carrousel horizontal
 * (Biblio → À venir → Pour toi → Profil), comme des diapositives.
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

  const handleTabChange = (tabId) => {
    const path = primaryTabToPath(tabId);
    if (path !== location.pathname) navigate(path);
  };

  const order = useMemo(() => PRIMARY_TABS.map((t) => t.id), []);

  const onTouchStart = (e) => {
    if (!isMobile || e.touches.length !== 1) return;
    touchRef.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
      locked: null,
    };
  };

  const onTouchMove = (e) => {
    const start = touchRef.current;
    if (!start || start.locked === 'v') return;
    const dx = e.touches[0].clientX - start.x;
    const dy = e.touches[0].clientY - start.y;
    if (start.locked == null && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
      start.locked = Math.abs(dx) > Math.abs(dy) ? 'h' : 'v';
    }
  };

  const onTouchEnd = (e) => {
    const start = touchRef.current;
    touchRef.current = null;
    if (!start || start.locked === 'v') return;
    const dx = e.changedTouches[0].clientX - start.x;
    if (Math.abs(dx) < SWIPE_MIN_DX) return;
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

  // Desktop : une seule page active (pas de carrousel)
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
        onTouchMove={onTouchMove}
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
