# BOOKTIME 📚

Une application de tracking de livres inspirée de TV Time, pour gérer votre collection de Romans, BD et Mangas.

## Fonctionnalités

- 🏷️ **3 catégories** : Roman, BD, Manga
- 📖 **Statuts** : À lire, En cours, Terminé
- ⭐ **Notes et avis**
- 📊 **Progression** (pages lues)
- 🔍 **Recherche et filtres**
- 📱 **Interface responsive**

## Stack Technique

- **Frontend** : React + Tailwind CSS
- **Backend** : FastAPI (Python)
- **Base de données** : MongoDB

## Installation

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

**Configuration** : copier `backend/.env.example` en `backend/.env` et renseigner les variables (voir section Variables d'environnement ci-dessous).

```bash
python server.py
```

Le backend démarre sur **http://localhost:8001**.

### 2. Frontend

```bash
cd frontend
yarn install
yarn start
```

Le frontend démarre sur **http://localhost:3000**.

> **Sécurité** : Ne jamais committer le fichier `.env` (il contient des secrets). Il est exclu via `.gitignore`.

### Variables d'environnement (backend)

| Variable | Description |
|----------|-------------|
| `RAILWAY_MONGODB_MOCK` | `true` = mode MOCK (données en mémoire, pas de MongoDB) ; `false` = connexion MongoDB réelle |
| `MONGO_URL` | URL MongoDB (local : `mongodb://localhost:27017/booktime` ou Atlas) |
| `SECRET_KEY` | Clé JWT. Générer : `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CORS_ORIGINS` | Origines autorisées (ex. `http://localhost:3000`) |

### Mode MOCK

Quand `RAILWAY_MONGODB_MOCK=true`, l'app fonctionne sans MongoDB : les données sont stockées en mémoire. Utile pour tester rapidement, mais les données sont perdues au redémarrage du serveur.

### Documentation API (Swagger)

Une fois le backend lancé : **http://localhost:8001/docs**

## Déploiement vers GitHub

```bash
git add .
git commit -m "BOOKTIME - Application de tracking de livres"
git push origin main
```
