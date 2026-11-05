/** Onglets principaux de la barre bas mobile (ordre = direction du glissement). */
export const PRIMARY_TABS = [
  { id: 'home', path: '/' },
  { id: 'upcoming', path: '/upcoming' },
  { id: 'recommendations', path: '/recommendations' },
  { id: 'profile', path: '/profile' },
];

export function pathToPrimaryTab(pathname = '') {
  if (pathname.startsWith('/upcoming')) return 'upcoming';
  if (pathname.startsWith('/recommendations')) return 'recommendations';
  if (pathname.startsWith('/profile')) return 'profile';
  if (pathname === '/' || pathname === '') return 'home';
  return null;
}

export function primaryTabToPath(tabId) {
  return PRIMARY_TABS.find((t) => t.id === tabId)?.path || '/';
}

export function primaryTabIndex(pathnameOrTab) {
  const tab =
    typeof pathnameOrTab === 'string' && pathnameOrTab.startsWith('/')
      ? pathToPrimaryTab(pathnameOrTab)
      : pathnameOrTab;
  const idx = PRIMARY_TABS.findIndex((t) => t.id === tab);
  return idx;
}
