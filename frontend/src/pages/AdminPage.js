import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import adminService from '../services/adminService';

const REFRESH_MS = 10000;
const PAGE_SIZE = 20;

/** "il y a 3 min" à partir d'une date ISO (ou rien si absente). */
export function timeAgo(iso, now = Date.now()) {
  if (!iso) return 'jamais';
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return 'jamais';
  const s = Math.max(0, Math.round((now - t) / 1000));
  if (s < 60) return "à l'instant";
  if (s < 3600) return `il y a ${Math.floor(s / 60)} min`;
  if (s < 86400) return `il y a ${Math.floor(s / 3600)} h`;
  return `il y a ${Math.floor(s / 86400)} j`;
}

const nf = new Intl.NumberFormat('fr-FR');
const fmt = (n) => nf.format(Number(n) || 0);

function Card({ label, value, hint, accent }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-3">
      <p className="text-[11px] uppercase tracking-wide text-gray-500 dark:text-gray-400">{label}</p>
      <p className={`text-2xl font-bold ${accent || 'text-gray-900 dark:text-white'}`}>{fmt(value)}</p>
      {hint ? <p className="text-[11px] text-gray-400 mt-0.5">{hint}</p> : null}
    </div>
  );
}

function Block({ title, children }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-white">{title}</h2>
      {children}
    </section>
  );
}

function Bars({ data, label }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-3"
      role="img"
      aria-label={label}
    >
      <div className="flex items-end gap-1 h-24">
        {data.map((d) => (
          <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full min-w-0">
            <span className="text-[9px] text-gray-500 dark:text-gray-400 leading-none mb-0.5">
              {d.count > 0 ? d.count : ''}
            </span>
            <div
              className="w-full rounded-t bg-green-500"
              style={{ height: `${d.count > 0 ? Math.max(4, (d.count / max) * 100) : 2}%`, opacity: d.count > 0 ? 1 : 0.25 }}
              title={`${d.date} : ${d.count}`}
            />
          </div>
        ))}
      </div>
      <div className="flex justify-between text-[10px] text-gray-400 mt-1">
        <span>{data[0]?.date?.slice(5)}</span>
        <span>{data[data.length - 1]?.date?.slice(5)}</span>
      </div>
    </div>
  );
}

function BanDialog({ user, onCancel, onConfirm, busy }) {
  const [reason, setReason] = useState('');
  return (
    <div
      className="fixed inset-0 z-[1100] bg-black/50 flex items-end sm:items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Bannir cet utilisateur"
    >
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 w-full max-w-sm space-y-3">
        <h3 className="font-semibold text-gray-900 dark:text-white">Bannir {user.display_name || user.email} ?</h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Cette personne ne pourra plus se connecter ni utiliser l'application. Ses avis seront masqués de la
          communauté. Tu pourras annuler le bannissement à tout moment.
        </p>
        <input
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          maxLength={200}
          placeholder="Motif (facultatif)"
          aria-label="Motif du bannissement"
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-red-500"
        />
        <div className="flex gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => onConfirm(reason)}
            className="flex-1 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {busy ? 'Bannissement…' : 'Bannir'}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={onCancel}
            className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-sm"
          >
            Annuler
          </button>
        </div>
      </div>
    </div>
  );
}

function UserRow({ user, onBan, onUnban, busy }) {
  return (
    <li className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-3 flex items-start gap-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {user.display_name || user.email}
          </p>
          {user.online ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300">
              en ligne
            </span>
          ) : null}
          {user.is_admin ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
              admin
            </span>
          ) : null}
          {user.banned ? (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300">
              banni
            </span>
          ) : null}
        </div>
        {user.display_name ? (
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
        ) : null}
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          {fmt(user.books_count)} livre(s) · {fmt(user.reviews_count)} avis · vu {timeAgo(user.last_seen)}
        </p>
        {user.banned && user.banned_reason ? (
          <p className="text-xs text-red-600 dark:text-red-400 mt-0.5">Motif : {user.banned_reason}</p>
        ) : null}
      </div>
      {user.is_admin ? null : user.banned ? (
        <button
          type="button"
          disabled={busy}
          onClick={() => onUnban(user)}
          className="shrink-0 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-medium disabled:opacity-50"
        >
          Débannir
        </button>
      ) : (
        <button
          type="button"
          disabled={busy}
          onClick={() => onBan(user)}
          className="shrink-0 px-3 py-1.5 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 ring-1 ring-red-200 dark:ring-red-800 text-xs font-medium disabled:opacity-50"
        >
          Bannir
        </button>
      )}
    </li>
  );
}

