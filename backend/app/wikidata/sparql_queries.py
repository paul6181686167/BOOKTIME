"""
Requêtes SPARQL pour Wikidata
Requêtes structurées pour auteurs, séries et livres
"""

# Requête pour obtenir les séries d'un auteur (OPTIMISÉE - Performance)
GET_AUTHOR_SERIES = """
SELECT DISTINCT ?series ?seriesLabel ?genre ?genreLabel ?startDate ?endDate ?description WHERE {
  # Recherche élargie auteur par nom avec aliases
  ?author rdfs:label|skos:altLabel ?authorName .
  FILTER(CONTAINS(LCASE(?authorName), LCASE("%(author_name)s")))
  
  # Trouve les séries de cet auteur - REQUÊTE SIMPLIFIÉE
  ?series wdt:P31 wd:Q277759 .      # Instance de série de livres (type principal)
  ?series wdt:P50 ?author .         # Auteur
  
  # Informations essentielles seulement
  OPTIONAL { ?series wdt:P136 ?genre . }
  OPTIONAL { ?series wdt:P571 ?startDate . }
  OPTIONAL { ?series wdt:P582 ?endDate . }
  OPTIONAL { ?series schema:description ?description . FILTER(LANG(?description) = "fr" || LANG(?description) = "en") }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
ORDER BY ?seriesLabel
LIMIT 20
"""

# Requête pour obtenir les livres individuels d'un auteur (OPTIMISÉE - Performance)
GET_AUTHOR_INDIVIDUAL_BOOKS = """
SELECT DISTINCT ?book ?bookLabel ?pubDate ?genre ?genreLabel ?type ?typeLabel ?isbn ?publisher ?publisherLabel WHERE {
  # Recherche élargie auteur par nom avec aliases
  ?author rdfs:label|skos:altLabel ?authorName .
  FILTER(CONTAINS(LCASE(?authorName), LCASE("%(author_name)s")))
  
  # Trouve les livres individuels - REQUÊTE SIMPLIFIÉE
  ?book wdt:P31 wd:Q571 .          # Instance de livre (type principal)
  ?book wdt:P50 ?author .          # Auteur
  
  # Exclure les livres de série (optimisé)
  FILTER NOT EXISTS { ?book wdt:P179 ?series . }
  
  # Informations essentielles seulement
  OPTIONAL { ?book wdt:P577 ?pubDate . }
  OPTIONAL { ?book wdt:P136 ?genre . }
  OPTIONAL { ?book wdt:P212 ?isbn . }
  OPTIONAL { ?book wdt:P123 ?publisher . }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
ORDER BY DESC(?pubDate)
LIMIT 20
"""

# Requête pour obtenir les livres d'une série
GET_SERIES_BOOKS = """
SELECT DISTINCT ?book ?bookLabel ?volumeNumber ?pubDate ?genre ?genreLabel ?pages ?isbn ?publisher ?publisherLabel WHERE {
  # Livres de la série spécifiée
  ?book wdt:P179 wd:%(series_id)s .    # Partie de la série
  
  # Informations optionnelles
  OPTIONAL { ?book wdt:P1545 ?volumeNumber . }
  OPTIONAL { ?book wdt:P577 ?pubDate . }
  OPTIONAL { ?book wdt:P136 ?genre . }
  OPTIONAL { ?book wdt:P1104 ?pages . }
  OPTIONAL { ?book wdt:P212 ?isbn . }
  OPTIONAL { ?book wdt:P123 ?publisher . }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
ORDER BY ?volumeNumber ?pubDate
"""

# Requête pour obtenir les informations complètes d'un auteur
GET_AUTHOR_INFO = """
SELECT DISTINCT ?author ?authorLabel ?birthDate ?deathDate ?nationality ?nationalityLabel ?occupation ?occupationLabel ?genre ?genreLabel ?award ?awardLabel ?image ?wikipedia WHERE {
  # Recherche l'auteur par nom
  ?author rdfs:label ?authorLabel .
  FILTER(CONTAINS(LCASE(?authorLabel), LCASE("%(author_name)s")))
  
  # Vérifier que c'est bien un auteur
  ?author wdt:P106 ?occupation .
  FILTER(?occupation IN (wd:Q36180, wd:Q482980, wd:Q49757, wd:Q6625963, wd:Q214917, wd:Q4853732))
  # Q36180: écrivain, Q482980: auteur, Q49757: poète, Q6625963: romancier, Q214917: dramaturge, Q4853732: nouvelliste
  
  # Informations optionnelles
  OPTIONAL { ?author wdt:P569 ?birthDate . }
  OPTIONAL { ?author wdt:P570 ?deathDate . }
  OPTIONAL { ?author wdt:P27 ?nationality . }
  OPTIONAL { ?author wdt:P136 ?genre . }
  OPTIONAL { ?author wdt:P166 ?award . }
  OPTIONAL { ?author wdt:P18 ?image . }
  OPTIONAL { 
    ?wikipedia schema:about ?author .
    ?wikipedia schema:isPartOf <https://fr.wikipedia.org/> .
  }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
LIMIT 1
"""

