# 🔌 **API ENDPOINTS CHAPITRES - DOCUMENTATION TECHNIQUE**

*Version 1.0 - 8 Nouveaux Endpoints - Juillet 2025*

---

## 📋 **APERÇU DES ENDPOINTS**

Le module chapitres ajoute **8 nouveaux endpoints** à l'API BookTime, portant le total à **99 endpoints**. Tous sont sécurisés avec authentification JWT et incluent une documentation Swagger automatique.

**Base URL :** `/api/chapters`  
**Authentification :** `Bearer token` requis pour tous endpoints

---

## 🔗 **LISTE COMPLÈTE DES ENDPOINTS**

| Méthode | Endpoint | Description | Authentification |
|---------|----------|-------------|------------------|
| `GET` | `/health` | Health check module | ❌ Public |
| `GET` | `/series/{series_name}` | Récupérer chapitres série | ✅ JWT |
| `POST` | `/series/{series_name}/refresh` | Actualiser données | ✅ JWT |
| `GET` | `/releases/upcoming` | Planning sorties | ✅ JWT |
| `GET` | `/user/stats` | Statistiques utilisateur | ✅ JWT |
| `GET` | `/search/{series_name}` | Rechercher dans APIs | ✅ JWT |
| `POST` | `/series/{series_name}/map-ids` | Mapper IDs externes | ✅ JWT |
| `GET` | `/integrations/status` | Statut intégrations | ✅ JWT |
| `PUT` | `/predictions/config` | Config prédictions | ✅ JWT |
| `GET` | `/debug/series/{series_name}` | Debug série | ✅ JWT |

---

## 📖 **DOCUMENTATION DÉTAILLÉE**

### **1. Health Check Module**

```http
GET /api/chapters/health
```

**Description :** Vérification de santé du module chapitres  
**Authentification :** Aucune  
**Rate Limiting :** Aucun  

**Réponse :**
```json
{
  "status": "ok",
  "module": "chapters", 
  "version": "1.0.0",
  "features": [
    "series_chapters",
    "predictions",
    "volume_grouping", 
    "external_apis"
  ]
}
```

**Codes de Réponse :**
- `200` : Module opérationnel
- `503` : Module en erreur

---

### **2. Récupération Chapitres Série**

```http
GET /api/chapters/series/{series_name}
```

**Description :** Récupère les informations complètes de chapitres pour une série  
**Authentification :** JWT Bearer Token  

**Paramètres Path :**
- `series_name` (string) : Nom de la série (encodé URL)

**Paramètres Query :**
- `force_refresh` (boolean, optional) : Force actualisation APIs externes
  - Default: `false`
  - Exemple: `?force_refresh=true`

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
```

**Exemple Requête :**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/series/One%20Piece?force_refresh=false"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "data": {
    "id": "uuid-12345",
    "series_name": "One Piece",
    "manga_id_anilist": 30013,
    "manga_id_mangaupdates": 319,
    "current_chapters": [
      {
        "chapter_number": 1101,
        "title": "Heavy Rotation",
        "release_date": "2024-01-15T00:00:00Z",
        "status": "released",
        "grouped_in_volume": null,
        "page_count": 17,
        "translated_languages": ["en", "fr"]
      }
    ],
    "volumes": [
      {
        "volume_number": 108,
        "chapters_range": "1095-1105",
        "chapters_included": [1095, 1096, 1097, 1098, 1099, 1100, 1101],
        "release_date": "2024-03-15T00:00:00Z",
        "status": "upcoming"
      }
    ],
    "predictions": {
      "next_chapter": {
        "estimated_number": 1102,
        "estimated_date": "2024-01-22T00:00:00Z",
        "confidence": 0.95,
        "method": "weekly_analysis"
      }
    },
    "release_schedule": "weekly",
    "total_chapters_released": 1101,
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "message": "Données récupérées pour One Piece",
  "cached": false
}
```

**Codes d'Erreur :**
- `401` : Token invalide/expiré
- `404` : Série non trouvée
- `500` : Erreur serveur interne

---

### **3. Actualisation Forcée Données**

```http
POST /api/chapters/series/{series_name}/refresh
```

**Description :** Force l'actualisation des données depuis les APIs externes  
**Authentification :** JWT Bearer Token  

