# 🔌 **BOOKTIME - DOCUMENTATION API COMPLÈTE**

## 🎯 **Vue d'ensemble API**

L'API BOOKTIME est une API REST complète construite avec FastAPI, offrant 89 endpoints opérationnels pour la gestion de bibliothèque personnelle.

### 📊 **Métriques API**
- **Endpoints totaux** : 89 endpoints tous opérationnels
- **Modules** : 15+ modules spécialisés
- **Performance** : <200ms temps réponse moyen
- **Authentification** : JWT avec système prénom/nom
- **Documentation** : Swagger/OpenAPI intégrée

### 🔧 **Architecture modulaire**
```
/app/backend/app/
├── auth/              # Authentification JWT
├── books/             # Gestion livres CRUD
├── series/            # Séries intelligentes
├── openlibrary/       # Intégration Open Library + Authors
├── wikipedia/         # API Wikipedia (Session 87.4)
├── stats/             # Statistiques avancées
├── export_import/     # Sauvegarde/restauration
├── monitoring/        # Performance analytics
├── social/            # Fonctionnalités sociales
├── recommendations/   # Recommandations IA
└── integrations/      # Intégrations externes
```

---

## 🔐 **Authentification**

### Base URL
```
http://localhost:8001/api
```

### Endpoints d'authentification

#### **POST /api/auth/login**
Connexion utilisateur avec système prénom/nom simplifié.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "first_name": "John",
    "last_name": "Doe",
    "created_at": "2025-07-16T10:00:00Z"
  }
}
```

#### **POST /api/auth/register**
Inscription nouvel utilisateur.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:** Identique à `/login`

#### **GET /api/auth/me**
Profil utilisateur actuel.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user_id",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2025-07-16T10:00:00Z",
  "stats": {
    "total_books": 15,
    "completed_books": 8,
    "reading_books": 3,
    "to_read_books": 4
  }
}
```

---

## 📚 **Gestion des livres**

### **GET /api/books**
Récupère tous les livres de la bibliothèque utilisateur.

**Query Parameters:**
- `category` (optional): roman, bd, manga
- `status` (optional): to_read, reading, completed
- `author` (optional): Nom d'auteur
- `limit` (optional): Nombre max résultats
- `offset` (optional): Décalage pour pagination

**Response:**
```json
{
  "books": [
    {
      "id": "book_id",
      "title": "Harry Potter à l'école des sorciers",
      "author": "J.K. Rowling",
      "category": "roman",
      "status": "completed",
      "pages": 320,
      "pages_read": 320,
      "saga": "Harry Potter",
      "volume": 1,
      "cover_url": "https://covers.openlibrary.org/b/id/123456-L.jpg",
      "date_added": "2025-07-15T10:00:00Z",
      "date_completed": "2025-07-16T15:30:00Z",
      "rating": 5,
      "notes": "Excellent premier tome !"
    }
  ],
  "total": 1
}
```

### **POST /api/books**
Ajoute un nouveau livre à la bibliothèque.

**Request Body:**
```json
{
  "title": "Le Hobbit",
  "author": "J.R.R. Tolkien",
  "category": "roman",
  "pages": 280,
  "cover_url": "https://example.com/cover.jpg",
  "saga": "Terres du Milieu",
  "volume": 1,
  "status": "to_read"
}
```

**Response:**
```json
{
  "id": "new_book_id",
  "title": "Le Hobbit",
  "author": "J.R.R. Tolkien",
  "category": "roman",
  "status": "to_read",
  "pages": 280,
  "pages_read": 0,
  "cover_url": "https://example.com/cover.jpg",
  "date_added": "2025-07-16T16:00:00Z"
}
```

### **PUT /api/books/{book_id}**
Met à jour un livre existant.

**Request Body:**
```json
{
  "status": "completed",
  "pages_read": 280,
  "rating": 4,
  "notes": "Très bonne introduction à l'univers"
}
```

### **DELETE /api/books/{book_id}**
Supprime un livre de la bibliothèque.

**Response:**
```json
{
  "message": "Livre supprimé avec succès"
}
```

---

## 🎭 **Profils auteurs enrichis**

### **GET /api/openlibrary/author/{author_name}**
Récupère le profil d'un auteur depuis OpenLibrary.

**Example:** `/api/openlibrary/author/Stephen King`

