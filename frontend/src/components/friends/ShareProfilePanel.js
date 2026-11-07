import React, { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import friendsService from '../../services/friendsService';
import { buildFriendLink, formatFriendCode } from '../../utils/friendLink';
import { copyLink, shareLink } from '../../utils/shareProfile';

/** Carte « Inviter des amis » : QR code, code d'ami, lien et bouton Partager. */
export default function ShareProfilePanel() {
  const [code, setCode] = useState('');
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [qr, setQr] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await friendsService.myCode();
      setCode(data.code);
      setUsername(data.username || '');
      setDisplayName(data.display_name || '');
      const { toDataURL } = await import('qrcode');
      setQr(
        await toDataURL(buildFriendLink(data.code), {
          margin: 1,
          width: 360,
          errorCorrectionLevel: 'M',
          color: { dark: '#14532d', light: '#ffffff' },
        })
      );
    } catch (err) {
      setError(err.message || 'Impossible de créer ton code');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const link = code ? buildFriendLink(code) : '';
  const name = displayName || (username ? `@${username}` : '');
  const shareText = name
    ? `Je suis ${name} sur Booktime. Ajoute-moi en un clic pour échanger nos lectures :`
    : 'Retrouve-moi sur Booktime. Ajoute-moi en un clic pour échanger nos lectures :';

  const onShare = async () => {
    const result = await shareLink({ title: 'Mon profil Booktime', text: shareText, url: link });
    if (result === 'copied') toast.success('Lien copié, colle-le dans ta conversation');
    else if (result === 'failed') toast.error('Partage impossible');
  };

  const onCopy = async () => {
    try {
      const ok = await copyLink(link);
      if (ok) toast.success('Lien copié');
      else toast.error('Copie impossible');
    } catch (_) {
      toast.error('Copie impossible');
    }
  };

  if (loading) {
    return <div className="h-64 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-amber-300 p-4 text-center space-y-2">
        <p className="text-sm text-amber-700 dark:text-amber-300">{error}</p>
        <button
          type="button"
          onClick={load}
          className="px-3 py-1.5 rounded-lg border border-green-600 text-green-700 dark:text-green-400 text-sm"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl bg-white dark:bg-gray-700/50 border border-green-200 dark:border-green-800 p-4 text-center space-y-3"
      data-testid="share-profile-panel"
    >
      <p className="text-sm text-gray-600 dark:text-gray-300">
        Fais scanner ce QR code ou envoie ton lien : la personne te retrouve en un geste.
      </p>
      {qr && (
        <img
          src={qr}
          alt="QR code de ton profil Booktime"
          className="mx-auto w-48 h-48 rounded-lg border border-gray-200"
        />
      )}
      <div>
        {username ? (
          <p className="text-base font-semibold text-gray-900 dark:text-white">@{username}</p>
        ) : null}
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Code ami <span className="font-mono tracking-wider">{formatFriendCode(code)}</span>
        </p>
        {!username && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Choisis un pseudo dans Paramètres pour être trouvé par son nom.
          </p>
        )}
      </div>
      <div className="flex gap-2 justify-center">
        <button
          type="button"
          onClick={onShare}
          className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium"
        >
          Partager mon profil
        </button>
        <button
          type="button"
          onClick={onCopy}
          className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 text-sm font-medium"
        >
          Copier le lien
        </button>
      </div>
    </div>
  );
}
