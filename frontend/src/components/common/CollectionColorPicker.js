import React from 'react';
import { COLLECTION_COLORS } from '../../utils/collectionsStorage';

/** Pastilles de couleur pour choisir la couleur d'une collection. */
export default function CollectionColorPicker({ value, onChange, className = '' }) {
  return (
    <div
      className={`flex flex-wrap items-center gap-2 ${className}`}
      role="radiogroup"
      aria-label="Couleur de la collection"
    >
      {COLLECTION_COLORS.map((c) => {
        const selected = (value || '').toLowerCase() === c.hex;
        return (
          <button
            key={c.id}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={c.label}
            title={c.label}
            onClick={() => onChange(c.hex)}
            className={`h-7 w-7 rounded-full transition-transform ${
              selected
                ? 'scale-110 ring-2 ring-offset-2 ring-gray-900 dark:ring-white ring-offset-white dark:ring-offset-gray-800'
                : 'opacity-80 hover:opacity-100'
            }`}
            style={{ backgroundColor: c.hex }}
          />
        );
      })}
    </div>
  );
}
