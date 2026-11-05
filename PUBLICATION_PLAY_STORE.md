# Publier Booktime sur le Google Play Store

L'application Android est un conteneur [Capacitor](https://capacitorjs.com/) qui embarque le
frontend React. Le projet natif vit dans `frontend/android/` et le bundle web y est recopié à
chaque synchronisation.

---

## 1. Construire une nouvelle version

Prérequis déjà installés sur cette machine : JDK 21 (Temurin) et le SDK Android 36
(`%LOCALAPPDATA%\Android\Sdk`). Les variables `JAVA_HOME`, `ANDROID_HOME` et `ANDROID_SDK_ROOT`
ont été ajoutées à l'environnement utilisateur.

```powershell
cd frontend
npm run android:bundle   # AAB signé, pour le Play Store
npm run android:apk      # APK signé, pour tester sur un téléphone
```

Artefacts produits :

| Fichier | Chemin |
|---------|--------|
| AAB (Play Store) | `frontend/android/app/build/outputs/bundle/release/app-release.aab` |
| APK (test direct) | `frontend/android/app/build/outputs/apk/release/app-release.apk` |

Avant chaque nouvelle publication, incrémenter `versionCode` (entier, strictement croissant) et
`versionName` (visible par l'utilisateur) dans `frontend/android/app/build.gradle`.

L'URL du backend est figée au moment du build, dans le script `build:native` de
`frontend/package.json`. Si le backend change d'adresse, c'est là qu'il faut la modifier.

---

## 2. Clé de signature

La clé d'upload se trouve dans **`D:\Booktime\booktime-signing\`** :

- `booktime-upload.jks` — le magasin de clés, alias `booktime-upload`
- `MOT-DE-PASSE.txt` — le mot de passe

Gradle la lit via `frontend/android/keystore.properties`, exclu du dépôt Git.

> **Sauvegardez ce dossier hors de l'ordinateur** (cloud chiffré, clé USB). Sans cette clé, plus
> aucune mise à jour de l'application ne peut être publiée. Activez également *Play App Signing*
> lors de la création de l'application dans la console : Google conserve alors la clé de
> signature finale et une clé d'upload perdue peut être réinitialisée.

---

## 3. Compte Google Play Console

1. Créez le compte sur [play.google.com/console](https://play.google.com/console) — frais uniques
   de 25 $. La vérification d'identité prend de quelques heures à une semaine.
2. Choisissez le type de compte en connaissance de cause :
   - **Compte personnel** : vous devrez faire un **test fermé avec 12 testeurs restés inscrits
     14 jours consécutifs** avant de pouvoir demander l'accès à la production.
   - **Compte organisation** (nécessite un numéro D-U-N-S) : exempté de cette obligation, mais la
     vérification est plus longue.

---

## 4. Créer l'application

| Champ | Valeur |
|-------|--------|
| Nom de l'application | Booktime |
| Langue par défaut | Français (France) |
| Type | Application |
| Gratuite ou payante | Gratuite |
| Nom du package | `com.booktime.app` |

Le nom du package est **définitif** : il ne pourra jamais être modifié après la première
publication.

---

## 5. Fiche Play Store

**Description courte** (80 caractères maximum) :

```
Suis tes lectures, gère ta bibliothèque et découvre quoi lire ensuite.
```
(76 caractères)

**Description complète** (4000 caractères maximum) — à coller dans la Play Console :

```
Booktime est ton carnet de lecture personnel. Ajoute tes livres, romans, mangas et bandes dessinées, suis ta progression et retrouve d’un coup d’œil tout ce que tu as lu.

CE QUE TU PEUX FAIRE

• Constituer ta bibliothèque en quelques secondes : recherche par titre ou auteur, ou scanne le code-barres ISBN.
• Suivre ta progression : à lire, en cours, terminé, à relire — avec la page en cours et les dates.
• Gérer tes séries : Booktime reconnaît les sagas (BD, manga, romans) et regroupe les tomes.
• Recevoir des recommandations et trouver des livres similaires à ceux que tu aimes.
• Voir les prochaines sorties des séries et auteurs que tu suis.
• Noter et commenter tes lectures.
• Fixer un objectif annuel et visualiser ton rythme.
• Exporter ta bibliothèque (JSON, CSV, Excel) et importer depuis Goodreads.

CONÇU POUR LES LECTEURS

Les fiches sont enrichies automatiquement (couverture, résumé, pages) via des catalogues publics : Open Library, Wikidata, Google Books.

RESPECTUEUX DE TA VIE PRIVÉE

Pas de publicité, pas de pistage, pas de revente de données. Tu peux exporter ou supprimer ton compte à tout moment.
```

**Catégorie Play Store suggérée :** Livres et ouvrages de référence  
**Tags / mots-clés (fiche) :** lecture, bibliothèque, livres, manga, BD, ISBN

**Éléments graphiques à fournir :**

| Élément | Format requis | Où le trouver |
|---------|---------------|---------------|
| Icône | PNG 512 × 512 | `frontend/public/play-store/icon-512.png` |
| Image de présentation | PNG 1024 × 500 | `frontend/public/play-store/feature-graphic.png` |
| Captures de téléphone | 2 minimum, 8 maximum, entre 320 et 3840 px de côté | à prendre sur le téléphone (voir ci-dessous) |

Régénérer l'image de présentation si besoin :

```powershell
python scripts/make_feature_graphic.py
```

**Captures téléphone (à faire sur l'APK installé)** — viser 5 écrans sans barre de notification si possible :

1. Bibliothèque (grille avec couvertures)
2. Fiche d'un livre (progression / statut)
3. Série avec tomes regroupés
4. Recommandations ou similaires
5. Statistiques / objectif annuel

Ne pas utiliser l'écran de connexion (l'URL API de debug y apparaît encore).

---

## 6. Politique de confidentialité

Pages en ligne (domaine Vercel actuel) :

- Politique : https://booktime-paul6181686167s-projects.vercel.app/privacy.html
- Suppression de compte : https://booktime-paul6181686167s-projects.vercel.app/delete-account.html

À coller dans la Play Console : la première dans *Règles de confidentialité*, la seconde dans
*Suppression du compte* (section « Sécurité des données »).

> **À faire** : remplacer `ADRESSE-EMAIL-A-COMPLETER` dans `frontend/public/privacy.html` et
> `frontend/public/delete-account.html` par une adresse e-mail réellement relevée, puis
> redéployer. Sans ça, Google peut refuser la fiche.

---

## 7. Formulaire « Sécurité des données »

Réponses conformes au code actuel de l'application.

**Questions générales**

| Question | Réponse |
|----------|---------|
| L'application collecte-t-elle des données utilisateur ? | Oui |
| Les données sont-elles chiffrées en transit ? | Oui (HTTPS) |
| L'utilisateur peut-il demander la suppression de ses données ? | Oui, depuis l'application et via une page web |
| Des données sont-elles partagées avec des tiers ? | Non |

**Types de données collectées**

| Type | Collectée | Partagée | Obligatoire | Finalité |
|------|-----------|----------|-------------|----------|
| Adresse e-mail | Oui | Non | Oui | Gestion du compte |
| Identifiants de connexion | Oui | Non | Oui | Gestion du compte |
| Autres contenus générés par l'utilisateur (bibliothèque, notes, avis) | Oui | Non | Oui | Fonctionnalité de l'application |
| Journaux de plantage | Oui | Non | Non | Diagnostic |
| Diagnostics et performances | Oui | Non | Non | Diagnostic |

Ne déclarez **rien** pour : position, informations financières, contacts, photos et vidéos,
fichiers audio, santé, identifiants publicitaires, historique de navigation, SMS. L'application
n'y touche pas.

Justification de l'accès à la caméra, si Google la demande : *l'accès à la caméra sert uniquement
à scanner un code-barres ISBN pour ajouter un livre. L'image est analysée sur l'appareil, elle
n'est ni stockée ni transmise.*

---

## 8. Autres déclarations obligatoires

| Section | Réponse |
|---------|---------|
| Classification du contenu | Questionnaire IARC : aucune violence, aucun contenu sexuel, aucun jeu d'argent. Catégorie attendue : Tout public |
| Public cible | 13 ans et plus (l'application n'est pas destinée aux enfants) |
| Publicités | L'application ne contient pas de publicités |
| Application gouvernementale | Non |
| Application financière | Non |
| COVID-19 | Non concerné |
| Sécurité des applications | Aucune API sensible utilisée hors caméra |

---

## 9. Parcours de publication

1. **Test interne** — jusqu'à 100 testeurs, disponible immédiatement. Commencez par là pour
   vérifier l'installation et le fonctionnement réel sur plusieurs téléphones.
2. **Test fermé** — obligatoire pour un compte personnel. Recrutez 15 à 20 personnes pour garder
   une marge : si le nombre de testeurs inscrits passe sous 12, le compteur des 14 jours repart
   de zéro. Les testeurs doivent réellement installer et ouvrir l'application, Google vérifie
   l'activité.
3. **Demande d'accès à la production** — une fois les 14 jours écoulés, depuis le tableau de bord.
4. **Publication** — la première revue prend généralement de quelques jours à deux semaines.

Comptez environ trois à quatre semaines entre l'ouverture du compte et la mise en ligne publique.

---

## 10. Points à traiter avant le test fermé

**Le réveil du backend.** Le serveur est hébergé sur Render. Si l'offre utilisée est la formule
gratuite, il se met en veille après quinze minutes d'inactivité et la requête suivante prend
environ cinquante secondes. Au lancement de l'application, cela donne un écran qui semble figé —
la pire impression possible pour un testeur comme pour un évaluateur Google. Trois options :
passer Render en formule payante, maintenir le service éveillé avec un ping externe toutes les
dix minutes, ou afficher dans l'application un message explicite pendant le réveil.

**Le CORS du backend.** Les origines `https://localhost`, `http://localhost` et
`capacitor://localhost` ont été ajoutées dans `backend/app/main.py`. Ce changement doit être
déployé sur Render, sinon toutes les requêtes de l'application Android seront rejetées. Pour un
effet immédiat sans redéploiement, ajoutez plutôt dans le tableau de bord Render la variable
d'environnement :

```
CORS_ORIGINS=https://localhost,http://localhost,capacitor://localhost
```

**Le déploiement du frontend.** Les pages `privacy.html` et `delete-account.html` doivent être en
ligne avant de renseigner leurs URL dans la console.

---

## 11. Publier une mise à jour

```powershell
cd frontend
# 1. incrémenter versionCode et versionName dans android/app/build.gradle
npm run android:bundle
```

Puis déposez le nouvel AAB dans la console. Le code web modifié est automatiquement réintégré :
`android:bundle` enchaîne la compilation React, la synchronisation Capacitor et la construction
Gradle.
