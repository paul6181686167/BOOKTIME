/**
 * Téléchargement de fichiers, web et Android.
 *
 * La WebView Android ignore l'attribut `download` d'un lien pointant vers une
 * URL blob : sur mobile, on écrit le fichier dans le dossier Documents via
 * Capacitor puis on ouvre la feuille de partage pour que l'utilisateur le
 * range où il veut.
 */
import { isNativeApp } from './platform';

const blobToBase64 = (blob) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => {
      const result = String(reader.result || '');
      resolve(result.slice(result.indexOf(',') + 1));
    };
    reader.readAsDataURL(blob);
  });

const downloadInBrowser = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

/**
 * @returns {Promise<{location: 'browser'|'device'}>}
 */
export const saveBlobAsFile = async (blob, filename) => {
  if (!isNativeApp()) {
    downloadInBrowser(blob, filename);
    return { location: 'browser' };
  }

  const [{ Filesystem, Directory }, { Share }] = await Promise.all([
    import('@capacitor/filesystem'),
    import('@capacitor/share'),
  ]);

  // Sans `encoding`, Filesystem attend du base64 et écrit un fichier binaire.
  const { uri } = await Filesystem.writeFile({
    path: filename,
    data: await blobToBase64(blob),
    directory: Directory.Documents,
    recursive: true,
  });

  try {
    await Share.share({ title: filename, url: uri });
  } catch {
    // L'utilisateur a annulé le partage : le fichier reste dans Documents.
  }
  return { location: 'device' };
};

export const saveTextAsFile = (text, filename, mimeType = 'application/json') =>
  saveBlobAsFile(new Blob([text], { type: mimeType }), filename);

export default { saveBlobAsFile, saveTextAsFile };
