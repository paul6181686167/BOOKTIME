import React, { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import AuthService from '../../services/authService';
import { READING_SPEEDS } from '../../utils/readingTime';
import ProfileEditForm from './ProfileEditForm';

const THEMES = [
  { id: 'light', label: 'Clair' },
  { id: 'dark', label: 'Foncé' },
  { id: 'void', label: 'Très foncé' },
];

const PRIVACY_OPTIONS = [
  {
    key: 'discoverable',
    label: 'Apparaître dans la recherche',
    help: 'Les autres lecteurs peuvent te trouver par ton nom ou ton email pour t’ajouter en ami.',
  },
  {
    key: 'share_favorites',
    label: 'Montrer mes livres préférés',
    help: 'Visibles par tes amis sur ton profil.',
  },
  {
    key: 'share_reviews',
    label: 'Montrer mes notes et avis',
    help: 'Visibles par tes amis sur ton profil.',
  },
  {
    key: 'share_reading',
    label: 'Montrer mes lectures en cours',
    help: 'Visibles par tes amis sur ton profil.',
  },
];

const DATA_LINKS = [
  { event: 'openExportImport', label: 'Export et import de ma bibliothèque' },
  { event: 'openAdvancedRecommendations', label: 'Recommandations avancées' },
  { event: 'openIntegrations', label: 'Intégrations' },
];

function Section({ title, children }) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h3>
      {children}
    </section>
  );
}

