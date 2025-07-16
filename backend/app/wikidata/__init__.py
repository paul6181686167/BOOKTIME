"""
Module Wikidata pour BOOKTIME
Intégration SPARQL pour détection native des séries et métadonnées structurées
"""

from .routes import router
from .service import WikidataService
from .models import WikidataAuthor, WikidataSeries, WikidataBook

__all__ = [
    'router',
    'WikidataService',
    'WikidataAuthor',
    'WikidataSeries', 
    'WikidataBook'
]