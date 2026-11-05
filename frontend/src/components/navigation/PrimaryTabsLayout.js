import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import MobileBottomNav from '../MobileBottomNav';
import MobileSlideOutlet from './MobileSlideOutlet';
import { pathToPrimaryTab, primaryTabToPath } from '../../utils/primaryTabs';

/**
 * Coquille des 4 destinations de la barre bas : pages + glissement.
 */
export default function PrimaryTabsLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeTab = pathToPrimaryTab(location.pathname) || 'home';

  const handleTabChange = (tabId) => {
    const path = primaryTabToPath(tabId);
    if (path !== location.pathname) {
      navigate(path);
    }
  };

  return (
    <>
      <MobileSlideOutlet />
      <MobileBottomNav activeTab={activeTab} onTabChange={handleTabChange} />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { marginBottom: 'calc(5.5rem + env(safe-area-inset-bottom))' },
        }}
        containerStyle={{ bottom: 0 }}
      />
    </>
  );
}
