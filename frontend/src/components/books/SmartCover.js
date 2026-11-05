/**
 * Couverture Booktime (même pipeline que la bibliothèque).
 * Fallbacks OL / proxy / recherche navigateur via resolveCoverForVisibleItem.
 */
import React, { useEffect, useMemo, useState } from 'react';
import {
  coverCanProxyFallback,
  coverFallbackCandidates,
  coverImgSrc,
  isBlankOrPlaceholderCover,
  isGoogleBooksCoverUrl,
  isLikelyPhotoNotCover,
  isUsableCoverUrl,
  normalizeCoverUrl,
} from '../../utils/helpers';
import { resolveCoverForVisibleItem } from '../../services/libraryMetaEnrichment';

export const CARD_SHELL =
  'h-full bg-transparent rounded-xl relative transition-transform duration-200';

export const COVER_FRAME =
  'aspect-[2/3] rounded-xl bg-[#141414] relative overflow-hidden shadow-[0_8px_24px_rgba(0,0,0,0.55)]';

export const COVER_IMAGE =
  'h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.05]';

export const PILL = 'backdrop-blur-sm ring-1 ring-white/10';

/** Fine bande claire sur le contour — par-dessus l’image pour la faire ressortir. */
export const COVER_RIM =
  'pointer-events-none absolute inset-0 z-[1] rounded-xl shadow-[inset_0_0_0_1px_rgba(255,255,255,0.28)]';

const PLACEHOLDER_TINTS = [
  'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
  'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200',
  'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
  'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
  'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200',
  'bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-200',
];

const INITIALS_SKIPPED = new Set([
  'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'the', 'a', 'an', 'of', 'and', 'et',
]);

const initialsFor = (text) => {
  const words = (text || '')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!words.length) return '?';
  const kept = words.filter((word) => !INITIALS_SKIPPED.has(word.toLowerCase()));
  return (kept.length ? kept : words)
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join('');
};

const tintFor = (text) => {
  let hash = 0;
  for (let i = 0; i < (text || '').length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) % 9973;
  }
  return PLACEHOLDER_TINTS[hash % PLACEHOLDER_TINTS.length];
};

export const CoverPlaceholder = ({ text, hidden = false }) => (
  <div
    className={`${hidden ? 'hidden ' : ''}absolute inset-0 flex items-center justify-center ${tintFor(text)}`}
  >
    <span className="font-display text-xl font-semibold tracking-tight sm:text-3xl">
      {initialsFor(text)}
    </span>
  </div>
);

export const CoverRim = () => <div aria-hidden className={COVER_RIM} />;

export const CoverScrim = () => (
  <>
    <CoverRim />
    <div className="pointer-events-none absolute inset-x-0 bottom-0 z-[1] h-2/5 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
  </>
);

/**
 * Image de couverture.
 * Google Books en dernier recours (souvent « image not available ») — mais on
 * l'affiche quand c'est la seule source (sinon vignette vide alors que la modale a l'image).
 */
const SmartCover = ({ item, alt, primarySrc, onCoverFound, priority = false }) => {
  const candidates = useMemo(() => {
    const list = coverFallbackCandidates(item);
    if (primarySrc) {
      const n = normalizeCoverUrl(primarySrc) || primarySrc;
      if (n && !list.includes(n) && !list.includes(primarySrc)) {
        if (isGoogleBooksCoverUrl(n) || isGoogleBooksCoverUrl(primarySrc)) {
          list.push(n);
        } else {
          list.unshift(n);
        }
      }
    }
    // Si cover_url brut existe mais a été écarté par isUsableCoverUrl (ex. archive.org),
    // le tenter quand même — la modale l'affiche tel quel.
    const raw = item?.cover_url || item?.cover_image_url;
    if (raw && String(raw).trim()) {
      const rawS = String(raw).trim();
      if (!list.includes(rawS) && !list.some((u) => u === normalizeCoverUrl(rawS))) {
        if (isGoogleBooksCoverUrl(rawS)) list.push(rawS);
        else list.push(rawS);
      }
    }
    const trusted = list.filter((u) => u && !isGoogleBooksCoverUrl(u));
    const google = list.filter((u) => u && isGoogleBooksCoverUrl(u));
    return [...trusted, ...google];
  }, [item, primarySrc]);
  const [idx, setIdx] = useState(0);
  const [fetched, setFetched] = useState(null);
  const [searchTried, setSearchTried] = useState(false);
  const [searching, setSearching] = useState(false);
  const [proxyFallback, setProxyFallback] = useState(false);

  useEffect(() => {
    setIdx(0);
    setFetched(null);
    setSearchTried(false);
    setSearching(false);
    setProxyFallback(false);
  }, [item?.id, item?.ol_key, primarySrc, candidates[0]]);

  const exhausted = !fetched && (candidates.length === 0 || idx >= candidates.length);

  useEffect(() => {
    if (!exhausted || fetched || searchTried) return;
    let cancelled = false;
    setSearchTried(true);
    setSearching(true);
    const safety = setTimeout(() => {
      if (!cancelled) setSearching(false);
    }, 28000);
    resolveCoverForVisibleItem(item)
      .then((url) => {
        if (cancelled || !url) return;
        const cover = isGoogleBooksCoverUrl(url)
          ? url
          : normalizeCoverUrl(url) || url;
        if (isUsableCoverUrl(cover) || isGoogleBooksCoverUrl(cover)) {
          setFetched(cover);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setSearching(false);
        clearTimeout(safety);
      });
    return () => {
      cancelled = true;
      clearTimeout(safety);
    };
  }, [item, exhausted, fetched, searchTried]);

  const src = fetched || (idx < candidates.length ? candidates[idx] : null);

  useEffect(() => {
    setProxyFallback(false);
  }, [src]);

  if (!src) {
    if (searching || (!searchTried && exhausted)) {
      return (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse" />
      );
    }
    return <CoverPlaceholder text={alt} />;
  }

  const imgSrc = coverImgSrc(src, { forceProxy: proxyFallback });
  const needsPlaceholderCheck = isGoogleBooksCoverUrl(src);
  const isWikiSrc = /upload\.wikimedia\.org/i.test(src || '');

  const failCurrent = () => {
    if (!proxyFallback && coverCanProxyFallback(src)) {
      setProxyFallback(true);
      return;
    }
    setProxyFallback(false);
    if (fetched) {
      setFetched(null);
      setSearchTried(false);
      return;
    }
    setIdx((i) => i + 1);
  };

  return (
    <img
      src={imgSrc}
      alt={alt}
      width={160}
      height={240}
      sizes="(max-width: 640px) 33vw, 160px"
      loading={priority ? 'eager' : 'lazy'}
      decoding="async"
      {...(priority ? { fetchpriority: 'high' } : {})}
      crossOrigin={needsPlaceholderCheck ? 'anonymous' : undefined}
      referrerPolicy="no-referrer"
      className={COVER_IMAGE}
      onLoad={(e) => {
        const img = e.currentTarget;
        if (isWikiSrc && isLikelyPhotoNotCover(img)) {
          failCurrent();
          return;
        }
        if (needsPlaceholderCheck && isBlankOrPlaceholderCover(img)) {
          failCurrent();
          return;
        }
        // Persister une cover manquante / différente — pas de rappel si déjà connue
        if (typeof onCoverFound === 'function') {
          const resolved = fetched || src;
          const existing = item?.cover_url || item?.cover_image_url;
          if (resolved && existing !== resolved) {
            onCoverFound(item, resolved);
          }
        }
      }}
      onError={failCurrent}
    />
  );
};

export default SmartCover;
