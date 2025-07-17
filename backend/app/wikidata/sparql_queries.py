"""
Requêtes SPARQL pour Wikidata
Requêtes structurées pour auteurs, séries et livres
"""

# Requête pour obtenir les séries d'un auteur (OPTIMISÉE - Performance)
# Requête pour trouver l'ID Wikidata d'un auteur par nom (SIMPLIFIÉE)
GET_AUTHOR_ID = """
SELECT DISTINCT ?author ?authorLabel WHERE {
  {
    ?author rdfs:label "%(author_name)s"@en .
  } UNION {
    ?author rdfs:label "%(author_name)s"@fr .
  } UNION {
    ?author rdfs:label "%(author_name_spaced)s"@en .
  } UNION {
    ?author rdfs:label "%(author_name_spaced)s"@fr .
  } UNION {
    ?author rdfs:label "%(author_name_nospace)s"@en .
  } UNION {
    ?author rdfs:label "%(author_name_nospace)s"@fr .
  }
  
  # Vérifier que c'est bien un auteur
  ?author wdt:P106 ?occupation .
  FILTER(?occupation IN (wd:Q36180, wd:Q482980, wd:Q49757, wd:Q6625963, wd:Q214917, wd:Q4853732))
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
LIMIT 1
"""

# Requête pour obtenir les séries d'un auteur par son ID Wikidata
GET_AUTHOR_SERIES_BY_ID = """
SELECT DISTINCT ?series ?seriesLabel ?genre ?genreLabel ?startDate ?endDate ?description WHERE {
  BIND(wd:%(author_id)s AS ?author)
  
  # Trouve les séries de cet auteur - REQUÊTE ÉLARGIE POUR INCLURE TOUS TYPES SÉRIES
  ?series wdt:P31 ?seriesType .     # Instance de différents types de séries
  FILTER(?seriesType IN (wd:Q277759, wd:Q47068459, wd:Q1667921, wd:Q614101, wd:Q53815))
  # Q277759: série de livres, Q47068459: children's book series, Q1667921: suite romanesque, Q614101: heptalogie, Q53815: canon
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

# Requête pour obtenir les séries d'un auteur (MÉTHODE HYBRIDE)
GET_AUTHOR_SERIES = """
SELECT DISTINCT ?series ?seriesLabel ?genre ?genreLabel ?startDate ?endDate ?description WHERE {
  # Recherche élargie auteur par nom avec aliases et variantes
  ?author rdfs:label|skos:altLabel ?authorName .
  FILTER(
    CONTAINS(LCASE(?authorName), LCASE("%(author_name)s")) ||
    CONTAINS(LCASE(?authorName), LCASE("%(author_name_spaced)s")) ||
    CONTAINS(LCASE(?authorName), LCASE("%(author_name_nospace)s"))
  )
  
  # Vérifier que c'est bien un auteur
  ?author wdt:P106 ?occupation .
  FILTER(?occupation IN (wd:Q36180, wd:Q482980, wd:Q49757, wd:Q6625963, wd:Q214917, wd:Q4853732))
  
  # Trouve les séries de cet auteur - REQUÊTE ÉLARGIE POUR INCLURE TOUS TYPES SÉRIES
  ?series wdt:P31 ?seriesType .     # Instance de différents types de séries
  FILTER(?seriesType IN (wd:Q277759, wd:Q47068459, wd:Q1667921, wd:Q614101, wd:Q53815))
  # Q277759: série de livres, Q47068459: children's book series, Q1667921: suite romanesque, Q614101: heptalogie, Q53815: canon
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
  
  # Trouve les livres individuels - SOLUTION UTILISATEUR VALIDÉE
  ?book wdt:P50 ?author .          # Auteur
  ?book wdt:P31 ?type .
  
  # Types d'œuvres élargis - SOLUTION EXACTE DE L'UTILISATEUR
  FILTER(?type IN (wd:Q7725634, wd:Q571, wd:Q47461344, wd:Q8261))
  
  # Exclure les livres de série
  FILTER NOT EXISTS { ?book wdt:P179 ?series . }
  
  # Informations essentielles
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
  # Recherche série par nom - REQUÊTE ÉLARGIE
  ?series wdt:P31 ?seriesType .     # Instance de différents types de séries
  FILTER(?seriesType IN (wd:Q277759, wd:Q47068459, wd:Q1667921, wd:Q614101, wd:Q53815))
  # Q277759: série de livres, Q47068459: children's book series, Q1667921: suite romanesque, Q614101: heptalogie, Q53815: canon
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
  
  # Compter les séries - REQUÊTE ÉLARGIE
  {
    SELECT ?author (COUNT(DISTINCT ?series) as ?seriesCount) WHERE {
      ?series wdt:P31 ?seriesType .
      FILTER(?seriesType IN (wd:Q277759, wd:Q47068459, wd:Q1667921, wd:Q614101, wd:Q53815))
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
  # Séries de livres - REQUÊTE ÉLARGIE
  ?series wdt:P31 ?seriesType .
  FILTER(?seriesType IN (wd:Q277759, wd:Q47068459, wd:Q1667921, wd:Q614101, wd:Q53815))
  # Q277759: série de livres, Q47068459: children's book series, Q1667921: suite romanesque, Q614101: heptalogie, Q53815: canon
  
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

# Requête de test pour vérifier la connectivité (OPTIMISÉE)
TEST_QUERY = """
SELECT ?series ?seriesLabel ?author ?authorLabel WHERE {
  # Recherche élargie avec aliases
  ?author rdfs:label|skos:altLabel ?authorName .
  FILTER(CONTAINS(LCASE(?authorName), "%(test_author)s"))
  
  # Séries de livres seulement - REQUÊTE ÉLARGIE
  ?series wdt:P31 ?seriesType .
  FILTER(?seriesType IN (wd:Q277759, wd:Q47068459, wd:Q1667921, wd:Q614101, wd:Q53815))
  # Q277759: série de livres, Q47068459: children's book series, Q1667921: suite romanesque, Q614101: heptalogie, Q53815: canon
  ?series wdt:P50 ?author .
  
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fr,en" . }
}
LIMIT 5
"""