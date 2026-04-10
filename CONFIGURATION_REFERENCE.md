# 🔧 CONFIGURATION RÉFÉRENCE - APPLICATION BOOKTIME ENTERPRISE

## 📋 VARIABLES D'ENVIRONNEMENT

### Frontend Configuration (/app/frontend/)

**`.env.local` (Développement)** :
```bash
DANGEROUSLY_DISABLE_HOST_CHECK=true
HOST=0.0.0.0
PORT=3000
REACT_APP_BACKEND_URL=http://localhost:8001
```

**`.env` (Principal)** :
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
PORT=3000
GENERATE_SOURCEMAP=false
```

### Backend Configuration (/app/backend/)

**`.env` (Principal)** :
```bash
MONGO_URL=mongodb://localhost:27017/booktime
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## 🏗️ ARCHITECTURE SERVICES

### Services Supervisor
```bash
backend     → FastAPI sur port 8001 (interne)
frontend    → React sur port 3000 (interne)  
mongodb     → MongoDB sur port 27017 (interne)
code-server → Développement IDE
```

### Commandes Service
```bash
# Statut services
sudo supervisorctl status

# Redémarrage individuel
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Redémarrage complet
sudo supervisorctl restart all
```

## 📊 PORTS ET URLS

### Accès Application
- **Frontend** : http://localhost:3000
- **Backend API** : http://localhost:8001
- **Health Check** : http://localhost:8001/health
- **Documentation API** : http://localhost:8001/docs

### URLs Internes
- **MongoDB** : mongodb://localhost:27017/booktime
- **Backend Health** : GET /health
- **API Base** : http://localhost:8001/api

## 🔌 ENDPOINTS API PRINCIPAUX

### Authentification
```bash
POST /api/auth/login     # Connexion utilisateur
POST /api/auth/register  # Inscription utilisateur
GET  /api/auth/me        # Profil utilisateur
```

### Gestion Livres
```bash
GET    /api/books            # Liste livres utilisateur
POST   /api/books            # Créer nouveau livre
PUT    /api/books/{book_id}  # Mettre à jour livre
DELETE /api/books/{book_id}  # Supprimer livre
```

### Système Séries
```bash
GET  /api/series/popular     # Séries populaires
GET  /api/series/search      # Recherche séries
POST /api/series/complete    # Auto-complétion série
```

### Intégrations Externes
```bash
GET  /api/openlibrary/search    # Recherche Open Library
POST /api/openlibrary/import    # Import depuis Open Library
GET  /api/wikipedia/author/{name}  # Profil auteur Wikipedia
GET  /api/wikidata/author/{name}   # Données auteur Wikidata
```

## 🗄️ STRUCTURE BASE DE DONNÉES

### Collections MongoDB

**users** :
```javascript
{
  id: "uuid-string",
  first_name: "string",
  last_name: "string",
  created_at: "ISODate"
}
```

**books** :
```javascript
{
  id: "uuid-string",
  user_id: "uuid-string",
  title: "string",
  author: "string",
  category: "roman|bd|manga",
  status: "to_read|reading|completed",
  // ... autres champs
}
```

## 📦 DÉPENDANCES PRINCIPALES

### Backend Python (requirements.txt)
```
fastapi>=0.115.0
starlette>=0.46.0
uvicorn==0.22.0
pymongo==4.6.0
motor==3.3.2
python-jose==3.3.0
bcrypt==4.1.2
# ... autres dépendances
```

### Frontend Node.js (package.json)
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.8.0",
  "axios": "^1.6.0",
  "tailwindcss": "^3.3.2"
}
```

## 🔒 SÉCURITÉ ET AUTHENTIFICATION

### Système JWT
- **Durée token** : 1440 minutes (24h)
- **Algorithme** : HS256
- **Stockage** : localStorage côté frontend
- **Validation** : Middleware FastAPI routes protégées

### Authentification Simplifiée
- **Méthode** : Prénom + Nom uniquement (pas de mot de passe)
- **Validation** : Existence utilisateur en base
- **Token** : JWT avec payload minimal (id, prénom, nom)

## 🎨 CONFIGURATION INTERFACE

### Tailwind CSS
```javascript
// tailwind.config.js
experimental: {
  optimizeUniversalDefaults: true,
},
corePlugins: {
  // Plugins désactivés pour performance
}
```

### Classes CSS Principales
```css
.modal-content-wide {
  max-width: 1024px;  /* Modals détaillés */
}

.modal-content {
  max-width: 500px;   /* Modals basiques */
}
```

## 🚀 DÉPLOIEMENT ET PRODUCTION

### Variables Production
```bash
NODE_ENV=production
REACT_APP_BACKEND_URL=https://your-domain.com/api
MONGO_URL=mongodb://production-host:27017/booktime
```

### Build Production
```bash
# Frontend
cd /app/frontend
yarn build

# Backend
cd /app/backend
pip install -r requirements.txt
```

## 📋 MONITORING ET HEALTH CHECKS

### Health Check Endpoint
```bash
GET /health
Response: {
  "status": "ok",
  "database": "connected", 
  "timestamp": "2025-09-07T18:50:06.979519"
}
```

### Logs Services
```bash
# Logs backend
tail -f /var/log/supervisor/backend.*.log

# Logs frontend  
tail -f /var/log/supervisor/frontend.*.log
```

## 🔧 DÉPANNAGE COMMUN

### Problème Host Header
**Solution** : Ajouter dans `/app/frontend/.env.local` :
```bash
DANGEROUSLY_DISABLE_HOST_CHECK=true
HOST=0.0.0.0
```

### Services Non Démarrés
**Solution** :
```bash
sudo supervisorctl restart all
```

### Erreur Base Données
**Vérification** :
```bash
curl -s http://localhost:8001/health
```

---
*Configuration référence - Application BOOKTIME Enterprise - Septembre 2025*