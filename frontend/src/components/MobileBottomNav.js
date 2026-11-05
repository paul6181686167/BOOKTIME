import React from 'react';
import {
  HomeIcon,
  BookOpenIcon,
  UserCircleIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  BookOpenIcon as BookIconSolid,
  UserCircleIcon as UserIconSolid,
  CalendarDaysIcon as CalendarIconSolid,
} from '@heroicons/react/24/solid';
import { useTheme } from '../contexts/ThemeContext';

const NAV_ITEMS = [
  { id: 'home',            label: 'Biblio',      Icon: HomeIcon,          IconActive: HomeIconSolid },
  { id: 'upcoming',        label: 'À venir',     Icon: CalendarDaysIcon,  IconActive: CalendarIconSolid },
  { id: 'recommendations', label: 'Pour toi',    Icon: BookOpenIcon,      IconActive: BookIconSolid },
  { id: 'profile',         label: 'Profil',      Icon: UserCircleIcon,    IconActive: UserIconSolid },
];

const MobileBottomNav = ({ activeTab, onTabChange }) => {
  const { isVoid } = useTheme();

  return (
    <nav
      className={`md:hidden fixed bottom-0 left-0 right-0 z-40 safe-area-bottom border-t bg-honeycomb ${
        isVoid
          ? 'border-white/[0.06]'
          : 'border-booktime-mist/80 dark:border-booktime-800/40'
      }`}
    >
      <div className="mx-auto flex h-14 max-w-lg items-stretch px-2">
        {NAV_ITEMS.map(({ id, label, Icon, IconActive }) => {
          const isActive = activeTab === id;
          const Ic = isActive ? IconActive : Icon;
          const activeCls = isVoid
            ? 'text-[#f0d060]'
            : 'text-booktime-700 dark:text-booktime-300';
          const idleCls = isVoid
            ? 'text-white/35 active:text-white/70'
            : 'text-booktime-800/45 dark:text-white/40 active:text-booktime-800/70 dark:active:text-white/70';
          return (
            <button
              key={id}
              type="button"
              onClick={() => onTabChange(id)}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
              className={`relative flex flex-1 flex-col items-center justify-center gap-0.5 transition-colors duration-200 ${
                isActive ? activeCls : idleCls
              }`}
            >
              <Ic className="relative z-[1] h-5 w-5" aria-hidden="true" />
              <span className="relative z-[1] text-[9px] font-medium leading-none tracking-wide">
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileBottomNav;