**Paramètres Path :**
- `series_name` (string) : Nom de la série

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
```

**Exemple Requête :**
```bash
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     "http://localhost:8001/api/chapters/series/One%20Piece/refresh"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "message": "Données rafraîchies pour One Piece",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Codes d'Erreur :**
- `400` : Impossible de rafraîchir
- `401` : Non authentifié
- `500` : Erreur serveur

---

### **4. Planning Sorties à Venir**

```http
GET /api/chapters/releases/upcoming
```

**Description :** Récupère le planning des sorties de chapitres organisé par période  
**Authentification :** JWT Bearer Token  

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Exemple Requête :**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/releases/upcoming"
```

**Réponse Succès (200) :**
```json
{
  "this_week": [
    {
      "series_name": "One Piece",
      "chapter_number": 1102,
      "estimated_date": "2024-01-22",
      "confidence": 0.95
    },
    {
      "series_name": "Naruto Next Gen",
      "chapter_number": 85,
      "estimated_date": "2024-01-24", 
      "confidence": 0.87
    }
  ],
  "next_week": [
    {
      "series_name": "Attack on Titan Final",
      "chapter_number": 140,
      "estimated_date": "2024-01-29",
      "confidence": 0.72
    }
  ],
  "this_month": [
    {
      "series_name": "Demon Slayer",
      "chapter_number": 210,
      "estimated_date": "2024-02-05",
      "confidence": 0.68
    }
  ]
}
```

**Organisation Temporelle :**
- `this_week` : Sorties jusqu'à la fin de semaine courante
- `next_week` : Sorties semaine suivante  
- `this_month` : Sorties jusqu'à la fin du mois

---

### **5. Statistiques Utilisateur Chapitres**

```http
GET /api/chapters/user/stats
```

**Description :** Statistiques personnalisées de l'utilisateur liées aux chapitres  
**Authentification :** JWT Bearer Token  

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Exemple Requête :**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/user/stats"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "user_id": "user-uuid-12345",
  "stats": {
    "chapters_read_this_week": 15,
    "series_following": 8,
    "predictions_accuracy": 0.89,
    "favorite_release_day": "Monday",
    "total_chapters_tracked": 1247
  },
  "last_updated": "2024-01-15T10:30:00Z"
}
```

**Métriques Calculées :**
- `chapters_read_this_week` : Chapitres lus cette semaine
- `series_following` : Nombre de séries suivies  
- `predictions_accuracy` : Précision prédictions précédentes
- `favorite_release_day` : Jour de sortie préféré
- `total_chapters_tracked` : Total chapitres trackés

---

### **6. Recherche dans APIs Externes**

```http
GET /api/chapters/search/{series_name}
```

**Description :** Recherche une série dans les APIs externes (AniList, MangaUpdates)  
**Authentification :** JWT Bearer Token  

**Paramètres Path :**
- `series_name` (string) : Nom de la série à rechercher

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Exemple Requête :**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/search/Attack%20on%20Titan"
```

**Réponse Succès (200) :**
```json
{
  "anilist_matches": [
    {
      "id": 1214,
      "title": "Attack on Titan",
      "alternative_titles": ["進撃の巨人", "Shingeki no Kyojin"],
      "chapters": 139,
      "status": "completed",
      "confidence": 0.98
    }
  ],
  "mangaupdates_matches": [
    {
      "id": 1214,
      "title": "Attack on Titan", 
      "type": "Manga",
      "year": 2009,
      "status": "Complete",
      "confidence": 0.95
    }
  ],
  "confidence_scores": {
    "anilist": 0.98,
    "mangaupdates": 0.95,
    "overall": 0.97
  }
}
```

**Algorithme de Confiance :**
- `1.0` : Correspondance exacte titre
- `0.9` : Correspondance partielle
- `0.8` : Correspondance synonymes
- `<0.8` : Basé sur popularité

---

### **7. Mapping IDs Externes**

```http
POST /api/chapters/series/{series_name}/map-ids
```

**Description :** Associe une série aux IDs des APIs externes pour améliorer la récupération  
**Authentification :** JWT Bearer Token  

**Paramètres Path :**
- `series_name` (string) : Nom de la série

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
```

**Body Requis :**
```json
{
  "anilist_id": 30013,
  "mangaupdates_id": 319
}
```

