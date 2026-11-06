/** Taille (en pixels) du carré enregistré pour la photo de profil. */
export const AVATAR_SIZE = 256;

/** Initiales affichées quand il n'y a pas de photo : nom affiché, sinon début de l'email. */
export function avatarInitials(user) {
  const name = String(user?.display_name || '').trim();
  if (name) {
    const parts = name.split(/\s+/).filter(Boolean);
    const letters = parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : parts[0].slice(0, 2);
    return letters.toUpperCase();
  }
  const mail = String(user?.email || '').trim();
  return (mail.slice(0, 2) || '?').toUpperCase();
}

/**
 * Transforme une image choisie en carré AVATAR_SIZE x AVATAR_SIZE (recadrage centré)
 * encodé en JPEG : quelques dizaines de Ko, adapté au stockage sur le compte.
 */
export function fileToAvatarDataUrl(file, size = AVATAR_SIZE) {
  return new Promise((resolve, reject) => {
    if (!file || !String(file.type || '').startsWith('image/')) {
      reject(new Error("Ce fichier n'est pas une image."));
      return;
    }
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      try {
        const side = Math.min(img.naturalWidth, img.naturalHeight);
        if (!side) throw new Error('Image illisible.');
        const sx = (img.naturalWidth - side) / 2;
        const sy = (img.naturalHeight - side) / 2;
        const canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext('2d');
        // Fond blanc : les PNG transparents ne deviennent pas noirs en JPEG
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, size, size);
        ctx.drawImage(img, sx, sy, side, side, 0, 0, size, size);
        resolve(canvas.toDataURL('image/jpeg', 0.85));
      } catch (err) {
        reject(err);
      } finally {
        URL.revokeObjectURL(url);
      }
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Impossible de lire l'image."));
    };
    img.src = url;
  });
}
