/**
 * Conditions générales d'utilisation de Booktime.
 *
 * - Changer TERMS_VERSION à chaque modification de fond : elle est enregistrée
 *   avec la date d'acceptation de chaque compte créé.
 * - L'éditeur et l'adresse de contact viennent de variables d'environnement
 *   (REACT_APP_LEGAL_EDITOR, REACT_APP_CONTACT_EMAIL) pour ne pas figer d'identité dans le code.
 */

export const TERMS_VERSION = '2026-11-06';
export const TERMS_UPDATED_LABEL = '6 novembre 2026';
export const MINIMUM_AGE = 15;

export function getLegalConfig(env = process.env) {
  return {
    editor: (env.REACT_APP_LEGAL_EDITOR || '').trim(),
    contactEmail: (env.REACT_APP_CONTACT_EMAIL || '').trim(),
  };
}

/** Chaque bloc de `body` est un paragraphe (texte) ou une liste à puces (tableau de textes). */
export function buildTermsSections({ editor = '', contactEmail = '' } = {}) {
  const contactSentence = contactEmail
    ? `Pour exercer ces droits, écris à ${contactEmail}.`
    : "Pour exercer ces droits, utilise les fonctions de l'application (modification du profil, export de la bibliothèque, suppression du compte) ou contacte l'éditeur du service.";

  const sections = [
    {
      id: 'objet',
      title: '1. Objet',
      body: [
        "Booktime est une application web et mobile gratuite qui permet de gérer sa bibliothèque personnelle (romans, bandes dessinées, mangas), de suivre ses lectures et ses séries, de consulter des statistiques de lecture, d'obtenir des recommandations et d'échanger avec d'autres lecteurs.",
        "Les présentes conditions générales d'utilisation (les « CGU ») fixent les règles d'utilisation du service. Créer un compte, ou utiliser le service après leur publication, vaut acceptation de ces règles.",
      ],
    },
    {
      id: 'editeur',
      title: "2. Éditeur du service",
      body: [
        editor
          ? `Le service est édité par ${editor}.`
          : "Le service est édité à titre personnel par son créateur.",
        contactEmail ? `Contact : ${contactEmail}.` : null,
      ].filter(Boolean),
    },
    {
      id: 'compte',
      title: '3. Compte utilisateur',
      body: [
        `L'inscription est réservée aux personnes âgées d'au moins ${MINIMUM_AGE} ans. Elle nécessite une adresse email valide et un mot de passe.`,
        'Tu t\'engages à fournir une adresse email exacte, à ne créer qu\'un seul compte et à garder ton mot de passe confidentiel. Toute action réalisée depuis ton compte est considérée comme faite par toi : si tu penses que ton compte est utilisé par quelqu\'un d\'autre, change ton mot de passe sans attendre.',
        "Tu peux modifier ton profil, changer ton mot de passe et supprimer ton compte à tout moment depuis les paramètres du profil.",
      ],
    },
    {
      id: 'donnees',
      title: '4. Données personnelles',
      body: [
        "Données que nous enregistrons :",
        [
          "ton adresse email et ton mot de passe (conservé uniquement sous forme chiffrée irréversible) ;",
          "ta bibliothèque : livres, séries, statuts de lecture, notes, avis et favoris ;",
          "ton profil : nom affiché, biographie et photo, si tu les renseignes ;",
          "tes relations avec les autres lecteurs et les messages que tu échanges avec eux (y compris les livres recommandés) ;",
          "tes réglages et la date de ta dernière activité sur le service.",
        ],
        "Pourquoi : faire fonctionner le service (compte, bibliothèque, recommandations, amis et messagerie), assurer sa sécurité et sa modération, et produire des statistiques d'utilisation globales. Ces données ne sont ni vendues ni utilisées à des fins publicitaires.",
        "Ce que voient les autres : tes amis voient ton profil selon les réglages de confidentialité que tu choisis (recherche, livres préférés, notes et avis, lectures en cours). Tes avis peuvent aussi apparaître dans les pages communautaires d'un livre. Les messages sont destinés à leurs deux participants ; ils ne sont pas chiffrés de bout en bout et peuvent être consultés par l'éditeur en cas de signalement ou d'obligation légale.",
        "Hébergement et prestataires : l'application est servie par des hébergeurs techniques (site web, serveur applicatif, base de données) et un service d'envoi d'emails pour la réinitialisation du mot de passe. Pour afficher les fiches, couvertures et résumés, le service interroge des catalogues publics tels que Open Library, Google Books, Wikipédia ou AniList : seules les recherches de livres leur sont transmises, jamais ton email, ton mot de passe ni tes messages.",
        "Durée de conservation : tes données sont conservées tant que ton compte existe. La suppression du compte efface ton profil, ta bibliothèque, tes avis, tes relations et tes messages.",
        "Stockage sur ton appareil : l'application enregistre localement un jeton de connexion et tes préférences pour fonctionner. Elle n'utilise aucun traceur publicitaire.",
        `Tes droits : conformément au règlement général sur la protection des données (RGPD) et à la loi Informatique et Libertés, tu disposes d'un droit d'accès, de rectification, d'effacement, de limitation, d'opposition et de portabilité de tes données. ${contactSentence} Tu peux aussi introduire une réclamation auprès de la CNIL (cnil.fr).`,
      ],
    },
    {
      id: 'contenus',
      title: '5. Contenus publiés par les utilisateurs',
      body: [
        "Tu restes propriétaire des contenus que tu publies (avis, notes, biographie, photo, messages). Tu accordes à Booktime le droit de les stocker et de les afficher aux personnes que tu as choisies (amis, communauté) pour faire fonctionner le service, pendant la durée de ton compte.",
        "Tu es responsable de ce que tu publies. Tu garantis que tu as le droit de diffuser ces contenus (notamment ta photo) et qu'ils respectent la loi et les règles ci-dessous.",
      ],
    },
    {
      id: 'regles',
      title: '6. Règles de bonne conduite',
      body: [
        "Il est interdit de :",
        [
          "publier ou envoyer des contenus injurieux, haineux, discriminatoires, harcelants, violents, sexuellement explicites ou portant atteinte à la vie privée d'autrui ;",
          "usurper l'identité d'une autre personne ou créer de faux profils ;",
          "envoyer des messages non sollicités en masse (spam) ou de la publicité ;",
          "publier des contenus qui violent les droits d'auteur ou d'autres droits de tiers ;",
          "chercher à accéder à des comptes ou données qui ne sont pas les tiens, perturber le service, ou l'utiliser de façon automatisée pour en extraire les données ;",
          "utiliser le service à des fins illégales.",
        ],
      ],
    },
    {
      id: 'moderation',
      title: '7. Modération, suspension et suppression de compte',
      body: [
        "En cas de non-respect des CGU, l'éditeur peut masquer un contenu, suspendre un compte ou le supprimer, avec ou sans préavis selon la gravité des faits. Un compte suspendu ne peut plus se connecter ; ses avis sont masqués de la communauté.",
        "Tu peux supprimer ton compte à tout moment. L'éditeur peut aussi mettre fin au service ou à un compte inactif, en prévenant les utilisateurs dans un délai raisonnable lorsque c'est possible.",
      ],
    },
    {
      id: 'propriete',
      title: '8. Propriété intellectuelle',
      body: [
        "L'application Booktime (code, design, nom, logo) est protégée par le droit de la propriété intellectuelle. Son usage est limité à une utilisation personnelle dans le cadre du service.",
        "Les couvertures, résumés, titres et autres informations sur les livres proviennent de sources tierces et restent la propriété de leurs auteurs, éditeurs et ayants droit.",
      ],
    },
    {
      id: 'responsabilite',
      title: '9. Disponibilité et responsabilité',
      body: [
        "Le service est fourni gratuitement et « en l'état ». Il peut être interrompu pour maintenance, subir des lenteurs (notamment au réveil du serveur) ou comporter des erreurs, en particulier dans les informations issues de sources tierces (résumés, dates de sortie, estimations de temps de lecture, recommandations).",
        "L'éditeur ne garantit pas une disponibilité continue et n'est pas responsable des dommages indirects, ni de la perte de données due à un incident technique. Nous te conseillons d'exporter régulièrement ta bibliothèque depuis l'application.",
        "Ces limites s'appliquent dans la mesure permise par la loi et ne remettent pas en cause les droits que la loi te reconnaît.",
      ],
    },
    {
      id: 'evolution',
      title: '10. Modification des CGU',
      body: [
        `Les CGU peuvent évoluer, par exemple lorsqu'une fonctionnalité est ajoutée. La version en vigueur est datée du ${TERMS_UPDATED_LABEL}. En cas de modification importante, les utilisateurs en sont informés dans l'application ; continuer à l'utiliser après cette information vaut acceptation de la nouvelle version.`,
      ],
    },
    {
      id: 'droit',
      title: '11. Droit applicable',
      body: [
        "Les CGU sont soumises au droit français. En cas de litige, une solution amiable sera recherchée en priorité. À défaut, les tribunaux compétents seront ceux déterminés par les règles légales applicables, sans préjudice des droits dont tu disposes en tant que consommateur.",
      ],
    },
  ];

  return sections;
}
