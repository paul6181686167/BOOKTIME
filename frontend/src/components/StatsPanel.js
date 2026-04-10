import React, { useState, useEffect } from 'react';
import { BookOpenIcon, CheckCircleIcon, ClockIcon, QueueListIcon } from '@heroicons/react/24/outline';

// Mini barre de progression avec label
function StatBar({ label, value, max, color = 'bg-blue-500' }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 dark:text-gray-400 w-24 flex-shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full ${color} reading-progress-bar transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-sm font-bold text-gray-800 dark:text-gray-200 w-8 text-right">{value}</span>
    </div>
  );
}

// Compteur animé
function Counter({ value, className }) {
  const [displayed, setDisplayed] = useState(0);
  useEffect(() => {
    if (!value) return;
    let cur = 0;
    const step = Math.max(1, Math.ceil(value / 25));
    const t = setInterval(() => {
      cur += step;
      if (cur >= value) { setDisplayed(value); clearInterval(t); }
      else setDisplayed(cur);
    }, 30);
    return () => clearInterval(t);
  }, [value]);
  return <span className={className}>{displayed.toLocaleString('fr-FR')}</span>;
}

const StatsPanel = ({ stats }) => {
  const [activeView, setActiveView] = useState('overview'); // 'overview' | 'categories' | 'details'
  const categoryStats = stats.categories || {};
  const total = stats.total_books || 0;

  const views = [
    { key: 'overview',   label: '📊 Vue générale' },
    { key: 'categories', label: '📚 Catégories'   },
    { key: 'details',    label: '🔍 Détails'       },
  ];

  return (
    <div className="mb-8">
      {/* Onglets */}
      <div className="flex gap-2 mb-5">
        {views.map(v => (
          <button
            key={v.key}
            onClick={() => setActiveView(v.key)}
            className={`px-3 py-1.5 text-sm rounded-full transition-colors font-medium ${
              activeView === v.key
                ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >{v.label}</button>
        ))}
      </div>

      {/* Vue générale */}
      {activeView === 'overview' && (
        <div className="animate-fadeIn">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[
              { title: 'Total',    value: stats.total_books || 0,     icon: '📚', bg: 'bg-blue-50 dark:bg-blue-900/20',    text: 'text-blue-600 dark:text-blue-400'    },
              { title: 'Terminés', value: stats.completed_books || 0, icon: '✅', bg: 'bg-green-50 dark:bg-green-900/20',  text: 'text-green-600 dark:text-green-400'  },
              { title: 'En cours', value: stats.reading_books || 0,   icon: '📖', bg: 'bg-yellow-50 dark:bg-yellow-900/20',text: 'text-yellow-600 dark:text-yellow-400'},
              { title: 'À lire',   value: stats.to_read_books || 0,   icon: '📌', bg: 'bg-gray-50 dark:bg-gray-700',       text: 'text-gray-700 dark:text-gray-200'    },
            ].map((s, i) => (
              <div
                key={s.title}
                className={`${s.bg} rounded-xl p-5 border border-gray-100 dark:border-gray-700 shadow-sm section-appear`}
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="text-2xl mb-1">{s.icon}</div>
                <Counter value={s.value} className={`text-3xl font-bold ${s.text} block`} />
                <p className={`text-sm ${s.text} opacity-80`}>{s.title}</p>
              </div>
            ))}
          </div>

          {/* Barres de statut */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">Répartition des statuts</h3>
            <div className="space-y-3">
              <StatBar label="Terminés"  value={stats.completed_books || 0} max={total} color="bg-green-500" />
              <StatBar label="En cours"  value={stats.reading_books || 0}   max={total} color="bg-blue-500"  />
              <StatBar label="À lire"    value={stats.to_read_books || 0}   max={total} color="bg-gray-400"  />
            </div>
          </div>
        </div>
      )}

      {/* Vue catégories */}
      {activeView === 'categories' && (
        <div className="animate-fadeIn space-y-4">
          {[
            { label: 'Romans',            value: categoryStats.roman || 0, emoji: '📚', color: 'bg-blue-500',   bgCard: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-700 dark:text-blue-300' },
            { label: 'Romans Graphiques', value: categoryStats.bd || 0,    emoji: '🎨', color: 'bg-green-500',  bgCard: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-300' },
            { label: 'Mangas',            value: categoryStats.manga || 0, emoji: '🇯🇵', color: 'bg-purple-500', bgCard: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-700 dark:text-purple-300' },
          ].map((cat, i) => {
            const pct = total > 0 ? Math.round((cat.value / total) * 100) : 0;
            return (
              <div key={cat.label} className={`${cat.bgCard} rounded-xl p-4 border border-gray-100 dark:border-gray-700 section-appear`} style={{ animationDelay: `${i * 80}ms` }}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{cat.emoji}</span>
                    <span className={`font-semibold ${cat.text}`}>{cat.label}</span>
                  </div>
                  <div className="text-right">
                    <Counter value={cat.value} className={`text-2xl font-bold ${cat.text}`} />
                    <div className={`text-xs ${cat.text} opacity-70`}>{pct}% du total</div>
                  </div>
                </div>
                <div className="w-full bg-white/60 dark:bg-gray-700/60 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-full ${cat.color} reading-progress-bar`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Vue détails */}
      {activeView === 'details' && (
        <div className="animate-fadeIn space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { label: 'Auteurs différents',  value: stats.authors_count || 0,   icon: '✍️' },
              { label: 'Séries / Sagas',      value: stats.sagas_count || 0,     icon: '📖' },
              { label: 'Pages lues',          value: stats.total_pages_read || 0,icon: '📄' },
              { label: 'Terminés cette année',value: stats.completed_this_year || 0, icon: '🗓️' },
            ].map((d, i) => (
              <div key={d.label} className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center gap-4 section-appear" style={{ animationDelay: `${i * 60}ms` }}>
                <span className="text-3xl">{d.icon}</span>
                <div>
                  <Counter value={d.value} className="text-2xl font-bold text-gray-800 dark:text-gray-200 block" />
                  <p className="text-sm text-gray-500 dark:text-gray-400">{d.label}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Temps de lecture estimé */}
          {stats.reading_hours_estimated > 0 && (
            <div className="bg-amber-50 dark:bg-amber-900/10 rounded-xl p-4 border border-amber-100 dark:border-amber-800 flex items-center gap-4 section-appear">
              <span className="text-3xl">⏱️</span>
              <div>
                <p className="text-2xl font-bold text-amber-700 dark:text-amber-300">
                  {stats.reading_hours_estimated.toLocaleString('fr-FR')}h
                </p>
                <p className="text-sm text-amber-600 dark:text-amber-400">de lecture estimées</p>
              </div>
            </div>
          )}

          {/* Note moyenne */}
          {stats.avg_rating > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm flex items-center gap-4 section-appear">
              <span className="text-3xl">⭐</span>
              <div className="flex-1">
                <p className="text-2xl font-bold text-gray-800 dark:text-gray-200">{stats.avg_rating} / 5</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">Note moyenne de tes livres</p>
                <div className="flex gap-0.5 mt-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <svg key={i} className={`h-4 w-4 ${i < Math.round(stats.avg_rating) ? 'text-yellow-400' : 'text-gray-200 dark:text-gray-600'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                    </svg>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Genres préférés */}
          {stats.top_genres?.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 shadow-sm section-appear">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Tes genres préférés</h3>
              <div className="space-y-2">
                {stats.top_genres.map((g, i) => (
                  <StatBar
                    key={g.genre}
                    label={g.genre.length > 16 ? g.genre.substring(0, 16) + '…' : g.genre}
                    value={g.count}
                    max={stats.top_genres[0]?.count || 1}
                    color={['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500', 'bg-pink-500'][i % 5]}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StatsPanel;
