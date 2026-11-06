import React, { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import AuthService from '../../services/authService';
import { avatarInitials, fileToAvatarDataUrl } from '../../utils/avatarImage';

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

/** Photo de profil, nom et biographie de l'utilisateur, avec édition. */
export default function ProfileIdentityCard() {
  const { user, updateUser } = useAuth();
  const authService = useRef(new AuthService()).current;
  const fileRef = useRef(null);

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [bio, setBio] = useState('');
  // undefined = inchangée, '' = retirée, sinon nouvelle photo (data URL)
  const [draftAvatar, setDraftAvatar] = useState(undefined);

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

  const startEdit = () => {
    setName(user?.display_name || '');
    setBio(user?.bio || '');
    setDraftAvatar(undefined);
    setEditing(true);
  };

  const cancelEdit = () => {
    setEditing(false);
    setDraftAvatar(undefined);
  };

  const handlePickFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    try {
      setDraftAvatar(await fileToAvatarDataUrl(file));
    } catch (err) {
      toast.error(err?.message || "Impossible d'utiliser cette image");
    }
  };

  const handleSave = async () => {
    const patch = {};
    const nextName = name.trim();
    const nextBio = bio.trim();
    if (nextName !== (user?.display_name || '')) patch.display_name = nextName;
    if (nextBio !== (user?.bio || '')) patch.bio = nextBio;
    if (draftAvatar !== undefined) patch.avatar_url = draftAvatar;

    if (Object.keys(patch).length === 0) {
      setEditing(false);
      return;
    }
    setSaving(true);
    const res = await authService.updateProfile(patch);
    setSaving(false);
    if (!res.success) {
      toast.error(res.error || 'Enregistrement impossible');
      return;
    }
    updateUser(res.profile);
    setEditing(false);
    setDraftAvatar(undefined);
    toast.success('Profil enregistré');
  };

  const shownAvatar = draftAvatar !== undefined ? draftAvatar : user?.avatar_url || '';

  if (!editing) {
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
        <button
          type="button"
          onClick={startEdit}
          className="mt-3 w-full py-2 rounded-lg border border-green-600 text-green-700 dark:text-green-400 text-sm font-medium hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
        >
          Modifier mon profil
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4 space-y-4">
      <div className="flex items-center gap-4">
        <UserAvatar user={{ ...user, display_name: name }} src={shownAvatar} size={80} />
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium"
          >
            {shownAvatar ? 'Changer la photo' : 'Ajouter une photo'}
          </button>
          {shownAvatar && (
            <button
              type="button"
              onClick={() => setDraftAvatar('')}
              className="px-3 py-1.5 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Retirer la photo
            </button>
          )}
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handlePickFile}
        />
      </div>

      <div>
        <label
          htmlFor="profile-display-name"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          Nom affiché
        </label>
        <input
          id="profile-display-name"
          type="text"
          value={name}
          maxLength={MAX_DISPLAY_NAME}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ton prénom ou un pseudo"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
        />
      </div>

      <div>
        <label
          htmlFor="profile-bio"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          Biographie
        </label>
        <textarea
          id="profile-bio"
          value={bio}
          maxLength={MAX_BIO}
          rows={4}
          onChange={(e) => setBio(e.target.value)}
          placeholder="Parle de tes goûts de lecture"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
        />
        <p className="text-right text-[11px] text-gray-400 mt-0.5">
          {bio.length} / {MAX_BIO}
        </p>
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="flex-1 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium disabled:opacity-50"
        >
          {saving ? 'Enregistrement…' : 'Enregistrer'}
        </button>
        <button
          type="button"
          onClick={cancelEdit}
          disabled={saving}
          className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-sm font-medium disabled:opacity-50"
        >
          Annuler
        </button>
      </div>
    </div>
  );
}
