# 🚀 **GUIDE DE DÉPLOIEMENT SYSTÈME CHAPITRES BOOKTIME**

*Version 1.0 - Production Ready - Juillet 2025*

---

## 🎯 **APERÇU DU DÉPLOIEMENT**

Ce guide couvre le déploiement complet du système chapitres individuels de BookTime, incluant les **8 nouveaux endpoints**, les **intégrations externes**, et l'**interface frontend enrichie**.

### **Composants à Déployer**

- ✅ **Backend** : Nouveau module `chapters` avec 3,525 lignes de code
- ✅ **Frontend** : Composants `ChapterSection` + hook `useSeriesChapters`
- ✅ **Base de données** : Nouvelle collection `series_chapters` MongoDB
- ✅ **Intégrations** : AniList GraphQL + MangaUpdates + ChapterPredictor
- ✅ **Cache** : Redis/MongoDB + localStorage frontend

---

## 🛠️ **PRÉ-REQUIS SYSTÈME**

### **Infrastructure Minimale**

```bash
# Serveur Backend
CPU: 2 vCPUs (4 vCPUs recommandé)
RAM: 4 GB (8 GB recommandé)
Stockage: 20 GB SSD
OS: Ubuntu 20.04+ / CentOS 8+ / Docker

# Base de Données
MongoDB: 5.0+
RAM: 2 GB dédiée
Stockage: 10 GB pour données + index

# Cache (optionnel mais recommandé)
Redis: 6.0+
RAM: 1 GB
```

### **Versions Logicielles**

```bash
Python: 3.9+
Node.js: 18.0+
FastAPI: 0.116.1+
React: 18.2.0+
MongoDB: 5.0+
Docker: 20.10+ (si conteneurisation)
```

---

## 📦 **DÉPLOIEMENT BACKEND**

### **1. Préparation Environnement**

```bash
# Cloner le repository (si applicable)
git clone https://github.com/your-org/booktime.git
cd booktime

# Créer environnement virtuel Python
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Installer dépendances backend
cd backend
pip install -r requirements.txt

# Vérifier installation nouveau module
python -c "from app.chapters import routes; print('✅ Module chapters importé')"
```

### **2. Configuration Variables d'Environnement**

```bash
# backend/.env
MONGO_URL=mongodb://localhost:27017/booktime_prod
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
ENABLE_CHAPTERS_PREDICTIONS=true
CHAPTERS_CACHE_TTL_HOURS=3
ANILIST_RATE_LIMIT_SECONDS=1
MANGAUPDATES_RATE_LIMIT_SECONDS=2

# APIs externes (si clés nécessaires)
ANILIST_CLIENT_ID=your-anilist-client-id
ANILIST_CLIENT_SECRET=your-anilist-secret
```

### **3. Base de Données MongoDB**

```bash
# Connexion MongoDB
mongo

# Sélection base de données
use booktime_prod

# Création collection chapitres
db.createCollection("series_chapters")

# Index pour performances
db.series_chapters.createIndex({"series_name": 1})
db.series_chapters.createIndex({"cache_expires": 1})
db.series_chapters.createIndex({"manga_id_anilist": 1})
db.series_chapters.createIndex({"manga_id_mangaupdates": 1})

# Vérification collections
show collections
```

### **4. Tests Validation Backend**

```bash
# Test santé module chapitres
curl http://localhost:8001/api/chapters/health
# Attendu: {"status":"ok","module":"chapters","version":"1.0.0"}

# Test intégrations (avec token)
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/api/chapters/integrations/status

# Validation base de données
python -c "
from app.database import db
collection = db['series_chapters']
print(f'Collection created: {collection.name}')
"
```

### **5. Démarrage Services Backend**

```bash
# Mode développement
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Mode production avec Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker \
         --bind 0.0.0.0:8001 --timeout 120

# Avec supervisord (recommandé production)
sudo supervisorctl restart backend
```

---

## 🎨 **DÉPLOIEMENT FRONTEND**

### **1. Installation Dépendances**

```bash
cd frontend

# Installer avec Yarn (recommandé)
yarn install

# Ou avec npm
npm install

# Vérifier nouveaux composants
ls -la src/components/ChapterSection.js
ls -la src/hooks/useSeriesChapters.js
```

