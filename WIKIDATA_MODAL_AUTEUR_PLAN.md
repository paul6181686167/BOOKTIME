# 📋 PLAN DÉTAILLÉ - CONTINUATION MODIFICATION WIKIDATA MODAL AUTEUR

## 🎯 **OBJECTIF PRINCIPAL**
Finaliser l'intégration Wikidata dans le modal auteur pour afficher les livres individuels ET les séries avec une hiérarchie de sources optimisée.

## 📊 **ÉTAT ACTUEL - Session 87.16**

### ✅ **TERMINÉ**
- **Modèle backend** : `WikidataAuthorResponse` modifié avec `individual_books` + `total_individual_books`
- **Frontend corrigé** : `AuthorModal.js` utilise maintenant les livres individuels Wikidata
- **Endpoint de test** : `/api/wikidata/test-individual-books/{author_name}` créé
- **Requête SPARQL** : `GET_AUTHOR_INDIVIDUAL_BOOKS` avec types corrects (Q571, Q7725634, Q47461344, Q8261)

### ⚠️ **PROBLÈMES IDENTIFIÉS**
1. **Couverture limitée** : Beaucoup d'auteurs ne sont pas trouvés dans Wikidata
2. **Recherche par nom** : Sensible aux variations de noms (J.K. Rowling vs Joanne Rowling)
3. **Livres individuels** : Peu d'auteurs ont des livres individuels détectés
4. **Fallback incomplet** : Transition vers Wikipedia/OpenLibrary pas optimale

## 🗺️ **PLAN DÉTAILLÉ - 4 PHASES**

---

### **PHASE 1 : TESTS ET VALIDATION ENDPOINTS** ⏳

#### **1.1 Tests endpoint livres individuels**
- **Action** : Tester `/api/wikidata/test-individual-books/{author_name}`
- **Auteurs à tester** :
  - J.K. Rowling (séries connues)
  - Amélie Nothomb (livres individuels potentiels)
  - Douglas Adams (livres individuels + séries)
  - Paulo Coelho (livres individuels)
  - Haruki Murakami (livres individuels)
- **Validation** : Structure des données, performances, erreurs

#### **1.2 Identification auteurs avec livres individuels**
- **Objectif** : Trouver des auteurs avec des livres individuels dans Wikidata
- **Méthode** : Tests systématiques avec différents auteurs
- **Documentation** : Créer liste d'auteurs de test validés

#### **1.3 Validation structure des données**
- **Champs requis** : id, title, publication_date, genre, book_type, isbn, publisher, description
- **Format** : JSON cohérent avec les séries
- **Fallback** : Gestion des champs manquants

---

### **PHASE 2 : AMÉLIORATION REQUÊTES SPARQL** ⏳

#### **2.1 Analyse des échecs de recherche**
- **Problème** : Recherche par nom trop restrictive
- **Solutions** :
  - Recherche par labels alternatifs (`skos:altLabel`)
  - Recherche par aliases (`schema:alternateName`)
  - Recherche approximative (distance de Levenshtein)

#### **2.2 Optimisation requêtes**
- **Requête séries** : Ajouter plus de types de séries
- **Requête livres individuels** : Élargir les critères de sélection
- **Performance** : Optimiser les LIMIT et FILTER

#### **2.3 Fallbacks pour noms d'auteurs**
```sparql
# Recherche élargie avec aliases
?author rdfs:label|skos:altLabel|schema:alternateName ?name .
FILTER(CONTAINS(LCASE(?name), LCASE("%(author_name)s")))
```

---

### **PHASE 3 : TESTS FRONTEND COMPLETS** ⏳

#### **3.1 Tests modal auteur**
- **Scénarios** :
  - Auteur avec séries seulement (J.K. Rowling)
  - Auteur avec livres individuels seulement
  - Auteur avec séries + livres individuels
  - Auteur non trouvé (fallback vers Wikipedia)
- **Validation** : Affichage, performance, UX

