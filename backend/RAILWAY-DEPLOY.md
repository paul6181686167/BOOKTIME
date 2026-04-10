# 🚂 Déploiement Railway BOOKTIME Backend

## ✅ Correction Erreur PORT Appliquée

### Problème Résolu
- **Erreur** : `'$PORT' is not a valid integer`
- **Cause** : Variable `$PORT` non résolue dans `railway.json`
- **Solution** : Script démarrage Python robuste

## 📋 Configuration Railway

### 1. Variables d'Environnement Requises
```bash
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/booktime
EMERGENT_LLM_KEY=sk-emergent-xxxxxxxxxxxxx
```
**Note** : `PORT` est définie automatiquement par Railway

### 2. Configuration Repository
- **Root Directory** : `/backend` (IMPORTANT)
- **Build** : Dockerfile automatique
- **Deploy** : railway.json utilisé

### 3. Fichiers de Configuration

#### railway.json
```json
{
  "build": { "builder": "DOCKERFILE" },
  "deploy": {
    "startCommand": "python start.py",
    "healthcheckPath": "/health"
  }
}
```

#### Dockerfile
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD python start.py
```

## 🚀 Scripts de Démarrage

### start.py (Principal)
- Gestion robuste variable `PORT`
- Validation + fallback port 8001
- Logs détaillés démarrage
- Configuration production automatique

### railway-debug.py (Diagnostic)
```bash
python railway-debug.py
```
- Vérification variables environnement
- Test conversion PORT
- Validation fichiers critiques
- Test import application

## 📊 Validation Locale

### Test Configuration
```bash
# Test diagnostic complet
python railway-debug.py

# Test démarrage avec port custom
PORT=3000 python start.py

# Test health check
curl http://localhost:3000/health
```

### Réponses Attendues
- ✅ Variables masquées correctement
- ✅ PORT convertie en entier
- ✅ Application importée
- ✅ Démarrage sur port spécifié
- ✅ Health check : `{"status":"ok"}`

## 🔧 Troubleshooting

### Erreur Port
```bash
❌ Error: Invalid value for '--port': '$PORT'
```
**Solution** : Vérifiez que `railway.json` utilise `"startCommand": "python start.py"`

### Variables Manquantes
```bash
❌ MONGO_URL: NON DÉFINIE
```
**Solution** : Ajoutez variables dans Railway Dashboard → Settings → Variables

### Import Application
```bash
❌ Erreur import: No module named 'app'
```
**Solution** : Vérifiez Root Directory = `/backend` dans Railway

## 🎯 Déploiement Step-by-Step

1. **Railway Dashboard** → New Project
2. **Deploy from GitHub** → Sélectionner repo booktime
3. **Settings** → Root Directory → `/backend`
4. **Variables** → Ajouter `MONGO_URL` + `EMERGENT_LLM_KEY`
5. **Deploy** → Railway build automatique
6. **URL générée** → Tester `/health` endpoint

## ✅ Validation Déploiement

```bash
# Test health check production
curl https://your-app.railway.app/health

# Réponse attendue
{"status":"ok","database":"connected","environment":"production"}
```

**🚂 Configuration Railway Optimisée - Déploiement Garanti**