**Response:**
```json
{
  "found": true,
  "author": {
    "name": "Stephen King",
    "bio": "Stephen Edwin King is an American author of horror, supernatural fiction, suspense, crime, science-fiction, and fantasy novels.",
    "birth_date": "21 September 1947",
    "death_date": null,
    "photo_url": "https://covers.openlibrary.org/a/id/14853840-L.jpg",
    "works_count": 65,
    "top_work": "The Shining",
    "wikipedia_url": "https://en.wikipedia.org/wiki/Stephen_King",
    "source": "openlibrary"
  }
}
```

### **GET /api/wikipedia/author/{author_name}** *(Session 87.4)*
Récupère le profil d'un auteur depuis Wikipedia avec données curées.

**Example:** `/api/wikipedia/author/Stephen King`

**Response:**
```json
{
  "found": true,
  "author": {
    "name": "Stephen King",
    "bio": "Stephen Edwin King is an American author... has written approximately 200 short stories, most of which have been published in collections.",
    "birth_date": "1947",
    "death_date": null,
    "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Stephen_King%2C_Comicon.jpg/800px-Stephen_King%2C_Comicon.jpg",
    "work_summary": "65 novels, 12 short story collections, 5 non-fiction books",
    "details": "approximately 200 short stories published in collections",
    "specialties": ["Horror", "Supernatural fiction", "Suspense"],
    "awards": ["Hugo Award", "Bram Stoker Award", "World Fantasy Award"],
    "wikipedia_url": "https://en.wikipedia.org/wiki/Stephen_King",
    "source": "wikipedia"
  }
}
```

---

## 📖 **Système séries intelligent**

### **GET /api/series/popular**
Récupère les séries populaires avec filtres.

**Query Parameters:**
- `category` (optional): roman, bd, manga
- `limit` (optional): Nombre max résultats (défaut: 10)

**Response:**
```json
{
  "series": [
    {
      "name": "Harry Potter",
      "category": "roman",
      "authors": ["J.K. Rowling"],
      "volumes": 7,
      "description": "Saga de fantasy britannique",
      "score": 95,
      "keywords": ["magic", "wizards", "hogwarts"],
      "first_published": "1997",
      "status": "completed",
      "cover_url": "https://example.com/harry-potter-cover.jpg"
    }
  ],
  "total": 1
}
```

### **GET /api/series/search**
Recherche de séries avec terme de recherche.

**Query Parameters:**
- `q` (required): Terme de recherche
- `category` (optional): Filtrer par catégorie
- `limit` (optional): Nombre max résultats

**Response:**
```json
{
  "series": [
    {
      "name": "One Piece",
      "category": "manga",
      "authors": ["Eiichiro Oda"],
      "volumes": 100,
      "description": "Manga de pirates et aventures",
      "search_score": 180,
      "match_reasons": ["title_match", "author_match"]
    }
  ],
  "total": 1,
  "search_term": "one piece"
}
```

### **GET /api/series/detect**
Détecte à quelle série appartient un livre.

**Query Parameters:**
- `title` (required): Titre du livre
- `author` (optional): Auteur du livre

**Response:**
```json
{
  "detected": true,
  "series": {
    "name": "Harry Potter",
    "category": "roman",
    "authors": ["J.K. Rowling"],
    "confidence": 180,
    "match_reasons": ["author_match", "title_variation", "keywords_match_2"],
    "volume_detected": 2,
    "volume_title": "Harry Potter et la Chambre des Secrets"
  }
}
```

### **POST /api/series/complete**
Auto-complète une série en ajoutant les volumes manquants.

**Request Body:**
```json
{
  "series_name": "Harry Potter",
  "base_book_id": "existing_book_id",
  "volumes_to_add": 6
}
```

**Response:**
```json
{
  "message": "Série complétée avec succès",
  "books_added": [
    {
      "id": "new_book_id_1",
      "title": "Harry Potter et la Chambre des Secrets",
      "volume": 2,
      "auto_added": true
    }
  ],
  "total_added": 6
}
```

---

## 🔍 **Recherche Open Library**

### **GET /api/openlibrary/search**
Recherche de livres dans le catalogue Open Library.

**Query Parameters:**
- `q` (required): Terme de recherche
- `limit` (optional): Nombre max résultats (défaut: 20)
- `category` (optional): Filtrer par catégorie