#### **3.2 Hiérarchie des sources**
- **Ordre** : Wikidata → Wikipedia → OpenLibrary → Bibliothèque
- **Logique** : Afficher la source la plus riche
- **Badges** : Identification claire de la source

#### **3.3 Interface utilisateur**
- **Séries expandables** : Affichage des livres dans les séries
- **Livres individuels** : Section séparée sous les séries
- **Statuts** : Badges de statut pour les livres possédés

---

### **PHASE 4 : DOCUMENTATION COMPLÈTE** ⏳

#### **4.1 Documentation CHANGELOG.md**
- **Session 87.16** : Continuation modification Wikidata modal auteur
- **Changements** : Modèle, frontend, endpoints, requêtes
- **Métriques** : Performance, couverture, tests

#### **4.2 Documentation technique**
- **Architecture** : Diagramme flux de données
- **API** : Documentation endpoints Wikidata
- **Frontend** : Logique hiérarchie sources

#### **4.3 Exemples d'utilisation**
- **Cas d'usage** : Auteurs avec différents profils
- **Réponses types** : Structures JSON complètes
- **Troubleshooting** : Problèmes fréquents et solutions

---

## 🛠️ **ACTIONS IMMÉDIATES**

### **Étape 1 : Tests endpoint livres individuels**
```bash
# Test avec token valide
curl "http://localhost:8001/api/wikidata/test-individual-books/J.K. Rowling" -H "Authorization: Bearer {token}"
```

### **Étape 2 : Identifier auteurs de test**
- Tester 10 auteurs différents
- Documenter résultats dans `/app/WIKIDATA_TESTS_RESULTS.md`
- Identifier patterns de succès/échec

### **Étape 3 : Améliorer requêtes**
- Modifier `GET_AUTHOR_INDIVIDUAL_BOOKS` pour recherche élargie
- Ajouter logging détaillé pour debug
- Optimiser performances

---

## 📋 **CHECKLIST VALIDATION**

### **Backend**
- [ ] Endpoint test-individual-books fonctionnel
- [ ] Requêtes SPARQL optimisées
- [ ] Modèles de données complets
- [ ] Gestion erreurs robuste
- [ ] Cache et performance

### **Frontend**
- [ ] Modal auteur intègre livres individuels
- [ ] Hiérarchie sources respectée
- [ ] Affichage cohérent séries/livres
- [ ] États de chargement et erreurs
- [ ] Responsive design

### **Tests**
- [ ] 10 auteurs testés minimum
- [ ] Cas d'usage couverts
- [ ] Performance validée
- [ ] Fallbacks fonctionnels
- [ ] Documentation complète

---

## 🎯 **RÉSULTATS ATTENDUS**

### **Fonctionnalité finale**
- Modal auteur avec **séries ET livres individuels** depuis Wikidata
- Fallback intelligent vers Wikipedia/OpenLibrary
- Interface utilisateur cohérente et performante
- Documentation complète pour maintenance

### **Métriques de succès**
- **Couverture** : 80%+ auteurs trouvés (Wikidata + fallbacks)
- **Performance** : <3s chargement modal
- **UX** : Interface cohérente toutes sources
- **Maintenance** : Documentation complète

---

## 📅 **PLANNING ESTIMÉ**

- **Phase 1** : 30 minutes (tests et validation)
- **Phase 2** : 45 minutes (amélioration requêtes)
- **Phase 3** : 30 minutes (tests frontend)
- **Phase 4** : 15 minutes (documentation)

**TOTAL ESTIMÉ** : 2 heures

---

**📚 BOOKTIME WIKIDATA MODAL AUTEUR - PLAN DÉTAILLÉ COMPLET**  
**🎯 OBJECTIF : LIVRES INDIVIDUELS + SÉRIES INTÉGRÉS AVEC HIÉRARCHIE SOURCES OPTIMISÉE**  
**📋 DOCUMENTATION EXHAUSTIVE POUR CONTINUATION OPTIMALE**