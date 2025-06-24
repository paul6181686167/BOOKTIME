# 🚀 Guide de Déploiement BOOKTIME

## Solution de Déploiement Rapide (Phase de Test)

### Architecture de Déploiement
- **Frontend** : Vercel (React)
- **Backend** : Railway (FastAPI)
- **Base de données** : MongoDB Atlas (Cloud)

---

## 📋 Prérequis

1. **Compte GitHub** (pour le code)
2. **Compte Vercel** (gratuit) : https://vercel.com
3. **Compte Railway** (gratuit) : https://railway.app
4. **Compte MongoDB Atlas** (gratuit) : https://www.mongodb.com/atlas

---

## 🗄️ Étape 1 : Configuration MongoDB Atlas

### 1.1 Créer une base de données
```bash
1. Aller sur https://www.mongodb.com/atlas
2. Créer un compte gratuit
3. Créer un nouveau projet "BOOKTIME"
4. Créer un cluster (M0 Sandbox - Gratuit)
5. Attendre la création (2-3 minutes)
```

### 1.2 Configuration de sécurité
```bash
1. Database Access → Add New Database User
   - Username: booktime_user
   - Password: [générer un mot de passe fort]
   - Role: Read and write to any database

2. Network Access → Add IP Address
   - IP Address: 0.0.0.0/0 (Allow access from anywhere)
   - Description: "All IPs for Railway deployment"
```

### 1.3 Récupérer l'URL de connexion
```bash
1. Clusters → Connect → Connect your application
2. Driver: Python, Version: 3.12 or later
3. Copier l'URL de connexion (format):
   mongodb+srv://booktime_user:<password>@cluster0.xxxxx.mongodb.net/booktime?retryWrites=true&w=majority
```

---

## 🖥️ Étape 2 : Déploiement Backend (Railway)

### 2.1 Préparer Railway
```bash
1. Aller sur https://railway.app
2. Se connecter avec GitHub
3. New Project → Deploy from GitHub repo
4. Sélectionner votre repo BOOKTIME
5. Railway détecte automatiquement le Dockerfile
```

### 2.2 Variables d'environnement Railway
```bash
Dans Railway → Variables:
- MONGO_URL: [votre URL MongoDB Atlas]
- SECRET_KEY: [générer une clé secrète]
- ALGORITHM: HS256
- ACCESS_TOKEN_EXPIRE_MINUTES: 30
```

### 2.3 Déploiement
```bash
1. Railway démarre automatiquement le build
2. Attendre la fin du déploiement (3-5 minutes)
3. Noter l'URL générée: https://[nom-projet].railway.app
```

---

## 🌐 Étape 3 : Déploiement Frontend (Vercel)

### 3.1 Préparer Vercel
```bash
1. Aller sur https://vercel.com
2. Se connecter avec GitHub
3. Import Project → Sélectionner votre repo BOOKTIME
4. Framework Preset: Create React App
5. Root Directory: frontend/
```

### 3.2 Variables d'environnement Vercel
```bash
Dans Vercel → Settings → Environment Variables:
- REACT_APP_BACKEND_URL: https://[votre-url-railway].railway.app
```

### 3.3 Configuration Build
```bash
Build Command: yarn build
Output Directory: build
Install Command: yarn install
```

### 3.4 Déploiement
```bash
1. Cliquer "Deploy"
2. Attendre le build (2-3 minutes)
3. Votre app est disponible : https://[nom-projet].vercel.app
```

---

## ✅ Étape 4 : Tests et Vérification

### 4.1 Test Backend
```bash
1. Ouvrir: https://[votre-backend].railway.app
2. Vérifier: {"message": "Welcome to BOOKTIME API 📚"}
3. Tester API: https://[votre-backend].railway.app/api/books
```

### 4.2 Test Frontend
```bash
1. Ouvrir: https://[votre-frontend].vercel.app
2. Vérifier que l'interface se charge
3. Tester l'ajout d'un livre
4. Vérifier la connexion à l'API
```

---

## 🔧 Dépannage Rapide

### Erreur de CORS
```bash
Si erreur CORS, vérifier que REACT_APP_BACKEND_URL est correct dans Vercel
```

### Erreur MongoDB
```bash
1. Vérifier l'URL MongoDB dans Railway
2. Vérifier que l'IP 0.0.0.0/0 est autorisée dans Atlas
3. Vérifier le mot de passe (pas de caractères spéciaux)
```

### Build Frontend échoue
```bash
1. Vérifier que yarn.lock existe dans frontend/
2. Nettoyer le cache Vercel et redéployer
```

---

## 🚀 Déploiement Automatique

Une fois configuré, chaque push sur `main` déclenche :
1. Tests automatiques (GitHub Actions)
2. Build et déploiement automatique sur Railway (backend)
3. Build et déploiement automatique sur Vercel (frontend)

---

## 📱 URLs Finales

- **Frontend** : https://[nom-projet].vercel.app
- **Backend API** : https://[nom-projet].railway.app
- **Admin MongoDB** : https://cloud.mongodb.com

Ces URLs restent **privées** et non-indexées par défaut.

---

## 🔒 Sécurité pour les Tests

- URLs privées (non-indexées)
- Authentification MongoDB
- Variables d'environnement sécurisées
- HTTPS par défaut sur toutes les plateformes

**Temps total de déploiement : 15-20 minutes** ⚡