**Response:**
```json
{
  "results": [
    {
      "title": "Dune",
      "author": "Frank Herbert",
      "cover_url": "https://covers.openlibrary.org/b/id/123456-L.jpg",
      "ol_key": "OL123456W",
      "category": "roman",
      "categoryBadge": {
        "key": "roman",
        "label": "Roman",
        "color": "blue"
      },
      "first_publish_year": 1965,
      "relevance_score": 95,
      "relevance_level": "Très pertinent"
    }
  ],
  "total": 1,
  "search_term": "dune"
}
```

### **POST /api/openlibrary/import**
Importe un livre depuis Open Library vers la bibliothèque.

**Request Body:**
```json
{
  "ol_key": "OL123456W",
  "title": "Dune",
  "author": "Frank Herbert",
  "cover_url": "https://covers.openlibrary.org/b/id/123456-L.jpg",
  "category": "roman",
  "status": "to_read"
}
```

**Response:**
```json
{
  "message": "Livre importé avec succès",
  "book": {
    "id": "new_book_id",
    "title": "Dune",
    "author": "Frank Herbert",
    "category": "roman",
    "status": "to_read",
    "date_added": "2025-07-16T16:00:00Z"
  }
}
```

---

## 📊 **Statistiques**

### **GET /api/stats**
Récupère les statistiques détaillées de l'utilisateur.

**Response:**
```json
{
  "total_books": 25,
  "completed_books": 15,
  "reading_books": 5,
  "to_read_books": 5,
  "categories": {
    "roman": 15,
    "bd": 8,
    "manga": 2
  },
  "authors_count": 20,
  "sagas_count": 8,
  "auto_added_count": 3,
  "pages_read": 5420,
  "average_rating": 4.2,
  "reading_streak": 15,
  "monthly_stats": {
    "books_completed_this_month": 3,
    "pages_read_this_month": 890
  }
}
```

### **GET /api/stats/advanced**
Statistiques avancées avec graphiques et tendances.

**Response:**
```json
{
  "reading_trends": {
    "last_30_days": [
      {
        "date": "2025-07-01",
        "books_completed": 1,
        "pages_read": 320
      }
    ]
  },
  "category_distribution": {
    "roman": 60,
    "bd": 32,
    "manga": 8
  },
  "author_stats": {
    "most_read_author": "J.K. Rowling",
    "books_by_most_read": 7
  },
  "predictions": {
    "books_this_year": 45,
    "favorite_genre": "fantasy"
  }
}
```

---

## 💾 **Export/Import**

### **GET /api/export-import/export/formats**
Récupère les formats d'export supportés.

**Response:**
```json
{
  "supported_formats": ["json", "csv", "excel", "full_backup"],
  "formats_details": {
    "json": {
      "name": "JSON",
      "description": "Format JSON complet avec métadonnées",
      "extension": ".json",
      "size_estimate": "small"
    },
    "csv": {
      "name": "CSV",
      "description": "Format CSV pour tableurs",
      "extension": ".csv",
      "size_estimate": "small"
    },
    "excel": {
      "name": "Excel",
      "description": "Fichier Excel avec feuilles multiples",
      "extension": ".xlsx",
      "size_estimate": "medium"
    },
    "full_backup": {
      "name": "Backup complet",
      "description": "Archive ZIP avec tous les formats",
      "extension": ".zip",
      "size_estimate": "large"
    }
  }
}
```

### **GET /api/export-import/export**
Exporte la bibliothèque dans le format demandé.

**Query Parameters:**
- `format` (required): json, csv, excel, full_backup
- `include_metadata` (optional): true/false
- `category` (optional): Filtrer par catégorie

**Response:** Fichier téléchargeable avec Content-Type approprié

### **POST /api/export-import/import/preview**
Prévisualise l'import d'un fichier sans l'importer.

**Request:** Multipart form avec fichier

**Response:**
```json
{
  "file_info": {
    "name": "library.csv",
    "size": 15420,
    "format": "csv"
  },
  "preview": {
    "total_books_found": 25,
    "books_to_import": 20,
    "duplicates_found": 5,
    "sample_books": [
      {
        "title": "Dune",
        "author": "Frank Herbert",
        "category": "roman",
        "action": "import"
      }
    ]
  }
}
```

### **POST /api/export-import/import**
Importe réellement un fichier de bibliothèque.

**Request:** Multipart form avec fichier + options