function Switch({ checked, onChange, disabled, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative shrink-0 w-11 h-6 rounded-full transition-colors disabled:opacity-50 ${
        checked ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
          checked ? 'translate-x-5' : ''
        }`}
      />
    </button>
  );
}

function ChoiceRow({ options, value, onSelect, getKey, getLabel, isActive }) {
  return (
    <div className="grid grid-cols-3 gap-1.5">
      {options.map((opt) => (
        <button
          key={getKey(opt)}
          type="button"
          onClick={() => onSelect(opt)}
          className={`px-2 py-2 rounded-lg text-xs font-medium transition-colors ${
            isActive(opt, value)
              ? 'bg-green-600 text-white'
              : 'bg-gray-50 dark:bg-gray-700 text-gray-600 dark:text-gray-300 ring-1 ring-gray-200 dark:ring-gray-600'
          }`}
        >
          {getLabel(opt)}
        </button>
      ))}
    </div>
  );
}

function PasswordForm() {
  const authService = useRef(new AuthService()).current;
  const [open, setOpen] = useState(false);
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [saving, setSaving] = useState(false);

  const reset = () => {
    setOpen(false);
    setCurrent('');
    setNext('');
    setConfirm('');
  };

  const submit = async (e) => {
    e.preventDefault();
    if (next.length < 8) {
      toast.error('Le nouveau mot de passe doit faire au moins 8 caractères');
      return;
    }
    if (next !== confirm) {
      toast.error('La confirmation ne correspond pas');
      return;
    }
    setSaving(true);
    const res = await authService.changePassword(current, next);
    setSaving(false);
    if (!res.success) {
      toast.error(res.error || 'Changement impossible');
      return;
    }
    toast.success('Mot de passe modifié');
    reset();
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="w-full py-2.5 rounded-lg bg-gray-50 dark:bg-gray-700 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-600"
      >
        Changer mon mot de passe
      </button>
    );
  }

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500';

  return (
    <form onSubmit={submit} className="space-y-2">
      <input
        type="password"
        value={current}
        onChange={(e) => setCurrent(e.target.value)}
        placeholder="Mot de passe actuel"
        aria-label="Mot de passe actuel"
        autoComplete="current-password"
        className={inputClass}
      />
      <input
        type="password"
        value={next}
        onChange={(e) => setNext(e.target.value)}
        placeholder="Nouveau mot de passe (8 caractères minimum)"
        aria-label="Nouveau mot de passe"
        autoComplete="new-password"
        className={inputClass}
      />
      <input
        type="password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        placeholder="Confirmer le nouveau mot de passe"
        aria-label="Confirmer le nouveau mot de passe"
        autoComplete="new-password"
        className={inputClass}
      />
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving || !current || !next || !confirm}
          className="flex-1 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium disabled:opacity-40"
        >
          {saving ? 'Enregistrement…' : 'Enregistrer'}
        </button>
        <button
          type="button"
          onClick={reset}
          disabled={saving}
          className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-sm"
        >
          Annuler
        </button>
      </div>
    </form>
  );
}

/** Paramètres du profil : compte, confidentialité, lecture, apparence, données. */
export default function ProfileSettings({
  user,
  theme,
  setTheme,
  readingWpm,
  onChangeWpm,
  onTriggerEvent,
  onLogout,
  onDeleteAccount,
}) {
  const authService = useRef(new AuthService()).current;
  const navigate = useNavigate();
  const [settings, setSettings] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [savingKey, setSavingKey] = useState(null);

  useEffect(() => {
    let cancelled = false;
    authService.fetchSettings().then((res) => {
      if (cancelled) return;
      setIsAdmin(res.success && res.isAdmin === true);
      // En cas d'échec réseau, on affiche les valeurs par défaut (tout activé)
      setSettings(
        res.success
          ? res.settings
          : { discoverable: true, share_favorites: true, share_reviews: true, share_reading: true }
      );
    });
    return () => {
      cancelled = true;
    };
  }, [authService]);

  const togglePrivacy = async (key, value) => {
    const previous = settings;
    setSettings((s) => ({ ...s, [key]: value }));
    setSavingKey(key);
    const res = await authService.updateSettings({ [key]: value });
    setSavingKey(null);
    if (!res.success) {
      setSettings(previous);
      toast.error(res.error || 'Réglage non enregistré');
    }
  };

  return (
    <div className="space-y-4 animate-fadeIn">
      <Section title="Compte">
        <p className="text-sm text-gray-600 dark:text-gray-400 break-all">{user?.email}</p>
        {editingProfile ? (
          <ProfileEditForm onDone={() => setEditingProfile(false)} />
        ) : (
          <button
            type="button"
            onClick={() => setEditingProfile(true)}
            className="w-full py-2.5 rounded-lg bg-gray-50 dark:bg-gray-700 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-600"
          >
            Modifier mon profil (photo, nom, biographie)
          </button>
        )}
        <PasswordForm />
      </Section>

      <Section title="Confidentialité">
        {settings === null ? (
          <div className="space-y-2">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-10 rounded bg-gray-100 dark:bg-gray-700 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {PRIVACY_OPTIONS.map((opt) => (
              <div key={opt.key} className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{opt.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{opt.help}</p>
                </div>
                <Switch
                  checked={!!settings[opt.key]}
                  disabled={savingKey === opt.key}
                  label={opt.label}
                  onChange={(value) => togglePrivacy(opt.key, value)}
                />
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Lecture">
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-white">Ma vitesse de lecture</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
            Sert à estimer ton temps de lecture dans les statistiques.
          </p>
          <ChoiceRow
            options={READING_SPEEDS}
            value={readingWpm}
            onSelect={(opt) => onChangeWpm(opt.wpm)}
            getKey={(opt) => opt.id}
            getLabel={(opt) => `${opt.label} · ${opt.wpm}`}
            isActive={(opt, value) => opt.wpm === value}
          />
          <p className="text-[11px] text-gray-400 mt-1.5">En mots par minute.</p>
        </div>
      </Section>

      <Section title="Apparence">
        <ChoiceRow
          options={THEMES}
          value={theme}
          onSelect={(opt) => setTheme(opt.id)}
          getKey={(opt) => opt.id}
          getLabel={(opt) => opt.label}
          isActive={(opt, value) => opt.id === value}
        />
      </Section>

      <Section title="Données et services">
        <div className="space-y-1.5">
          {DATA_LINKS.map((link) => (
            <button
              key={link.event}
              type="button"
              onClick={() => onTriggerEvent(link.event)}
              className="w-full text-left px-3 py-2.5 rounded-lg bg-gray-50 dark:bg-gray-700 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              {link.label}
            </button>
          ))}
        </div>
      </Section>

      {isAdmin ? (
        <Section title="Administration">
          <button
            type="button"
            onClick={() => navigate('/admin')}
            className="w-full py-2.5 rounded-lg bg-gray-50 dark:bg-gray-700 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-600"
          >
            Ouvrir le tableau de bord administrateur
          </button>
        </Section>
      ) : null}

      <Section title="Informations légales">
        <button
          type="button"
          onClick={() => navigate('/cgu')}
          className="w-full text-left px-3 py-2.5 rounded-lg bg-gray-50 dark:bg-gray-700 text-sm font-medium text-gray-800 dark:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-600"
        >
          Conditions générales d'utilisation
        </button>
      </Section>

      <Section title="Session">
        <button
          type="button"
          onClick={onLogout}
          className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors text-sm"
        >
          Se déconnecter
        </button>
        <button
          type="button"
          onClick={onDeleteAccount}
          className="w-full text-xs text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors py-1"
        >
          Supprimer mon compte
        </button>
      </Section>
    </div>
  );
}