### **2. Configuration Variables d'Environnement**

```bash
# frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_ENABLE_CHAPTERS_FEATURE=true
REACT_APP_CHAPTERS_CACHE_DURATION=3600000
REACT_APP_NODE_ENV=production

# Pour production
REACT_APP_BACKEND_URL=https://api.your-domain.com
```

### **3. Build Production**

```bash
# Build optimisé
yarn build
# ou npm run build

# Vérifier taille bundle
du -sh build/static/js/*.js

# Test build local
serve -s build -l 3000
```

### **4. Déploiement Serveur Web**

#### **Option A : Nginx (Recommandé)**

```nginx
# /etc/nginx/sites-available/booktime
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/booktime/build;
    index index.html;

    # Gestion SPA React
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache statiques
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Compression
    gzip on;
    gzip_types text/css application/javascript application/json;
}
```

#### **Option B : Apache**

```apache
# /etc/apache2/sites-available/booktime.conf
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /var/www/booktime/build
    
    # SPA React support
    <Directory "/var/www/booktime/build">
        FallbackResource /index.html
    </Directory>
    
    # Cache headers
    <LocationMatch "\.(js|css|png|jpg|jpeg|gif|ico|svg)$">
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </LocationMatch>
</VirtualHost>
```

---

## 🐳 **DÉPLOIEMENT DOCKER**

### **1. Dockerfile Backend**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installation dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie code application
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Port exposition
EXPOSE 8001

# Commande démarrage
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8001"]
```

### **2. Dockerfile Frontend**

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html

# Configuration Nginx pour SPA
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### **3. Docker Compose Complet**

```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: booktime-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    environment:
      MONGO_INITDB_DATABASE: booktime_prod

  redis:
    image: redis:7-alpine
    container_name: booktime-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    container_name: booktime-backend
    ports:
      - "8001:8001"
    depends_on:
      - mongodb
      - redis
    environment:
      - MONGO_URL=mongodb://mongodb:27017/booktime_prod
      - REDIS_URL=redis://redis:6379
      - ENABLE_CHAPTERS_PREDICTIONS=true
    volumes:
      - ./backend:/app
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: booktime-frontend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
      - REACT_APP_ENABLE_CHAPTERS_FEATURE=true
    restart: unless-stopped

volumes:
  mongodb_data:
  redis_data:
```

### **4. Commandes Docker**

```bash
# Build et démarrage
docker-compose up -d --build

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Arrêt
docker-compose down

# Mise à jour
docker-compose pull && docker-compose up -d
```

---

## 🔧 **CONFIGURATION PRODUCTION**

### **1. Reverse Proxy (Nginx)**

```nginx
# /etc/nginx/sites-available/booktime-prod
upstream backend {
    server localhost:8001;
}

server {
    listen 80;
    server_name api.your-domain.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
        access_log off;
    }
}
```

### **2. SSL/HTTPS (Let's Encrypt)**

```bash
# Installation Certbot
sudo apt install certbot python3-certbot-nginx

# Génération certificats
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Auto-renouvellement
sudo crontab -e
# Ajouter: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **3. Monitoring et Logging**

```bash
# Logrotate pour logs application
# /etc/logrotate.d/booktime
/var/log/booktime/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 0644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}

# Prometheus monitoring (optionnel)
# Ajouter métriques FastAPI
pip install prometheus-fastapi-instrumentator
```

---

## 🧪 **TESTS DÉPLOIEMENT**

### **1. Tests Automatisés**

```bash
# Script de test déploiement
#!/bin/bash
# test_deployment.sh

echo "=== Tests Déploiement BookTime ==="

# 1. Health check backend
echo "🔍 Test backend health..."
curl -f http://localhost:8001/health || exit 1

# 2. Test module chapitres
echo "🔍 Test module chapitres..."
curl -f http://localhost:8001/api/chapters/health || exit 1

# 3. Test intégrations (nécessite token)
if [ -n "$TEST_TOKEN" ]; then
    echo "🔍 Test intégrations..."
    curl -H "Authorization: Bearer $TEST_TOKEN" \
         -f http://localhost:8001/api/chapters/integrations/status || exit 1
fi

# 4. Test frontend
echo "🔍 Test frontend..."
curl -f http://localhost:3000 | grep -q "BookTime" || exit 1

# 5. Test base de données
echo "🔍 Test base de données..."
mongo --eval "db.runCommand('ping')" booktime_prod || exit 1

echo "✅ Tous les tests passés !"
```

