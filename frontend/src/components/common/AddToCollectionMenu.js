import React, { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';
import {
  addItemToCollection,
  createCollection,
  getCollections,
  collectionContains,
} from '../../utils/collectionsStorage';

/**
 * Menu pour ajouter un livre ou une série à une collection.
 * item = { type: 'book'|'series', id, title, author?, cover_url? }
 */
export default function AddToCollectionMenu({ item, onClose, onChanged }) {
  const [collections, setCollections] = useState(() => getCollections());
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    setCollections(getCollections());
  }, [item?.id, item?.type]);

  if (!item?.id) return null;

  const handleAdd = (collectionId) => {
    const result = addItemToCollection(collectionId, item);
    if (!result.ok) {
      if (result.reason === 'duplicate') {
        toast.error('Déjà dans cette collection');
      } else {
        toast.error('Collection introuvable');
      }
      return;
    }
    setCollections(result.collections);
    onChanged?.(result.collections);
    toast.success(
      item.type === 'series'
        ? 'Série ajoutée à la collection'
        : 'Livre ajouté à la collection'
    );
  };

  const handleCreateAndAdd = () => {
    const created = createCollection(newName);
    if (!created.ok) {
      if (created.reason === 'exists') toast.error('Cette collection existe déjà');
      else toast.error('Nom invalide');
      return;
    }
    setNewName('');
    setCreating(false);
    const result = addItemToCollection(created.collection.id, item);
    setCollections(result.collections || created.collections);
    onChanged?.(result.collections || created.collections);
    toast.success(`Ajouté à « ${created.collection.name} »`);
  };

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 shadow-lg p-3 w-full max-w-sm">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
          Ajouter à une collection
        </h4>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-sm px-1"
          >
            ✕
          </button>
        )}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3 truncate">
        {item.title}
      </p>

      {collections.length === 0 && !creating ? (
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
          Aucune collection pour l&apos;instant. Crée-en une ci-dessous.
        </p>
      ) : (
        <div className="space-y-1 max-h-48 overflow-y-auto mb-2">
          {collections.map((c) => {
            const already = collectionContains(c, item.type, item.id);
            return (
              <button
                key={c.id}
                type="button"
                disabled={already}
                onClick={() => handleAdd(c.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                  already
                    ? 'bg-gray-100 dark:bg-gray-700/40 text-gray-400 cursor-default'
                    : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-green-50 dark:hover:bg-green-900/20 text-gray-900 dark:text-white'
                }`}
              >
                <span className="truncate font-medium">{c.name}</span>
                <span className="text-xs text-gray-500 shrink-0 ml-2">
                  {already ? 'Déjà ajouté' : `${(c.items || []).length} élément${(c.items || []).length !== 1 ? 's' : ''}`}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {creating ? (
        <div className="flex gap-2 mt-1">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nom de la collection…"
            className="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
            onKeyDown={(e) => e.key === 'Enter' && handleCreateAndAdd()}
            autoFocus
          />
          <button
            type="button"
            onClick={handleCreateAndAdd}
            className="px-2.5 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg"
          >
            OK
          </button>
          <button
            type="button"
            onClick={() => { setCreating(false); setNewName(''); }}
            className="px-2 py-1.5 text-sm bg-gray-200 dark:bg-gray-600 rounded-lg"
          >
            ✕
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setCreating(true)}
          className="w-full mt-1 py-2 text-sm border border-dashed border-green-300 dark:border-green-700 rounded-lg text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/10"
        >
          + Nouvelle collection
        </button>
      )}
    </div>
  );
}
