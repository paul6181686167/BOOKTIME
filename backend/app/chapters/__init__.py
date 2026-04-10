"""
Chapters Module - Système de gestion des chapitres individuels
==============================================================

Ce module gère :
- Chapitres individuels de manga/webtoon
- Regroupement automatique chapitres → volumes
- Prédictions dates de sorties
- Intégrations APIs externes (AniList, MangaUpdates)

Créé dans le cadre de l'enrichissement des modals séries BOOKTIME.
"""

from .service import ChapterService
from .models import Chapter, Volume, SeriesChapters

__all__ = ["ChapterService", "Chapter", "Volume", "SeriesChapters"]