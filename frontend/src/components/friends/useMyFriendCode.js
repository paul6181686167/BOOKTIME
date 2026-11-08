import { useCallback, useEffect, useState } from 'react';
import friendsService from '../../services/friendsService';
import { buildFriendLink } from '../../utils/friendLink';

/** QR code du lien d'ami, en SVG (aucune dépendance au canvas : fonctionne partout). */
async function buildQrSrc(link) {
  const QRCode = await import('qrcode');
  const toString = QRCode.toString || QRCode.default?.toString;
  const svg = await toString(link, {
    type: 'svg',
    margin: 1,
    errorCorrectionLevel: 'M',
    color: { dark: '#14532d', light: '#ffffff' },
  });
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

/**
 * Code d'ami de l'utilisateur connecté, son lien et son QR code.
 * Le QR code est facultatif : si sa fabrication échoue, le code et le lien restent utilisables.
 */
export default function useMyFriendCode({ withQr = false } = {}) {
  const [state, setState] = useState({
    loading: true,
    error: '',
    code: '',
    username: '',
    displayName: '',
    link: '',
    qrSrc: '',
    qrFailed: false,
  });

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: '', qrFailed: false }));
    try {
      const data = await friendsService.myCode();
      const link = buildFriendLink(data.code);
      let qrSrc = '';
      let qrFailed = false;
      if (withQr) {
        try {
          qrSrc = await buildQrSrc(link);
        } catch (_) {
          qrFailed = true;
        }
      }
      setState({
        loading: false,
        error: '',
        code: data.code,
        username: data.username || '',
        displayName: data.display_name || '',
        link,
        qrSrc,
        qrFailed,
      });
    } catch (err) {
      setState((s) => ({
        ...s,
        loading: false,
        error: err?.message || 'Impossible de créer ton code',
      }));
    }
  }, [withQr]);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, reload: load };
}
