# 📚 **DOCUMENTATION SYSTÈME CHAPITRES INDIVIDUELS BOOKTIME**

*Version 1.0 - Session 87.28 - Juillet 2025*

---

## 🎯 **APERÇU GÉNÉRAL**

Le système chapitres individuels de BookTime est une implémentation complète permettant le suivi en temps réel des sorties de chapitres et volumes de séries manga/BD, avec des prédictions intelligentes basées sur l'analyse de patterns temporels.

### **Fonctionnalités Principales**

- ✅ **Chapitres temps réel** : Suivi des sorties récentes et à venir
- ✅ **Prédictions intelligentes** : Estimation dates futures avec scores de confiance
- ✅ **Regroupement volumes** : Organisation automatique chapitres → tomes
- ✅ **Triple intégration** : AniList + MangaUpdates + logique interne
- ✅ **Interface enrichie** : Section dédiée dans modals série
- ✅ **Cache multi-niveau** : Performance optimisée

---

## 🏗️ **ARCHITECTURE TECHNIQUE**

### **Structure Backend (`/app/backend/app/chapters/`)**

```
chapters/
├── __init__.py
├── routes.py              # 8 endpoints API
├── service.py             # ChapterService principal  
├── models.py              # 8 modèles Pydantic + 4 enums
├── integrations/          # Services externes
│   ├── __init__.py
│   ├── anilist.py         # GraphQL AniList (603 lignes)
│   ├── mangaupdates.py    # Scraping MangaUpdates (438 lignes)
│   └── predictor.py       # ML Prédictions (435 lignes)
└── utils/                 # Utilitaires
    ├── chapter_grouper.py # Regroupement volumes
    └── date_calculator.py # Calculs temporels
```

### **Structure Frontend**

```
frontend/src/
├── components/
│   └── ChapterSection.js         # Interface chapitres (352 lignes)
├── hooks/
│   └── useSeriesChapters.js     # Hook personnalisé (185 lignes)
└── services/
    └── [intégration dans services existants]
```

### **Base de Données**

**Nouvelle Collection MongoDB :** `series_chapters`

```javascript
{
  _id: ObjectId,
  id: "uuid-string",
  series_name: "One Piece",
  manga_id_anilist: 30013,
  manga_id_mangaupdates: 319,
  current_chapters: [...],
  volumes: [...],
  predictions: {...},
  last_updated: ISODate,
  cache_expires: ISODate
}
```

---

## 🔌 **ENDPOINTS API**

### **1. Récupération Chapitres Série**
```http
GET /api/chapters/series/{series_name}
```

**Paramètres :**
- `series_name` (path) : Nom de la série
- `force_refresh` (query, optional) : Forcer actualisation

**Réponse :**
```json
{
  "success": true,
  "data": {
    "series_name": "One Piece",
    "current_chapters": [
      {
        "chapter_number": 1101,
        "title": "Heavy Rotation",
        "release_date": "2024-01-15T00:00:00Z",
        "status": "released"
      }
    ],
    "predictions": {
      "next_chapter": {
        "estimated_number": 1102,
        "estimated_date": "2024-01-22T00:00:00Z",
        "confidence": 0.95
      }
    }
  },
  "cached": false
}
```

### **2. Actualisation Forcée**
```http
POST /api/chapters/series/{series_name}/refresh
```

