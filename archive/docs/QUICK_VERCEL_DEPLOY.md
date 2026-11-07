# 🚀 DÉPLOIEMENT RAPIDE VERCEL FULLSTACK

## ⚡ COMMANDES ESSENTIELLES

### 1. Installer Vercel CLI
```bash
npm i -g vercel
```

### 2. Se connecter
```bash
vercel login
# Suivre les instructions
```

### 3. Déployer (depuis /app/)
```bash
vercel --prod
```

---

## 📋 VARIABLES ENVIRONNEMENT À CONFIGURER

Dans le Dashboard Vercel → Settings → Environment Variables :

```
MONGO_URL = mongodb+srv://user:password@cluster.mongodb.net/booktime?retryWrites=true&w=majority
EMERGENT_LLM_KEY = sk-emergent-xxxxx (optionnel)
ENVIRONMENT = production
```

---

## ✅ TESTS APRÈS DÉPLOIEMENT

```bash
# Frontend
curl https://votre-app.vercel.app

# API Health
curl https://votre-app.vercel.app/api/health

# Réponse attendue API :
{
  "status": "ok",
  "database": "connected",
  "timestamp": "...",
  "environment": "production",
  "version": "1.0.0"
}
```

---

## 🎯 RÉSULTAT

✅ **Frontend + Backend sur même domaine**
✅ **MongoDB Atlas intégré**  
✅ **HTTPS automatique**
✅ **Auto-deploy via Git**

**BOOKTIME VERCEL FULLSTACK READY! 🚀**