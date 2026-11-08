/**
 * Aides d'accessibilité partagées.
 */

/**
 * Rend un élément non natif (carte, ligne…) utilisable comme un bouton :
 * focus clavier, Entrée / Espace, rôle annoncé par les lecteurs d'écran.
 *
 * À étaler sur l'élément : `<div {...clickableProps(() => ouvrir(item), 'Ouvrir Dune')}>`.
 * `label` est facultatif : sans lui, le nom accessible vient du contenu texte de l'élément.
 * La touche n'est prise en compte que si le focus est sur l'élément lui-même, pour ne pas
 * déclencher la carte quand on appuie sur Entrée dans un bouton imbriqué.
 */
export function clickableProps(onActivate, label) {
  return {
    role: 'button',
    tabIndex: 0,
    ...(label ? { 'aria-label': label } : {}),
    onClick: onActivate,
    onKeyDown: (e) => {
      if (e.target !== e.currentTarget) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onActivate(e);
      }
    },
  };
}
