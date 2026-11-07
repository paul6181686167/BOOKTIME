import React, { useEffect, useRef } from 'react';
import { useAuth } from '../../hooks/useAuth';
import AuthService from '../../services/authService';
import { avatarInitials } from '../../utils/avatarImage';

export const MAX_DISPLAY_NAME = 40;
export const MAX_BIO = 300;

/** Pastille ronde : photo si elle existe, sinon initiales. */
export function UserAvatar({ user, src, size = 56, className = '' }) {
  const url = src !== undefined ? src : user?.avatar_url;
  const style = { width: size, height: size, fontSize: Math.round(size * 0.38) };
  if (url) {
    return (
      <img
        src={url}
        alt=""
        style={style}
        className={`rounded-full object-cover shrink-0 bg-gray-200 dark:bg-gray-700 ${className}`}
      />
    );
  }
  return (
    <div
      style={style}
      className={`rounded-full shrink-0 flex items-center justify-center font-bold bg-green-600 text-white ${className}`}
      aria-hidden
    >
      {avatarInitials(user)}
    </div>
  );
}

/**
 * Photo de profil, nom et biographie de l'utilisateur (lecture seule).
 * La modification se fait uniquement depuis les paramètres.
 */
export default function ProfileIdentityCard() {
  const { user, updateUser } = useAuth();
  const authService = useRef(new AuthService()).current;

  // Récupère nom, biographie et photo depuis le serveur (autre appareil, nouvelle session)
  useEffect(() => {
    let cancelled = false;
    authService.fetchProfile().then((res) => {
      if (!cancelled && res.success) updateUser(res.profile);
    });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const title = user?.display_name || user?.email || '';
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
      <div className="flex items-start gap-3">
        <UserAvatar user={user} size={64} />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white truncate">{title}</p>
          {user?.display_name && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email}</p>
          )}
          {user?.bio ? (
            <p className="mt-1.5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line break-words">
              {user.bio}
            </p>
          ) : (
            <p className="mt-1.5 text-sm text-gray-400 dark:text-gray-500 italic">
              Aucune biographie pour le moment.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