**Validation :**
- Au moins un ID doit être fourni
- IDs doivent être des entiers positifs

**Exemple Requête :**
```bash
curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"anilist_id": 30013, "mangaupdates_id": 319}' \
     "http://localhost:8001/api/chapters/series/One%20Piece/map-ids"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "series_name": "One Piece",
  "mapped_ids": {
    "anilist_id": 30013,
    "mangaupdates_id": 319
  },
  "message": "IDs mappés avec succès"
}
```

**Codes d'Erreur :**
- `400` : IDs invalides ou manquants
- `401` : Non authentifié
- `500` : Erreur base de données

---

### **8. Statut Intégrations Externes**

```http
GET /api/chapters/integrations/status
```

**Description :** Vérifie le statut de santé des intégrations avec les APIs externes  
**Authentification :** JWT Bearer Token  

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Exemple Requête :**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/integrations/status"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "integrations": {
    "anilist": {
      "status": "ok",
      "response_time": 150,
      "last_success": "2024-01-15T10:28:00Z",
      "error_message": null
    },
    "mangaupdates": {
      "status": "ok", 
      "response_time": 890,
      "last_success": "2024-01-15T10:25:00Z",
      "error_message": null
    }
  },
  "checked_at": "2024-01-15T10:30:00Z"
}
```

**Statuts Possibles :**
- `ok` : API accessible et fonctionnelle
- `error` : Erreur de connexion ou API
- `timeout` : Timeout de connexion
- `unknown` : Statut indéterminé

**Métriques :**
- `response_time` : Temps de réponse en millisecondes
- `last_success` : Dernière requête réussie
- `error_message` : Message d'erreur si applicable

---

### **9. Configuration Prédictions**

```http
PUT /api/chapters/predictions/config
```

**Description :** Met à jour la configuration globale des prédictions  
**Authentification :** JWT Bearer Token  

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
```

**Body Requis :**
```json
{
  "enable_predictions": true,
  "confidence_threshold": 0.8
}
```

**Paramètres :**
- `enable_predictions` (boolean) : Activer/désactiver prédictions
- `confidence_threshold` (float) : Seuil de confiance (0.0-1.0)

**Validation :**
- `enable_predictions` doit être boolean
- `confidence_threshold` doit être entre 0.0 et 1.0

**Exemple Requête :**
```bash
curl -X PUT \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"enable_predictions": true, "confidence_threshold": 0.85}' \
     "http://localhost:8001/api/chapters/predictions/config"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "config": {
    "enable_predictions": true,
    "confidence_threshold": 0.85,
    "updated_at": "2024-01-15T10:30:00Z",
    "updated_by": "user-uuid-12345"
  },
  "message": "Configuration mise à jour avec succès"
}
```

---

### **10. Debug Série (Développement)**

```http
GET /api/chapters/debug/series/{series_name}
```

**Description :** Endpoint de debug pour analyser les données d'une série  
**Authentification :** JWT Bearer Token  
**Usage :** Développement et dépannage uniquement  

**Paramètres Path :**
- `series_name` (string) : Nom de la série

**Paramètres Query :**
- `include_raw` (boolean, optional) : Inclure données brutes APIs
  - Default: `false`

**Headers Requis :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Exemple Requête :**
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/debug/series/One%20Piece?include_raw=true"
```

**Réponse Succès (200) :**
```json
{
  "success": true,
  "debug_info": {
    "series_name": "One Piece",
    "cache_status": "found",
    "last_sync": "2024-01-15T10:00:00Z",
    "mapped_ids": {
      "anilist": 30013,
      "mangaupdates": 319
    },
    "chapters_count": 1101,
    "volumes_count": 107,
    "prediction_accuracy": 0.92,
    "last_errors": []
  },
  "generated_at": "2024-01-15T10:30:00Z"
}
```

---

## 🔐 **AUTHENTIFICATION**

### **Obtention Token JWT**

1. **Connexion utilisateur :**
```http
POST /api/auth/login
Content-Type: application/json

