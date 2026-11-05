import React from 'react';
import { useNavigate } from 'react-router-dom';
import UpcomingPanel from '../components/UpcomingPanel';

/** Page pleine « À venir » (mobile / route /upcoming). */
export default function UpcomingPage() {
  const navigate = useNavigate();
  return (
    <UpcomingPanel
      variant="page"
      isOpen
      onClose={() => navigate('/')}
    />
  );
}
