# Guide de déploiement Booktime

## Architecture
```
Vercel (frontend React)  →  Render (backend FastAPI)  →  MongoDB Atlas
```

---

## ÉTAPE 1 — Pousser le code sur GitHub

```bash
cd "d:\Booktime\Nouveau dossier\BOOKTIME-main"
git add .
git commit -m "config: ajout render.yaml + préparation déploiement"
git push origin main
```

> ⚠️ Si c'est ton premier push, crée d'abord le repo sur github.com
> puis : git remote add origin https://github.com/TON_USERNAME/booktime.git

---

## ÉTAPE 2 — Déployer le backend sur Render

### 2a — Créer le compte
1. Va sur [render.com](https://render.com) → "Get Started for Free"
2. Connecte-toi avec GitHub

### 2b — Créer le service web
1. Dashboard → **"New +"** → **"Web Service"**
2. Connecte ton repo GitHub booktime
3. Render détecte automatiquement le `render.yaml` → confirme
4. Vérifie ces paramètres :
   - **Name** : `booktime-backend`
   - **Root Directory** : `backend`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `python start_render.py`
   - **Plan** : Free

### 2c — Variables d'environnement (OBLIGATOIRE)
Dans Render → ton service → **"Environment"** → ajoute :

| Variable | Valeur |
|---|---|
| `MONGO_URL` | Copie depuis MongoDB Atlas (voir ci-dessous) |
| `ENVIRONMENT` | `production` |
| `RAILWAY_MONGODB_MOCK` | `false` |
| `CORS_ORIGINS` | `https://booktime.vercel.app,http://localhost:3000` |

> La variable `SECRET_KEY` est générée automatiquement par Render ✅

### 2d — Récupérer MONGO_URL depuis MongoDB Atlas
1. Va sur [cloud.mongodb.com](https://cloud.mongodb.com)
2. Ton cluster → **"Connect"** → **"Drivers"**
3. Copie la chaîne de connexion (commence par `mongodb+srv://...`)
4. Remplace `<password>` par ton vrai mot de passe

### 2e — Déployer
- Render démarre le déploiement automatiquement
- Attends 2-3 minutes → tu verras "Live" en vert
- Note l'URL : `https://booktime-backend.onrender.com`

### 2f — Tester le backend
Ouvre dans ton navigateur :
```
https://booktime-backend.onrender.com/health
```
Tu dois voir : `{"status": "ok", ...}`

---

## ÉTAPE 3 — Déployer le frontend sur Vercel

### 3a — Créer le compte
1. Va sur [vercel.com](https://vercel.com) → "Sign Up"
2. Connecte-toi avec GitHub

### 3b — Importer le projet
1. Dashboard → **"New Project"**
2. Importe ton repo GitHub booktime
3. Configure :
   - **Framework Preset** : Create React App
   - **Root Directory** : `frontend`
4. Clique **"Deploy"**

### 3c — Variables d'environnement Vercel
Settings → Environment Variables → ajoute :

| Variable | Valeur |
|---|---|
| `REACT_APP_BACKEND_URL` | `https://booktime-backend.onrender.com` |
| `REACT_APP_ENVIRONMENT` | `production` |

> ⚠️ Si l'URL Render est différente de `booktime-backend.onrender.com`,
> mets à jour `frontend/vercel.json` et cette variable.

### 3d — Redéployer après changement de variables
Settings → Deployments → **"Redeploy"**

---

## ÉTAPE 4 — Vérifier que tout fonctionne

1. **Backend** : `https://booktime-backend.onrender.com/health` → `{"status":"ok"}`
2. **Frontend** : `https://booktime.vercel.app` → l'app se charge
3. **Login** : crée un compte → vérifie que ça se connecte à MongoDB
4. **Catalogue** : recherche un livre → les résultats apparaissent

---

## ⚠️ Notes importantes

### Cold start Render (plan gratuit)
Le backend "s'endort" après 15 minutes d'inactivité.
Le premier appel après inactivité prend ~30 secondes.
**Solution** : utilise [UptimeRobot](https://uptimerobot.com) (gratuit) pour
pinger `/health` toutes les 14 minutes → le backend reste éveillé.

### Catalogue (catalog_cache.json)
Ce fichier (142 MB) est exclu du git car trop lourd pour GitHub.
Sur Render, le catalogue démarrera vide pour les romans.
Les manga/BD (manga_bd_cache.json, 3.5 MB) sont disponibles.

Pour remplir le catalogue complet après déploiement :
→ Va dans Render → ton service → **"Shell"** → exécute :
```bash
python scripts/seed_catalog.py
```

### Mises à jour futures
Chaque `git push` sur `main` redéclenche automatiquement :
- Le build Render (backend)
- Le build Vercel (frontend)
Les données MongoDB ne sont JAMAIS effacées par les mises à jour.

---

## URLs de production

| Service | URL |
|---|---|
| Frontend | https://booktime.vercel.app |
| Backend API | https://booktime-backend.onrender.com |
| Santé backend | https://booktime-backend.onrender.com/health |