{
  "firstName": "John",
  "lastName": "Doe"
}
```

2. **Réponse avec token :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

3. **Utilisation dans requêtes :**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Gestion Erreurs Authentification**

**401 Unauthorized :**
```json
{
  "detail": "Token invalide ou expiré"
}
```

**Solutions :**
- Renouveler le token via `/api/auth/refresh`
- Reconnecter l'utilisateur via `/api/auth/login`

---

## 🚦 **CODES DE RÉPONSE HTTP**

| Code | Signification | Description |
|------|---------------|-------------|
| `200` | OK | Requête réussie |
| `201` | Created | Ressource créée |
| `400` | Bad Request | Paramètres invalides |
| `401` | Unauthorized | Authentification requise |
| `403` | Forbidden | Accès interdit |
| `404` | Not Found | Ressource non trouvée |
| `429` | Too Many Requests | Rate limit dépassé |
| `500` | Internal Server Error | Erreur serveur |
| `503` | Service Unavailable | Service temporairement indisponible |

---

## ⚡ **RATE LIMITING**

### **Limites Par Endpoint**

| Endpoint | Limite | Fenêtre |
|----------|--------|---------|
| `/health` | Aucune | - |
| `/series/*` | 100 req/min | Par utilisateur |
| `/search/*` | 30 req/min | Par utilisateur |
| `/refresh` | 10 req/min | Par utilisateur |
| Autres | 60 req/min | Par utilisateur |

### **Headers Rate Limiting**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642521600
```

---

## 🧪 **EXEMPLES COMPLETS D'USAGE**

### **Workflow Complet : Suivi Série**

```bash
#!/bin/bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."
BASE_URL="http://localhost:8001/api/chapters"

# 1. Rechercher la série dans APIs externes
echo "=== Recherche série ==="
curl -s -H "Authorization: Bearer $TOKEN" \
     "$BASE_URL/search/One%20Piece" | jq

# 2. Mapper les IDs trouvés
echo "=== Mapping IDs ==="
curl -s -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"anilist_id": 30013, "mangaupdates_id": 319}' \
     "$BASE_URL/series/One%20Piece/map-ids" | jq

# 3. Récupérer données chapitres
echo "=== Récupération chapitres ==="
curl -s -H "Authorization: Bearer $TOKEN" \
     "$BASE_URL/series/One%20Piece" | jq

# 4. Vérifier planning sorties
echo "=== Planning sorties ==="
curl -s -H "Authorization: Bearer $TOKEN" \
     "$BASE_URL/releases/upcoming" | jq

# 5. Actualiser si nécessaire
echo "=== Actualisation ==="
curl -s -X POST \
     -H "Authorization: Bearer $TOKEN" \
     "$BASE_URL/series/One%20Piece/refresh" | jq
```

### **Monitoring Intégrations**

```bash
#!/bin/bash
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Vérification santé
curl -s "http://localhost:8001/api/chapters/health" | jq

# Statut intégrations
curl -s -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/integrations/status" | jq

# Statistiques utilisateur  
curl -s -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8001/api/chapters/user/stats" | jq
```

---

## 🛠️ **OUTILS DÉVELOPPEMENT**

### **Swagger UI**
```
http://localhost:8001/docs#/chapters
```
Interface interactive pour tester tous les endpoints avec authentification.

### **ReDoc**
```
http://localhost:8001/redoc
```
Documentation alternative générée automatiquement.

### **Postman Collection**

```json
{
  "info": {
    "name": "BookTime Chapters API",
    "version": "1.0"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{jwt_token}}"
      }
    ]
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": "{{base_url}}/api/chapters/health"
      }
    },
    {
      "name": "Get Series Chapters",
      "request": {
        "method": "GET",
        "header": [],
        "url": "{{base_url}}/api/chapters/series/One Piece"
      }
    }
  ]
}
```

---

## 📊 **MÉTRIQUES API**

### **Performance Cible**
- **Temps de réponse** : <200ms (95th percentile)
- **Disponibilité** : >99.9% 
- **Cache hit ratio** : >80%
- **Erreur rate** : <1%

### **Monitoring**
```bash
# Métriques temps réel
curl -s "http://localhost:8001/api/chapters/integrations/status" | \
jq '.integrations | to_entries[] | "\(.key): \(.value.response_time)ms"'
```

---

*Documentation générée automatiquement - Version 1.0 - Juillet 2025*  
*API Endpoints Chapitres BookTime - 8 Nouveaux Endpoints*