### **2. Tests de Charge**

```bash
# Installation Apache Bench
sudo apt install apache2-utils

# Test charge API
ab -n 1000 -c 10 http://localhost:8001/api/chapters/health

# Test charge frontend  
ab -n 500 -c 5 http://localhost:3000/

# Monitoring ressources pendant tests
htop  # CPU/RAM
iotop # I/O disque
```

### **3. Tests Fonctionnels**

```bash
# Test workflow complet chapitres
python3 << EOF
import requests
import json

BASE_URL = "http://localhost:8001"
HEADERS = {"Authorization": "Bearer your-test-token"}

# 1. Login
response = requests.post(f"{BASE_URL}/api/auth/login", 
                        json={"firstName": "Test", "lastName": "Deploy"})
assert response.status_code == 200
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Test recherche série
response = requests.get(f"{BASE_URL}/api/chapters/search/One%20Piece", 
                       headers=headers)
assert response.status_code == 200
print("✅ Recherche séries OK")

# 3. Test récupération chapitres
response = requests.get(f"{BASE_URL}/api/chapters/series/One%20Piece", 
                       headers=headers)
print(f"Status: {response.status_code}")
print("✅ Tests fonctionnels OK")
EOF
```

---

## 📊 **MONITORING PRODUCTION**

### **1. Métriques Clés à Surveiller**

```python
# Métriques importantes
METRICS_TO_MONITOR = {
    "backend": {
        "response_time": "<200ms (95th percentile)",
        "error_rate": "<1%",
        "requests_per_minute": "Variable selon trafic",
        "memory_usage": "<2GB",
        "cpu_usage": "<80%"
    },
    "chapters_module": {
        "cache_hit_ratio": ">80%",
        "external_api_success_rate": ">95%",
        "predictions_accuracy": ">85%",
        "integration_response_time": "<500ms"
    },
    "database": {
        "connection_pool": "Stable",
        "query_time": "<100ms avg",
        "storage_usage": "Monitor growth",
        "index_efficiency": ">90%"
    }
}
```

### **2. Alertes Recommandées**

```bash
# Exemples alertes Nagios/Zabbix/Prometheus

# Backend indisponible
check_http -H localhost -p 8001 -u /health

# Module chapitres en erreur  
check_http -H localhost -p 8001 -u /api/chapters/health

# Base de données
check_mongodb -H localhost -P 27017 -d booktime_prod

# Espace disque
check_disk -w 20% -c 10% /var/lib/mongodb

# Mémoire
check_memory -w 80 -c 90
```

---

## 🔄 **MISE À JOUR ET MAINTENANCE**

### **1. Stratégie de Déploiement**

```bash
# Déploiement Blue-Green (recommandé)
# 1. Déployer nouvelle version sur environnement staging
# 2. Tests automatisés complets
# 3. Switch trafic progressif
# 4. Rollback rapide si problème

# Script de déploiement
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Déploiement BookTime v$(cat VERSION)"

# 1. Sauvegarde base de données
mongodump --db booktime_prod --out backup/$(date +%Y%m%d_%H%M%S)/

# 2. Pull dernière version
git pull origin main

# 3. Installation dépendances
cd backend && pip install -r requirements.txt
cd ../frontend && yarn install

# 4. Build frontend
yarn build

# 5. Tests rapides
curl -f http://localhost:8001/health

# 6. Restart services
sudo supervisorctl restart all

# 7. Tests post-déploiement
./test_deployment.sh

echo "✅ Déploiement réussi !"
```

### **2. Sauvegardes**

