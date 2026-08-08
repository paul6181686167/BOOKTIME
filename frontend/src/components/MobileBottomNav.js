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

const NAV_ITEMS = [
  { id: 'home',            label: 'Biblio',      Icon: HomeIcon,          IconActive: HomeIconSolid },
  { id: 'upcoming',        label: 'À venir',     Icon: CalendarDaysIcon,  IconActive: CalendarIconSolid },
  { id: 'recommendations', label: 'Pour toi',    Icon: BookOpenIcon,      IconActive: BookIconSolid },
  { id: 'profile',         label: 'Profil',      Icon: UserCircleIcon,    IconActive: UserIconSolid },
];

const MobileBottomNav = ({ activeTab, onTabChange }) => {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl border-t border-booktime-mist/55 dark:border-booktime-800/50 safe-area-bottom">
      <div className="flex items-stretch h-14">
        {NAV_ITEMS.map(({ id, label, Icon, IconActive }) => {
          const isActive = activeTab === id;
          const Ic = isActive ? IconActive : Icon;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onTabChange(id)}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
              className={`relative flex-1 flex flex-col items-center justify-center gap-0.5 transition-colors duration-150 ${
                isActive
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-400 dark:text-gray-500 active:text-green-600'
              }`}
            >
              {isActive && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-8 bg-green-500 rounded-b-full" />
              )}
              <Ic className="w-5 h-5" aria-hidden="true" />
              <span className="text-[11px] font-medium leading-none">{label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileBottomNav;
