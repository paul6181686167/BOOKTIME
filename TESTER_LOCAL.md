# Tester Booktime en local (nouvelles données Wikidata)

## Prérequis

- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- Fichiers à la racine `BOOKTIME-main/` :
  - `wikidata_series_db.json` (~154 Mo, **532 104** séries indexées)
  - `popular_standalone_books.json` (~10 000 livres populaires hors série)
- `backend/.env` : `SECRET_KEY`, `MONGO_URL` ou `RAILWAY_MONGODB_MOCK=true`, `GOOGLE_BOOKS_API_KEY` (optionnel mais utile pour les couvertures en modale série)

## 1. Vérifier les exports Wikidata

```powershell
cd "d:\Booktime\Nouveau dossier\BOOKTIME-main"
python verify_wikidata_series_export.py
```

Attendu : compteurs alignés (~532k séries), pas d’erreur bloquante en fin de script.

## 2. Démarrer le backend

```powershell
cd backend
python server.py
```

- API : http://localhost:8001  
- Swagger : http://localhost:8001/docs  
- Redis absent = normal (mode dégradé sans cache).

## 3. Démarrer le frontend

```powershell
cd frontend
npm install
npm start
```

- App : http://localhost:3000  
- `frontend/.env` : `REACT_APP_API_URL=http://localhost:8001`

## 4. Scénarios de test (nouvelles données)

### Compte

1. Créer un compte (email + mot de passe) ou se connecter.
2. Le JWT est stocké dans `localStorage` (`token`).

### Recherche globale (barre d’accueil)

1. Chercher **Harry Potter**, **One Piece**, **Astérix**.
2. Vérifier :
   - livres Open Library ;
   - cartes série OL regroupées par tome ;
   - cartes **Wikidata** (badge / `isStaticWikidataCard`) ;
   - pas de doublon évident WD + OL pour le même titre/auteur.

### Modale série Wikidata

1. Cliquer une carte Wikidata → chargement `GET /api/static-wikidata/series/{qid}`.
2. Liste des tomes : fusion **WD + OL + Google Books** (couvertures si clé API OK).
3. Bouton **JSON Wikidata** (aperçu brut) si présent.
4. **Ajouter à ma bibliothèque** → tomes issus de `mergedLibraryVolumes`.

### Modale série Open Library / live

1. Carte série issue d’OL ou recherche auteur → modale avec merge OL + WD live si trouvé.

### Bibliothèque séries

1. Après ajout : onglet bibliothèque / séries → série visible, tomes cohérents.

### API rapide (Swagger ou curl)

Avec un token `Bearer …` :

- `GET /api/static-wikidata/status`
- `GET /api/static-wikidata/series/search?q=harry&limit=10`
- `GET /api/static-wikidata/series/top/by-popularity?limit=5`
- `GET /api/openlibrary/search?q=harry&limit=10`

## 5. Tests automatisés (optionnel)

```powershell
cd backend
python -m pytest tests/ -q

cd ..\frontend
npm run test:pipelines
```

## Backend qui « s’endort »

| Contexte | Cause | Solution |
|----------|--------|----------|
| **booktime.vercel.app** | Render gratuit : veille après ~15 min | `scripts\keep-render-warm.ps1` ou UptimeRobot sur `/ping` |
| **localhost:3000** | Pas de veille si le terminal backend reste ouvert | `scripts\start-local.ps1` |

Le front **force localhost:8001** quand tu es sur `localhost:3000` (pas Render).

Mode dev : `backend/.env.local` avec `RAILWAY_MONGODB_MOCK=true` (données en mémoire, **sans toucher Mongo Atlas**).

## Dépannage

| Problème | Piste |
|----------|--------|
| Cartes Wikidata vides | `wikidata_series_db.json` absent ou mauvais chemin (`WIKIDATA_SERIES_DB_PATH` dans `.env`) |
| 401 sur recherche OL / WD | Se reconnecter (JWT expiré) |
| Pas de couvertures GB | Renseigner `GOOGLE_BOOKS_API_KEY` dans `backend/.env` |
| Front ne compile pas | `npm start` : `DISABLE_ESLINT_PLUGIN=true` dans `frontend/.env` |
| Mongo lent / erreur | `backend/.env.local` → `RAILWAY_MONGODB_MOCK=true` |
| 1er clic Wikidata lent | Normal sans préchargement ; au redémarrage le backend précharge l’index (~15 s) |