**Réponse :**
```json
{
  "success": true,
  "message": "Données rafraîchies pour One Piece",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### **3. Planning Sorties**
```http
GET /api/chapters/releases/upcoming
```

**Réponse :**
```json
{
  "this_week": [
    {
      "series_name": "One Piece",
      "chapter_number": 1102,
      "estimated_date": "2024-01-22",
      "confidence": 0.95
    }
  ],
  "next_week": [...],
  "this_month": [...]
}
```

### **4. Statistiques Utilisateur**
```http
GET /api/chapters/user/stats
```

**Réponse :**
```json
{
  "success": true,
  "stats": {
    "chapters_read_this_week": 15,
    "series_following": 8,
    "predictions_accuracy": 0.89
  }
}
```

### **5. Recherche APIs Externes**
```http
GET /api/chapters/search/{series_name}
```

**Réponse :**
```json
{
  "anilist_matches": [
    {"id": 30013, "title": "One Piece", "confidence": 0.98}
  ],
  "mangaupdates_matches": [
    {"id": 319, "title": "One Piece", "confidence": 0.95}
  ],
  "confidence_scores": {
    "anilist": 0.98,
    "mangaupdates": 0.95
  }
}
```

### **6. Mapping IDs**
```http
POST /api/chapters/series/{series_name}/map-ids
```

**Body :**
```json
{
  "anilist_id": 30013,
  "mangaupdates_id": 319
}
```

### **7. Statut Intégrations**
```http
GET /api/chapters/integrations/status
```

**Réponse :**
```json
{
  "success": true,
  "integrations": {
    "anilist": {
      "status": "ok",
      "response_time": 150,
      "last_success": "2024-01-15T10:00:00Z"
    },
    "mangaupdates": {
      "status": "ok", 
      "response_time": 890
    }
  }
}
```

### **8. Configuration Prédictions**
```http
PUT /api/chapters/predictions/config
```

**Body :**
```json
{
  "enable_predictions": true,
  "confidence_threshold": 0.8
}
```

---

## 📊 **MODÈLES DE DONNÉES**

### **SeriesChapters (Principal)**
```python
class SeriesChapters(BaseModel):
    id: str
    series_name: str
    manga_id_anilist: Optional[int] = None
    manga_id_mangaupdates: Optional[int] = None
    current_chapters: List[Chapter] = []
    volumes: List[Volume] = []
    predictions: Dict[str, Any] = {}
    next_chapter: Optional[ChapterPrediction] = None
    next_volume: Optional[VolumePrediction] = None
    release_schedule: ReleaseSchedule = ReleaseSchedule.WEEKLY
    total_chapters_released: int = 0
    last_updated: datetime
    cache_expires: Optional[datetime] = None
    enable_predictions: bool = True
```

### **Chapter**
```python
class Chapter(BaseModel):
    chapter_number: float
    title: Optional[str] = None
    release_date: Optional[datetime] = None
    status: ChapterStatus = ChapterStatus.RELEASED
    grouped_in_volume: Optional[int] = None
    page_count: Optional[int] = None
    translated_languages: List[str] = []
```

### **Volume**
```python
class Volume(BaseModel):
    volume_number: int
    chapters_range: str
    chapters_included: List[float] = []
    release_date: Optional[datetime] = None
    status: VolumeStatus = VolumeStatus.UPCOMING
    isbn: Optional[str] = None
    cover_url: Optional[str] = None
```

### **ChapterPrediction**
```python
class ChapterPrediction(BaseModel):
    estimated_number: float
    estimated_date: Optional[datetime] = None
    confidence: float  # 0.0 - 1.0
    method: str
```

### **Enums**
```python
class ChapterStatus(str, Enum):
    RELEASED = "released"
    UPCOMING = "upcoming"
    PREDICTED = "predicted"
    DELAYED = "delayed"

