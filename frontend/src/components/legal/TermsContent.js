import React, { useMemo } from 'react';
import { buildTermsSections, getLegalConfig, TERMS_UPDATED_LABEL } from '../../legal/terms';

/** Texte des conditions générales d'utilisation (réutilisé par la page /cgu et la fenêtre d'inscription). */
export default function TermsContent({ config }) {
  const sections = useMemo(() => buildTermsSections(config || getLegalConfig()), [config]);

  return (
    <article className="space-y-5 text-sm leading-relaxed text-gray-700 dark:text-gray-300">
      <p className="text-xs text-gray-500 dark:text-gray-400">Dernière mise à jour : {TERMS_UPDATED_LABEL}</p>
      {sections.map((section) => (
        <section key={section.id} aria-labelledby={`cgu-${section.id}`} className="space-y-2">
          <h2 id={`cgu-${section.id}`} className="text-base font-semibold text-gray-900 dark:text-white">
            {section.title}
          </h2>
          {section.body.map((block, i) =>
            Array.isArray(block) ? (
              <ul key={i} className="list-disc pl-5 space-y-1">
                {block.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            ) : (
              <p key={i}>{block}</p>
            )
          )}
        </section>
      ))}
    </article>
  );
}
