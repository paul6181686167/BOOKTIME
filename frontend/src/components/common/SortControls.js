// Composant de contrôles de tri
export default function SortControls({ sortConfig, setSortConfig, isVoid = false }) {
  const fields = [
    { key: 'date_added', label: 'Date' },
    { key: 'title',      label: 'Titre' },
    { key: 'author',     label: 'Auteur' },
  ];
  return (
    <div className="flex items-center gap-2 ml-4">
      <span className={`text-xs ${isVoid ? 'text-white/65' : 'text-gray-500 dark:text-gray-400'}`}>Trier</span>
      {fields.map(f => (
        <button
          key={f.key}
          onClick={() => setSortConfig(prev =>
            prev.field === f.key
              ? { ...prev, order: prev.order === 'asc' ? 'desc' : 'asc' }
              : { field: f.key, order: 'asc' }
          )}
          className={`px-2 py-1 text-xs rounded-full transition-colors ${
            sortConfig.field === f.key
              ? isVoid
                ? 'bg-[#4ade80] text-black font-medium'
                : 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 font-medium'
              : isVoid
                ? 'bg-white/[0.06] text-white/65 hover:bg-white/[0.1]'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          {f.label} {sortConfig.field === f.key ? (sortConfig.order === 'asc' ? '↑' : '↓') : ''}
        </button>
      ))}
    </div>
  );
}