```bash
# Script sauvegarde quotidienne
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/booktime/$DATE"

mkdir -p $BACKUP_DIR

# Sauvegarde MongoDB
mongodump --db booktime_prod --out $BACKUP_DIR/mongodb/

# Sauvegarde code (si nécessaire)
tar -czf $BACKUP_DIR/app_code.tar.gz /var/www/booktime/

# Sauvegarde configuration
cp -r /etc/nginx/sites-available/ $BACKUP_DIR/nginx/
cp -r /etc/supervisor/conf.d/ $BACKUP_DIR/supervisor/

# Nettoyage anciennes sauvegardes (>30 jours)
find /backups/booktime/ -type d -mtime +30 -exec rm -rf {} +

echo "✅ Sauvegarde terminée: $BACKUP_DIR"

# Crontab pour automatisation
# 0 2 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
```

---

## 🐛 **DÉPANNAGE PRODUCTION**

### **1. Problèmes Courants**

```bash
# Module chapitres ne répond pas
curl http://localhost:8001/api/chapters/health
# Si erreur 503:
tail -f /var/log/supervisor/backend.*.log | grep chapters

# Intégrations externes en timeout
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/api/chapters/integrations/status
# Vérifier configuration rate limiting

# Base de données lente
mongo --eval "db.runCommand({currentOp: true})"
# Vérifier index: db.series_chapters.getIndexes()

# Problème cache
mongo
> use booktime_prod
> db.series_chapters.find({cache_expires: {$lt: new Date()}}).count()
```

### **2. Logs Importants**

```bash
# Logs application
tail -f /var/log/supervisor/backend.*.log
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Logs MongoDB
tail -f /var/log/mongodb/mongod.log

# Logs système
journalctl -u supervisor -f
dmesg | tail
```

### **3. Commandes Diagnostic**

```bash
# Statut services
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status mongodb

# Ressources système
df -h          # Espace disque
free -h        # Mémoire
top            # CPU/processus
netstat -tlnp  # Ports ouverts

# Test connectivité APIs externes
curl -I https://graphql.anilist.co/
curl -I https://www.mangaupdates.com/
```

---

## ✅ **CHECKLIST DÉPLOIEMENT**

### **Pré-déploiement**
- [ ] Variables d'environnement configurées
- [ ] Base de données MongoDB opérationnelle
- [ ] Index MongoDB créés
- [ ] Dépendances backend installées
- [ ] Dépendances frontend installées
- [ ] Tests unitaires passés
- [ ] Sauvegarde base de données effectuée

### **Déploiement**
- [ ] Code déployé sur serveur
- [ ] Configuration nginx/apache mise à jour
- [ ] Services backend redémarrés
- [ ] Build frontend optimisé
- [ ] Certificats SSL valides
- [ ] DNS configurés

### **Post-déploiement**
- [ ] Health check backend OK
- [ ] Module chapitres opérationnel
- [ ] Intégrations externes testées
- [ ] Interface frontend accessible
- [ ] Tests fonctionnels passés
- [ ] Monitoring activé
- [ ] Alertes configurées
- [ ] Documentation mise à jour

---

## 📚 **RESSOURCES ADDITIONNELLES**

### **Documentation Technique**
- [CHAPTERS_SYSTEM_DOCUMENTATION.md](./CHAPTERS_SYSTEM_DOCUMENTATION.md) : Documentation complète système
- [API_CHAPTERS_ENDPOINTS.md](./API_CHAPTERS_ENDPOINTS.md) : Endpoints API détaillés
- [FRONTEND_CHAPTERS_GUIDE.md](./FRONTEND_CHAPTERS_GUIDE.md) : Guide développeur frontend

### **Outils de Déploiement**
- Docker & Docker Compose
- Kubernetes (pour déploiements à grande échelle)
- Ansible (automatisation déploiement)
- GitHub Actions / GitLab CI (CI/CD)

### **Monitoring et Observabilité**
- Prometheus + Grafana (métriques)
- ELK Stack (logs centralisés)
- Sentry (error tracking)
- Uptime Robot (monitoring uptime)

---

**Guide de Déploiement Système Chapitres BookTime - Version 1.0 - Production Ready**

*Documentation générée pour déploiement enterprise - Juillet 2025*