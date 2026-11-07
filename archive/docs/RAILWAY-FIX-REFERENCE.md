# 🚂 Référence Rapide - Correction Railway BOOKTIME

## ⚡ Solution Express

### Erreur
```bash
Error: Invalid value for '--port': '$PORT' is not a valid integer.
```

### Fix Immédiat
```json
// railway.json - AVANT (INCORRECT)
"startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT"

// railway.json - APRÈS (CORRECT)  
"startCommand": "python start.py"
```

## 📋 Checklist Déploiement Railway

### ✅ Configuration Fichiers
- [ ] `railway.json` utilise `"python start.py"`
- [ ] `start.py` existe et gère PORT robustement  
- [ ] `Dockerfile` utilise `CMD python start.py`
- [ ] Root Directory Railway = `/backend`

### ✅ Variables Environnement
- [ ] `MONGO_URL` définie (MongoDB Atlas connection string)
- [ ] `EMERGENT_LLM_KEY` définie (clé LLM universelle)
- [ ] `PORT` NOT définie (Railway auto)

### ✅ Validation Locale
```bash
# Test diagnostic
python railway-debug.py

# Test démarrage
PORT=3000 python start.py

# Test health check
curl http://localhost:3000/health
```

## 🔧 Scripts Essentiels

### start.py (Démarrage Principal)
```python
import os
import uvicorn

def main():
    port = os.environ.get("PORT")
    if port is None:
        port = 8001
    else:
        try:
            port = int(port)
        except (ValueError, TypeError):
            port = 8001
    
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
```

### railway-debug.py (Diagnostic)
```python
import os

def main():
    print("🔍 DIAGNOSTIC RAILWAY")
    
    # Test variables critiques
    env_vars = ['PORT', 'MONGO_URL', 'EMERGENT_LLM_KEY']
    for var in env_vars:
        value = os.environ.get(var)
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {'SET' if value else 'NOT SET'}")
    
    # Test import app
    try:
        from app.main import app
        print("  ✅ Application: IMPORTABLE")
        return True
    except Exception as e:
        print(f"  ❌ Application: {e}")
        return False

if __name__ == "__main__":
    main()
```

## 🎯 Déploiement Step-by-Step

1. **Railway Dashboard** → New Project
2. **Deploy from GitHub** → Repo booktime  
3. **Settings** → Root Directory → `/backend`
4. **Variables** → Add `MONGO_URL` + `EMERGENT_LLM_KEY`
5. **Deploy** → Wait build complete
6. **Test** → `curl https://your-app.railway.app/health`

## 🚨 Troubleshooting Common

### Port Error Persiste
```bash
# Vérifiez railway.json
cat railway.json | grep startCommand
# Doit afficher: "startCommand": "python start.py"
```

### App Import Error
```bash
# Vérifiez Root Directory
# Railway Settings → Root Directory = /backend (pas /)
```

### Variables Missing
```bash
# Railway Dashboard → Settings → Variables
# MONGO_URL: mongodb+srv://...
# EMERGENT_LLM_KEY: sk-emergent-...
```

## 📚 Références

- **Session 90.3** : Plan déploiement original  
- **Session 90.11** : Correction erreur PORT
- **RAILWAY-DEPLOY.md** : Guide complet
- **CHANGELOG.md** : Documentation exhaustive

**🚂 Railway Fix Applied - Deployment Ready**