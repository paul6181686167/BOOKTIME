"""
Module intégrations - APIs externes
==================================

Centralise l'accès aux services externes :
- AniList GraphQL API
- MangaUpdates scraping service
- ChapterPredictor ML algorithms
"""

from .anilist import AniListService
from .mangaupdates import MangaUpdatesService  
from .predictor import ChapterPredictor

__all__ = [
    "AniListService",
    "MangaUpdatesService", 
    "ChapterPredictor"
]