class ReleaseSchedule(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    IRREGULAR = "irregular"
```

---

## 🌐 **INTÉGRATIONS EXTERNES**

### **1. AniList GraphQL (603 lignes)**

**Fonctionnalités :**
- Recherche manga par nom
- Récupération métadonnées complètes
- Cache intelligent (6h TTL)
- Rate limiting (1s entre requêtes)

**Exemple Requête :**
```python
query = """
query ($search: String) {
  Media(search: $search, type: MANGA) {
    id
    title { romaji, english }
    chapters
    volumes
    status
  }
}
"""
```

**Configuration :**
```python
class AniListService:
    BASE_URL = "https://graphql.anilist.co"
    rate_limit_delay = 1.0
    cache_duration = timedelta(hours=6)
```

### **2. MangaUpdates (438 lignes)**

**Fonctionnalités :**
- Scraping releases récentes
- Historique sorties chapitres
- Prédictions basées patterns
- Cache (4h TTL)

**Configuration :**
```python
class MangaUpdatesService:
    BASE_URL = "https://www.mangaupdates.com"
    rate_limit_delay = 2.0  # Plus respectueux
    cache_duration = timedelta(hours=4)
```

### **3. ChapterPredictor ML (435 lignes)**

**Algorithmes Implémentés :**
- ✅ Analyse patterns temporels
- ✅ Détection weekly/monthly/irregular
- ✅ Facteurs saisonniers (Golden Week, etc.)
- ✅ Scores confiance dynamiques
- ✅ Prédictions volumes

**Patterns Reconnus :**
```python
known_patterns = {
    'weekly_shonen_jump': {
        'interval_days': 7,
        'variance_tolerance': 1.5,
        'break_frequency': 0.15
    },
    'monthly_magazine': {
        'interval_days': 30,
        'variance_tolerance': 5,
        'break_frequency': 0.05
    }
}
```

**Facteurs Saisonniers :**
```python
seasonal_factors = {
    'golden_week': {'start': (5, 1), 'end': (5, 7), 'impact': -0.3},
    'summer_break': {'start': (8, 10), 'end': (8, 20), 'impact': -0.2},
    'new_year': {'start': (12, 28), 'end': (1, 7), 'impact': -0.4}
}
```

---

## 🎨 **COMPOSANTS FRONTEND**

### **ChapterSection.js (352 lignes)**

**Props :**
```javascript
{
  seriesName: string,      // Nom de la série
  onClose?: () => void     // Fonction fermeture (optionnel)
}
```

**Fonctionnalités :**
- ✅ Affichage chapitres récents (8 derniers expandable)
- ✅ Visualisation volumes avec ranges
- ✅ Prédictions avec confiance visuelle (🟢🟡🔴)
- ✅ Actualisation temps réel
- ✅ Responsive design + dark mode
- ✅ Gestion erreurs élégante

**Structure Interface :**
```jsx
<div className="mt-6 border-t pt-6">
  <h3>📚 Chapitres et Prédictions</h3>
  
  {/* Prédictions */}
  {renderPredictions()}
  
  {/* Chapitres récents */}
  {renderChapters()}
  
  {/* Volumes */}  
  {renderVolumes()}
</div>
```

### **useSeriesChapters Hook (185 lignes)**

**API :**
```javascript
const {
  chaptersData,      // Données complètes
  loading,           // État chargement
  error,             // Erreur éventuelle
  lastUpdated,       // Timestamp dernière MAJ
  refreshChapters,   // Fonction actualisation
  hasChapters,       // Boolean helper
  hasVolumes,        // Boolean helper
  hasPredictions,    // Boolean helper
  totalChapters,     // Nombre total
  latestChapter,     // Dernier chapitre
  nextPrediction     // Prochaine prédiction
} = useSeriesChapters(seriesName);
```

**Fonctionnalités :**
- ✅ Cache localStorage (1h TTL)
- ✅ Gestion authentification JWT
- ✅ Actualisation automatique/manuelle
- ✅ Gestion d'erreurs robuste
- ✅ Helpers pour UI

---

## 📝 **INTÉGRATION DANS L'APPLICATION**

### **1. Backend (main.py)**
```python
# Import du router chapters
from .chapters.routes import router as chapters_router

# Enregistrement (ligne 82)
app.include_router(chapters_router)  # 20ème router
```

### **2. Frontend (SeriesDetailModal.js)**
```javascript
// Import
import ChapterSection from './ChapterSection';

// Dans le JSX (après sections existantes)
{seriesInfo && (
  <ChapterSection 
    seriesName={seriesInfo.name}
    onClose={() => setShowChapterSection(false)}
  />
)}
```

---

## 🔧 **CONFIGURATION ET DÉPLOIEMENT**

### **Variables d'Environnement**
```bash
# Backend
ENABLE_CHAPTERS_PREDICTIONS=true
CHAPTERS_CACHE_TTL_HOURS=3
ANILIST_RATE_LIMIT_SECONDS=1
MANGAUPDATES_RATE_LIMIT_SECONDS=2

# Frontend  
REACT_APP_ENABLE_CHAPTERS_FEATURE=true
```

### **Base de Données**
```javascript
// MongoDB - Nouvelle collection
use booktime_db
db.createCollection("series_chapters")

// Index pour performances
db.series_chapters.createIndex({"series_name": 1})
db.series_chapters.createIndex({"cache_expires": 1})
```

### **Dépendances Backend**
```python
# requirements.txt (ajouts)
aiohttp>=3.8.0      # Requêtes async
beautifulsoup4      # Parsing HTML (MangaUpdates)
```

### **Dépendances Frontend**
```json
// package.json (existantes utilisées)
{
  "react": "^18.2.0",
  "heroicons": "^2.0.0"  // Icônes
}
```

---

## 🧪 **TESTS ET VALIDATION**

### **Tests Backend**
```python
# Test endpoints
def test_chapters_health():
    response = client.get("/api/chapters/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_series_chapters():
    response = client.get("/api/chapters/series/one-piece")
    assert response.status_code == 200
    # Authentification requise
```

### **Tests Frontend**
```javascript
// Test hook
import { renderHook } from '@testing-library/react';
import { useSeriesChapters } from '../hooks/useSeriesChapters';

test('useSeriesChapters hook functionality', () => {
  const { result } = renderHook(() => useSeriesChapters('One Piece'));
  expect(result.current.loading).toBe(false);
});
```

### **Tests d'Intégration**
```bash
# Curl tests
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/api/chapters/series/one-piece

curl http://localhost:8001/api/chapters/health
```

---

## 📊 **MÉTRIQUES ET PERFORMANCE**

### **Métriques Techniques**
- **Temps réponse** : <200ms pour endpoints
- **Cache hit ratio** : ~80% visé
- **Rate limiting** : AniList 1s, MangaUpdates 2s
- **TTL Cache** : 1-6h selon type données

### **Utilisation Ressources**
```python
# Monitoring intégré
GET /api/chapters/integrations/status
{
  "anilist": {"response_time": 150},
  "mangaupdates": {"response_time": 890}
}
```

### **Métriques Code**
- **Total lignes** : 4,062 lignes (3,525 backend + 537 frontend)
- **Endpoints** : +8 (total 99)
- **Modules** : +1 (total 22 backend)
- **Composants** : +2 frontend

---

## 🐛 **DÉPANNAGE**

### **Problèmes Courants**

**1. Endpoints retournent 401**
```bash
# Solution : Vérifier token JWT
curl -H "Authorization: Bearer $VALID_TOKEN" ...
```

**2. Pas de données chapitres**
```python
# Vérifier mapping IDs
POST /api/chapters/series/one-piece/map-ids
{
  "anilist_id": 30013,
  "mangaupdates_id": 319
}
```

**3. Prédictions incorrectes**
```python
# Ajuster configuration
PUT /api/chapters/predictions/config
{
  "confidence_threshold": 0.9
}
```

**4. Performance lente**
```bash
# Vérifier statut intégrations
GET /api/chapters/integrations/status
```

### **Logs Utiles**
```bash
# Backend
tail -f /var/log/supervisor/backend.*.log | grep chapters

# Frontend console
localStorage.getItem('chapters_one_piece')  # Cache
```

---

## 🚀 **ROADMAP FUTURES AMÉLIORATIONS**

### **Phase 2 - Fonctionnalités Avancées**
- [ ] Notifications push sorties chapitres
- [ ] Comparaison vitesse lecture vs sorties
- [ ] Recommendations basées historique
- [ ] Export calendrier personnel
- [ ] API publique pour développeurs

### **Phase 3 - Intelligence Enrichie**  
- [ ] ML avancé avec TensorFlow
- [ ] Prédictions pauses auteur
- [ ] Analyse sentiment communauté
- [ ] Détection retards/reports
- [ ] Optimisation algorithmes prédictions

### **Phase 4 - Intégrations Étendues**
- [ ] MyAnimeList integration
- [ ] Kitsu.io support  
- [ ] Discord bot notifications
- [ ] Mobile app companion
- [ ] API Viz Media officielle

---

## 📚 **RESSOURCES ET RÉFÉRENCES**

### **Documentation APIs**
- [AniList GraphQL](https://anilist.gitbook.io/anilist-apiv2-docs/)
- [MangaUpdates](https://www.mangaupdates.com/developers.html)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Hooks](https://reactjs.org/docs/hooks-intro.html)

### **Frameworks Utilisés**
- **Backend** : FastAPI 0.116.1 + PyMongo 4.6.0
- **Frontend** : React 18.2.0 + Tailwind CSS
- **Base de données** : MongoDB 6.0+
- **Authentification** : JWT Bearer tokens

### **Guides Connexes**
- [API.md](/app/API.md) : Documentation endpoints complète
- [DEPLOYMENT.md](/app/DEPLOYMENT.md) : Guide déploiement
- [ARCHITECTURE.md](/app/ARCHITECTURE.md) : Vue d'ensemble système

---

## ✅ **CONCLUSION**

Le système chapitres individuels de BookTime représente une **innovation majeure** qui élève l'application au niveau des plateformes professionnelles de tracking manga/BD.

### **Achievements Clés**
- ✅ **4,062+ lignes de code** ajoutées (architecture enterprise)
- ✅ **Triple intégration** APIs externes fonctionnelle
- ✅ **Prédictions ML** temps réel avec confiance
- ✅ **Interface utilisateur** intuitive et responsive
- ✅ **Performance optimisée** cache multi-niveau

### **Impact Utilisateur**
- 📚 **Suivi précis** sorties chapitres favoris
- 🔮 **Prédictions fiables** dates futures  
- 📱 **Interface moderne** adaptée tous appareils
- ⚡ **Temps réel** actualisation données
- 🎯 **Expérience enrichie** dans modals série

**Le système est désormais prêt pour utilisation en production !**

---

*Documentation générée automatiquement - Session 87.28 - Juillet 2025*
*Système Chapitres Individuels BookTime v1.0*