# Requête pour rechercher des séries par nom
SEARCH_SERIES = """
SELECT DISTINCT ?series ?seriesLabel ?author ?authorLabel ?genre ?genreLabel ?startDate ?description WHERE {
  # Recherche série par nom
  ?series wdt:P31 wd:Q277759 .     # Instance de "série de livres"
  ?series rdfs:label ?seriesLabel .
  FILTER(CONTAINS(LCASE(?seriesLabel), LCASE("%(search_term)s")))
  
  # Auteur de la série
  ?series wdt:P50 ?author .
  
  # Informations optionnelles
  OPTIONAL { ?series wdt:P136 ?genre . }
  OPTIONAL { ?series wdt:P571 ?startDate . }
  OPTIONAL { ?series schema:description ?description . FILTER(LANG(?description) = "fr" || LANG(?description) = "en") }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
ORDER BY ?seriesLabel
LIMIT 20
"""

# Requête pour obtenir les informations d'une série spécifique
GET_SERIES_INFO = """
SELECT DISTINCT ?series ?seriesLabel ?author ?authorLabel ?genre ?genreLabel ?startDate ?endDate ?description ?bookCount WHERE {
  # Série spécifiée
  BIND(wd:%(series_id)s AS ?series)
  
  # Auteur
  ?series wdt:P50 ?author .
  
  # Informations optionnelles
  OPTIONAL { ?series wdt:P136 ?genre . }
  OPTIONAL { ?series wdt:P571 ?startDate . }
  OPTIONAL { ?series wdt:P582 ?endDate . }
  OPTIONAL { ?series schema:description ?description . FILTER(LANG(?description) = "fr" || LANG(?description) = "en") }
  
  # Compter les livres
  {
    SELECT ?series (COUNT(?book) as ?bookCount) WHERE {
      ?book wdt:P179 ?series .
    } GROUP BY ?series
  }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
"""

# Requête pour rechercher un auteur par nom exact
SEARCH_AUTHOR_EXACT = """
SELECT DISTINCT ?author ?authorLabel ?birthDate ?deathDate ?nationality ?nationalityLabel ?occupation ?occupationLabel ?seriesCount ?booksCount WHERE {
  # Recherche exacte par nom
  ?author rdfs:label "%(author_name)s"@fr .
  
  # Vérifier que c'est un auteur
  ?author wdt:P106 ?occupation .
  FILTER(?occupation IN (wd:Q36180, wd:Q482980, wd:Q49757, wd:Q6625963, wd:Q214917, wd:Q4853732))
  
  # Informations de base
  OPTIONAL { ?author wdt:P569 ?birthDate . }
  OPTIONAL { ?author wdt:P570 ?deathDate . }
  OPTIONAL { ?author wdt:P27 ?nationality . }
  
  # Compter les séries
  {
    SELECT ?author (COUNT(DISTINCT ?series) as ?seriesCount) WHERE {
      ?series wdt:P31 wd:Q277759 .
      ?series wdt:P50 ?author .
    } GROUP BY ?author
  }
  
  # Compter les livres
  {
    SELECT ?author (COUNT(DISTINCT ?book) as ?booksCount) WHERE {
      ?book wdt:P50 ?author .
      ?book wdt:P31 wd:Q571 .  # Instance de livre
    } GROUP BY ?author
  }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
LIMIT 1
"""

# Requête pour obtenir les séries populaires par genre
GET_POPULAR_SERIES = """
SELECT DISTINCT ?series ?seriesLabel ?author ?authorLabel ?genre ?genreLabel ?startDate ?bookCount WHERE {
  # Séries de livres
  ?series wdt:P31 wd:Q277759 .
  
  # Auteur
  ?series wdt:P50 ?author .
  
  # Filtrage par genre si spécifié
  %(genre_filter)s
  
  # Informations optionnelles
  OPTIONAL { ?series wdt:P136 ?genre . }
  OPTIONAL { ?series wdt:P571 ?startDate . }
  
  # Compter les livres pour popularité
  {
    SELECT ?series (COUNT(?book) as ?bookCount) WHERE {
      ?book wdt:P179 ?series .
    } GROUP BY ?series
  }
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
ORDER BY DESC(?bookCount)
LIMIT 30
"""

# Requête de test pour vérifier la connectivité
TEST_QUERY = """
SELECT ?series ?seriesLabel ?author ?authorLabel WHERE {
  ?series wdt:P31 wd:Q277759 .
  ?series wdt:P50 ?author .
  ?author rdfs:label ?authorLabel .
  FILTER(CONTAINS(LCASE(?authorLabel), "%(test_author)s"))
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
LIMIT 5
"""