/** Tableau de bord administrateur : chiffres en direct et gestion des comptes. */
export default function AdminPage() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState({ total: 0, users: [] });
  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState('');
  const [updatedAt, setUpdatedAt] = useState(null);
  const [, setTick] = useState(0);
  const [paused, setPaused] = useState(false);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [status, setStatus] = useState('all');
  const [page, setPage] = useState(0);
  const [banTarget, setBanTarget] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const filters = useRef({ q: '', status: 'all', page: 0 });
  filters.current = { q: debouncedQuery, status, page };

  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedQuery(query);
      setPage(0);
    }, 350);
    return () => clearTimeout(t);
  }, [query]);

  const load = useCallback(async () => {
    const { q, status: st, page: pg } = filters.current;
    try {
      const [s, u] = await Promise.all([
        adminService.getStats(),
        adminService.listUsers({ q, status: st, skip: pg * PAGE_SIZE, limit: PAGE_SIZE }),
      ]);
      setStats(s);
      setUsers(u);
      setError('');
      setUpdatedAt(Date.now());
    } catch (e) {
      if (e.status === 403 || e.status === 401) setForbidden(true);
      else setError(e.message || 'Chargement impossible');
    }
  }, []);

  // Rafraîchissement automatique (suspendu si l'onglet est masqué ou en pause)
  useEffect(() => {
    if (forbidden) return undefined;
    load();
    if (paused) return undefined;
    const id = setInterval(() => {
      if (document.visibilityState !== 'hidden') load();
    }, REFRESH_MS);
    return () => clearInterval(id);
  }, [load, paused, forbidden, debouncedQuery, status, page]);

  // Fait avancer l'étiquette "mis à jour il y a X s"
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const confirmBan = async (reason) => {
    const target = banTarget;
    setBusyId(target.id);
    try {
      await adminService.banUser(target.id, reason);
      toast.success('Compte banni');
      setBanTarget(null);
      await load();
    } catch (e) {
      toast.error(e.message || 'Bannissement impossible');
    } finally {
      setBusyId(null);
    }
  };

  const unban = async (user) => {
    setBusyId(user.id);
    try {
      await adminService.unbanUser(user.id);
      toast.success('Compte réactivé');
      await load();
    } catch (e) {
      toast.error(e.message || 'Action impossible');
    } finally {
      setBusyId(null);
    }
  };

  const header = (
    <div
      className="sticky top-0 z-10 bg-white/95 dark:bg-gray-900/95 backdrop-blur border-b border-gray-100 dark:border-gray-800"
      style={{ paddingTop: 'env(safe-area-inset-top)' }}
    >
      <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
        <button
          type="button"
          onClick={() => navigate('/')}
          aria-label="Retour"
          className="p-1.5 -ml-1.5 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div className="min-w-0 flex-1">
          <h1 className="text-base font-bold text-gray-900 dark:text-white">Administration</h1>
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            {updatedAt
              ? `Mis à jour ${timeAgo(new Date(updatedAt).toISOString())}${paused ? ' (en pause)' : ''}`
              : 'Chargement…'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setPaused((p) => !p)}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200"
        >
          {paused ? 'Reprendre' : 'Pause'}
        </button>
        <button
          type="button"
          onClick={load}
          className="px-3 py-1.5 rounded-lg text-xs font-medium bg-green-600 text-white"
        >
          Actualiser
        </button>
      </div>
    </div>
  );

  if (forbidden) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {header}
        <div className="max-w-md mx-auto p-6 text-center space-y-3">
          <p className="text-sm text-gray-700 dark:text-gray-200">Cette page est réservée aux administrateurs.</p>
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  const u = stats?.users;
  const b = stats?.books;
  const e = stats?.engagement;
  const pages = Math.max(1, Math.ceil((users.total || 0) / PAGE_SIZE));

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
      {header}
      <div className="max-w-3xl mx-auto px-4 py-4 space-y-6">
        {error ? (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm p-3">
            {error}
          </div>
        ) : null}

        {!stats ? (
          <div className="grid grid-cols-2 gap-2">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
            ))}
          </div>
        ) : (
          <>
            <Block title="Utilisateurs">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <Card label="Inscrits" value={u.total} />
                <Card label="En ligne" value={u.online} hint="actifs ces 15 dernières minutes" accent="text-green-600" />
                <Card label="Actifs 24 h" value={u.active_24h} />
                <Card label="Nouveaux aujourd'hui" value={u.new_today} hint={`${fmt(u.new_7d)} sur 7 jours`} />
                <Card label="Bannis" value={u.banned} accent={u.banned > 0 ? 'text-red-600' : undefined} />
              </div>
              <Bars data={u.signups_per_day} label="Inscriptions par jour sur 14 jours" />
              <p className="text-[11px] text-gray-400">Inscriptions par jour, 14 derniers jours.</p>
            </Block>

            <Block title="Livres">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <Card label="Livres inscrits" value={b.total} hint={`${fmt(b.series_in_libraries)} série(s) suivie(s)`} />
                <Card label="Ajoutés aujourd'hui" value={b.added_today} hint={`${fmt(b.added_7d)} sur 7 jours`} />
                <Card label="Terminés" value={b.completed} />
                <Card label="En cours" value={b.reading} />
                <Card label="À lire" value={b.to_read} />
                <Card label="Romans" value={b.by_category.roman} />
                <Card label="BD" value={b.by_category.bd} />
                <Card label="Mangas" value={b.by_category.manga} />
                <Card label="Autres" value={b.by_category.autre} />
              </div>
              <Bars data={b.added_per_day} label="Livres ajoutés par jour sur 14 jours" />
              <p className="text-[11px] text-gray-400">Livres ajoutés par jour, 14 derniers jours.</p>
            </Block>

            <Block title="Activité">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <Card label="Avis rédigés" value={e.reviews} />
                <Card label="Notes données" value={e.ratings} />
                <Card label="Favoris" value={e.favorites} />
                <Card label="Messages" value={e.messages} hint={`${fmt(e.messages_24h)} ces 24 h`} />
                <Card label="Recommandations" value={e.book_recommendations} hint="livres envoyés par chat" />
                <Card label="Amitiés" value={e.friendships} />
                <Card label="Demandes en attente" value={e.friend_requests_pending} />
              </div>
            </Block>
          </>
        )}

        <Block title={`Comptes (${fmt(users.total)})`}>
          <div className="flex gap-2">
            <input
              type="search"
              value={query}
              onChange={(ev) => setQuery(ev.target.value)}
              placeholder="Rechercher par nom ou email"
              aria-label="Rechercher un compte"
              className="flex-1 min-w-0 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <select
              value={status}
              onChange={(ev) => {
                setStatus(ev.target.value);
                setPage(0);
              }}
              aria-label="Filtrer les comptes"
              className="px-2 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white"
            >
              <option value="all">Tous</option>
              <option value="banned">Bannis</option>
            </select>
          </div>

          {users.users.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">Aucun compte trouvé.</p>
          ) : (
            <ul className="space-y-2">
              {users.users.map((user) => (
                <UserRow key={user.id} user={user} busy={busyId === user.id} onBan={setBanTarget} onUnban={unban} />
              ))}
            </ul>
          )}

          {pages > 1 ? (
            <div className="flex items-center justify-between pt-1">
              <button
                type="button"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-40"
              >
                Précédent
              </button>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Page {page + 1} sur {pages}
              </span>
              <button
                type="button"
                disabled={page + 1 >= pages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-40"
              >
                Suivant
              </button>
            </div>
          ) : null}
        </Block>
      </div>

      {banTarget ? (
        <BanDialog
          user={banTarget}
          busy={busyId === banTarget.id}
          onCancel={() => setBanTarget(null)}
          onConfirm={confirmBan}
        />
      ) : null}
    </div>
  );
}
