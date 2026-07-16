# Booktime — backlog produit / recherche / sources

## Schéma des flux (sources de vérité)

```mermaid
flowchart LR
  subgraph Client
    UI[Recherche + grilles + modales]
  end
  subgraph API_lecture_JWT
    OL[Open Library /api/openlibrary]
    WDlive[Wikidata live /api/wikidata]
    WDstat[Wikidata statique /api/static-wikidata]
    GB[Google Books /api/google-books]
  end
  subgraph Legacy_compat
    IntGB[/api/integrations/google-books/*]
  end
  UI -->|JWT| OL
  UI -->|JWT| WDlive
  UI -->|JWT| WDstat
  UI -->|JWT| GB
  IntGB -.->|délègue au même moteur que GB| GB
```

- **Wikidata statique** : export local (`wikidata_series_db.json`) — recherche `title_index`, détail par QID, popularité. **JWT requis** (aligné Open Library).
- **Wikidata live** : SPARQL / service métier — volumes par nom de série dans la modale quand pas de fiche statique préchargée.
- **Open Library** : recherche globale, import, sagas.
- **Google Books** : **canonique** `GET /api/google-books/volumes`, `GET /api/google-books/volume/{id}`, `GET /api/google-books/isbn/{isbn}`. Les routes `GET /api/integrations/google-books/*` restent pour **compatibilité** mais appellent le même code serveur que le module `google_books`.

---

## Déjà réalisé (à jour)

1. **Fusion par tome (Open Library)**  
   Regroupement des éditions / langues du même tome dans les cartes série issues de la recherche OL (`mergeOpenLibraryBooksByVolume` + choix d’édition préférée FR / couverture). Même logique côté **liste des tomes** dans `SeriesDetailModal` pour les livres issus d’OL.

2. **Titres affichés en priorité « français »**  
   Champ `display_title` + `displayBookTitleFrFirst` (langue `fre` OL, heuristique accents, `title_fr` / `title_en` pour les œuvres Wikidata statiques dans la modale).

3. **Wikidata statique dans la recherche**  
   `GET /api/static-wikidata/series/search` sur la requête utilisateur ; repli `.../series/top/by-popularity`. Cartes `isStaticWikidataCard` ; clic → chargement `GET .../series/{qid}` → **SeriesDetailModal** (volumes depuis `works`, lien Wikidata, JSON brut optionnel).

4. **Ajout bibliothèque depuis la modale série**  
   Si **`mergedLibraryVolumes`** est fourni (liste fusionnée affichée : WD statique, WD live, ou OL seul), **`generateVolumesList`** l’utilise **en priorité** pour les titres / ordre des tomes, quel que soit `fromStaticWikidata`. La **couverture série** utilise la première couverture de ce snapshot quand elle existe. **Modal auteur** : ajout série depuis cartes OL envoie aussi **`mergedLibraryVolumes`** via `buildMergedLibraryVolumeRowsFromOlBooks` (`openLibraryBookDisplay.js`). **Page `/serie/...` (séries populaires)** : appel **`addSeriesToLibrary`** (`seriesLibraryService`) + **`enrichSeriesMetadata`** (description, couverture Open Library en repli), **`generateVolumesList`** + référentiel étendu, couverture API si présente. **Backend** : doublon série à l’insertion (`series_library_duplicate_query` sur `series_name` + repli `name` legacy) ; **`GET /api/library/series`** et **`POST /api/library/series`** (création + « déjà présent ») complètent **`name`** depuis **`series_name`** si le document n’a que le champ canonique. Sinon repli sur les **`works`** WD statique ou référentiel seul. Auteurs WD statique dérivés des œuvres si besoin (`SeriesActions.handleAddSeriesToLibrary`).

5. **Google Books unifié côté implémentation**  
   Service unique `app/google_books/service.py` ; le front **Intégrations** appelle directement `/api/google-books/*` ; les routes integrations Google Books sont des **wrappers** de compatibilité.

6. **Fusion WD > OL > GB (modale série)**  
   Liste des tomes : **WD statique** : merge OL + export local (`mergeStaticWdWorksWithOpenLibrary`), puis Google Books **ISBN** (6 requêtes max) puis repli **`intitle` + `inauthor`** si auteur connu (3 requêtes max), via `enrichVolumeRowsGoogleBooksIsbnThenIntitle`. **WD live** : mêmes étapes après `mapLiveWikidataVolumesToWorks` + OL + GB. Quotas partagés : `DEFAULT_SERIES_MODAL_GOOGLE_BOOKS` dans `searchSourcePipeline.js` (utilisé par `SeriesDetailModal`). Ajout bibliothèque : `mergedLibraryVolumes` (modale ou modal auteur). Tests front : `sourceMerge.test.js`, `seriesLibraryService.test.js`, `openLibraryBookDisplay.test.js`, `searchSourcePipeline.test.js` ; `npm run test:pipelines` ; backend : `pytest.ini` + `test_google_books_simplify.py`, `test_google_books_category_infer.py`, `test_static_wikidata_norm_title.py`, `test_series_library_helpers.py` (conftest sans import `motor` inutilisé).

7. **Recherche globale : priorité WD sur cartes OL en doublon**  
   Après agrégation OL + spotlight Wikidata statique, `dedupeWikidataStaticSeriesOverOpenLibrary` retire une carte série Open Library si une carte Wikidata partage le même couple (titre, auteur) normalisé (`normalizeTitleKey`). Catégorie spotlight : `inferCategoryFromWikidataSearchEntry` (mots-clés titre / type / auteur).

8. **Catégorisation Google Books (backend)**  
   `infer_book_category_from_google_item` : `roman` / `bd` / `manga` à partir des `categories` Google + titre / description ; utilisé par `simplified_volume_to_integration_book`. Champ `categories` ajouté à `simplify_item`.

9. **Nettoyage intégrations**  
   Fichier legacy `app/integrations/google_books_service.py` supprimé (aucun import actif) ; la santé du module intégrations indique toujours la délégation vers `app.google_books.service`.

---

## À faire (priorité)

_Rien de bloquant : les points ci-dessus sont traités dans le code. **Suite pytest** : `cd backend && python -m pytest tests/` (66 tests, client httpx `ASGITransport` + `pytest-asyncio` 0.24+). Améliorations possibles plus tard : migration Mongo systématique `name` → `series_name`, affinage des heuristiques catégorie (synonymes, QID Wikidata)._

---
_Document mis à jour pour refléter l’état du code (auth static Wikidata, bibliothèque WD, Google Books canonique)._