**Response:**
```json
{
  "message": "Import réussi",
  "summary": {
    "total_processed": 25,
    "imported": 20,
    "skipped": 5,
    "errors": 0
  },
  "imported_books": [
    {
      "id": "new_book_id",
      "title": "Dune",
      "author": "Frank Herbert"
    }
  ]
}
```

---

## 🎯 **Recommandations IA**

### **GET /api/recommendations**
Recommandations personnalisées basées sur l'historique.

**Query Parameters:**
- `category` (optional): Filtrer par catégorie
- `limit` (optional): Nombre max résultats
- `algorithm` (optional): collaborative, content_based, hybrid

**Response:**
```json
{
  "recommendations": [
    {
      "title": "Foundation",
      "author": "Isaac Asimov",
      "category": "roman",
      "score": 92,
      "reason": "Basé sur vos lectures de science-fiction",
      "cover_url": "https://example.com/foundation-cover.jpg",
      "similar_to": ["Dune", "Hyperion"]
    }
  ],
  "algorithm_used": "hybrid",
  "total": 1
}
```

### **GET /api/recommendations/advanced**
Recommandations avancées avec IA et machine learning.

**Response:**
```json
{
  "personalized_recommendations": [
    {
      "title": "The Expanse",
      "author": "James S.A. Corey",
      "ml_score": 95,
      "factors": ["space_opera", "political_intrigue", "character_development"],
      "confidence": 0.92
    }
  ],
  "trending_books": [
    {
      "title": "Project Hail Mary",
      "author": "Andy Weir",
      "trend_score": 88,
      "trend_reason": "Popular cette semaine"
    }
  ],
  "similar_users_reads": [
    {
      "title": "Klara and the Sun",
      "author": "Kazuo Ishiguro",
      "user_overlap": 0.85,
      "avg_rating": 4.3
    }
  ]
}
```

---

## 🔍 **Monitoring et santé**

### **GET /health**
Vérification santé de l'API.

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2025-07-16T16:38:32.919134",
  "version": "1.0.0",
  "uptime": "2h 15m 30s"
}
```

### **GET /api/monitoring/metrics**
Métriques de performance et utilisation.

**Response:**
```json
{
  "api_metrics": {
    "total_requests": 15420,
    "average_response_time": 180,
    "error_rate": 0.01,
    "requests_per_minute": 45
  },
  "database_metrics": {
    "connection_pool_size": 10,
    "active_connections": 3,
    "query_time_avg": 25
  },
  "system_metrics": {
    "cpu_usage": 45,
    "memory_usage": 60,
    "disk_usage": 30
  }
}
```

---

## 🔒 **Codes d'erreur**

### Codes HTTP standards
- **200** : Succès
- **201** : Créé avec succès
- **400** : Requête invalide
- **401** : Non authentifié
- **403** : Accès interdit
- **404** : Ressource non trouvée
- **409** : Conflit (ex: livre déjà existant)
- **422** : Données invalides
- **500** : Erreur serveur interne

### Exemples de réponses d'erreur
```json
{
  "error": "BOOK_NOT_FOUND",
  "message": "Le livre demandé n'existe pas",
  "code": 404,
  "details": {
    "book_id": "invalid_id"
  }
}
```

---

## 🔧 **Utilisation avancée**

### Authentification Bearer Token
```bash
curl -H "Authorization: Bearer your_jwt_token" \
     http://localhost:8001/api/books
```

### Pagination
```bash
curl "http://localhost:8001/api/books?limit=10&offset=20"
```

### Filtrage multiple
```bash
curl "http://localhost:8001/api/books?category=roman&status=completed&author=Tolkien"
```

### Upload de fichier
```bash
curl -X POST \
     -H "Authorization: Bearer your_jwt_token" \
     -F "file=@library.csv" \
     http://localhost:8001/api/export-import/import
```

---

## 📚 **Ressources**

### Documentation interactive
- **Swagger UI** : http://localhost:8001/docs
- **ReDoc** : http://localhost:8001/redoc

### Exemples de code
- **Python** : Voir `/examples/python/`
- **JavaScript** : Voir `/examples/javascript/`
- **cURL** : Voir `/examples/curl/`

### Postman Collection
Collection Postman complète disponible : `/postman/booktime_api.json`

---

**🎯 Cette documentation API est mise à jour automatiquement et reflète l'état actuel de l'API BOOKTIME avec ses 89 endpoints opérationnels.**

*Version : 87.5.1 - Juillet 2025*
*Statut : Production Ready - Enterprise Level*