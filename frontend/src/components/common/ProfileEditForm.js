import React, { useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import AuthService from '../../services/authService';
import { fileToAvatarDataUrl } from '../../utils/avatarImage';
import { UserAvatar, MAX_BIO, MAX_DISPLAY_NAME } from './ProfileIdentityCard';

export const MIN_USERNAME = 3;
export const MAX_USERNAME = 20;

/** Pseudo saisi -> minuscules, sans « @ » ni espaces. */
export function normalizeHandleInput(raw) {
  return String(raw || '').trim().replace(/^@+/, '').toLowerCase();
}

/** Message d'erreur si le pseudo est invalide, '' sinon (un pseudo vide est permis). */
export function validateHandle(handle) {
  if (!handle) return '';
  if (handle.length < MIN_USERNAME || handle.length > MAX_USERNAME) {
    return `Entre ${MIN_USERNAME} et ${MAX_USERNAME} caractères.`;
  }
  if (!/^[a-z0-9][a-z0-9_.]*$/.test(handle)) {
    return 'Lettres sans accent, chiffres, « _ » et « . » uniquement.';
  }
  return '';
}

/** Champs modifiés par rapport au profil courant ({} si rien n'a changé). */
export function buildProfilePatch(user, { name, bio, avatar, username }) {
  const patch = {};
  if (username !== undefined) {
    const nextHandle = normalizeHandleInput(username);
    if (nextHandle !== (user?.username || '')) patch.username = nextHandle;
  }
  const nextName = String(name || '').trim();
  const nextBio = String(bio || '').trim();
  if (nextName !== (user?.display_name || '')) patch.display_name = nextName;
  if (nextBio !== (user?.bio || '')) patch.bio = nextBio;
  if (avatar !== undefined) patch.avatar_url = avatar;
  return patch;
}

/**
 * Formulaire de modification du profil (photo, nom, biographie), affiché dans les paramètres.
 * L'enregistrement est optimiste : le profil change et le formulaire se ferme tout de suite,
 * l'envoi se termine en arrière-plan et le profil est rétabli s'il échoue.
 */
export default function ProfileEditForm({ onDone }) {
  const { user, updateUser } = useAuth();
  const authService = useRef(new AuthService()).current;
  const fileRef = useRef(null);

  const [name, setName] = useState(user?.display_name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [handle, setHandle] = useState(user?.username || '');
  const handleError = validateHandle(normalizeHandleInput(handle));
  // undefined = inchangée, '' = retirée, sinon nouvelle photo (data URL)
  const [avatar, setAvatar] = useState(undefined);

  const shownAvatar = avatar !== undefined ? avatar : user?.avatar_url || '';

  const handlePickFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    try {
      setAvatar(await fileToAvatarDataUrl(file));
    } catch (err) {
      toast.error(err?.message || "Impossible d'utiliser cette image");
    }
  };

  const handleSave = () => {
    if (handleError) {
      toast.error(`Pseudo invalide : ${handleError}`);
      return;
    }
    const patch = buildProfilePatch(user, { name, bio, avatar, username: handle });
    if (Object.keys(patch).length === 0) {
      onDone?.();
      return;
    }

    const previous = {
      display_name: user?.display_name || '',
      bio: user?.bio || '',
      avatar_url: user?.avatar_url || '',
    };
    if ('username' in patch) previous.username = user?.username || '';
    updateUser(patch);
    onDone?.();

    const toastId = toast.loading('Enregistrement du profil…');
    authService.updateProfile(patch).then((res) => {
      if (res.success) {
        updateUser(res.profile);
        toast.success('Profil enregistré', { id: toastId });
      } else {
        updateUser(previous);
        toast.error(`Profil non enregistré : ${res.error || 'erreur inconnue'}`, { id: toastId });
      }
    });
  };

  return (
    <div className="space-y-4">
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
              onClick={() => setAvatar('')}
              className="px-3 py-1.5 rounded-lg text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
            >
              Retirer la photo
            </button>
          )}
        </div>
        <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handlePickFile} />
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
          htmlFor="profile-username"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
        >
          Pseudo
        </label>
        <div className="flex items-center gap-1">
          <span className="text-gray-500 dark:text-gray-400">@</span>
          <input
            id="profile-username"
            type="text"
            value={handle}
            maxLength={MAX_USERNAME + 1}
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="ex. lectrice_sf"
            aria-invalid={handleError ? 'true' : 'false'}
            className="flex-1 min-w-0 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
        {handleError ? (
          <p className="text-xs text-red-600 dark:text-red-400 mt-1">{handleError}</p>
        ) : (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Unique. Tes amis te trouvent avec @pseudo dans la recherche.
          </p>
        )}
      </div>

      <div>
        <label htmlFor="profile-bio" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
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
          className="flex-1 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium"
        >
          Enregistrer
        </button>
        <button
          type="button"
          onClick={() => onDone?.()}
          className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-sm font-medium"
        >
          Annuler
        </button>
      </div>
    </div>
  );
}
