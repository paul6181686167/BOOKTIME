import React, { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'react-hot-toast';
import { CheckIcon, MagnifyingGlassIcon } from '@heroicons/react/24/solid';
import ModalOverlay, { MODAL_Z } from '../common/ModalOverlay';
import { addOnboardingWorks, fetchOnboardingWorks } from '../../services/onboardingService';

/**
 * Écran d'accueil d'un compte vide : « Qu'as-tu déjà lu ? ».
 * Deux étapes (romans, puis romans graphiques) : l'utilisateur touche les
 * couvertures des oeuvres lues, elles sont ajoutées « terminées » à la fin.
 */

const STEPS = [
  { group: 'roman', label: 'Romans', title: 'Quels romans as-tu déjà lus ?' },
  { group: 'graphic_novel', label: 'Romans graphiques', title: 'Quels romans graphiques, BD et mangas as-tu déjà lus ?' },
];

const PLACEHOLDER_TONES = [
  'from-emerald-700 to-emerald-900',
  'from-teal-700 to-teal-900',
  'from-sky-700 to-sky-900',
  'from-violet-700 to-violet-900',
  'from-rose-700 to-rose-900',
  'from-amber-700 to-amber-900',
];

function toneFor(id) {
  let h = 0;
  for (let i = 0; i < id.length; i += 1) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return PLACEHOLDER_TONES[h % PLACEHOLDER_TONES.length];
}

const WorkTile = memo(function WorkTile({ work, selected, onToggle }) {
  const [imgFailed, setImgFailed] = useState(false);
  const showImage = work.cover_url && !imgFailed;

  return (
    <li>
      <button
        type="button"
        aria-pressed={selected}
        aria-label={`${work.title}, ${work.author}`}
        onClick={() => onToggle(work.id)}
        className={`group block w-full text-left rounded-xl bg-white dark:bg-gray-800 overflow-hidden border-2 transition-shadow ${
          selected
            ? 'border-green-600 dark:border-green-400 shadow-md'
            : 'border-transparent shadow-sm hover:shadow-md'
        }`}
      >
        <span className="relative block aspect-[2/3] w-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
          {showImage ? (
            <img
              src={work.cover_url}
              alt=""
              loading="lazy"
              decoding="async"
              onError={() => setImgFailed(true)}
              className={`h-full w-full object-cover transition-opacity ${selected ? 'opacity-80' : ''}`}
            />
          ) : (
            <span
              aria-hidden="true"
              className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${toneFor(work.id)} p-2 text-center text-xs font-semibold leading-snug text-white`}
            >
              {work.title}
            </span>
          )}
          {selected && (
            <span
              aria-hidden="true"
              className="absolute right-1.5 top-1.5 flex h-7 w-7 items-center justify-center rounded-full bg-green-600 text-white shadow ring-2 ring-white"
            >
              <CheckIcon className="h-4 w-4" />
            </span>
          )}
        </span>
        <span className="block px-2 pb-2 pt-1.5">
          <span className="block text-xs font-semibold leading-tight text-gray-900 dark:text-white line-clamp-2">
            {work.title}
          </span>
          <span className="mt-0.5 block text-tiny leading-tight text-gray-500 dark:text-gray-400 line-clamp-1">
            {work.author}
          </span>
        </span>
      </button>
    </li>
  );
});

export default function OnboardingLibraryPicker({ onFinish }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [catalog, setCatalog] = useState({}); // group -> { works, genres }
  const [loadError, setLoadError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(() => new Set());
  const [genre, setGenre] = useState('');
  const [query, setQuery] = useState('');
  const [saving, setSaving] = useState(false);
  const scrollRef = useRef(null);

  const step = STEPS[stepIndex];
  const isLast = stepIndex === STEPS.length - 1;
  const data = catalog[step.group];

  const load = useCallback(async (group) => {
    setLoading(true);
    setLoadError(false);
    try {
      const result = await fetchOnboardingWorks(group);
      setCatalog((prev) => ({ ...prev, [group]: result }));
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!catalog[step.group]) load(step.group);
    else setLoading(false);
    setGenre('');
    setQuery('');
    if (scrollRef.current) scrollRef.current.scrollTop = 0;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepIndex]);

  const toggle = useCallback((id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const sections = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    const matches = (w) =>
      !q || w.title.toLowerCase().includes(q) || w.author.toLowerCase().includes(q);
    return data.genres
      .filter((g) => !genre || g === genre)
      .map((g) => ({ genre: g, works: data.works.filter((w) => w.genre === g && matches(w)) }))
      .filter((s) => s.works.length > 0);
  }, [data, genre, query]);

  const countInStep = useMemo(
    () => (data ? data.works.filter((w) => selected.has(w.id)).length : 0),
    [data, selected]
  );

  const finish = async () => {
    if (saving) return;
    const ids = [...selected];
    if (ids.length === 0) {
      onFinish(0);
      return;
    }
    setSaving(true);
    try {
      const { added = 0 } = await addOnboardingWorks(ids);
      toast.success(
        added > 0
          ? `${added} livre${added > 1 ? 's' : ''} ajouté${added > 1 ? 's' : ''} à ta bibliothèque`
          : 'Ces livres sont déjà dans ta bibliothèque'
      );
      onFinish(added);
    } catch {
      toast.error("L'ajout a échoué. Vérifie ta connexion et réessaie.");
      setSaving(false);
    }
  };

  const next = () => {
    if (isLast) finish();
    else setStepIndex((i) => i + 1);
  };

  const total = selected.size;
  const primaryLabel = saving
    ? 'Ajout en cours…'
    : isLast
      ? total > 0
        ? `Terminer (${total})`
        : 'Terminer'
      : `Suivant : ${STEPS[stepIndex + 1].label}`;

  return (
    <ModalOverlay
      onClose={() => { if (selected.size === 0) onFinish(0); }}
      zIndex={MODAL_Z.panel}
      ariaLabel="Constitue ta bibliothèque"
      closeOnBackdrop={false}
      className="fixed inset-0 flex flex-col bg-honeycomb"
    >

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 pb-6 sm:px-6">
        <header className="pt-[max(1rem,env(safe-area-inset-top))] pb-3">
          <div className="mx-auto w-full max-w-6xl">
            <div className="flex items-start justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-green-800 dark:text-green-300">
                Étape {stepIndex + 1} sur {STEPS.length} · {step.label}
              </p>
              {total === 0 && (
                <button
                  type="button"
                  onClick={() => onFinish(0)}
                  className="shrink-0 rounded-lg px-2 py-1 text-xs font-medium text-gray-700 underline underline-offset-2 hover:text-gray-900 dark:text-gray-200"
                >
                  Ignorer et voir ma bibliothèque
                </button>
              )}
            </div>
            <h1 className="mt-1 text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">
              {step.title}
            </h1>
            <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
              Touche les couvertures des œuvres que tu as lues : elles seront ajoutées à ta
              bibliothèque comme « terminées ». Tu pourras tout modifier ensuite.
            </p>

            <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
              <div className="relative sm:w-72">
                <MagnifyingGlassIcon
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500"
                />
                <input
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  aria-label="Filtrer par titre ou auteur"
                  placeholder="Titre ou auteur…"
                  className="w-full rounded-full border border-gray-300 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                />
              </div>
              {data && data.genres.length > 1 && (
                <div
                  role="group"
                  aria-label="Genre"
                  className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0"
                >
                  {['', ...data.genres].map((g) => (
                    <button
                      key={g || 'tous'}
                      type="button"
                      aria-pressed={genre === g}
                      onClick={() => setGenre(g)}
                      className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                        genre === g
                          ? 'bg-green-700 text-white'
                          : 'bg-white text-gray-700 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      {g || 'Tous'}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </header>
        <div className="mx-auto w-full max-w-6xl">
          {loading && !data && (
            <p role="status" className="py-16 text-center text-sm text-gray-700 dark:text-gray-300">
              Chargement de la sélection…
            </p>
          )}

          {loadError && !data && (
            <div className="py-16 text-center">
              <p className="text-sm text-gray-800 dark:text-gray-200">
                La sélection n&apos;a pas pu être chargée.
              </p>
              <button
                type="button"
                onClick={() => load(step.group)}
                className="mt-3 rounded-lg bg-green-700 px-4 py-2 text-sm font-semibold text-white hover:bg-green-800"
              >
                Réessayer
              </button>
            </div>
          )}

          {data && sections.length === 0 && (
            <p className="py-16 text-center text-sm text-gray-700 dark:text-gray-300">
              Aucune œuvre ne correspond à « {query} ».
            </p>
          )}

          {sections.map((s) => (
            <section key={s.genre} className="mb-6" aria-labelledby={`onb-${stepIndex}-${s.genre}`}>
              <h2
                id={`onb-${stepIndex}-${s.genre}`}
                className="mb-2 text-base font-semibold text-green-800 dark:text-white"
              >
                {s.genre}
              </h2>
              <ul className="grid grid-cols-3 gap-2.5 sm:grid-cols-4 sm:gap-3 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7">
                {s.works.map((w) => (
                  <WorkTile key={w.id} work={w} selected={selected.has(w.id)} onToggle={toggle} />
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>

      <footer className="shrink-0 border-t border-green-900/10 bg-white/95 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 dark:border-white/10 dark:bg-gray-900/95 sm:px-6">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center gap-3">
          <p aria-live="polite" className="mr-auto text-sm font-medium text-gray-900 dark:text-white">
            {total === 0
              ? 'Aucune œuvre sélectionnée'
              : `${total} œuvre${total > 1 ? 's' : ''} sélectionnée${total > 1 ? 's' : ''}`}
            {stepIndex > 0 && total > countInStep && (
              <span className="ml-1 font-normal text-gray-600 dark:text-gray-300">
                ({countInStep} dans cette étape)
              </span>
            )}
          </p>
          {stepIndex > 0 && (
            <button
              type="button"
              onClick={() => setStepIndex((i) => i - 1)}
              disabled={saving}
              className="rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              Retour
            </button>
          )}
          <button
            type="button"
            onClick={next}
            disabled={saving}
            className="rounded-lg bg-green-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-green-800 disabled:opacity-60"
          >
            {primaryLabel}
          </button>
        </div>
      </footer>
    </ModalOverlay>
  );
}
