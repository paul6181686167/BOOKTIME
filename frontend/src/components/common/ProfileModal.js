import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../contexts/ThemeContext';
import { bookService } from '../../services/bookService';

// ─── Clé localStorage pour persistance locale ───────────────────────────────
const PROFILE_STORAGE_KEY = 'booktime_profile_data';

function loadProfileData() {
  try { return JSON.parse(localStorage.getItem(PROFILE_STORAGE_KEY)) || {}; }
  catch { return {}; }
}
function saveProfileData(data) {
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(data));
}

// ─── Heatmap de lecture ──────────────────────────────────────────────────────
function ReadingHeatmap({ completionDates }) {
  const today = new Date();
  const cells = [];
  // 52 semaines × 7 jours = 364 derniers jours
  for (let w = 51; w >= 0; w--) {
    const week = [];
    for (let d = 6; d >= 0; d--) {
      const date = new Date(today);
      date.setDate(today.getDate() - w * 7 - d);
      const key = date.toISOString().slice(0, 10);
      const count = completionDates[key] || 0;
      week.push({ key, count, date });
    }
    cells.push(week);
  }

  const getColor = (count) => {
    if (count === 0) return 'bg-gray-100 dark:bg-gray-700';
    if (count === 1) return 'bg-green-200 dark:bg-green-800';
    if (count === 2) return 'bg-green-400 dark:bg-green-600';
    return 'bg-green-600 dark:bg-green-400';
  };

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-0.5 min-w-max">
        {cells.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-0.5">
            {week.map(({ key, count, date }) => (
              <div
                key={key}
                title={`${date.toLocaleDateString('fr-FR')} : ${count} livre${count > 1 ? 's' : ''} terminé${count > 1 ? 's' : ''}`}
                className={`w-3 h-3 rounded-sm ${getColor(count)} transition-colors cursor-default`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-1 mt-2 text-xs text-gray-500 dark:text-gray-400">
        <span>Moins</span>
        {['bg-gray-100 dark:bg-gray-700','bg-green-200','bg-green-400','bg-green-600'].map((c,i) => (
          <div key={i} className={`w-3 h-3 rounded-sm ${c}`} />
        ))}
        <span>Plus</span>
      </div>
    </div>
  );
}

// ─── Composant principal ─────────────────────────────────────────────────────
function ProfileModal({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stats'); // 'stats' | 'goal' | 'heatmap' | 'collections'

  // Données persistées localement
  const [profileData, setProfileData] = useState(() => loadProfileData());
  // Objectif annuel
  const [goalInput, setGoalInput] = useState('');
  const [editingGoal, setEditingGoal] = useState(false);
  // Collections
  const [newCollectionName, setNewCollectionName] = useState('');
  // Heatmap : dates de complétion extraites des livres
  const [completionDates, setCompletionDates] = useState({});

  const currentYear = new Date().getFullYear();

  useEffect(() => {
    if (isOpen) {
      loadStats();
      setProfileData(loadProfileData());
    }
  }, [isOpen]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await bookService.getStats();
      setStats(data);
      // Extraire les dates de complétion depuis l'API si disponible
      if (data.completion_dates) {
        setCompletionDates(data.completion_dates);
      }
    } catch (error) {
      console.error('Erreur chargement stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateProfileData = useCallback((update) => {
    setProfileData(prev => {
      const next = { ...prev, ...update };
      saveProfileData(next);
      return next;
    });
  }, []);

  const handleLogout = () => {
    logout();
    onClose();
    toast.success('Déconnexion réussie');
  };

  const handleSaveGoal = () => {
    const val = parseInt(goalInput);
    if (!val || val < 1 || val > 500) {
      toast.error('Objectif invalide (1-500)');
      return;
    }
    updateProfileData({ [`goal_${currentYear}`]: val });
    setEditingGoal(false);
    toast.success(`Objectif ${currentYear} fixé : ${val} livres`);
  };

  const handleAddCollection = () => {
    const name = newCollectionName.trim();
    if (!name) return;
    const collections = profileData.collections || [];
    if (collections.find(c => c.name === name)) {
      toast.error('Cette collection existe déjà');
      return;
    }
    updateProfileData({ collections: [...collections, { name, id: Date.now(), books: [] }] });
    setNewCollectionName('');
    toast.success(`Collection "${name}" créée`);
  };

  const handleDeleteCollection = (id) => {
    const collections = (profileData.collections || []).filter(c => c.id !== id);
    updateProfileData({ collections });
    toast.success('Collection supprimée');
  };

  const currentGoal = profileData[`goal_${currentYear}`] || 0;
  const booksThisYear = stats.completed_this_year || stats.completed_books || 0;
  const goalPercent = currentGoal > 0 ? Math.min(100, Math.round((booksThisYear / currentGoal) * 100)) : 0;

  if (!isOpen) return null;

  const tabs = [
    { key: 'stats',       label: '📊 Stats'       },
    { key: 'goal',        label: '🎯 Objectif'     },
    { key: 'heatmap',     label: '📅 Calendrier'   },
    { key: 'collections', label: '📁 Collections'  },
  ];

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-end md:items-center justify-center z-50 md:p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white dark:bg-gray-800 md:rounded-2xl shadow-2xl w-full md:max-w-lg max-h-[92dvh] md:max-h-[90vh] flex flex-col modal-animate" style={{ borderRadius: '20px 20px 0 0' }}>
        {/* Header */}
        <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Profil</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">{user?.email}</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >✕</button>
          </div>

          {/* Onglets */}
          <div className="flex gap-1 mt-3 overflow-x-auto">
            {tabs.map(t => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
                  activeTab === t.key
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >{t.label}</button>
            ))}
          </div>
        </div>

        {/* Contenu */}
        <div className="flex-1 overflow-y-auto p-4">

          {/* ─── STATS ─── */}
          {activeTab === 'stats' && (
            <div className="space-y-4 animate-fadeIn">
              {loading ? (
                <div className="space-y-2">{[...Array(4)].map((_, i) => (
                  <div key={i} className="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                ))}</div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { v: stats.total_books || 0,     label: 'Total',       color: 'blue'   },
                      { v: stats.completed_books || 0, label: 'Terminés',    color: 'green'  },
                      { v: stats.reading_books || 0,   label: 'En cours',    color: 'yellow' },
                      { v: stats.to_read_books || 0,   label: 'À lire',      color: 'orange' },
                    ].map(s => (
                      <div key={s.label} className={`bg-${s.color}-50 dark:bg-${s.color}-900/20 rounded-xl p-4 text-center`}>
                        <div className={`text-2xl font-bold text-${s.color}-600 dark:text-${s.color}-400`}>{s.v}</div>
                        <div className={`text-xs text-${s.color}-600 dark:text-${s.color}-400`}>{s.label}</div>
                      </div>
                    ))}
                  </div>
                  {stats.total_pages_read > 0 && (
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 text-center">
                      <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {stats.total_pages_read?.toLocaleString('fr-FR')}
                      </div>
                      <div className="text-xs text-purple-600 dark:text-purple-400">Pages lues</div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* ─── OBJECTIF ─── */}
          {activeTab === 'goal' && (
            <div className="animate-fadeIn space-y-4">
              <div className="text-center">
                <div className="text-4xl mb-2">🎯</div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">Objectif {currentYear}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">Combien de livres voulez-vous lire cette année ?</p>
              </div>

              {currentGoal > 0 ? (
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-400">{booksThisYear} livres terminés</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">{booksThisYear} / {currentGoal}</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
                    <div
                      className="h-4 rounded-full bg-gradient-to-r from-green-400 to-green-600 reading-progress-bar transition-all duration-700"
                      style={{ width: `${goalPercent}%` }}
                    />
                  </div>
                  <div className="text-center mt-2">
                    <span className={`text-2xl font-bold ${goalPercent >= 100 ? 'text-green-600' : 'text-gray-700 dark:text-gray-300'}`}>
                      {goalPercent}%
                    </span>
                    {goalPercent >= 100 && <p className="text-sm text-green-600 mt-1">🎉 Objectif atteint !</p>}
                    {goalPercent < 100 && currentGoal > 0 && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        encore {currentGoal - booksThisYear} livre{currentGoal - booksThisYear > 1 ? 's' : ''} pour atteindre votre objectif
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                  <p className="mb-2">Aucun objectif défini pour {currentYear}</p>
                </div>
              )}

              {editingGoal ? (
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={goalInput}
                    onChange={e => setGoalInput(e.target.value)}
                    placeholder="Ex: 24"
                    min="1" max="500"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500 text-center text-lg font-bold"
                    onKeyDown={e => e.key === 'Enter' && handleSaveGoal()}
                    autoFocus
                  />
                  <button onClick={handleSaveGoal} className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">✓</button>
                  <button onClick={() => setEditingGoal(false)} className="px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg transition-colors">✕</button>
                </div>
              ) : (
                <button
                  onClick={() => { setGoalInput(currentGoal || ''); setEditingGoal(true); }}
                  className="w-full py-2 border-2 border-dashed border-green-300 dark:border-green-700 rounded-lg text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/10 transition-colors text-sm font-medium"
                >
                  {currentGoal ? '✏️ Modifier l\'objectif' : '+ Définir un objectif'}
                </button>
              )}
            </div>
          )}

          {/* ─── HEATMAP ─── */}
          {activeTab === 'heatmap' && (
            <div className="animate-fadeIn">
              <div className="mb-4">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">Activité de lecture (12 derniers mois)</h3>
                <p className="text-xs text-gray-500 dark:text-gray-400">Chaque case représente un jour. Plus la case est foncée, plus vous avez terminé de livres ce jour-là.</p>
              </div>
              <ReadingHeatmap completionDates={completionDates} />
              {Object.keys(completionDates).length === 0 && (
                <div className="text-center mt-4 text-gray-400 text-sm">
                  <p>Terminez des livres pour voir votre activité apparaître ici.</p>
                </div>
              )}
            </div>
          )}

          {/* ─── COLLECTIONS ─── */}
          {activeTab === 'collections' && (
            <div className="animate-fadeIn space-y-3">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Créez des étagères personnalisées pour organiser vos livres (ex: "À offrir", "Lu en vacances", "Coups de cœur").
              </p>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={newCollectionName}
                  onChange={e => setNewCollectionName(e.target.value)}
                  placeholder="Nom de la collection..."
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                  onKeyDown={e => e.key === 'Enter' && handleAddCollection()}
                />
                <button
                  onClick={handleAddCollection}
                  className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm"
                >+ Créer</button>
              </div>

              {(profileData.collections || []).length === 0 ? (
                <div className="text-center py-6 text-gray-400">
                  <div className="text-3xl mb-2">📁</div>
                  <p className="text-sm">Aucune collection créée</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {(profileData.collections || []).map(c => (
                    <div key={c.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg group">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white text-sm">📁 {c.name}</span>
                        <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                          {(c.books || []).length} livre{(c.books || []).length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDeleteCollection(c.id)}
                        className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all text-xs px-2 py-1"
                        title="Supprimer"
                      >✕</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Paramètres (toujours visibles en bas) */}
          {activeTab === 'stats' && (
            <div className="mt-4 space-y-2">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mt-2 mb-3">⚙️ Paramètres</h3>
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <span className="text-sm font-medium text-gray-900 dark:text-white">Mode sombre</span>
                <button
                  onClick={toggleTheme}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${isDark ? 'bg-blue-600' : 'bg-gray-200'}`}
                >
                  <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${isDark ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
              </div>

              {[
                { event: 'openSocial',                  label: '🌐 Social',            color: 'purple' },
                { event: 'openExportImport',            label: '📤 Export/Import',      color: 'green'  },
                { event: 'openAdvancedRecommendations', label: '🤖 Recommandations IA', color: 'purple' },
                { event: 'openIntegrations',            label: '🔗 Intégrations',       color: 'orange' },
              ].map(({ event, label, color }) => (
                <button
                  key={event}
                  onClick={() => { onClose(); window.dispatchEvent(new CustomEvent(event)); }}
                  className={`w-full p-2.5 bg-${color}-50 dark:bg-${color}-900/20 hover:bg-${color}-100 dark:hover:bg-${color}-900/30 rounded-lg transition-colors text-sm font-medium text-${color}-700 dark:text-${color}-300`}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm"
          >
            Se déconnecter
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProfileModal;
