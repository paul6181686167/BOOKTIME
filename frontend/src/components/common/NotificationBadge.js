import React from 'react';

/** Pastille rouge du nombre de notifications non lues (rien si 0). */
export default function NotificationBadge({ count, className = '' }) {
  if (!count) return null;
  return (
    <span
      data-testid="notification-badge"
      aria-label={`${count} notification${count > 1 ? 's' : ''} non lue${count > 1 ? 's' : ''}`}
      className={`inline-flex min-w-[1.1rem] h-[1.1rem] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold leading-none text-white ${className}`}
    >
      {count > 9 ? '9+' : count}
    </span>
  );
}
