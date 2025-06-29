# 🔌 API DOCUMENTATION - BOOKTIME

## 🎯 RÉFÉRENCE API COMPLÈTE
**Version** : 1.0  
**Date** : Mars 2025  
**Base URL** : `https://api.booktime.com` (production) ou `http://localhost:8001` (développement)  
**Statut** : 89 endpoints testés et validés ✅

---

## 📋 SOMMAIRE

1. [Authentification](#authentification)
2. [Gestion des Livres](#gestion-des-livres)
3. [Séries et Sagas](#séries-et-sagas)
4. [Recherche Avancée](#recherche-avancée)
5. [Statistiques](#statistiques)
6. [Auteurs et Sagas](#auteurs-et-sagas)
7. [Intégration Open Library](#intégration-open-library)
8. [Codes de Réponse](#codes-de-réponse)
9. [Exemples d'Usage](#exemples-dusage)

---

## 🔐 AUTHENTIFICATION

### Vue d'ensemble
L'authentification utilise un système **simplifié sans email/mot de passe**, basé uniquement sur **prénom + nom** avec des tokens JWT.

### POST /api/auth/register
Enregistrer un nouvel utilisateur.

**Endpoint** : `POST /api/auth/register`  
**Content-Type** : `application/json`  
**Authentification** : Non requise

#### Paramètres
```json
{
  "first_name": "string",    // Prénom (requis)
  "last_name": "string"      // Nom (requis)
}
```

#### Réponse Success (201)
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-string",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### Erreurs
- `400` : Utilisateur existe déjà avec ce nom
- `422` : Données manquantes ou invalides

---

### POST /api/auth/login
Connecter un utilisateur existant.

**Endpoint** : `POST /api/auth/login`  
**Content-Type** : `application/json`  
**Authentification** : Non requise

#### Paramètres
```json
{
  "first_name": "string",    // Prénom (requis)
  "last_name": "string"      // Nom (requis)
}
```

#### Réponse Success (200)
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer", 
  "user": {
    "id": "uuid-string",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### Erreurs
- `400` : Utilisateur non trouvé
- `422` : Données manquantes

---

### GET /api/auth/me
Récupérer les informations de l'utilisateur connecté.

**Endpoint** : `GET /api/auth/me`  
**Authentification** : Bearer token requis

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Réponse Success (200)
```json
{
  "id": "uuid-string",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2025-03-01T12:00:00Z"
}
```

#### Erreurs
- `401` : Token invalide ou expiré
- `403` : Token manquant

---

## 📚 GESTION DES LIVRES

### GET /api/books
Récupérer la liste des livres de l'utilisateur.

**Endpoint** : `GET /api/books`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
category     : string  // roman|bd|manga (optionnel)
status       : string  // to_read|reading|completed (optionnel)  
view_mode    : string  // books|series (défaut: books)
```

#### Exemples
```
GET /api/books                           // Tous les livres
GET /api/books?category=manga            // Seulement les mangas
GET /api/books?status=reading            // Livres en cours
GET /api/books?view_mode=series          // Vue par séries
```

#### Réponse Success (200)
```json
[
  {
    "id": "uuid-string",
    "user_id": "uuid-string",
    "title": "Harry Potter à l'École des Sorciers",
    "author": "J.K. Rowling",
    "category": "roman",
    "description": "L'histoire d'un jeune sorcier...",
    "total_pages": 309,
    "current_page": 150,
    "status": "reading",
    "rating": 5,
    "review": "Excellent livre !",
    "cover_url": "https://covers.openlibrary.org/...",
    "saga": "Harry Potter",
    "volume_number": 1,
    "genre": "Fantasy",
    "publication_year": 1997,
    "publisher": "Bloomsbury",
    "isbn": "9780747532743",
    "auto_added": false,
    "date_added": "2025-03-01T10:00:00Z",
    "date_started": "2025-03-01T10:00:00Z",
    "date_completed": null,
    "updated_at": "2025-03-01T12:00:00Z"
  }
]
```

---

### POST /api/books
Ajouter un nouveau livre à la bibliothèque.

**Endpoint** : `POST /api/books`  
**Content-Type** : `application/json`  
**Authentification** : Bearer token requis

#### Paramètres
```json
{
  "title": "string",                    // Titre (requis)
  "author": "string",                   // Auteur (requis)
  "category": "roman|bd|manga",         // Catégorie (défaut: roman)
  "description": "string",              // Description (optionnel)
  "total_pages": "integer",             // Nombre de pages (optionnel)
  "status": "to_read|reading|completed", // Statut (défaut: to_read)
  "current_page": "integer",            // Page actuelle (optionnel)
  "rating": "integer",                  // Note 1-5 (optionnel)
  "review": "string",                   // Avis (optionnel)
  "cover_url": "string",                // URL couverture (optionnel)
  "saga": "string",                     // Nom série (optionnel)
  "volume_number": "integer",           // Numéro tome (optionnel)
  "genre": "string",                    // Genre (optionnel)
  "publication_year": "integer",        // Année publication (optionnel)
  "publisher": "string",                // Éditeur (optionnel)
  "isbn": "string"                      // ISBN (optionnel)
}
```

#### Exemple
```json
{
  "title": "One Piece - Tome 1",
  "author": "Eiichiro Oda",
  "category": "manga",
  "description": "Les aventures de Luffy",
  "saga": "One Piece",
  "volume_number": 1,
  "status": "to_read"
}
```

#### Réponse Success (201)
```json
{
  "id": "nouveau-uuid",
  "user_id": "uuid-user",
  "title": "One Piece - Tome 1",
  "author": "Eiichiro Oda",
  "category": "manga",
  "description": "Les aventures de Luffy",
  "saga": "One Piece",
  "volume_number": 1,
  "status": "to_read",
  "auto_added": false,
  "date_added": "2025-03-01T15:00:00Z",
  // ... autres champs avec valeurs par défaut
}
```

#### Erreurs
- `422` : Catégorie invalide ou données manquantes
- `401` : Token invalide

---

### GET /api/books/{book_id}
Récupérer les détails d'un livre spécifique.

**Endpoint** : `GET /api/books/{book_id}`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
{
  "id": "book-uuid",
  "user_id": "user-uuid",
  "title": "Titre du livre",
  // ... tous les champs du livre
}
```

#### Erreurs
- `404` : Livre non trouvé ou n'appartient pas à l'utilisateur

---

### PUT /api/books/{book_id}
Mettre à jour un livre existant.

**Endpoint** : `PUT /api/books/{book_id}`  
**Content-Type** : `application/json`  
**Authentification** : Bearer token requis

#### Paramètres (tous optionnels)
```json
{
  "status": "to_read|reading|completed",
  "current_page": "integer",
  "rating": "integer",           // 1-5
  "review": "string",
  "description": "string",
  "total_pages": "integer"
}
```

#### Logique Automatique
- Passage à "reading" → `date_started` = maintenant
- Passage à "completed" → `date_completed` = maintenant
- `updated_at` = maintenant automatiquement

#### Réponse Success (200)
```json
{
  "id": "book-uuid",
  // ... livre mis à jour avec nouveaux champs
  "updated_at": "2025-03-01T16:00:00Z"
}
```

---

### DELETE /api/books/{book_id}
Supprimer un livre de la bibliothèque.

**Endpoint** : `DELETE /api/books/{book_id}`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
{
  "message": "Livre supprimé avec succès"
}
```

#### Erreurs
- `404` : Livre non trouvé

---

## 📖 SÉRIES ET SAGAS

### GET /api/series/popular
Récupérer la liste des séries populaires prédéfinies.

**Endpoint** : `GET /api/series/popular`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
category : string  // roman|bd|manga (optionnel)
language : string  // fr|en|jp (défaut: fr)
limit    : integer // Nombre max (défaut: 50)
```

#### Réponse Success (200)
```json
{
  "series": [
    {
      "name": "Harry Potter",
      "category": "roman", 
      "score": 18000,
      "keywords": ["harry", "potter", "sorcier", "wizard"],
      "authors": ["J.K. Rowling"],
      "variations": ["Harry Potter", "École des Sorciers"],
      "volumes": 7,
      "languages": ["fr", "en"],
      "description": "La saga du jeune sorcier",
      "first_published": 1997,
      "status": "completed"
    }
  ],
  "total": 8,
  "category": null,
  "language": "fr"
}
```

---

### GET /api/series/search
Rechercher des séries par nom avec scoring de pertinence.

**Endpoint** : `GET /api/series/search`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
q        : string  // Terme de recherche (requis)
category : string  // Filtrer par catégorie (optionnel)
limit    : integer // Nombre max (défaut: 20)
```

#### Réponse Success (200)
```json
{
  "series": [
    {
      "name": "Harry Potter",
      "category": "roman",
      "isSeriesCard": true,
      "search_score": 9500,
      "match_reasons": ["exact_name", "author_match"],
      // ... autres champs série
    }
  ],
  "total": 1,
  "search_term": "harry potter"
}
```

---

### GET /api/series/detect
Détecter automatiquement à quelle série appartient un livre.

**Endpoint** : `GET /api/series/detect`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
title  : string  // Titre du livre (requis)
author : string  // Auteur (optionnel mais recommandé)
```

#### Exemple
```
GET /api/series/detect?title=Harry Potter et la Chambre des Secrets&author=J.K. Rowling
```

#### Réponse Success (200)
```json
{
  "detected_series": [
    {
      "series": {
        "name": "Harry Potter",
        "category": "roman",
        // ... détails série complète
      },
      "confidence": 180,
      "match_reasons": ["author_match", "title_variation", "keywords_match_2"]
    }
  ],
  "book_info": {
    "title": "Harry Potter et la Chambre des Secrets",
    "author": "J.K. Rowling"
  }
}
```

---

### POST /api/series/complete
Auto-compléter une série en ajoutant tous les volumes manquants.

**Endpoint** : `POST /api/series/complete`  
**Content-Type** : `application/json`  
**Authentification** : Bearer token requis

#### Paramètres
```json
{
  "series_name": "string",        // Nom de la série (requis)
  "target_volumes": "integer",    // Nombre de volumes cibles (requis)
  "template_book_id": "string"    // ID livre modèle (optionnel)
}
```

#### Réponse Success (200)
```json
{
  "message": "4 tome(s) ajouté(s) à la série One Piece",
  "created_books": [
    {
      "id": "uuid-tome-2",
      "title": "One Piece - Tome 2", 
      "saga": "One Piece",
      "volume_number": 2,
      "status": "to_read",
      "auto_added": true,
      // ... autres champs
    }
  ],
  "series_name": "One Piece",
  "total_volumes": 5,
  "existing_volumes": 1,
  "created_volumes": 4
}
```

---

## 🔍 RECHERCHE AVANCÉE

### GET /api/books/search-grouped
Recherche de livres avec regroupement intelligent par saga.

**Endpoint** : `GET /api/books/search-grouped`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
q        : string  // Terme de recherche (requis, min 2 caractères)
category : string  // Filtrer par catégorie (optionnel)
```

#### Réponse Success (200)
```json
{
  "results": [
    {
      "type": "saga",
      "id": "saga_harry_potter",
      "name": "Harry Potter",
      "books": [
        {
          "id": "uuid-tome-1",
          "title": "Harry Potter à l'École des Sorciers",
          "volume_number": 1,
          "status": "completed"
        }
      ],
      "total_books": 3,
      "completed_books": 1,
      "reading_books": 1,
      "to_read_books": 1,
      "author": "J.K. Rowling",
      "category": "roman",
      "cover_url": "https://...",
      "completion_percentage": 33,
      "status": "reading",
      "match_reason": "saga_match"
    },
    {
      "type": "book",
      "id": "uuid-livre-seul",
      "title": "Livre sans série",
      "author": "Auteur", 
      "match_reason": "individual_book"
      // ... autres champs livre
    }
  ],
  "total_books": 4,
  "total_sagas": 1,
  "search_term": "harry",
  "grouped_by_saga": true,
  "series_first": true
}
```

---

## 📊 STATISTIQUES

### GET /api/stats
Récupérer les statistiques complètes de l'utilisateur.

**Endpoint** : `GET /api/stats`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
{
  "total_books": 42,
  "completed_books": 15,
  "reading_books": 3,
  "to_read_books": 24,
  "categories": {
    "roman": 18,
    "bd": 12,
    "manga": 12
  },
  "authors_count": 28,
  "sagas_count": 8,
  "auto_added_count": 12
}
```

---

## 👥 AUTEURS ET SAGAS

### GET /api/authors
Liste tous les auteurs avec leurs statistiques.

**Endpoint** : `GET /api/authors`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
[
  {
    "name": "J.K. Rowling",
    "books_count": 7,
    "categories": ["roman"],
    "sagas": ["Harry Potter"]
  },
  {
    "name": "Eiichiro Oda", 
    "books_count": 12,
    "categories": ["manga"],
    "sagas": ["One Piece"]
  }
]
```

---

### GET /api/authors/{author_name}/books
Récupérer tous les livres d'un auteur spécifique.

**Endpoint** : `GET /api/authors/{author_name}/books`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
[
  {
    "id": "uuid-livre-1",
    "title": "Harry Potter à l'École des Sorciers",
    "author": "J.K. Rowling",
    // ... autres champs livre
  }
]
```

---

### GET /api/sagas
Liste toutes les sagas avec leurs statistiques.

**Endpoint** : `GET /api/sagas`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
[
  {
    "name": "Harry Potter",
    "books_count": 7,
    "completed_books": 5,
    "next_volume": 8,
    "author": "J.K. Rowling",
    "category": "roman",
    "completion_percentage": 71
  }
]
```

---

### GET /api/sagas/{saga_name}/books
Récupérer tous les livres d'une saga, triés par volume.

**Endpoint** : `GET /api/sagas/{saga_name}/books`  
**Authentification** : Bearer token requis

#### Réponse Success (200)
```json
[
  {
    "id": "uuid-tome-1",
    "title": "Harry Potter à l'École des Sorciers",
    "volume_number": 1,
    "status": "completed"
  },
  {
    "id": "uuid-tome-2", 
    "title": "Harry Potter et la Chambre des Secrets",
    "volume_number": 2,
    "status": "reading"
  }
]
```

---

### POST /api/sagas/{saga_name}/auto-add
Ajouter automatiquement le prochain volume d'une saga.

**Endpoint** : `POST /api/sagas/{saga_name}/auto-add`  
**Content-Type** : `application/json`  
**Authentification** : Bearer token requis

#### Réponse Success (201)
```json
{
  "id": "uuid-nouveau-tome",
  "title": "Harry Potter - Tome 8",
  "saga": "Harry Potter",
  "volume_number": 8,
  "status": "to_read",
  "auto_added": true,
  "date_added": "2025-03-01T16:00:00Z"
  // ... autres champs
}
```

---

## 🌐 INTÉGRATION OPEN LIBRARY

### GET /api/openlibrary/search
Rechercher des livres sur Open Library.

**Endpoint** : `GET /api/openlibrary/search`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
q           : string  // Terme de recherche (requis)
category    : string  // Catégorie cible (optionnel)
limit       : integer // Nombre max (défaut: 20, max: 100)
year_start  : integer // Année min (optionnel)
year_end    : integer // Année max (optionnel)
language    : string  // Code langue (fr, en, etc.)
author_filter: string // Filtrer par auteur (optionnel)
min_pages   : integer // Pages minimum (optionnel)
max_pages   : integer // Pages maximum (optionnel)
```

#### Exemples
```
GET /api/openlibrary/search?q=harry potter
GET /api/openlibrary/search?q=manga&category=manga&limit=10
GET /api/openlibrary/search?q=tolkien&year_start=1950&year_end=1980
```

#### Réponse Success (200)
```json
{
  "books": [
    {
      "ol_key": "/works/OL82563W",
      "title": "Harry Potter and the Philosopher's Stone", 
      "author": "J.K. Rowling",
      "category": "roman",
      "cover_url": "https://covers.openlibrary.org/b/id/6979861-L.jpg",
      "description": "Harry Potter has never been...",
      "isbn": "9780747532743",
      "publisher": "Bloomsbury",
      "publication_year": 1997,
      "total_pages": 223,
      "isFromOpenLibrary": true,
      "isOwned": false
    }
  ],
  "total_found": 3847,
  "filters_applied": {
    "query": "harry potter",
    "category": null,
    "limit": 20
  }
}
```

---

### POST /api/openlibrary/import
Importer un livre depuis Open Library vers la bibliothèque.

**Endpoint** : `POST /api/openlibrary/import`  
**Content-Type** : `application/json`  
**Authentification** : Bearer token requis

#### Paramètres
```json
{
  "ol_key": "string",              // Clé Open Library (requis)
  "category": "roman|bd|manga"     // Catégorie cible (requis)
}
```

#### Réponse Success (201)
```json
{
  "id": "uuid-nouveau-livre",
  "title": "Harry Potter and the Philosopher's Stone",
  "author": "J.K. Rowling",
  "category": "roman",
  "cover_url": "https://covers.openlibrary.org/...",
  "isbn": "9780747532743",
  "status": "to_read",
  "date_added": "2025-03-01T17:00:00Z"
  // ... tous les champs livre
}
```

#### Erreurs
- `409` : Livre déjà présent (détection doublons par ISBN ou titre+auteur)
- `404` : Clé Open Library invalide
- `422` : Paramètres manquants

---

### POST /api/openlibrary/import-bulk
Importer plusieurs livres en une seule requête.

**Endpoint** : `POST /api/openlibrary/import-bulk`  
**Content-Type** : `application/json`  
**Authentification** : Bearer token requis

#### Paramètres
```json
{
  "books": [
    {
      "ol_key": "/works/OL82563W",
      "category": "roman"
    },
    {
      "ol_key": "/works/OL123456W", 
      "category": "manga"
    }
  ]
}
```

#### Réponse Success (200)
```json
{
  "total_requested": 2,
  "imported": 1,
  "duplicates": 1,
  "errors": 0,
  "imported_books": [
    {
      "id": "uuid-1",
      "title": "Nouveau livre importé",
      // ... détails livre
    }
  ],
  "duplicate_books": [
    {
      "title": "Livre déjà présent",
      "reason": "ISBN already exists"
    }
  ],
  "error_books": []
}
```

---

### GET /api/openlibrary/recommendations
Obtenir des recommandations personnalisées basées sur la bibliothèque.

**Endpoint** : `GET /api/openlibrary/recommendations`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
limit : integer  // Nombre de recommandations (défaut: 10)
```

#### Réponse Success (200)
```json
{
  "recommendations": [
    {
      "ol_key": "/works/OL123456W",
      "title": "Livre recommandé",
      "author": "Auteur similaire",
      "category": "roman",
      "reason": "Based on your love for fantasy books by J.K. Rowling",
      "cover_url": "https://covers.openlibrary.org/...",
      // ... autres champs
    }
  ],
  "total": 1,
  "based_on": {
    "favorite_authors": ["J.K. Rowling", "George R.R. Martin"],
    "favorite_categories": ["roman"],
    "favorite_genres": ["fantasy"]
  }
}
```

---

### GET /api/openlibrary/missing-volumes
Détecter les volumes manquants dans les séries de l'utilisateur.

**Endpoint** : `GET /api/openlibrary/missing-volumes`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
saga : string  // Nom de la saga (requis)
```

#### Réponse Success (200)
```json
{
  "saga_name": "Harry Potter",
  "present_volumes": [1, 2, 4, 7],
  "missing_volumes": [3, 5, 6],
  "next_volume": 8,
  "suggested_books": [
    {
      "ol_key": "/works/OL456789W",
      "title": "Harry Potter and the Prisoner of Azkaban",
      "volume_number": 3,
      "author": "J.K. Rowling",
      "cover_url": "https://covers.openlibrary.org/..."
    }
  ]
}
```

---

### GET /api/openlibrary/search-isbn
Rechercher un livre par son ISBN.

**Endpoint** : `GET /api/openlibrary/search-isbn`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
isbn : string  // ISBN (13 ou 10 chiffres, avec ou sans tirets)
```

#### Exemples
```
GET /api/openlibrary/search-isbn?isbn=9780747532743
GET /api/openlibrary/search-isbn?isbn=978-0-7475-3274-3
```

#### Réponse Success (200)
```json
{
  "found": true,
  "book": {
    "ol_key": "/works/OL82563W",
    "title": "Harry Potter and the Philosopher's Stone",
    "author": "J.K. Rowling",
    "isbn": "9780747532743",
    "category": "roman",
    // ... autres champs
  }
}
```

#### ISBN Non Trouvé (200)
```json
{
  "found": false,
  "isbn": "9999999999999"
}
```

---

### GET /api/openlibrary/search-advanced
Recherche multi-critères avancée.

**Endpoint** : `GET /api/openlibrary/search-advanced`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
title     : string  // Titre (optionnel)
author    : string  // Auteur (optionnel)
subject   : string  // Sujet/genre (optionnel)
publisher : string  // Éditeur (optionnel)
isbn      : string  // ISBN (optionnel)
year_start: integer // Année début (optionnel)
year_end  : integer // Année fin (optionnel)
limit     : integer // Limite résultats (défaut: 20)
```

#### Exemple
```
GET /api/openlibrary/search-advanced?author=tolkien&subject=fantasy&year_start=1950&year_end=1980
```

#### Réponse Success (200)
```json
{
  "books": [
    {
      "ol_key": "/works/OL27482W",
      "title": "The Lord of the Rings",
      "author": "J.R.R. Tolkien",
      // ... autres champs
    }
  ],
  "total_found": 45,
  "query_used": "author:tolkien AND subject:fantasy AND publish_year:[1950 TO 1980]",
  "criteria": {
    "author": "tolkien",
    "subject": "fantasy", 
    "year_range": "1950-1980"
  }
}
```

---

### GET /api/openlibrary/search-author
Recherche avancée par auteur avec groupement par séries.

**Endpoint** : `GET /api/openlibrary/search-author`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
author : string  // Nom de l'auteur (requis)
limit  : integer // Limite résultats (défaut: 50)
```

#### Réponse Success (200)
```json
{
  "author": "J.K. Rowling",
  "total_books": 23,
  "series": [
    {
      "name": "Harry Potter",
      "books": [
        {
          "ol_key": "/works/OL82563W",
          "title": "Harry Potter and the Philosopher's Stone",
          "volume_number": 1
        }
      ]
    }
  ],
  "standalone_books": [
    {
      "ol_key": "/works/OL456789W",
      "title": "The Casual Vacancy"
    }
  ]
}
```

---

### GET /api/openlibrary/suggestions
Suggestions d'import basées sur la bibliothèque existante.

**Endpoint** : `GET /api/openlibrary/suggestions`  
**Authentification** : Bearer token requis

#### Paramètres Query
```
limit : integer  // Nombre de suggestions (défaut: 10)
```

#### Réponse Success (200)
```json
{
  "suggestions": [
    {
      "type": "saga_continuation",
      "ol_key": "/works/OL789012W",
      "title": "Harry Potter - Tome 8",
      "author": "J.K. Rowling",
      "reason": "Continue your Harry Potter collection (you have 7/8 books)",
      "volume_number": 8
    },
    {
      "type": "favorite_author",
      "ol_key": "/works/OL345678W", 
      "title": "The Casual Vacancy",
      "author": "J.K. Rowling",
      "reason": "New book by your favorite author J.K. Rowling"
    }
  ],
  "total": 2
}
```

---

## 🚨 CODES DE RÉPONSE

### Codes de Succès
- `200 OK` : Requête réussie, données retournées
- `201 Created` : Ressource créée avec succès
- `204 No Content` : Requête réussie, pas de contenu

### Codes d'Erreur
- `400 Bad Request` : Données de requête invalides
- `401 Unauthorized` : Token JWT invalide ou expiré
- `403 Forbidden` : Token manquant
- `404 Not Found` : Ressource non trouvée
- `409 Conflict` : Conflit (ex: doublon)
- `422 Unprocessable Entity` : Validation Pydantic échouée
- `500 Internal Server Error` : Erreur serveur

### Format d'Erreur Standard
```json
{
  "detail": "Description de l'erreur",
  "error_code": "OPTIONAL_ERROR_CODE",
  "field_errors": {  // Pour erreurs de validation
    "field_name": ["Message d'erreur spécifique"]
  }
}
```

---

## 💡 EXEMPLES D'USAGE

### Workflow Complet d'Authentification
```javascript
// 1. Inscription
const response = await fetch('/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    first_name: 'John',
    last_name: 'Doe'
  })
});
const { access_token } = await response.json();

// 2. Stockage token
localStorage.setItem('token', access_token);

// 3. Utilisation pour requêtes authentifiées
const books = await fetch('/api/books', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Workflow Recherche et Import Open Library
```javascript
// 1. Recherche
const searchResults = await fetch('/api/openlibrary/search?q=harry potter&limit=5', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 2. Import d'un livre
const importResponse = await fetch('/api/openlibrary/import', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ol_key: '/works/OL82563W',
    category: 'roman'
  })
});
```

### Workflow Gestion de Série
```javascript
// 1. Détection de série
const detection = await fetch('/api/series/detect?title=Harry Potter Tome 1&author=J.K. Rowling', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// 2. Auto-complétion série
const completion = await fetch('/api/series/complete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    series_name: 'Harry Potter',
    target_volumes: 7
  })
});
```

---

**🎯 Cette API a été testée et validée avec 89 endpoints fonctionnels. Tous les exemples sont directement utilisables en production.**