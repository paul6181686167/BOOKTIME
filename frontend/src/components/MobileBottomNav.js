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

/** Barre d’onglets flottante oblongue — distincte de la barre système Android. */
const MobileBottomNav = ({ activeTab, onTabChange }) => {
  const { isVoid } = useTheme();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 pointer-events-none safe-area-bottom">
      <div className="px-5 pb-3 pt-1">
        <div
          className={`pointer-events-auto mx-auto flex h-[3.35rem] max-w-sm items-stretch overflow-hidden rounded-full backdrop-blur-2xl ${
            isVoid
              ? 'border border-white/[0.08] bg-[#121212]/92 shadow-[0_12px_40px_rgba(0,0,0,0.65)]'
              : 'border border-booktime-800/20 bg-white/90 dark:bg-gray-900/90 shadow-lg dark:border-white/10'
          }`}
        >
          {NAV_ITEMS.map(({ id, label, Icon, IconActive }) => {
            const isActive = activeTab === id;
            const Ic = isActive ? IconActive : Icon;
            const activeCls = isVoid
              ? 'text-[#4ade80]'
              : 'text-booktime-600 dark:text-booktime-400';
            const idleCls = isVoid
              ? 'text-white/35 active:text-white/70'
              : 'text-gray-400 dark:text-gray-500 active:text-gray-600';
            return (
              <button
                key={id}
                type="button"
                onClick={() => onTabChange(id)}
                aria-label={label}
                aria-current={isActive ? 'page' : undefined}
                className={`relative flex flex-1 flex-col items-center justify-center gap-0.5 transition-all duration-200 ${
                  isActive ? activeCls : idleCls
                }`}
              >
                {isActive && (
                  <span
                    className={`absolute inset-1.5 rounded-full ${
                      isVoid
                        ? 'bg-[#4ade80]/12 shadow-[inset_0_0_20px_rgba(74,222,128,0.08)]'
                        : 'bg-booktime-50 dark:bg-booktime-900/40'
                    }`}
                  />
                )}
                <Ic
                  className={`relative z-[1] h-5 w-5 ${
                    isActive && isVoid ? 'drop-shadow-[0_0_8px_rgba(74,222,128,0.45)]' : ''
                  }`}
                  aria-hidden="true"
                />
                <span className="relative z-[1] text-[9px] font-medium leading-none tracking-wide">
                  {label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default MobileBottomNav;
